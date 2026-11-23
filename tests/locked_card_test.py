"""PR-3 replaces historical art tests with temporary, image-free achievement cards."""
import unittest
import progress_cards_test as progress

class LockedCardTest(unittest.TestCase):
    setUpClass=classmethod(progress.ProgressCardsTest.setUpClass.__func__)
    tearDownClass=classmethod(progress.ProgressCardsTest.tearDownClass.__func__)
    setUp=progress.ProgressCardsTest.setUp
    tearDown=progress.ProgressCardsTest.tearDown
    ready=progress.ProgressCardsTest.ready
    seed=progress.ProgressCardsTest.seed
    snapshot=progress.ProgressCardsTest.snapshot

    def test_placeholder_cards_never_request_historical_images(self):
        requests=[]
        self.page.on('request',lambda r:requests.append(r.url))
        self.page.reload();self.ready()
        self.assertEqual(self.page.locator('#card-gallery .locked').count(),10)
        self.assertEqual(self.page.locator('#card-gallery img').count(),0)
        self.assertEqual(self.page.locator('#card-gallery button').count(),0)
        self.assertEqual(self.page.locator('#card-gallery .complete-card').count(),1)
        before=self.snapshot()
        for card in self.page.locator('#card-gallery .trophy').all():
            self.assertIn('制作待ち',card.inner_text())
            self.assertIn('習得あと',card.inner_text())
            card.click()
            self.assertFalse(self.page.locator('#card-detail-dialog').evaluate('d=>d.open'))
        self.assertEqual(self.snapshot(),before)
        self.assertFalse(any('/assets/cards/' in url for url in requests))

    def test_owned_detail_close_and_independent_profiles(self):
        self.seed(count=9);self.seed(count=18,who='test');self.page.evaluate('ensureEarnedCards()')
        for who,count in [('student',1),('test',2)]:
            self.page.evaluate('who=>navigateHome(who)',who)
            self.assertEqual(self.page.locator('#card-gallery button').count(),count)
            for width in [375,768]:
                self.page.set_viewport_size(dict(width=width,height=1024))
                self.page.locator('#card-gallery button').first.click()
                dialog=self.page.locator('#card-detail-dialog')
                self.assertTrue(dialog.evaluate('d=>d.open'))
                self.assertIn('獲得済み',dialog.inner_text())
                self.assertIn('制作待ち',dialog.inner_text())
                bounds=dialog.bounding_box()
                self.assertGreaterEqual(bounds['x'],0)
                self.assertLessEqual(bounds['x']+bounds['width'],width+1)
                self.page.locator('#card-detail-close').click()
                self.assertFalse(dialog.evaluate('d=>d.open'))

    def test_admin_previews_ten_without_awarding(self):
        before=self.snapshot()
        self.page.evaluate('navigate("admin")')
        self.page.locator('#admin-other-group > summary').click()
        self.page.locator('#card-preview-panel > summary').click()
        self.page.wait_for_function('document.querySelectorAll("#admin-card-preview button").length===10')
        for card in self.page.locator('#admin-card-preview button').all():
            card.click()
            self.assertIn('獲得状況は変更されません',self.page.locator('#card-detail-dialog').inner_text())
            self.page.locator('#card-detail-close').click()
        self.assertEqual(self.snapshot(),before)
