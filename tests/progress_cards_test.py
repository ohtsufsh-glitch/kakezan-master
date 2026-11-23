"""PR-3: synthetic progress, atomic achievements, lifetime parent report and compatibility."""
import copy
import json
from pathlib import Path
import unittest
from playwright.sync_api import expect
import multiplication_test as numeric

SEED = """async ({count=0,who='student',partial=false,awards=false})=>{
  const d=await snapshotAllStores(),at='2020-01-01T00:00:00.000Z';
  for(const q of SAMPLE_QUESTIONS.slice(0,count))d.progress.push({key:`${who}:${q.id}`,profile:who,
    questionId:q.id,revision:1,attempts:2,streak:partial?1:2,mastered:!partial,everWrong:false,lastAnsweredAt:at});
  if(awards)for(const [era] of ERAS)d.awards.push({key:`${who}:${era}`,profile:who,era,earnedAt:at,questionCountAtEarn:9});
  await replaceAllStores(d);
}"""

class ProgressCardsTest(unittest.TestCase):
    setUpClass=classmethod(numeric.MultiplicationTest.setUpClass.__func__)
    tearDownClass=classmethod(numeric.MultiplicationTest.tearDownClass.__func__)
    setUp=numeric.MultiplicationTest.setUp
    tearDown=numeric.MultiplicationTest.tearDown
    ready=numeric.MultiplicationTest.ready
    answer=numeric.MultiplicationTest.answer

    def seed(self, **kwargs):self.page.evaluate(SEED,kwargs)
    def awards(self):return self.page.evaluate('readAll("awards")')
    def snapshot(self):return self.page.evaluate('snapshotAllStores()')
    def question(self, index):
        self.page.evaluate('i=>{pickQuestion=()=>QUESTIONS[i]}',index)
        era=f'T{index//9+1:02}'
        self.page.evaluate('era=>startEra(era)',era)
        self.page.evaluate('era=>advance(era,null)',era)
        self.page.wait_for_function('quizReady&&phase==="question"')

    def test_radar_half_mastery_wrong_and_profiles(self):
        self.question(0)
        for correct,expected in [(True,0.5),(True,1),(False,0)]:
            self.answer(correct)
            self.page.evaluate('navigateHome()')
            stat=self.page.evaluate('async()=>{const p=await readAll("progress");return masteryStats("T01",new Map(p.map(x=>[x.questionId,x])))}')
            self.assertAlmostEqual(stat['percentage'],expected/9*100)
            self.assertEqual(self.page.locator('#overall-mastery-percent').inner_text(),f'{int(expected/81*100)}%')
            self.assertEqual(self.page.locator('#radar-chart line').count(),9)
            self.assertEqual(self.page.locator('#radar-chart circle').count(),9)
            for i in range(1,10):self.assertIn(f'{i}の段:',self.page.locator('#radar-chart').get_attribute('aria-label'))
            self.question(0)
        self.seed(count=9,who='test',partial=True)
        self.page.evaluate('navigateHome("test")')
        self.assertIn('1の段: 50%',self.page.locator('#radar-chart').get_attribute('aria-label'))
        self.page.evaluate('navigateHome("student")')
        self.assertIn('1の段: 0%',self.page.locator('#radar-chart').get_attribute('aria-label'))
        self.assertNotRegex(self.page.locator('#home').inner_text(),r'歴史|れきし|縄文|江戸')

    def test_eight_then_nine_mastered_and_owned_after_wrong(self):
        self.seed(count=8)
        self.page.evaluate('ensureEarnedCards()')
        self.assertEqual(self.awards(),[])
        self.question(8);self.answer()
        self.assertEqual(self.awards(),[])
        self.question(8);self.answer()
        owned=self.awards();self.assertEqual([a['era'] for a in owned],['T01'])
        self.assertEqual(owned[0]['questionCountAtEarn'],9)
        self.assertEqual(self.page.evaluate('getAvailableCoins()'),2) # card adds no coins
        self.question(8);self.answer(False)
        self.page.reload();self.ready()
        self.assertEqual(self.awards(),owned)
        self.page.evaluate('navigateHome()')
        self.assertEqual(self.page.locator('#card-total').inner_text(),'1 / 10枚')
        self.page.locator('#card-gallery button').click()
        self.assertIn('1の段達成カード',self.page.locator('#card-detail-title').inner_text())
        self.assertIn('1の段の9問を同時に習得',self.page.locator('#card-detail-era').inner_text())

    def test_all81_requires_current_mastery_and_grants_two_cards_at_once(self):
        self.seed(count=80,awards=True)
        self.page.evaluate('ensureEarnedCards()')
        self.assertEqual(len(self.awards()),9)
        self.question(80);self.answer();self.question(80);self.answer()
        self.assertEqual(len(self.awards()),10)
        self.assertEqual(next(a for a in self.awards() if a['era']=='ALL81')['questionCountAtEarn'],81)
        before=self.awards();self.question(0);self.answer(False)
        self.page.evaluate('ensureEarnedCards()')
        self.assertEqual(self.awards(),before)
        # Fresh fixture: T09 and ALL81 awarded by the final answer together.
        d=self.snapshot();d['awards']=[]
        self.page.evaluate('d=>replaceAllStores(d)',d)
        self.question(0);self.answer();self.question(0);self.answer()
        self.assertEqual(len(self.awards()),10)

    def test_final_answer_grants_row_and_all_in_one_transaction(self):
        self.seed(count=80)
        self.page.evaluate('ensureEarnedCards()')
        self.assertEqual(len(self.awards()),8)
        self.question(80);self.answer();self.question(80);self.answer()
        self.assertEqual(len(self.awards()),10)
        both=[a for a in self.awards() if a['era'] in ['T09','ALL81']]
        self.assertEqual(both[0]['earnedAt'],both[1]['earnedAt'])

    def test_abort_rolls_back_card_answer_coin_and_session(self):
        self.seed(count=8);self.question(8);self.answer();self.question(8)
        before=self.snapshot()
        self.page.evaluate('''()=>{window.originalAdd=IDBObjectStore.prototype.add;window.cardWritten=false;
          IDBObjectStore.prototype.add=function(...args){const r=originalAdd.apply(this,args);
            if(this.name==='awards')r.addEventListener('success',()=>cardWritten=true);
            if(this.name==='answers')r.addEventListener('success',()=>this.transaction.abort());return r;};}''')
        self.page.evaluate('numericInput=String(currentQuestion.answer);grade()')
        self.assertTrue(self.page.evaluate('cardWritten'))
        self.assertEqual(self.snapshot(),before)
        self.page.evaluate('()=>{IDBObjectStore.prototype.add=originalAdd;}')
        self.page.reload();self.ready();self.answer()
        self.assertEqual(len(self.awards()),1)

    def test_two_tabs_and_reconciliation_do_not_duplicate_or_overwrite(self):
        self.seed(count=8);self.question(8);self.answer();self.question(8)
        other=self.context.new_page();other.goto(self.url);other.wait_for_function('appReady')
        other.evaluate('startEra("T01")');other.wait_for_function('quizReady')
        for page in [self.page,other]:page.evaluate('numericInput=String(currentQuestion.answer);updateChoices()')
        self.page.evaluate('window.pending=grade()')
        other.evaluate('Promise.all([grade(),ensureEarnedCards()])');self.page.evaluate('pending')
        before=self.snapshot();self.assertEqual(len(before['awards']),1);self.assertEqual(len(before['answers']),2)
        self.page.evaluate('Promise.all([ensureEarnedCards(),ensureEarnedCards()])')
        self.page.reload();self.ready()
        self.assertEqual(self.snapshot(),before);other.close()

    def test_backfill_both_profiles_is_idempotent_and_no_rewards(self):
        self.seed(count=81);self.seed(count=9,who='test')
        before=self.snapshot()
        self.page.evaluate('Promise.all([ensureEarnedCards(),ensureEarnedCards()])')
        self.assertEqual(len(self.awards()),11)
        after=self.snapshot();self.page.reload();self.ready()
        self.assertEqual(self.snapshot(),after)
        for store in before:
            if store!='awards':self.assertEqual(after[store],before[store],store)
        self.page.evaluate('navigateHome("test")')
        self.assertEqual(self.page.locator('#card-total').inner_text(),'1 / 10枚')
        self.page.evaluate('navigateHome("student")')
        self.assertEqual(self.page.locator('#card-total').inner_text(),'10 / 10枚')

    def test_report_lifetime_sort_history_legacy_exclusion_and_profiles(self):
        self.page.evaluate('''async()=>{
          const d=plushFixture(['shiba'],'student'),at='2020-01-01T00:00:00.000Z';
          for(const [index,n,correct,profile] of [[0,25,5,'student'],[1,4,3,'student'],[2,10,2,'student'],[0,1,1,'test']]) {
            const q=SAMPLE_QUESTIONS[index];
            for(let i=0;i<n;i++)d.answers.push({id:d.answers.length+1,profile,questionId:q.id,revision:1,
              answerType:'number',answer:i<correct?q.answer:99,correct:i<correct,at,token:crypto.randomUUID()});
          }
          await replaceAllStores(d);
        }''')
        self.seed(count=1)
        self.page.evaluate('navigate("admin")')
        self.assertEqual(self.page.locator('#report-list > section').count(),81)
        first=self.page.locator('#report-list > section').first
        self.assertIn('通算回答 25回 ／ 通算正解 5回 ／ 正答率 20% ／ 習得済み',first.inner_text())
        first.locator('summary').click()
        history=first.locator('details')
        # click完了後にtoggleイベントで生成される明細を、件数も含めて待つ。
        expect(history).to_have_js_property('open',True)
        expect(history.locator('li')).to_have_count(25)
        self.assertEqual(first.locator('li').filter(has_text='○').count(),5)
        self.assertIn('—（0回）',self.page.locator('#report-list > section').nth(3).inner_text())
        self.assertIn('通算39回答',self.page.locator('#report-summary').inner_text())
        for order,expected in [('accuracy-asc',['01','03','02','04']),('accuracy-desc',['02','01','03','04'])]:
            self.page.select_option('#report-sort',order)
            self.page.wait_for_function('!document.querySelector("#report-list").textContent.includes("読み込み")')
            self.page.wait_for_function('(id)=>document.querySelector("#report-list > section").dataset.questionId===id',arg='MULT:T01:'+expected[0])
            ids=self.page.locator('#report-list > section').evaluate_all('rows=>rows.slice(0,4).map(r=>r.dataset.questionId)')
            self.assertEqual(ids,['MULT:T01:'+n for n in expected])
        self.page.select_option('#report-era','T09');self.page.wait_for_function('document.querySelectorAll("#report-list > section").length===9')
        self.assertIn('通算0回答',self.page.locator('#report-summary').inner_text())
        self.page.select_option('#report-era','all');self.page.select_option('#report-profile','test')
        self.page.wait_for_function('document.querySelector("#report-summary").textContent.includes("テスト用")')
        self.assertIn('通算1回答',self.page.locator('#report-summary').inner_text())
        self.assertIn('正答率 100%',self.page.locator('#report-list > section').first.inner_text())
        self.assertTrue(self.page.locator('#admin-questions-group').is_hidden())

    def test_backup40_cards_legacy_games_validation_and_confirmed_restore(self):
        self.page.evaluate('''async()=>{
          const d=plushFixture(['shiba'],'student'),at='2020-01-01T00:00:00.000Z';
          d.awards=[];
          for(const profile of ['student','test'])for(const [era] of LEGACY_ERAS)d.awards.push({key:`${profile}:${era}`,profile,era,earnedAt:at,questionCountAtEarn:50});
          await replaceAllStores(d);
        }''')
        self.seed(count=81);self.seed(count=81,who='test');self.page.evaluate('ensureEarnedCards()')
        # Include a real active paid runner snapshot alongside crane prizes and coins.
        self.page.evaluate("purchaseRunnerPlay({profile:'student',stageId:'S01',characterId:'shiba'})")
        before=self.snapshot();self.assertEqual(len(before['awards']),40)
        with self.page.expect_download() as event:self.page.evaluate('exportBackup()')
        backup=json.loads(Path(event.value.path()).read_text())
        self.assertEqual(backup['backupVersion'],12)
        self.assertEqual(backup['data'],before)
        for mutation in ['id','count','oldcount','duplicate','future','history']:
            bad=copy.deepcopy(backup)
            if mutation=='id':bad['data']['awards'][0]['era']='T10'
            if mutation=='count':next(a for a in bad['data']['awards'] if a['era']=='ALL81')['questionCountAtEarn']=9
            if mutation=='oldcount':next(a for a in bad['data']['awards'] if a['era']=='E01')['questionCountAtEarn']=9
            if mutation=='duplicate':bad['data']['awards'][-1]=bad['data']['awards'][0]
            if mutation=='future':bad['backupVersion']=13
            if mutation=='history':bad['backupFormat']='history-master-backup'
            self.assertTrue(self.page.evaluate('b=>{try{validateBackup(b);return false}catch{return true}}',bad),mutation)
        self.page.evaluate('navigate("admin")')
        self.page.locator('#backup-file').set_input_files(dict(name='synthetic.json',mimeType='application/json',buffer=json.dumps(backup).encode()))
        self.page.wait_for_function('pendingRestore!==null')
        self.assertEqual(self.snapshot(),before)
        self.page.evaluate('applyRestore()');self.page.wait_for_function('pendingRestore===null&&!backingUp')
        self.page.reload();self.ready();self.assertEqual(self.snapshot(),before)

    def test_upgrade_v10_v11_preserves_all_stores_and_backfills_safely(self):
        for version in [10,11]:
            with self.subTest(version=version):
                self.page.evaluate('''async version=>{
                  const d=plushFixture(['shiba'],'student');
                  const schemas=BACKUP_STORES.map(name=>{const s=db.transaction(name).objectStore(name);return {name,keyPath:s.keyPath,autoIncrement:s.autoIncrement}});
                  db.close();await new Promise((ok,no)=>{const r=indexedDB.deleteDatabase(DB_NAME);r.onsuccess=ok;r.onerror=no});
                  db=await new Promise((ok,no)=>{const r=indexedDB.open(DB_NAME,version);r.onupgradeneeded=()=>schemas.forEach(({name,...opts})=>r.result.createObjectStore(name,opts));r.onsuccess=()=>ok(r.result);r.onerror=no});
                  await replaceAllStores(d);
                }''',version)
                if version==11:self.seed(count=9)
                before=self.snapshot()
                self.assertEqual(self.page.evaluate('x=>validateBackup(x)',dict(backupFormat='kakezan-master-backup',backupVersion=version,data=before)),before)
                self.page.reload();self.ready()
                after=self.snapshot();self.assertEqual(self.page.evaluate('db.version'),12)
                for store in before:
                    if store!='awards':self.assertEqual(after[store],before[store],store)
                self.assertTrue(all(a in after['awards'] for a in before['awards']))
                self.assertEqual(len(after['awards']),len(before['awards'])+(version==11))

    def test_phone_tablet_radar_labels_cards_report_fit(self):
        for width,height in [(375,667),(667,375),(390,844),(844,390),(768,1024),(1024,768),(820,1180),(1180,820),(507,768)]:
            with self.subTest(size=(width,height)):
                self.page.set_viewport_size(dict(width=width,height=height));self.page.evaluate('navigateHome()')
                self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                self.assertTrue(self.page.evaluate('''()=>{
                  const svg=document.querySelector('#radar-chart svg'),b=svg.viewBox.baseVal;
                  return [...svg.querySelectorAll('text')].every(t=>{const r=t.getBBox();return r.x>=b.x&&r.y>=b.y&&r.x+r.width<=b.x+b.width&&r.y+r.height<=b.y+b.height});
                }'''))
                self.assertEqual(self.page.locator('#card-gallery .trophy').count(),10)
                self.page.evaluate('navigate("admin")')
                self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
