"""20-question exam: synthetic data in disposable Chromium contexts only."""
import copy
import unittest
import app_isolation_test as isolation


class MultiplicationExamTest(unittest.TestCase):
    setUpClass = classmethod(isolation.AppIsolationTest.setUpClass.__func__)
    tearDownClass = classmethod(isolation.AppIsolationTest.tearDownClass.__func__)
    setUp = isolation.AppIsolationTest.setUp
    tearDown = isolation.AppIsolationTest.tearDown
    ready = isolation.AppIsolationTest.ready

    def start(self):
        self.page.evaluate('startStudy("mix")')
        self.page.wait_for_function('quizReady && phase==="question"')

    def grade(self, correct=True):
        self.page.evaluate('''async correct=>{
          numericInput=String(correct?currentQuestion.answer:99);updateChoices();
          await grade();
        }''', correct)
        self.page.wait_for_function('quizReady && phase==="result" && !saving')

    def valid(self, data, version=12):
        return self.page.evaluate('''([data,version])=>{
          try {validateBackup({backupFormat:BACKUP_FORMAT,backupVersion:version,data});return true;}
          catch {return false;}
        }''', [data,version])

    def test_uniform_draw_ignores_history_and_weak_stays_weighted_ten(self):
        result=self.page.evaluate('''()=>{
          const saved=Math.random,ids=QUESTIONS.map(q=>q.id),first=[],draws=[];
          const events=QUESTIONS.flatMap((q,i)=>Array.from({length:30},()=>({profile:'student',questionId:q.id,revision:1,correct:i!==0})));
          const draw=(events,k)=>{let n=0;Math.random=()=>n++===0?(k+.5)/81:.999999;
            return sampleStudyEntries(QUESTIONS,events,'student','mix').map(e=>e.questionId);};
          try {
            for(let k=0;k<81;k++) {const a=draw([],k),b=draw(events,k);first.push(a[0]);draws.push({a,b});}
            Math.random=()=>.5;
            const weak=sampleStudyEntries(QUESTIONS,events,'student','weak');
            const weakEmpty=sampleStudyEntries(QUESTIONS,[],'student','weak');
            Math.random=()=>0;const shuffled=sampleStudyEntries(QUESTIONS,[],'student','mix').map(e=>e.questionId);
            return {ids,first,draws,weak,weakEmpty,shuffled};
          } finally {Math.random=saved;}
        }''')
        self.assertEqual(result['first'],result['ids'])  # 81 equal-width bins, no history weights.
        for draw in result['draws']:
            self.assertEqual(draw['a'],draw['b'])
            self.assertEqual(len(draw['a']),20)
            self.assertEqual(len(set(draw['a'])),20)
        self.assertEqual(len(result['weak']),10)
        self.assertNotEqual(result['weak'],result['weakEmpty'])  # Existing weak weights still apply.
        self.assertEqual(set(result['shuffled']),set(result['ids'][:20]))
        self.assertNotEqual(result['shuffled'],result['ids'][:20])

    def test_scores_progress_persisted_results_and_fresh_retry(self):
        for correct in [0,10,17,20]:
            with self.subTest(correct=correct):
                self.page.evaluate('startStudy("mix",null,true)')
                self.page.wait_for_function('quizReady && phase==="question"')
                old_id=self.page.evaluate('currentSession.setId')
                for i in range(20):
                    self.assertIn(f'{i+1} / 20もん',self.page.locator('#study-progress').inner_text())
                    self.grade(i<correct)
                    self.assertEqual(self.page.evaluate('currentSession.position'),i)
                    if i==19:self.assertEqual(self.page.locator('#next').inner_text(),'けっかをみる！')
                    self.page.evaluate('nextStudy()')
                self.assertEqual(self.page.locator('#study-result-score').inner_text(),f'{correct*5}てん！')
                self.assertEqual(self.page.locator('#study-result-summary').inner_text(),f'20もんちゅう {correct}もん せいかい')
                before=self.page.evaluate('snapshotAllStores()')
                self.assertTrue(self.valid(before))
                self.page.reload();self.ready()
                self.assertEqual(self.page.locator('#study-result-score').inner_text(),f'{correct*5}てん！')
                self.page.locator('#study-home').click()
                self.page.locator('#genre-dashboard').click()
                self.assertEqual(self.page.locator('#study-result-score').inner_text(),f'{correct*5}てん！')
                self.assertEqual(self.page.evaluate('snapshotAllStores()'),before)
                self.page.locator('#study-again').click()
                self.page.wait_for_function('quizReady && phase==="question"')
                self.assertNotEqual(self.page.evaluate('currentSession.setId'),old_id)
                self.assertEqual(self.page.evaluate('currentSession.results'),[])

    def test_whole_card_keyboard_and_touch(self):
        card=self.page.locator('#genre-dashboard')
        self.assertEqual(card.evaluate('(e)=>e.tagName'),'BUTTON')
        self.assertEqual(card.locator('button,a,input,[tabindex]').count(),0)
        self.assertIn('20問、100点満点',card.get_attribute('aria-label'))
        for selector in ['.test-card-title','.test-card-intro','.test-card-full','#test-card-action','#test-card-note']:
            self.page.locator(selector).click()
            self.page.wait_for_function('quizReady && phase==="question"')
            self.page.evaluate('navigateHome()')
        for key in ['Enter','Space']:
            card.focus();card.press(key)
            self.page.wait_for_function('quizReady && phase==="question"')
            self.page.evaluate('navigateHome()')
        # An actual touch event at the card padding, away from its child spans.
        ctx=self.browser.new_context(has_touch=True,viewport={'width':390,'height':844})
        try:
            page=ctx.new_page();page.goto(self.url);page.wait_for_function('appReady')
            page.locator('#genre-dashboard').tap(position={'x':5,'y':5})
            page.wait_for_function('quizReady && phase==="question"')
            self.assertEqual(page.evaluate('currentSession.entries.length'),20)
        finally:ctx.close()

    def test_resume_backup_and_simultaneous_grading_no_extra_coins(self):
        self.start();entries=self.page.evaluate('currentSession.entries')
        self.grade();self.page.evaluate('nextStudy()');self.grade(False)
        before=self.page.evaluate('snapshotAllStores()')
        self.page.reload();self.ready()
        self.assertEqual(self.page.evaluate('currentSession.entries'),entries)
        self.assertEqual(self.page.evaluate('[currentSession.position,phase]'),[1,'result'])
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),before)
        self.assertTrue(self.valid(before))
        self.page.evaluate('data=>replaceAllStores(validateBackup({backupFormat:BACKUP_FORMAT,backupVersion:12,data}))',before)
        self.page.reload();self.ready()
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),before)
        self.page.evaluate('nextStudy()')
        other=self.context.new_page();other.goto(self.url);other.wait_for_function('appReady')
        other.evaluate('startStudy("mix")')
        for page in [self.page,other]:page.evaluate('numericInput=String(currentQuestion.answer);updateChoices()')
        reward=self.page.evaluate('TABLE_COIN_REWARDS[currentQuestion.left]')
        coins=self.page.evaluate('getAvailableCoins()')
        self.page.evaluate('window.pendingGrade=grade()');other.evaluate('grade()');self.page.evaluate('pendingGrade')
        self.assertEqual(len(self.page.evaluate('readAll("answers")')),3)
        self.assertEqual(self.page.evaluate('getAvailableCoins()'),coins+reward)
        before=self.page.evaluate('snapshotAllStores()')
        self.page.evaluate('Promise.all([grade(),grade()])')
        self.page.reload();self.ready()
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),before)
        other.close()

    def test_old_ten_backup_resumes_without_becoming_hundred_point_test(self):
        self.start()
        # Old v0.4.5 numeric mix shape: only ten entries, same keys/fields.
        self.page.evaluate('''()=>changeStudySet(currentSession.key,old=>({...old,entries:old.entries.slice(0,10)}))''')
        self.page.reload();self.ready()
        self.grade();before=self.page.evaluate('snapshotAllStores()')
        for version in [11,12]:self.assertTrue(self.valid(before,version))
        self.assertFalse(self.valid(before,10))  # Numeric sets were never part of v10.
        self.page.evaluate('data=>replaceAllStores(validateBackup({backupFormat:BACKUP_FORMAT,backupVersion:12,data}))',before)
        self.page.reload();self.ready()
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),before)
        self.assertIn('以前の10問セット',self.page.locator('#study-progress').inner_text())
        self.page.evaluate('navigateHome()')
        self.assertIn('以前の10問セット',self.page.locator('#genre-dashboard').inner_text())
        self.assertNotIn('100てん',self.page.locator('#genre-dashboard').inner_text())
        self.page.locator('#genre-dashboard').click()
        for i in range(10):
            if i:self.grade()
            self.page.evaluate('nextStudy()')
        self.assertIn('以前の10問セット',self.page.locator('#study-result-title').inner_text())
        self.assertTrue(self.page.locator('#study-result-score').is_hidden())
        self.assertIn('回答数 10問',self.page.locator('#study-result-summary').inner_text())
        finished=self.page.evaluate("snapshotAllStores()")
        self.page.locator('#study-again').click()
        self.page.wait_for_function('quizReady && phase==="question"')
        self.assertEqual(self.page.evaluate('currentSession.entries.length'),20)
        after=self.page.evaluate('snapshotAllStores()')
        for store in before:
            if store!='studySets':self.assertEqual(after[store],finished[store])
        self.assertEqual(len(after['answers']),10)

    def test_validation_keeps_weak_limit_and_rejects_malformed_exam(self):
        self.start();data=self.page.evaluate('snapshotAllStores()')
        self.assertTrue(self.valid(data))
        for length in [11,19,21]:
            bad=copy.deepcopy(data)
            bad['studySets'][0]['entries']=(bad['studySets'][0]['entries']+bad['studySets'][0]['entries'])[:length]
            self.assertFalse(self.valid(bad))
        bad=copy.deepcopy(data);s=bad['studySets'][0];s['mode']='weak';s['key']='student:numeric:weak'
        self.assertFalse(self.valid(bad))
        self.grade();data=self.page.evaluate('snapshotAllStores()')
        for mutation in ['duplicate','missing','wrong']:
            bad=copy.deepcopy(data);s=bad['studySets'][0]
            if mutation=='duplicate':s['results'].append(s['results'][0].copy())
            elif mutation=='missing':s['results']=[]
            else:s['results'][0]['correct']=False
            self.assertFalse(self.valid(bad))

    def test_mobile_layout_and_optional_screenshots(self):
        import json
        import os
        from pathlib import Path
        evidence=os.environ.get('KAKEZAN_EXAM_EVIDENCE')
        folder=Path(evidence) if evidence else None
        if folder:folder.mkdir(parents=True,exist_ok=True)
        self.start()
        for i in range(20):self.grade(i<17);self.page.evaluate('nextStudy()')
        dimensions=[(390,844),(844,390),(768,1024),(1024,768),(320,568),(375,667),(507,768),(820,1180)]
        metrics=[]
        for width,height in dimensions:
            for percent in [100,200]:
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate('n=>document.documentElement.style.fontSize=n+"%"',percent)
                for screen in ['home','result']:
                    if screen=='home':self.page.evaluate('navigateHome()')
                    else:self.page.locator('#genre-dashboard').click()
                    selector='#genre-dashboard' if screen=='home' else '#study-finished'
                    self.page.locator(selector).wait_for(state='visible')
                    measured=self.page.locator(selector).evaluate('''e=>{
                      const r=e.getBoundingClientRect();
                      const children=[...e.querySelectorAll('*')].filter(x=>x.getClientRects().length);
                      return {elementWidth:r.width,scrollWidth:document.documentElement.scrollWidth,
                        viewport:innerWidth,overflow:children.filter(x=>{
                          const c=x.getBoundingClientRect();return c.left<r.left||c.right>r.right+1||x.scrollWidth>x.clientWidth+1;
                        }).map(x=>x.id||x.className),
                        scoreFont:parseFloat(getComputedStyle(document.querySelector('#study-result-score')).fontSize)};
                    }''')
                    self.assertLessEqual(measured['scrollWidth'],width)
                    self.assertEqual(measured['overflow'],[],(width,height,percent,screen,measured))
                    metrics.append(dict(width=width,height=height,percent=percent,screen=screen,**measured))
                    if screen=='result':self.assertGreaterEqual(measured['scoreFont'],48)
                    if folder and percent==100 and (width,height) in dimensions[:4]:
                        if screen=='home':
                            capture_context=self.browser.new_context(viewport={'width':width,'height':height})
                            try:
                                capture=capture_context.new_page();capture.goto(self.url);capture.wait_for_function('appReady')
                                bottom=capture.locator('#dashboard').evaluate('e=>e.getBoundingClientRect().bottom')
                                capture.screenshot(path=str(folder/f'{screen}-{width}x{height}.png'),full_page=True,
                                                   clip={'x':0,'y':0,'width':width,'height':bottom+16})
                            finally:capture_context.close()
                        else:
                            self.page.evaluate('window.scrollTo(0,0)')
                            self.page.screenshot(path=str(folder/f'{screen}-{width}x{height}.png'),full_page=True)
        if folder:(folder/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
