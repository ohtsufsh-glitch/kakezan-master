"""PR-2 numeric learning; all data are synthetic, in ephemeral browser contexts."""
import copy
import unittest
import app_isolation_test as isolation

class MultiplicationTest(unittest.TestCase):
    setUpClass = classmethod(isolation.AppIsolationTest.setUpClass.__func__)
    tearDownClass = classmethod(isolation.AppIsolationTest.tearDownClass.__func__)
    setUp = isolation.AppIsolationTest.setUp
    tearDown = isolation.AppIsolationTest.tearDown
    ready = isolation.AppIsolationTest.ready

    def quiz(self, era='T03'):
        self.page.evaluate('era=>startEra(era)',era)
        self.page.wait_for_function('quizReady && phase==="question"')

    def answer(self, correct=True):
        n=self.page.evaluate('currentQuestion.answer' if correct else 'currentQuestion.answer===99?98:99')
        for d in str(n): self.page.locator(f'[data-key="{d}"]').click()
        self.page.locator('#check').click()
        self.page.wait_for_function('quizReady && phase==="result" && !saving')

    def test_generation_and_fixed_catalog(self):
        qs=self.page.evaluate('QUESTIONS')
        self.assertEqual(len(qs),81)
        self.assertEqual(len({q['id'] for q in qs}),81)
        for a in range(1,10):
            row=[q for q in qs if q['left']==a]
            self.assertEqual(len(row),9)
            for q in row:
                self.assertEqual(q['answer'],a*q['right'])
                self.assertEqual(q['id'],f'MULT:T{a:02}:{q["right"]:02}')
                self.assertNotIn('options',q)
                self.assertNotIn('answers',q)
                self.assertEqual(q['difficulty'],'basic')
        self.assertTrue(self.page.evaluate('Object.isFrozen(SAMPLE_QUESTIONS)&&SAMPLE_QUESTIONS.every(Object.isFrozen)'))
        self.assertEqual(self.page.locator('#era-list button').count(),9)
        self.assertEqual(self.errors,[])

    def test_keypad_result_reload_and_duplicate(self):
        self.quiz('T01')
        self.assertTrue(self.page.locator('#check').is_disabled())
        self.page.locator('[data-key="0"]').click()
        self.assertEqual(self.page.evaluate('numericInput'),'')
        for d in ['1','0','9']:self.page.locator(f'[data-key="{d}"]').click()
        self.assertEqual(self.page.evaluate('numericInput'),'10')
        self.page.locator('[data-key="けす"]').click()
        self.assertEqual(self.page.evaluate('numericInput'),'1')
        self.assertEqual(self.page.evaluate("async()=>[...(await readAll('answers'))].length"),0)
        q=self.page.evaluate('currentQuestion.id')
        self.page.reload();self.ready()
        self.assertEqual(self.page.evaluate('currentQuestion.id'),q)
        self.assertEqual(self.page.evaluate('numericInput'),'')
        self.answer(False)
        self.assertIn(self.page.evaluate('`${currentQuestion.left} × ${currentQuestion.right} = ${currentQuestion.answer}`'),self.page.locator('#result').inner_text())
        before=self.page.evaluate('snapshotAllStores()')
        self.page.evaluate('Promise.all([grade(),grade()])')
        self.page.reload();self.ready()
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),before)
        self.assertEqual(self.page.evaluate('phase'),'result')
        self.assertEqual(self.errors,[])

    def test_mix_twenty_unique_and_explicit_next(self):
        self.page.evaluate('startStudy("mix")')
        self.page.wait_for_function('quizReady')
        entries=self.page.evaluate('currentSession.entries')
        self.assertEqual(len(entries),20);self.assertEqual(len({e['questionId'] for e in entries}),20)
        for i in range(20):
            self.answer()
            self.assertEqual(self.page.evaluate('phase'),'result')
            self.assertEqual(self.page.evaluate('currentSession.position'),i)
            self.assertTrue(self.page.evaluate('async()=>{const d=await snapshotAllStores();return !!validateBackup({backupFormat:BACKUP_FORMAT,backupVersion:BACKUP_VERSION,data:d});}'))
            self.page.locator('#next').click()
            self.page.wait_for_function('currentSession.phase==="complete" || (quizReady&&phase==="question")')
        self.assertIn('20もんちゅう 20もん せいかい',self.page.locator('#study-result-summary').inner_text())
        self.assertEqual(len(self.page.evaluate("readAll('answers')")),20)
        self.assertEqual(self.errors,[])

    def test_mastery_shared_modes_coins_and_test_separation(self):
        self.quiz()
        q=self.page.evaluate('currentQuestion.id')
        self.answer(False)
        self.page.evaluate('startStudy("weak")');self.page.wait_for_function('quizReady&&phase==="question"')
        self.assertEqual(self.page.evaluate('currentQuestion.id'),q)
        self.answer()
        self.page.locator('#next').click();self.page.wait_for_function('currentSession.phase==="complete"')
        self.page.evaluate('startStudy("weak",null,true)');self.page.wait_for_function('quizReady&&phase==="question"')
        self.answer()
        p=self.page.evaluate('id=>readOne("progress",`student:${id}`)',q)
        self.assertTrue(p['mastered']);self.assertEqual(p['streak'],2);self.assertEqual(p['attempts'],3)
        self.assertEqual(self.page.evaluate('getAvailableCoins()'),6)
        self.assertEqual(self.page.evaluate('studyCandidates("weak",null,QUESTIONS,new Map([[currentQuestion.id,currentProgress]])).length'),0)
        self.page.evaluate('beginTestMode()');self.quiz()
        self.assertEqual(self.page.evaluate('getAvailableCoins()'),0)
        self.assertIsNone(self.page.evaluate('id=>readOne("progress",`test:${id}`)',q))
        # Force the same numeric question as a normal next draw, then wrong clears mastery.
        self.page.evaluate('returnToStudentHome()')
        self.page.evaluate('id=>{pickQuestion=()=>QUESTIONS.find(q=>q.id===id)}',q)
        self.page.evaluate('startEra("T03")');self.page.evaluate('advance(currentEra,currentQuestion.id)');self.page.wait_for_function('phase==="question"')
        self.answer(False)
        self.assertFalse(self.page.evaluate('id=>readOne("progress",`student:${id}`).then(p=>p.mastered)',q))

    def test_legacy_backup_preserved_and_numeric_validation(self):
        self.page.evaluate('''()=>{window.plushFixture=undefined;}''')
        import plush_test
        self.page.evaluate(plush_test.FIXTURE_HELPERS)
        legacy=self.page.evaluate("""async()=>{
          const d=plushFixture(['shiba'],'student'),q=d.questions[0],at='2020-01-01T00:00:00.000Z';
          d.studySets=[{key:'student:weak',profile:'student',mode:'weak',genre:null,setId:crypto.randomUUID(),
            entries:[{questionId:q.id,revision:1}],position:0,phase:'question',questionId:q.id,revision:1,
            selected:[0],optionOrder:[0,1],results:[],startedAt:at,updatedAt:at}];
          d.questionFeedback=[{reportId:crypto.randomUUID(),questionId:q.id,questionRevision:1,
            questionHash:await sha256Text(questionFingerprintSource(q)),questionSnapshot:{...exportableQuestion(q),deleted:false},
            reporterRole:'admin',category:'other',comment:'Synthetic legacy feedback',createdAt:at,status:'unreviewed',statusUpdatedAt:at}];
          return d;
        }""")
        legacy['sampleSettings']=[{'id':'SAMPLE-E01-001','hidden':True}]
        self.assertEqual(self.page.evaluate('data=>validateBackup({backupFormat:BACKUP_FORMAT,backupVersion:10,data})',legacy),legacy)
        self.page.evaluate('data=>replaceAllStores(data)',legacy)
        legacy=self.page.evaluate('snapshotAllStores()')
        self.page.reload();self.ready()
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),legacy)
        self.quiz();self.answer()
        data=self.page.evaluate('snapshotAllStores()')
        for store in ['questions','awards','coinSpends','arcadePlays','arcadePrizes','arcadeBoards','sampleSettings','studySets','questionFeedback']:
            self.assertEqual(data[store],legacy[store])
        self.assertEqual(self.page.evaluate('data=>validateBackup({backupFormat:BACKUP_FORMAT,backupVersion:BACKUP_VERSION,data})',data),data)
        bad=copy.deepcopy(data);bad['answers'][-1]['answer']=0
        for payload in [dict(backupFormat='kakezan-master-backup',backupVersion=11,data=bad),dict(backupFormat='history-master-backup',backupVersion=11,data=data)]:
            self.assertTrue(self.page.evaluate('x=>{try{validateBackup(x);return false}catch{return true}}',payload))
        self.assertEqual(self.errors,[])

    def test_weights_recent_exclusion_and_candidates(self):
        result=self.page.evaluate("""()=>{
          const oldRandom=Math.random,oldEvents=answerEvents;answerEvents=[];
          try {
            const row=QUESTIONS.filter(q=>q.era==='T01'),records=new Map(row.map(q=>[q.id,{revision:1,mastered:true,streak:2}]));
            records.delete(row[0].id);
            // Equal base weight 5: first item spans 10/(10+8) of the draw.
            Math.random=()=>0.5;
            const weighted=pickQuestion('T01',records,null).id;
            const recent=row.slice(0,3).map(q=>q.id);
            const fresh=pickQuestion('T01',records,recent[0],recent).id;
            const mix=sampleStudyEntries(row,[],profile).map(e=>e.questionId);
            const weakRecords=new Map([[row[0].id,{everWrong:true,mastered:false}],[row[1].id,{everWrong:true,mastered:true}],[row[2].id,{everWrong:false,mastered:false}]]);
            return {weighted,fresh,recent,mix,weak:studyCandidates('weak',null,row,weakRecords).map(q=>q.id),weights:[questionWeight(),questionWeight({attempts:8,correct:4})]};
          } finally {Math.random=oldRandom;answerEvents=oldEvents;}
        }""")
        self.assertEqual(result['weighted'],'MULT:T01:01')
        self.assertNotIn(result['fresh'],result['recent'])
        self.assertEqual(len(result['mix']),9)
        self.assertEqual(result['weak'],['MULT:T01:01'])
        self.assertEqual(result['weights'],[5,3])

    def test_simultaneous_tabs_and_numeric_restore(self):
        self.quiz('T09')
        other=self.context.new_page();other.goto(self.url);other.wait_for_function('appReady')
        other.evaluate('startEra("T09")');other.wait_for_function('quizReady')
        for page in [self.page,other]:
            page.evaluate('numericInput=String(currentQuestion.answer);updateChoices()')
        self.page.evaluate('window.pendingGrade=grade()')
        other.evaluate('grade()');self.page.evaluate('pendingGrade')
        self.assertEqual(len(self.page.evaluate("readAll('answers')")),1)
        self.assertEqual(self.page.evaluate('getAvailableCoins()'),5)
        before=self.page.evaluate('snapshotAllStores()')
        with self.page.expect_download() as event:self.page.evaluate('exportBackup()')
        import json
        from pathlib import Path
        backup=json.loads(Path(event.value.path()).read_text())
        self.assertEqual(backup['backupVersion'],12)
        self.page.evaluate('x=>replaceAllStores(validateBackup(x))',backup)
        self.page.reload();self.ready()
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),before)
        self.assertEqual(self.page.evaluate('phase'),'result')
        other.close()

    def test_actual_v10_database_upgrade_preserves_all_stores(self):
        import plush_test
        self.page.evaluate(plush_test.FIXTURE_HELPERS)
        self.page.evaluate("""async()=>{
          const data=plushFixture(['shiba'],'student');
          const schemas=BACKUP_STORES.map(name=>{const s=db.transaction(name).objectStore(name);return {name,keyPath:s.keyPath,autoIncrement:s.autoIncrement};});
          db.close();await new Promise((ok,no)=>{const r=indexedDB.deleteDatabase(DB_NAME);r.onsuccess=ok;r.onerror=no;});
          db=await new Promise((ok,no)=>{const r=indexedDB.open(DB_NAME,10);r.onupgradeneeded=()=>schemas.forEach(({name,...opts})=>r.result.createObjectStore(name,opts));r.onsuccess=()=>ok(r.result);r.onerror=no;});
          await replaceAllStores(data);
        }""")
        before=self.page.evaluate('snapshotAllStores()')
        self.page.reload();self.ready()
        self.assertEqual(self.page.evaluate('db.version'),12)
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),before)

    def test_mix_draft_and_result_resume_and_malformed_backup(self):
        self.page.evaluate('startStudy("mix")');self.page.wait_for_function('quizReady')
        self.page.locator('[data-key="1"]').click()
        q=self.page.evaluate('currentQuestion.id');entries=self.page.evaluate('currentSession.entries')
        self.page.reload();self.ready()
        self.assertEqual(self.page.evaluate('numericInput'),'')
        self.assertEqual(self.page.evaluate('currentQuestion.id'),q)
        self.assertEqual(self.page.evaluate('currentSession.entries'),entries)
        self.answer(False);before=self.page.evaluate('snapshotAllStores()')
        self.page.evaluate('navigateHome()');self.page.go_back();self.page.wait_for_function('quizReady')
        self.assertEqual(self.page.evaluate('phase'),'result')
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),before)
        self.assertTrue(self.page.evaluate("""data=>[
          d=>d.answers.at(-1).answer=100,
          d=>d.answers.at(-1).correct=!d.answers.at(-1).correct,
          d=>d.answers.push({...d.answers.at(-1)}),
          d=>d.studySets[0].selected=[0],
          d=>d.studySets[0].results[0].answer=0,
          d=>d.studySets[0].entries[1]={...d.studySets[0].entries[0]},
          d=>d.studySets[0].questionId='unknown'
        ].every(m=>{const d=structuredClone(data);m(d);try{validateBackup({backupFormat:BACKUP_FORMAT,backupVersion:BACKUP_VERSION,data:d});return false}catch{return true}})""",before))
