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

    def assert_mistakes(self, results):
        wrong=sorted((r for r in results if not r['correct']),key=lambda r:r['position'])
        self.assertEqual(self.page.locator('#study-mistakes').is_visible(),bool(wrong))
        items=self.page.locator('#study-mistakes-list li')
        self.assertEqual(items.count(),len(wrong))
        for i,result in enumerate(wrong):
            _,table,right=result['questionId'].split(':')
            left,right=int(table[1:]),int(right)
            answer=left*right
            self.assertEqual(items.nth(i).inner_text(),f'{left} × {right} = {answer}')
            self.assertEqual(items.nth(i).locator('strong').inner_text(),str(answer))
            self.assertEqual(items.nth(i).get_by_role('img').get_attribute('aria-label'),
                             f'{left} かける {right}、ただしい こたえは {answer}')
        if wrong:
            self.assertEqual(self.page.locator('#study-mistakes-title').inner_text(),
                             'まちがえた もんだいを かくにんしよう！')

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
        messages={
            20:'100てん おめでとう！',
            17:'すごい！ よくがんばったね！',
            19:'すごい！ よくがんばったね！',
            10:'さいごまで よくがんばったね！',
            0:'20もんに ちょうせんできたね！\nまた やってみよう！',
        }
        for correct,message in messages.items():
            with self.subTest(correct=correct):
                self.page.evaluate('startStudy("mix",null,true)')
                self.page.wait_for_function('quizReady && phase==="question"')
                old_id=self.page.evaluate('currentSession.setId')
                for i in range(20):
                    self.assertIn(f'{i+1} / 20もん',self.page.locator('#study-progress').inner_text())
                    # Include wrong answers at the start, middle and final position.
                    wrong={0,8,19} if correct==17 else {9} if correct==19 else set(range(correct,20))
                    self.grade(i not in wrong)
                    self.assertEqual(self.page.evaluate('currentSession.position'),i)
                    self.assertTrue(self.page.locator('#quiz #result').is_visible())
                    if i==19:self.assertEqual(self.page.locator('#next').inner_text(),'けっかをみる！')
                    self.page.evaluate('nextStudy()')
                perfect=correct==20
                self.assertEqual(self.page.locator('#study-result-title').inner_text(),
                                 '🎉 テストの けっか 🎉' if perfect else '🌸 テストの けっか')
                self.assertEqual(self.page.locator('#study-result-score').inner_text(),f'{correct*5}てん！')
                self.assertEqual(self.page.locator('#study-result-correct').inner_text(),
                                 'ぜんぶ せいかい！' if perfect else f'{correct}もん せいかい！')
                self.assertEqual(self.page.locator('#study-result-summary').inner_text(),
                                 '20もん ぜんぶ せいかい' if perfect else '')
                self.assertEqual(self.page.locator('#study-result-summary').is_visible(),perfect)
                if not perfect:
                    self.assertEqual(self.page.locator('#study-finished').inner_text().count(f'{correct}もん せいかい'),1)
                self.assertEqual(self.page.locator('#study-result-remaining').inner_text(),message)
                self.assertEqual(self.page.locator('#study-again').inner_text(),'もういちど テスト')
                self.assertEqual(self.page.locator('#study-home').inner_text(),'ホームへ もどる')
                self.assertTrue(self.page.locator('#study-last-result').is_hidden())
                stars=self.page.locator('#study-result-stars')
                self.assertEqual(stars.is_visible(),perfect)
                self.assertEqual(self.page.locator('#study-finished').evaluate(
                    'e=>getComputedStyle(e).borderTopColor'),
                    'rgb(223, 173, 76)' if perfect else 'rgb(237, 190, 208)')
                if perfect:
                    self.assertEqual(stars.get_attribute('aria-hidden'),'true')
                    animation=stars.evaluate('''async e=>{
                      const animations=e.getAnimations({subtree:true});
                      const duration=animations.map(a=>a.effect.getComputedTiming().endTime);
                      await Promise.all(animations.map(a=>a.finished));
                      return {duration,finished:animations.every(a=>a.playState==='finished')};
                    }''')
                    self.assertEqual(len(animation['duration']),2)
                    self.assertTrue(all(1000<=duration<=2000 for duration in animation['duration']))
                    self.assertTrue(animation['finished'])
                    self.page.emulate_media(reduced_motion='reduce')
                # results array order need not equal question order; position is authoritative.
                self.page.evaluate('()=>changeStudySet(currentSession.key,old=>({...old,results:[...old.results].reverse()}))')
                before=self.page.evaluate('snapshotAllStores()')
                self.assertEqual(len(before),17)
                results=next(s['results'] for s in before['studySets'] if s['setId']==old_id)
                self.assertEqual(sum(not r['correct'] for r in results),20-correct)
                self.assert_mistakes(results)
                self.assertTrue(self.valid(before))
                self.page.reload();self.ready()
                self.assertEqual(self.page.locator('#study-result-score').inner_text(),f'{correct*5}てん！')
                self.assert_mistakes(results)
                self.page.locator('#study-home').click()
                self.page.locator('#genre-dashboard').click()
                self.page.locator('#study-finished').wait_for(state='visible')
                self.assertEqual(self.page.locator('#study-result-score').inner_text(),f'{correct*5}てん！')
                self.assert_mistakes(results)
                self.assertEqual(self.page.evaluate('snapshotAllStores()'),before)
                self.page.evaluate('data=>replaceAllStores(validateBackup({backupFormat:BACKUP_FORMAT,backupVersion:12,data}))',before)
                self.page.reload();self.ready()
                self.assert_mistakes(results)
                self.assertEqual(self.page.evaluate('snapshotAllStores()'),before)
                if perfect:
                    self.assertTrue(stars.is_visible())
                    self.assertEqual(stars.evaluate('e=>e.getAnimations({subtree:true}).length'),0)
                    self.page.emulate_media(reduced_motion='no-preference')
                self.page.locator('#study-again').click()
                self.page.wait_for_function('quizReady && phase==="question"')
                self.assertNotEqual(self.page.evaluate('currentSession.setId'),old_id)
                self.assertEqual(self.page.evaluate('currentSession.results'),[])

        self.page.evaluate('navigateHome()')
        self.page.evaluate('startStudy("weak")')
        entries=self.page.evaluate('currentSession.entries.length')
        self.assertEqual(entries,10)
        for _ in range(entries):
            self.grade()
            self.page.evaluate('nextStudy()')
        self.assertEqual(self.page.locator('#study-result-title').inner_text(),'苦手克服 セット結果')
        self.assertIn('回答数 10問 ｜ 正解数 10問',self.page.locator('#study-result-summary').inner_text())
        self.assertTrue(self.page.locator('#study-last-result').is_visible())
        self.assertTrue(self.page.locator('#study-result-stars').is_hidden())
        self.assertTrue(self.page.locator('#study-result-score').is_hidden())
        self.assertTrue(self.page.locator('#study-mistakes').is_hidden())
        self.assertEqual(self.page.locator('#study-mistakes-list li').count(),0)

    def test_whole_card_keyboard_and_touch(self):
        card=self.page.locator('#genre-dashboard')
        self.assertEqual(card.evaluate('(e)=>e.tagName'),'BUTTON')
        self.assertEqual(card.locator('button,a,input,[tabindex]').count(),0)
        self.assertEqual(card.get_attribute('aria-label'),'かけざんテスト、20問、100点満点、テストを はじめる！')
        copy_by_selector={
            '.test-card-title':'📝 かけざんテスト',
            '.test-card-intro':'20もん といて、なんてん とれるかな？',
            '.test-card-full':'⭐ 100てん まんてん ⭐',
            '#test-card-action':'テストを はじめる！',
        }
        for selector,copy_text in copy_by_selector.items():
            self.assertEqual(card.locator(selector).inner_text(),copy_text)
        self.assertNotIn('81もんから ランダムに しゅつだい',card.inner_text())
        self.assertTrue(card.locator('#test-card-note').is_hidden())
        for selector in copy_by_selector:
            self.page.locator(selector).click()
            self.page.wait_for_function('quizReady && phase==="question"')
            self.page.evaluate('navigateHome()')
            self.assertEqual(card.locator('#test-card-action').inner_text(),'テストを つづける！')
            self.assertEqual(card.get_attribute('aria-label'),'かけざんテスト、20問、100点満点、テストを つづける！')
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
        self.assertEqual(self.page.locator('.test-card-intro').inner_text(),'前のつづきから はじめよう！')
        self.assertEqual(self.page.locator('#test-card-action').inner_text(),'以前の10問セットを再開')
        self.assertTrue(self.page.locator('#test-card-note').is_visible())
        self.page.locator('#genre-dashboard').click()
        for i in range(10):
            if i:self.grade()
            self.page.evaluate('nextStudy()')
        self.assertIn('以前の10問セット',self.page.locator('#study-result-title').inner_text())
        self.assertTrue(self.page.locator('#study-result-score').is_hidden())
        self.assertTrue(self.page.locator('#study-result-stars').is_hidden())
        self.assertTrue(self.page.locator('#study-last-result').is_visible())
        self.assertIn('回答数 10問',self.page.locator('#study-result-summary').inner_text())
        self.assertTrue(self.page.locator('#study-result-summary').is_visible())
        self.assertTrue(self.page.locator('#study-mistakes').is_hidden())
        self.assertEqual(self.page.locator('#study-mistakes-list li').count(),0)
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

    def test_missing_question_and_revision_do_not_guess_answers(self):
        self.start()
        for _ in range(20):self.grade(False);self.page.evaluate('nextStudy()')
        # Deliberately damaged local records, not an accepted backup shape.
        self.page.evaluate('''()=>changeStudySet(currentSession.key,old=>{
          old.results[0].questionId='MULT:T99:99';old.entries[0].questionId='MULT:T99:99';
          old.results[1].revision=2;old.entries[1].revision=2;
          old.results[2].questionId=old.entries[3].questionId;
          return old;
        })''')
        before=self.page.evaluate('snapshotAllStores()')
        self.page.evaluate('restoreStudy("mix",null)')
        items=self.page.locator('#study-mistakes-list li')
        self.assertEqual(items.count(),20)
        for i in range(3):
            self.assertEqual(items.nth(i).inner_text(),'この もんだいは ひょうじできません。')
            self.assertEqual(items.nth(i).locator('strong,[role="img"]').count(),0)
        self.assertEqual(items.locator('strong').count(),17)
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),before)

    def test_mobile_layout_and_optional_screenshots(self):
        import json
        import os
        from pathlib import Path
        evidence=os.environ.get('KAKEZAN_EXAM_EVIDENCE')
        folder=Path(evidence) if evidence else None
        if folder:folder.mkdir(parents=True,exist_ok=True)
        dimensions=[(390,844),(844,390),(768,1024),(1024,768),(320,568),(375,667),(507,768),(820,1180)]
        metrics=[]
        self.page.emulate_media(reduced_motion='reduce')
        for correct in [17,0,20]:
            self.page.evaluate('startStudy("mix",null,true)')
            for i in range(20):self.grade(i<correct);self.page.evaluate('nextStudy()')
            screens=['home',f'result-{correct*5}'] if correct==17 else [f'result-{correct*5}']
            for width,height in dimensions:
                for percent in [100,200]:
                    self.page.set_viewport_size({'width':width,'height':height})
                    self.page.evaluate('n=>document.documentElement.style.fontSize=n+"%"',percent)
                    for screen in screens:
                        if screen=='home':self.page.evaluate('navigateHome()')
                        elif self.page.locator('#home').is_visible():self.page.locator('#genre-dashboard').click()
                        selector='#genre-dashboard' if screen=='home' else '#study-finished'
                        self.page.locator(selector).wait_for(state='visible')
                        self.page.evaluate('window.scrollTo(0,0)')
                        measured=self.page.locator(selector).evaluate('''e=>{
                          const r=e.getBoundingClientRect();
                          const children=[...e.querySelectorAll('*')].filter(x=>x.getClientRects().length);
                          const score=document.querySelector('#study-result-score');
                          return {elementWidth:r.width,scrollWidth:document.documentElement.scrollWidth,
                            viewport:innerWidth,overflow:children.filter(x=>{
                              const c=x.getBoundingClientRect();return c.left<r.left||c.right>r.right+1||x.scrollWidth>x.clientWidth+1;
                            }).map(x=>x.id||x.className),
                            scoreFont:parseFloat(getComputedStyle(score).fontSize),
                            resultControls:[score,...e.querySelectorAll('#study-again,#study-home')].map(x=>{
                              const box=x.getBoundingClientRect();return {top:box.top,bottom:box.bottom,height:box.height};
                            })};
                        }''')
                        self.assertLessEqual(measured['scrollWidth'],width)
                        self.assertEqual(measured['overflow'],[],(width,height,percent,screen,measured))
                        metrics.append(dict(width=width,height=height,percent=percent,screen=screen,**measured))
                        if screen!='home':
                            self.assertGreaterEqual(measured['scoreFont'],48)
                            for control in measured['resultControls']:
                                self.assertGreaterEqual(control['height'],44)
                                if correct==20 and percent==100 and (width,height) in dimensions[:4]:
                                    self.assertGreaterEqual(control['top'],0)
                                    self.assertLessEqual(control['bottom'],height,(width,height,screen,measured))
                        if screen!='home':
                            self.assertEqual(self.page.locator('#study-mistakes-list li').count(),20-correct)
                            for item in self.page.locator('#study-mistakes-list li').all():
                                item.scroll_into_view_if_needed()
                                box=item.bounding_box()
                                self.assertGreaterEqual(box['y'],0)
                                self.assertLessEqual(box['y']+box['height'],height+1)
                            for button in ['#study-again','#study-home']:
                                control=self.page.locator(button)
                                control.scroll_into_view_if_needed()
                                box=control.bounding_box()
                                self.assertTrue(control.is_enabled())
                                self.assertGreaterEqual(box['y'],0)
                                self.assertLessEqual(box['y']+box['height'],height+1)
                                control.focus()
                                self.assertTrue(control.evaluate('e=>document.activeElement===e'))
                            self.page.evaluate('window.scrollTo(0,0)')
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
                                self.page.screenshot(path=str(folder/f'{screen}-{width}x{height}.png'),full_page=True)
        if folder:(folder/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
