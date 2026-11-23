"""PR-2: fixed basic numeric questions, reward stages and atomic persistence."""
import unittest
import multiplication_test as numeric

class PositiveCoinRewardTest(unittest.TestCase):
    setUpClass=classmethod(numeric.MultiplicationTest.setUpClass.__func__)
    tearDownClass=classmethod(numeric.MultiplicationTest.tearDownClass.__func__)
    setUp=numeric.MultiplicationTest.setUp
    tearDown=numeric.MultiplicationTest.tearDown
    ready=numeric.MultiplicationTest.ready
    quiz=numeric.MultiplicationTest.quiz
    answer=numeric.MultiplicationTest.answer

    def same_question(self):
        self.page.evaluate('pickQuestion=()=>QUESTIONS[0]')
        self.quiz('T01')

    def next_question(self):
        self.page.locator('#next').click();self.page.wait_for_function('quizReady&&phase==="question"')

    def fallback_question(self):
        self.same_question();self.answer();self.next_question();self.answer(False);self.next_question()

    def snapshot(self):return self.page.evaluate('snapshotAllStores()')

    def test_basic_rewards_first_master_review_relearning_and_reload(self):
        self.same_question()
        steps=[(True,1,'correct'),(False,0,None),(True,1,'correct'),(True,1,'correct'),(True,1,'correct'),(False,0,None),(True,1,'correct'),(True,1,'correct'),(True,1,'correct')]
        total=0
        for i,(correct,amount,stage) in enumerate(steps):
            if i:self.next_question()
            self.answer(correct);total+=amount
            self.assertEqual(self.page.evaluate('getAvailableCoins()'),total)
            self.assertEqual(self.page.evaluate('({amount:currentSession.coinAward,stages:currentSession.coinStages})'),dict(amount=amount,stages=[stage] if stage else []))
            before=self.snapshot();self.page.reload();self.ready()
            self.assertEqual(self.snapshot(),before)
            self.page.evaluate('pickQuestion=()=>QUESTIONS[0]')
        saved=self.snapshot()
        self.assertEqual(len(saved['answers']),9);self.assertEqual(len(saved['coinClaims']),0);self.assertEqual(len(saved['reviewEvents']),7)
        self.assertTrue(all(e['difficulty']=='basic' for e in saved['coinEvents']+saved['reviewEvents']))

    def test_mastery_without_legacy_claims_has_one_fixed_reward(self):
        self.same_question();self.answer()
        self.page.evaluate('''async()=>{const t=db.transaction(['coinClaims','coinEvents'],'readwrite');for(const n of ['coinClaims','coinEvents'])t.objectStore(n).clear();await new Promise(r=>t.oncomplete=r)}''')
        self.next_question();self.answer()
        self.assertEqual(self.page.evaluate('getAvailableCoins()'),2)
        self.assertEqual(self.page.evaluate('currentSession.coinStages'),['correct'])

    def test_double_submit_cannot_duplicate_fallback(self):
        self.fallback_question();self.answer()
        before=self.snapshot();self.page.evaluate('Promise.all([grade(),grade()])')
        self.assertEqual(self.snapshot(),before);self.assertEqual(len(before['reviewEvents']),2)

    test_two_tabs_commit_only_once=numeric.MultiplicationTest.test_simultaneous_tabs_and_numeric_restore

    def test_abort_after_reward_write_rolls_back_all_stores_and_retry(self):
        self.fallback_question();before=self.snapshot()
        self.page.evaluate('''()=>{window.originalAdd=IDBObjectStore.prototype.add;window.rewardWritten=false;
          IDBObjectStore.prototype.add=function(...args){const r=originalAdd.apply(this,args);
            if(this.name==='reviewEvents')r.addEventListener('success',()=>rewardWritten=true);
            if(this.name==='answers')r.addEventListener('success',()=>this.transaction.abort());return r;};}''')
        self.page.evaluate('numericInput=String(currentQuestion.answer);grade()')
        self.assertTrue(self.page.evaluate('rewardWritten'));self.assertEqual(self.snapshot(),before)
        self.page.evaluate('()=>{IDBObjectStore.prototype.add=originalAdd;}')
        self.page.reload();self.ready();self.answer()
        self.assertEqual(self.page.evaluate('getAvailableCoins()'),2)
        self.assertEqual(len(self.snapshot()['reviewEvents']),2)

    def test_profiles_independent_fallback_claims_balances(self):
        for who in ['student','test']:
            self.page.evaluate('who=>navigateHome(who)',who)
            self.fallback_question();self.answer()
            self.assertEqual(self.page.evaluate('getAvailableCoins()'),2)
        data=self.snapshot()
        for who in ['student','test']:
            self.assertEqual(len([r for r in data['reviewEvents'] if r['profile']==who]),2)
            self.assertEqual(len([r for r in data['coinClaims'] if r['profile']==who]),0)

    test_backup_preserves_rewards_and_existing_game_data=numeric.MultiplicationTest.test_legacy_backup_preserved_and_numeric_validation

    def test_saved_zero_result_no_retroactive_payment(self):
        self.fallback_question();self.answer()
        self.page.evaluate('''async()=>{const data=await snapshotAllStores();data.reviewEvents=[];
          data.sessions[0].coinAward=0;data.sessions[0].coinStages=[];await replaceAllStores(data)}''')
        before=self.snapshot();self.page.reload();self.ready()
        self.assertEqual(self.snapshot(),before);self.assertEqual(self.page.evaluate('getAvailableCoins()'),0)

    def test_numeric_learning_coins_pay_for_existing_games(self):
        self.same_question()
        for i in range(131):
            if i:self.page.evaluate('advance(currentEra,currentQuestion.id)')
            self.page.evaluate('numericInput=String(currentQuestion.answer);grade()')
        self.assertEqual(self.page.evaluate('getAvailableCoins()'),131)
        self.page.evaluate("purchaseRunnerPlay({profile:'student',stageId:'S01',characterId:'shiba'})")
        self.assertEqual(self.page.evaluate('getAvailableCoins()'),101)
        self.page.evaluate('openArcade()');self.page.evaluate('startCrane()')
        self.assertEqual(self.page.evaluate('getAvailableCoins()'),1)
        self.assertEqual(len(self.page.evaluate("readAll('awards')")),0)
        self.assertEqual(len(self.page.evaluate("readAll('coinSpends')")),2)
