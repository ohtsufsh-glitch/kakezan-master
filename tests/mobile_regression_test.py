"""PR-4: Chromium viewport checks; these do not certify physical Safari devices."""
import json
from pathlib import Path
import unittest

from playwright.sync_api import expect
import progress_cards_test as progress

CAPTURES = Path('/tmp/kakezan-pr4-review')
SIZES = [(320, 568), (568, 320), (375, 667), (667, 375), (390, 844),
         (844, 390), (768, 1024), (1024, 768), (820, 1180),
         (1180, 820), (507, 768), (320, 1024)]


class MobileRegressionTest(unittest.TestCase):
    setUpClass = classmethod(progress.ProgressCardsTest.setUpClass.__func__)
    tearDownClass = classmethod(progress.ProgressCardsTest.tearDownClass.__func__)
    setUp = progress.ProgressCardsTest.setUp
    tearDown = progress.ProgressCardsTest.tearDown
    ready = progress.ProgressCardsTest.ready
    seed = progress.ProgressCardsTest.seed
    answer = progress.ProgressCardsTest.answer

    def capture(self, name):
        CAPTURES.mkdir(exist_ok=True)
        self.page.screenshot(path=str(CAPTURES / f'{name}.png'), full_page=True)
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'), name)

    def test_learning_home_report_and_games_across_viewports(self):
        metrics = []
        for width, height in SIZES:
            with self.subTest(size=(width, height)):
                self.page.set_viewport_size(dict(width=width, height=height))
                self.page.evaluate('navigateHome()')
                self.assertEqual(self.page.locator('#radar-chart line').count(), 9)
                self.capture(f'home-{width}x{height}')
                self.page.evaluate('startEra("T03")')
                if self.page.evaluate('phase') == 'result':
                    self.page.locator('#next').click()
                self.page.wait_for_function('quizReady&&phase==="question"')
                sizes = self.page.locator('.numeric-keypad button').evaluate_all(
                    'bs=>bs.map(b=>{const r=b.getBoundingClientRect();return [r.width,r.height]})')
                self.assertEqual(len(sizes), 11)
                self.assertTrue(all(w >= 44 and h >= 44 for w, h in sizes))
                self.assertEqual(self.page.locator('#numeric-answer').get_attribute('aria-live'), 'polite')
                self.capture(f'quiz-{width}x{height}')
                self.answer(False)
                self.capture(f'result-{width}x{height}')
                self.page.evaluate('navigate("admin")')
                if not self.page.locator('#learning-report').evaluate('el=>el.open'):
                    self.page.locator('#learning-report > summary').click()
                expect(self.page.locator('#learning-report')).to_have_js_property('open', True)
                expect(self.page.locator('#report-list > section')).to_have_count(81)
                self.assertTrue(self.page.locator('#admin-questions-group').is_hidden())
                self.capture(f'report-{width}x{height}')
                self.page.evaluate('openArcade()')
                self.capture(f'crane-{width}x{height}')
                self.page.evaluate('navigate("runner")')
                expect(self.page.locator('#runner iframe')).to_be_visible()
                self.page.frame_locator('iframe').locator('#runner-toggle').wait_for()
                self.capture(f'runner-{width}x{height}')
                metrics.append(dict(width=width, height=height, keys=sizes))
        (CAPTURES / 'metrics.json').write_text(json.dumps(metrics, indent=2))
        self.assertEqual(self.errors, [])

    def test_dynamic_height_text_enlargement_and_dialog_keyboard(self):
        self.seed(count=81)
        self.page.evaluate('ensureEarnedCards()')
        self.page.set_viewport_size(dict(width=390, height=844))
        self.page.evaluate('navigateHome()')
        for height in [664, 844, 600]:
            self.page.set_viewport_size(dict(width=390, height=height))
            self.page.locator('#card-gallery button').last.focus()
            self.page.keyboard.press('Enter')
            dialog = self.page.locator('#card-detail-dialog')
            expect(dialog).to_be_visible()
            self.assertTrue(dialog.evaluate('d=>d.scrollWidth<=d.clientWidth'))
            self.capture(f'dynamic-dialog-{height}')
            self.page.keyboard.press('Escape')
            expect(dialog).not_to_be_visible()
            expect(self.page.locator('#card-gallery button').last).to_be_focused()
        # CSS text enlargement is a reproducible stress check, not iOS text settings.
        self.page.add_style_tag(content='html {font-size:200% !important}')
        for width, height in [(320, 568), (667, 375), (507, 768), (1024, 768)]:
            self.page.set_viewport_size(dict(width=width, height=height))
            self.page.evaluate('navigateHome()')
            self.capture(f'text200-home-{width}')
            self.page.evaluate('navigate("admin")')
            if not self.page.locator('#learning-report').evaluate('el=>el.open'):
                self.page.locator('#learning-report > summary').click()
            expect(self.page.locator('#learning-report')).to_have_js_property('open', True)
            self.capture(f'text200-report-{width}')
            self.page.evaluate('startEra("T01")')
            self.page.wait_for_function('quizReady')
            self.capture(f'text200-quiz-{width}')
        self.assertEqual(self.errors, [])


if __name__ == '__main__':
    unittest.main()
