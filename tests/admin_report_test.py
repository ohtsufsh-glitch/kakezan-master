"""Admin order/disclosure regression; ephemeral synthetic data, not Safari certification."""
import unittest

from playwright.sync_api import expect
import app_isolation_test as isolation
from mobile_regression_test import SIZES


class AdminReportTest(unittest.TestCase):
    setUpClass = classmethod(isolation.AppIsolationTest.setUpClass.__func__)
    tearDownClass = classmethod(isolation.AppIsolationTest.tearDownClass.__func__)
    tearDown = isolation.AppIsolationTest.tearDown
    ready = isolation.AppIsolationTest.ready

    def setUp(self):
        self.context = self.browser.new_context(viewport=dict(width=390, height=844), has_touch=True)
        self.page = self.context.new_page()
        self.page.set_default_timeout(7000)
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.dialogs = []
        self.page.on('dialog', lambda d: (self.dialogs.append(d.message), d.accept()))
        self.page.goto(self.url)
        self.ready()
        self.page.evaluate("plushInstall(plushFixture(['shiba'],'student'))")
        self.before = self.page.evaluate('snapshotAllStores()')
        self.page.locator('#open-admin').tap()
        expect(self.page.locator('#admin')).to_be_visible()
        self.report = self.page.locator('#learning-report')
        self.summary = self.page.locator('#learning-report > summary')

    def assert_unchanged(self):
        self.assertEqual(self.page.evaluate('snapshotAllStores()'), self.before)
        self.assertEqual(self.page.evaluate('[DB_VERSION,BACKUP_VERSION,db.objectStoreNames.length]'), [12, 12, 17])

    def test_initial_order_closed_report_and_other_controls(self):
        self.assertEqual(self.page.locator('#admin > .admin-test-area, #admin > details:not([hidden])')
                         .evaluate_all('els=>els.map(el=>el.id||el.className)'),
                         ['admin-test-area', 'learning-report', 'answer-history',
                          'admin-backup-group', 'admin-other-group'])
        expect(self.report).to_have_js_property('open', False)
        expect(self.page.locator('#report-profile')).not_to_be_visible()
        expect(self.page.locator('#admin-start-test')).to_have_text('テストモードを開始（問題・クレーン）')
        expect(self.page.locator('.admin-test-area p')).to_have_text(
            'テストモードで解いた結果・コイン・クレーン景品は娘さん用に反映されません。'
            'クレーンは残高0枚でも無料で何度でも遊べます。問題データ自体は共通です。')
        self.page.locator('#answer-history > summary').tap()
        expect(self.page.locator('#answer-history-list')).to_contain_text('合成データの動作確認です。')
        self.page.locator('#admin-backup-group > summary').tap()
        self.page.locator('#toggle-backup').tap()
        expect(self.page.locator('#backup-export')).to_be_visible()
        self.page.locator('#admin-other-group > summary').tap()
        self.page.locator('#toggle-reset').tap()
        expect(self.page.locator('#reset-apply')).to_be_disabled()
        expect(self.report).to_have_js_property('open', False)
        self.assert_unchanged()

    def test_touch_keyboard_redraw_and_navigation_preserve_user_choice(self):
        expect(self.report).to_have_js_property('open', False)
        for opened in [True, False]:
            self.summary.tap()
            expect(self.report).to_have_js_property('open', opened)
            if opened:
                expect(self.page.locator('#report-list > section')).to_have_count(81)
                expect(self.page.locator('#report-list > section').last).to_be_visible()
            # These are existing asynchronous refresh/navigation paths, not DOM mocks.
            self.page.evaluate('renderLearningReport()')
            self.page.evaluate('refreshDashboardStay()')
            self.page.evaluate('reconcilePage()')
            expect(self.report).to_have_js_property('open', opened)
            self.page.locator('#admin-back').tap()
            self.page.locator('#open-admin').tap()
            expect(self.report).to_have_js_property('open', opened)
        self.summary.focus()
        self.summary.press('Enter')
        expect(self.report).to_have_js_property('open', True)
        expect(self.summary).to_be_focused()
        self.summary.press('Tab')
        expect(self.page.locator('#report-profile')).to_be_focused()
        self.summary.focus()
        self.summary.press('Space')
        expect(self.report).to_have_js_property('open', False)
        expect(self.summary).to_be_focused()
        self.assert_unchanged()

    def test_test_mode_start_return_and_closed_report_do_not_write(self):
        self.page.locator('#admin-start-test').tap()
        expect(self.page.locator('#home')).to_be_visible()
        self.assertEqual(self.page.evaluate('profile'), 'test')
        self.assertEqual(len(self.dialogs), 1)
        self.page.locator('#test-return-admin').tap()
        expect(self.page.locator('#admin')).to_be_visible()
        expect(self.report).to_have_js_property('open', False)
        self.page.locator('#admin-back').tap()
        expect(self.page.locator('#home')).to_be_visible()
        self.assertEqual(self.page.evaluate('profile'), 'student')
        self.assert_unchanged()

    def test_closed_and_open_layout_at_phone_tablet_and_enlarged_text_sizes(self):
        for text_size in [100, 200]:
            self.page.evaluate('size=>document.documentElement.style.fontSize=size+"%"', text_size)
            for width, height in SIZES:
                for opened in [False, True]:
                    with self.subTest(text_size=text_size, size=(width, height), opened=opened):
                        self.page.set_viewport_size(dict(width=width, height=height))
                        if self.report.evaluate('el=>el.open') != opened:
                            self.summary.tap()
                        expect(self.report).to_have_js_property('open', opened)
                        if opened:
                            expect(self.page.locator('#report-list > section')).to_have_count(81)
                        geometry = self.page.evaluate('''()=>{
                          const rect=s=>document.querySelector(s).getBoundingClientRect();
                          const test=rect('.admin-test-area'),report=rect('#learning-report'),history=rect('#answer-history');
                          const targets=[...document.querySelectorAll('#admin-start-test,#learning-report > summary,#learning-report select')]
                            .filter(el=>el.checkVisibility()).map(el=>el.getBoundingClientRect());
                          return {ordered:test.bottom<=report.top&&report.bottom<=history.top,
                            fits:document.documentElement.scrollWidth<=innerWidth&&targets.every(r=>r.left>=0&&r.right<=innerWidth),
                            touch:targets.every(r=>r.width>=44&&r.height>=44)};
                        }''')
                        self.assertEqual(geometry, dict(ordered=True, fits=True, touch=True))
        self.assert_unchanged()


if __name__ == '__main__':
    unittest.main()
