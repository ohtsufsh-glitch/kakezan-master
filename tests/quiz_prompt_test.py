"""Question presentation and non-overlap checks; not physical Safari certification."""
import unittest

from playwright.sync_api import expect
import multiplication_test as multiplication

SIZES = [(320, 568), (568, 320), (375, 667), (667, 375), (390, 844),
         (844, 390), (768, 1024), (1024, 768), (820, 1180),
         (1180, 820), (507, 768), (320, 1024)]


class QuizPromptTest(unittest.TestCase):
    setUpClass = classmethod(multiplication.MultiplicationTest.setUpClass.__func__)
    tearDownClass = classmethod(multiplication.MultiplicationTest.tearDownClass.__func__)
    setUp = multiplication.MultiplicationTest.setUp
    tearDown = multiplication.MultiplicationTest.tearDown
    ready = multiplication.MultiplicationTest.ready
    answer = multiplication.MultiplicationTest.answer

    def start(self):
        self.page.evaluate('startEra("T03")')
        self.page.wait_for_function('quizReady')
        if self.page.evaluate('phase') == 'result':
            self.page.locator('#next').click()
        self.page.wait_for_function('quizReady && phase==="question"')

    def assert_layout(self):
        expect(self.page.locator('#question-text')).to_have_text('3 × 4')
        geometry = self.page.evaluate("""() => {
          const q=document.querySelector('#question-text'),style=getComputedStyle(q);
          const range=document.createRange();range.selectNodeContents(q);
          const text=range.getBoundingClientRect(),box=q.getBoundingClientRect();
          const selectors=['#question-kind','#question-text','#numeric-answer','.numeric-keypad','#check'];
          const rects=selectors.map(s=>document.querySelector(s).getBoundingClientRect());
          return {font:parseFloat(style.fontSize),align:style.textAlign,
            horizontal:Math.abs((text.left+text.right)-(box.left+box.right))/2,
            vertical:Math.abs((text.top+text.bottom)-(box.top+box.bottom))/2,
            lines:range.getClientRects().length,
            fits:text.left>=box.left && text.right<=box.right && text.top>=box.top && text.bottom<=box.bottom,
            ordered:rects.every((r,i)=>!i || rects[i-1].bottom<=r.top),
            inWidth:rects.every(r=>r.left>=0 && r.right<=innerWidth),
            noOverflow:document.documentElement.scrollWidth<=innerWidth,
            keys:[...document.querySelectorAll('.numeric-keypad button')].map(b=>{const r=b.getBoundingClientRect();return [r.width,r.height]})};
        }""")
        self.assertGreaterEqual(geometry['font'], 40)  # main: 18.4px
        self.assertEqual(geometry['align'], 'center')
        self.assertLessEqual(geometry['horizontal'], 1)
        self.assertLessEqual(geometry['vertical'], 4)  # font line box / glyph metrics
        self.assertEqual(geometry['lines'], 1)
        for key in ['fits', 'ordered', 'inWidth', 'noOverflow']:
            self.assertTrue(geometry[key], (key, geometry))
        self.assertEqual(len(geometry['keys']), 11)
        self.assertTrue(all(w>=44 and h>=44 for w,h in geometry['keys']))

    def test_all_81_presentations_preserve_catalog_and_stores(self):
        self.start()
        before = self.page.evaluate('snapshotAllStores()')
        catalog = self.page.evaluate('QUESTIONS')
        displayed = self.page.evaluate("""() => QUESTIONS.map(q=>{
          currentQuestion=q;renderQuestion();
          return document.querySelector('#question-text').textContent;
        })""")
        self.assertEqual(displayed, [f'{q["left"]} × {q["right"]}' for q in catalog])
        self.assertEqual(self.page.evaluate('QUESTIONS'), catalog)
        self.assertEqual(self.page.evaluate('snapshotAllStores()'), before)

    def test_layout_input_grade_next_and_admin_across_viewports(self):
        self.page.evaluate('pickQuestion=()=>QUESTIONS.find(q=>q.left===3 && q.right===4)')
        for profile in ['student', 'test']:
            if profile == 'test':
                self.page.evaluate('beginTestMode()')
            for width, height in SIZES:
                with self.subTest(profile=profile, viewport=(width,height)):
                    self.page.set_viewport_size(dict(width=width,height=height))
                    self.start()
                    self.assert_layout()
                    expect(self.page.locator('#check')).to_be_disabled()
                    self.answer(correct=profile=='student')
                    expect(self.page.locator('#result')).to_contain_text('3 × 4 = 12')
                    self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                    self.page.locator('#next').click()
                    self.page.wait_for_function('quizReady && phase==="question"')
                    expect(self.page.locator('#numeric-answer')).to_have_text('—')
                    expect(self.page.locator('#check')).to_be_disabled()
                    self.assert_layout()
                    self.page.evaluate('navigate("admin")')
                    expect(self.page.locator('#report-list > section')).to_have_count(81)
                    self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))

    def test_text_enlargement_keeps_one_line_and_separate_controls(self):
        self.page.evaluate('pickQuestion=()=>QUESTIONS.find(q=>q.left===3 && q.right===4)')
        self.page.add_style_tag(content='html {font-size:200% !important}')
        for width,height in [(320,568), (667,375), (507,768), (1024,768)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size(dict(width=width,height=height))
                self.start()
                self.assert_layout()
