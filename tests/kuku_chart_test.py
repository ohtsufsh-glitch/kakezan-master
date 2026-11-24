"""九九ひょうの閲覧だけを検査。Chromium再現でありSafari実機確認ではない。"""
import hashlib
import json
from pathlib import Path
import unittest

from playwright.sync_api import expect
import app_isolation_test as isolation
from mobile_regression_test import SIZES

ROOT = Path(__file__).resolve().parents[1]
CAPTURES = Path('/tmp/kakezan-kuku-review')
SHA256 = 'c4ffd8a6cf4ea01bb3a7a1c389b7a75250a8d1f8a311ba9b8ea3805d8044ef42'


class KukuChartTest(unittest.TestCase):
    setUpClass = classmethod(isolation.AppIsolationTest.setUpClass.__func__)
    tearDownClass = classmethod(isolation.AppIsolationTest.tearDownClass.__func__)
    ready = isolation.AppIsolationTest.ready
    tearDown = isolation.AppIsolationTest.tearDown

    def setUp(self):
        self.context = self.browser.new_context(viewport=dict(width=768, height=1024), has_touch=True)
        self.page = self.context.new_page()
        self.page.set_default_timeout(7000)
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.on('dialog', lambda d: d.accept())
        self.page.goto(self.url)
        self.ready()
        self.opener = self.page.locator('#open-kuku-chart')
        self.dialog = self.page.get_by_role('dialog', name='九九ひょう', exact=True)
        self.close = self.page.get_by_role('button', name='とじる', exact=True)

    def open_chart(self):
        self.opener.tap()
        expect(self.dialog).to_be_visible()
        self.page.locator('#kuku-chart-image').evaluate('img=>img.decode()')

    def geometry(self):
        return self.page.evaluate('''() => {
          const rect=id=>{const r=document.getElementById(id).getBoundingClientRect();
            return {x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom};};
          const image=document.getElementById('kuku-chart-image'),i=rect('kuku-chart-image');
          const scale=Math.min(i.w/image.naturalWidth,i.h/image.naturalHeight);
          return {dialog:rect('kuku-chart-dialog'),close:rect('kuku-chart-close'),image:i,
            painted:{w:scale*image.naturalWidth,h:scale*image.naturalHeight},
            fit:getComputedStyle(image).objectFit,
            overflow:document.documentElement.scrollWidth>innerWidth};
        }''')

    def assert_layout(self, width, height):
        g = self.geometry()
        for key in ['dialog', 'close', 'image']:
            r = g[key]
            self.assertGreater(r['w'], 0)
            self.assertGreater(r['h'], 0)
            self.assertGreaterEqual(r['x'], -0.1)
            self.assertGreaterEqual(r['y'], -0.1)
            self.assertLessEqual(r['right'], width + 0.1)
            self.assertLessEqual(r['bottom'], height + 0.1)
        self.assertGreaterEqual(g['close']['w'], 44)
        self.assertGreaterEqual(g['close']['h'], 44)
        self.assertLessEqual(g['close']['bottom'], g['image']['y'])
        self.assertEqual(g['fit'], 'contain')
        self.assertAlmostEqual(g['painted']['w']/g['painted']['h'], 3/4)
        self.assertFalse(g['overflow'])
        self.assertTrue(self.dialog.evaluate('d=>d.scrollWidth<=d.clientWidth && d.scrollHeight<=d.clientHeight'))
        return g

    def test_provided_asset_and_all_81_text_alternatives(self):
        self.assertEqual(hashlib.sha256((ROOT/'assets/kuku/kuku-chart.webp').read_bytes()).hexdigest(), SHA256)
        rows = json.loads((ROOT/'docs/kuku_readings_verified.json').read_text())
        self.assertEqual(len(rows), 81)
        self.assertEqual(len({r['id'] for r in rows}), 81)
        self.assertEqual({(r['a'], r['b']) for r in rows}, {(a,b) for a in range(1,10) for b in range(1,10)})
        for r in rows:
            self.assertEqual(r['answer'], r['a'] * r['b'])
            self.assertEqual(r['expression'], f"{r['a']}×{r['b']}={r['answer']}")
            self.assertEqual(''.join(r['display_lines']), r['reading'])
        self.open_chart()
        image = self.page.locator('#kuku-chart-image')
        self.assertEqual(image.evaluate('i=>[i.naturalWidth,i.naturalHeight]'), [2172,2896])
        self.assertEqual(image.get_attribute('src'), 'assets/kuku/kuku-chart.webp')
        response = self.page.request.get(self.url.replace('index.html', 'assets/kuku/kuku-chart.webp'))
        self.assertEqual(response.status, 200)
        self.assertEqual(hashlib.sha256(response.body()).hexdigest(), SHA256)
        self.assertIn('九九ひょう', image.get_attribute('alt'))
        self.assertEqual(self.page.locator('#kuku-chart-readings li').all_text_contents(),
                         [f"{r['a']} × {r['b']} = {r['answer']}。{r['reading']}" for r in rows])
        snapshot = self.dialog.aria_snapshot()
        self.assertIn('heading "1の段"', snapshot)
        self.assertIn('heading "9の段"', snapshot)
        for r in rows:
            self.assertIn(r['reading'], snapshot)

    def test_touch_close_focus_and_all_stores_unchanged(self):
        self.page.evaluate("plushInstall(plushFixture(['shiba'],'student'))")
        for who in ['student', 'test']:
            self.page.evaluate('navigateHome', who)
            expect(self.opener).to_be_visible()
            bounds = self.opener.bounding_box()
            self.assertGreaterEqual(bounds['width'], 44)
            self.assertGreaterEqual(bounds['height'], 44)
            self.assertLessEqual(bounds['y'] + bounds['height'],
                                 self.page.locator('#dashboard').bounding_box()['y'])
            before = self.page.evaluate('snapshotAllStores()')
            state = self.page.evaluate('[history.state,profile,phase,currentQuestion,arcadePlay,arcadeBusy]')
            catalog = self.page.evaluate('QUESTIONS')
            self.open_chart()
            expect(self.close).to_be_focused()
            self.assertEqual(self.page.evaluate('snapshotAllStores()'), before)
            self.close.tap()
            expect(self.dialog).not_to_be_visible()
            expect(self.opener).to_be_focused()
            self.assertEqual(self.page.evaluate('snapshotAllStores()'), before)
            self.assertEqual(self.page.evaluate('[history.state,profile,phase,currentQuestion,arcadePlay,arcadeBusy]'), state)
            self.assertEqual(self.page.evaluate('QUESTIONS'), catalog)
            self.assertEqual(self.page.evaluate('[DB_VERSION,BACKUP_VERSION,db.objectStoreNames.length]'), [12,12,17])

    def test_keyboard_modal_scroll_and_route_cleanup(self):
        self.opener.focus()
        self.page.evaluate('window.scrollTo(0,80)')
        scroll = self.page.evaluate('scrollY')
        for key in ['Enter', 'Space']:
            self.opener.press(key)
            expect(self.dialog).to_be_visible()
            expect(self.close).to_be_focused()
            # Native modality must keep background controls out of the tab order.
            for keypress in ['Tab', 'Tab', 'Shift+Tab']:
                self.page.keyboard.press(keypress)
                self.assertFalse(self.page.evaluate('document.activeElement.closest("#home,header")!==null'))
            self.page.keyboard.press('Escape')
            expect(self.dialog).not_to_be_visible()
            expect(self.opener).to_be_focused()
            self.assertEqual(self.page.evaluate('scrollY'), scroll)
            self.assertFalse(self.page.locator('body').evaluate('b=>b.classList.contains("kuku-chart-open")'))
        self.open_chart()
        self.page.evaluate('navigate("admin")')
        expect(self.dialog).not_to_be_visible()
        expect(self.page.locator('#admin')).to_be_visible()
        self.assertFalse(self.page.locator('body').evaluate('b=>b.classList.contains("kuku-chart-open")'))

    def test_viewports_rotation_dynamic_height_and_text_enlargement(self):
        CAPTURES.mkdir(exist_ok=True)
        self.open_chart()
        metrics = []
        # Resize while open also checks rotation and changing available browser height.
        for width, height in [*SIZES, (768,900), (768,1024), (390,664), (390,844)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size(dict(width=width,height=height))
                g = self.assert_layout(width,height)
                metrics.append(dict(width=width,height=height,**g))
                if (width,height)==(768,1024):
                    self.assertGreaterEqual(g['dialog']['w']/width, .94)
                    self.assertGreaterEqual(g['dialog']['h']/height, .94)
                    self.assertGreaterEqual(g['painted']['h']/height, .88)
                    self.page.screenshot(path=str(CAPTURES/'ipad-portrait-768x1024.png'))
        self.page.add_style_tag(content='html {font-size:200% !important}')
        for width,height in [(320,568),(568,320),(507,768),(1024,768)]:
            self.page.set_viewport_size(dict(width=width,height=height))
            self.assert_layout(width,height)
        (CAPTURES/'metrics.json').write_text(json.dumps(metrics,indent=2))
        self.close.tap()
        expect(self.opener).to_be_focused()

    def test_learning_starts_normally_after_close(self):
        self.open_chart()
        self.close.tap()
        self.page.locator('#era-list button').nth(2).tap()
        self.page.wait_for_function('quizReady && phase==="question"')
        expect(self.page.locator('#quiz')).to_be_visible()
        expect(self.page.locator('#numeric-answer')).to_have_text('—')
        self.page.get_by_role('button', name='1', exact=True).tap()
        expect(self.page.locator('#numeric-answer')).to_have_text('1')
        expect(self.page.locator('#check')).to_be_enabled()
        self.page.locator('#back-home').tap()
        expect(self.opener).to_be_visible()
        self.open_chart()
        self.page.keyboard.press('Escape')
        expect(self.opener).to_be_focused()


if __name__ == '__main__':
    unittest.main()
