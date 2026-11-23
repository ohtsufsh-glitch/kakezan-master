"""PR-5: canonical WebP, locked network privacy and actual image UI checks."""
import hashlib
from pathlib import Path
import unittest
from playwright.sync_api import expect
import progress_cards_test as progress

ROOT = Path(__file__).resolve().parents[1]
IDS = [f'T{i:02}' for i in range(1,10)] + ['ALL81']
# SHA-256 of the user's approved ZIP entries, not regenerated images.
HASHES = {'ALL81': '4eea6fece6e855c9289f5c6243a71d26f5dc93badc5810deeb8c3bb48df1890f', 'T01': 'df0a3a72718051b39fe593a863fb9cdf3097ee4e5f9d889d6c031f1038cf59fc', 'T02': '0ccb5865cd0d0ac7f720a57f84f795727b9d8651df5dd60480fad6b4019ba3e9', 'T03': 'de052f5883579c7ebbda6180207aa41de846d728950c998d546b45ca3744808a', 'T04': '570b4b3a8421305cbff58e4cc4f001c4e579ff16232d7ff823e90e9150d13429', 'T05': '5ea7ae1faca5d6e645b9e5e0365c223a63f2ae995b708ecc63be565ac02b65c4', 'T06': '2cff7229ef135bd968951140ce11666e1c7464bd09de65ebcc6f5b7db791dbf5', 'T07': '0ea881c8cf43b43854c6ff9adf5b25418dafd08056448ffb64a60cd69cacfdcf', 'T08': '9e0499e0deb85d8d5acd58eee924c2abc564a9f10aea4fd832e1549d80294e6a', 'T09': '9b125c3b95f547fcbdd119c1172ad6afb8c77ca53e63cfc62478d666274eff4e'}
CAPTURES = Path('/tmp/kakezan-pr5-review')

class LockedCardTest(unittest.TestCase):
    setUpClass=classmethod(progress.ProgressCardsTest.setUpClass.__func__)
    tearDownClass=classmethod(progress.ProgressCardsTest.tearDownClass.__func__)
    setUp=progress.ProgressCardsTest.setUp
    tearDown=progress.ProgressCardsTest.tearDown
    ready=progress.ProgressCardsTest.ready
    seed=progress.ProgressCardsTest.seed
    snapshot=progress.ProgressCardsTest.snapshot
    question=progress.ProgressCardsTest.question
    answer=progress.ProgressCardsTest.answer

    def image(self, selector, card_id):
        img=self.page.locator(selector)
        expect(img).to_have_attribute('src',f'assets/cards/{card_id}.webp')
        img.evaluate('i=>i.decode()')
        self.assertEqual(img.evaluate('i=>[i.naturalWidth,i.naturalHeight]'),[1086,1448])
        self.assertEqual(img.get_attribute('alt'),'')
        self.assertEqual(img.evaluate('i=>getComputedStyle(i).objectFit'),'contain')
        box=img.bounding_box()
        self.assertAlmostEqual(box['width']/box['height'],3/4,delta=.002)
        self.assertEqual(self.page.locator('.card-art-top,.card-art-bottom').count(),0)

    def preview(self):
        self.page.evaluate('navigate("admin")')
        self.page.locator('#admin-other-group > summary').click()
        self.page.locator('#card-preview-panel > summary').click()
        expect(self.page.locator('#admin-card-preview button')).to_have_count(10)

    def test_canonical_files_format_and_all_ten_decode(self):
        for card_id in IDS:
            data=(ROOT/'assets/cards'/f'{card_id}.webp').read_bytes()
            self.assertEqual(data[:4],b'RIFF')
            self.assertEqual(data[8:12],b'WEBP')
            self.assertEqual(hashlib.sha256(data).hexdigest(),HASHES[card_id])
        self.preview()
        for i,card_id in enumerate(IDS):
            self.image(f'#admin-card-preview button:nth-child({i+1}) img',card_id)
        self.assertEqual(self.errors,[])

    def test_unowned_never_request_faces_in_learning_screens(self):
        requests=[]
        self.page.on('request',lambda r:requests.append(r.url))
        self.page.reload();self.ready()
        self.assertEqual(self.page.locator('#card-gallery .locked').count(),10)
        self.assertEqual(self.page.locator('#card-gallery img,#card-gallery button').count(),0)
        before=self.snapshot()
        for card in self.page.locator('#card-gallery .trophy').all():
            self.assertIn('習得あと',card.inner_text())
            card.click()
            self.assertFalse(self.page.locator('#card-detail-dialog').evaluate('d=>d.open'))
        self.assertEqual(self.snapshot(),before)
        self.page.evaluate('startEra("T01")');self.page.wait_for_function('quizReady')
        self.page.evaluate('navigateHome("test")')
        self.page.evaluate('startStudy("mix")');self.page.wait_for_function('quizReady')
        self.page.evaluate('navigateHome("student")')
        self.assertEqual(self.page.locator('img[src*="assets/cards/"]').count(),0)
        self.assertFalse(any('/assets/cards/' in url for url in requests),requests)

    def test_owned_mapping_profiles_details_keyboard_and_touch(self):
        self.seed(count=81);self.seed(count=9,who='test');self.page.evaluate('ensureEarnedCards()')
        requests=[]
        self.page.on('request',lambda r:requests.append(r.url))
        self.page.evaluate('navigateHome("test")')
        self.assertEqual(self.page.locator('#card-gallery button').count(),1)
        self.image('#card-gallery button img','T01')
        self.assertTrue(all('/assets/cards/' not in u or u.endswith('/T01.webp') for u in requests))
        self.page.evaluate('navigateHome("student")')
        before=self.snapshot()
        for i,card_id in enumerate(IDS):
            selector=f'#card-gallery button:nth-child({i+1})'
            self.image(selector+' img',card_id)
            button=self.page.locator(selector)
            self.assertIn('獲得した',button.get_attribute('aria-label'))
            button.focus();self.page.keyboard.press('Enter')
            self.image('#card-detail-art-host img',card_id)
            self.assertIn('獲得済み',self.page.locator('#card-detail-status').inner_text())
            self.page.keyboard.press('Escape')
            expect(self.page.locator('#card-detail-art-host img')).to_have_count(0)
            expect(button).to_be_focused()
        # A touch-enabled context exercises the same earned button.
        touch=self.browser.new_context(has_touch=True,viewport=dict(width=390,height=844))
        try:
            p=touch.new_page();p.goto(self.url);p.wait_for_function('appReady')
            p.evaluate(progress.SEED,dict(count=9));p.evaluate('ensureEarnedCards()');p.evaluate('navigateHome()')
            p.locator('#card-gallery button').tap()
            expect(p.locator('#card-detail-dialog')).to_be_visible()
        finally:touch.close()
        self.page.evaluate('navigateHome("test")')
        self.assertEqual(self.page.locator('#card-gallery img').count(),1)
        self.assertEqual(self.snapshot(),before)

    def test_parent_preview_all_ten_no_awards_and_cleanup(self):
        before=self.snapshot();self.preview()
        for i,card_id in enumerate(IDS):
            self.page.locator('#admin-card-preview button').nth(i).click()
            self.image('#card-detail-art-host img',card_id)
            self.assertIn('獲得状況は変更されません',self.page.locator('#card-detail-status').inner_text())
            self.page.locator('#card-detail-close').click()
            expect(self.page.locator('#card-detail-art-host img')).to_have_count(0)
        self.assertEqual(self.snapshot(),before)
        self.page.evaluate('navigateHome()')
        self.assertEqual(self.page.locator('img[src*="assets/cards/"]').count(),0)
        requests=[];self.page.on('request',lambda r:requests.append(r.url))
        self.page.reload();self.ready()
        self.assertFalse(any('/assets/cards/' in u for u in requests))
        self.assertEqual(self.snapshot(),before)

    def test_notifications_all_ids_and_real_award_path(self):
        self.question(0)
        for card_id in IDS:
            self.page.evaluate('id=>showResult({era:id})',card_id)
            self.image('#result .award-banner img',card_id)
            self.page.locator('#result .award-see').click()
            self.image('#card-detail-art-host img',card_id)
            self.page.locator('#card-detail-close').click()
        # Real answer transaction: T01 and then final ALL81 notification.
        self.seed(count=8);self.question(8);self.answer();self.question(8);self.answer()
        self.image('#result .award-banner img','T01')
        d=self.snapshot();d['progress']=[];d['awards']=[]
        self.page.evaluate('d=>replaceAllStores(d)',d)
        self.seed(count=80);self.page.evaluate('ensureEarnedCards()')
        self.question(80);self.answer();self.question(80);self.answer()
        self.image('#result .award-banner img','ALL81')
        CAPTURES.mkdir(exist_ok=True)
        self.page.locator('#result').screenshot(path=str(CAPTURES/'award-all81.png'))
        before=self.snapshot()
        self.page.evaluate('navigateHome("test")')
        self.assertEqual(self.page.locator('img[src*="assets/cards/"]').count(),0)
        self.assertEqual(self.snapshot(),before)

    def test_image_failure_in_collection_detail_notification_and_preview(self):
        self.page.route('**/assets/cards/*.webp',lambda route:route.fulfill(status=404,body='missing'))
        self.seed(count=81);self.page.evaluate('ensureEarnedCards()');self.page.evaluate('navigateHome()')
        expect(self.page.locator('#card-gallery .art-load-failed')).to_have_count(10)
        for i,card_id in enumerate(IDS):
            card=self.page.locator('#card-gallery button').nth(i)
            name=self.page.evaluate('id=>CARDS[id].name',card_id)
            self.assertIn(name,card.locator('.card-art-fallback').inner_text())
            card.click()
            expect(self.page.locator('#card-detail-art-host .art-load-failed')).to_have_count(1)
            self.assertIn(name,self.page.locator('#card-detail-title').inner_text())
            self.page.locator('#card-detail-close').click()
        self.question(0);self.page.evaluate('showResult({era:"ALL81"})')
        expect(self.page.locator('#result .art-load-failed')).to_have_count(1)
        self.assertIn('九九完全制覇カード',self.page.locator('#result .award-banner').inner_text())
        self.preview()
        expect(self.page.locator('#admin-card-preview .art-load-failed')).to_have_count(10)
        self.assertEqual(self.errors,[])

    def test_phone_tablet_portrait_landscape_images_fit_and_captures(self):
        self.seed(count=81);self.page.evaluate('ensureEarnedCards()');self.page.evaluate('navigateHome()')
        CAPTURES.mkdir(exist_ok=True)
        for width,height in [(320,568),(375,667),(667,375),(390,844),(844,390),(768,1024),(1024,768),(820,1180),(1180,820),(507,768)]:
            with self.subTest(size=(width,height)):
                self.page.set_viewport_size(dict(width=width,height=height))
                self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                for i,card_id in enumerate(IDS):
                    self.image(f'#card-gallery button:nth-child({i+1}) img',card_id)
                self.page.locator('#collection').screenshot(path=str(CAPTURES/f'collection-{width}x{height}.png'))
                for index in [0,9]:
                    self.page.locator('#card-gallery button').nth(index).click()
                    self.image('#card-detail-art-host img',IDS[index])
                    self.assertTrue(self.page.locator('#card-detail-dialog').evaluate('d=>d.scrollWidth<=d.clientWidth'))
                    self.assertTrue(self.page.locator('#card-detail-art-host img').evaluate('i=>{const b=i.getBoundingClientRect();return b.x>=0&&b.right<=innerWidth&&b.y>=0&&b.bottom<=innerHeight}'))
                    self.page.screenshot(path=str(CAPTURES/f'detail-{IDS[index]}-{width}x{height}.png'))
                    self.page.locator('#card-detail-close').click()
        self.assertEqual(self.errors,[])
