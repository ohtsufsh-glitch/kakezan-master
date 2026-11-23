"""v0.4.3 fixed rewards and v12 compatibility; synthetic data only."""
import copy
import json
from pathlib import Path
import unittest
import multiplication_test as numeric
from mobile_regression_test import SIZES


class TableCoinRewardTest(unittest.TestCase):
    setUpClass = classmethod(numeric.MultiplicationTest.setUpClass.__func__)
    tearDownClass = classmethod(numeric.MultiplicationTest.tearDownClass.__func__)
    setUp = numeric.MultiplicationTest.setUp
    tearDown = numeric.MultiplicationTest.tearDown
    ready = numeric.MultiplicationTest.ready
    quiz = numeric.MultiplicationTest.quiz
    answer = numeric.MultiplicationTest.answer

    def valid(self, data, version=12):
        return self.page.evaluate('''x=>{try{return !!validateBackup({backupFormat:BACKUP_FORMAT,backupVersion:x.version,data:x.data})}catch{return false}}''', dict(data=data,version=version))

    def test_all_81_persisted_rewards_and_home_result_agree(self):
        rewards=[1,1,3,3,3,4,4,5,5]
        actual=self.page.evaluate('''async()=>{
          const results=[];
          for(const q of QUESTIONS){
            pickQuestion=()=>q;await startEra(q.era);
            if(phase==='result')await advance(q.era,q.id);
            numericInput=String(q.answer);await grade();
            results.push([q.left,q.right,lastCoinAward.amount,document.querySelector('#result').textContent]);
          }
          return results;
        }''')
        self.assertEqual(len(actual),81)
        for left,right,amount,text in actual:
            self.assertEqual(amount,rewards[left-1],(left,right))
            self.assertIn(f'コインを{amount}枚獲得！',text)
            self.assertNotIn('初習得',text);self.assertNotIn('初正解',text)
        data=self.page.evaluate('snapshotAllStores()')
        self.assertEqual(len(data['reviewEvents']),81)
        self.assertEqual(data['coinEvents'],[]);self.assertEqual(data['coinClaims'],[])
        self.assertTrue(self.valid(data))
        self.assertEqual(self.page.evaluate('getAvailableCoins()'),sum(rewards)*9)
        self.assertEqual(self.errors,[])

    def test_fixed_rewards_in_mix_weak_and_both_profiles(self):
        results=self.page.evaluate("""async()=>{
          const out=[];
          for(const who of ['student','test']){
            await navigateHome(who);
            for(const mode of ['mix','weak']){
              for(let left=1;left<=9;left++){
                const q=QUESTIONS.find(q=>q.left===left&&q.right===(mode==='mix'?1:2));
                // Real wrong answer makes this question eligible for weak mode.
                pickQuestion=()=>q;await startEra(q.era);
                if(phase==='result')await advance(q.era,q.id);
                numericInput='99';await grade();
                sampleStudyEntries=candidates=>candidates.filter(c=>c.id===q.id).map(c=>({questionId:c.id,revision:1}));
                await startStudy(mode,null,true);
                numericInput=String(q.answer);await grade();
                out.push([who,mode,left,lastCoinAward.amount]);
              }
            }
          }
          return out;
        }""")
        self.assertEqual(len(results),36)
        for who,mode,left,amount in results:self.assertEqual(amount,[1,1,3,3,3,4,4,5,5][left-1],(who,mode,left))
        for who in ['student','test']:self.assertEqual(self.page.evaluate('who=>getAvailableCoins(who)',who),58)
        self.assertTrue(self.valid(self.page.evaluate('snapshotAllStores()')))

    def test_replayed_reward_token_rolls_back_in_every_mode(self):
        for mode in ['era','mix','weak']:
            with self.subTest(mode=mode):
                self.page.evaluate("""async mode=>{
                  const q=QUESTIONS[['era','mix','weak'].indexOf(mode)*9];
                  pickQuestion=()=>q;await startEra(q.era);
                  if(phase==='result')await advance(q.era,q.id);
                  numericInput='99';await grade();
                  sampleStudyEntries=()=>[{questionId:q.id,revision:1}];
                  window.testMode=mode;
                  window.nextTest=async()=>mode==='era'?advance(q.era,q.id):startStudy(mode,null,true);
                  await nextTest();numericInput=String(q.answer);await grade();
                  window.replayToken=(await readAll('answers')).at(-1).token;
                  await nextTest();
                }""",mode)
                before=self.page.evaluate('snapshotAllStores()')
                self.page.evaluate("""async()=>{
                  const original=crypto.randomUUID;
                  crypto.randomUUID=()=>replayToken;
                  try{numericInput=String(currentQuestion.answer);await grade();}finally{crypto.randomUUID=original;}
                }""")
                self.assertEqual(self.page.evaluate('snapshotAllStores()'),before)
                self.assertEqual(self.page.evaluate('phase'),'question')
                self.answer()
                after=self.page.evaluate('snapshotAllStores()')
                self.assertEqual(len(after['answers']),len(before['answers'])+1)
                self.assertEqual(len(after['reviewEvents']),len(before['reviewEvents'])+1)
                self.assertTrue(self.valid(after))

    def test_old_numeric_rewards_mixed_restore_and_invalid_records(self):
        self.page.evaluate('pickQuestion=()=>QUESTIONS[18]');self.quiz('T03');self.answer()
        # Old numeric v12 history: first 2 + mastery 3 + review 2, with claims.
        old=self.page.evaluate('''async()=>{
          const d=await snapshotAllStores(),q=QUESTIONS[18],at=d.answers[0].at;
          d.reviewEvents[0].key=d.reviewEvents[0].key.replace('table:','review:');d.reviewEvents[0].amount=2;
          for(const stage of COIN_STAGES){const key=coinClaimKey('student',q.id,stage);
            d.coinClaims.push({key,profile:'student',questionId:q.id,stage,source:'reward',claimedAt:at});
            d.coinEvents.push({key,profile:'student',questionId:q.id,stage,amount:COIN_REWARDS.basic[stage],difficulty:'basic',at});}
          d.sessions[0].coinAward=2;d.sessions[0].coinStages=['review'];return d;
        }''')
        self.assertTrue(self.valid(old));self.assertTrue(self.valid(old,11))
        self.page.evaluate('d=>replaceAllStores(d)',old);self.page.reload();self.ready()
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),old)
        self.assertEqual(self.page.evaluate('getAvailableCoins()'),7)
        self.page.evaluate('pickQuestion=()=>QUESTIONS[18]');self.page.evaluate('advance("T03",currentQuestion.id)');self.answer()
        mixed=self.page.evaluate('snapshotAllStores()')
        self.assertEqual(mixed['coinClaims'],old['coinClaims']);self.assertEqual(mixed['coinEvents'],old['coinEvents'])
        self.assertEqual(mixed['reviewEvents'][:1],old['reviewEvents'])
        self.assertEqual(self.page.evaluate('getAvailableCoins()'),10)
        self.assertTrue(self.valid(mixed))
        with self.page.expect_download() as event:self.page.evaluate('exportBackup()')
        backup=json.loads(Path(event.value.path()).read_text())
        self.page.evaluate('x=>replaceAllStores(validateBackup(x))',backup);self.page.reload();self.ready()
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),mixed)
        broken=[]
        for amount in [0,-1,2,4,5,3.1,'3',None]:
            d=copy.deepcopy(mixed);d['reviewEvents'][-1]['amount']=amount;broken.append(d)
        for field,value in [('key','table:student:bad'),('profile','test'),('questionId','MULT:T08:03'),('difficulty','advanced'),('at','different')]:
            d=copy.deepcopy(mixed);d['reviewEvents'][-1][field]=value;broken.append(d)
        d=copy.deepcopy(mixed);d['reviewEvents'].append(d['reviewEvents'][-1]);broken.append(d)
        d=copy.deepcopy(mixed);d['answers'][-1]['correct']=False;broken.append(d)
        d=copy.deepcopy(mixed);d['answers'].pop();broken.append(d)
        d=copy.deepcopy(mixed);d['coinEvents'][0]['amount']=3;broken.append(d)
        d=copy.deepcopy(mixed);r=copy.deepcopy(d['reviewEvents'][-1]);r['key']=r['key'].replace('table:','review:');r['amount']=2;d['reviewEvents'].append(r);broken.append(d)
        d=copy.deepcopy(mixed);a=copy.deepcopy(d['answers'][-1]);a['id']+=1;d['answers'].append(a);broken.append(d)
        for i,d in enumerate(broken):self.assertFalse(self.valid(d),i)
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),mixed)

    def test_unclaimed_old_rewards_not_paid_and_unanswered_resume(self):
        self.page.evaluate('pickQuestion=()=>QUESTIONS[0]');self.quiz('T01');self.answer()
        old=self.page.evaluate('snapshotAllStores()');old['reviewEvents']=[]
        old['sessions'][0]['coinAward']=0;old['sessions'][0]['coinStages']=[]
        self.page.evaluate('d=>replaceAllStores(d)',old);self.page.reload();self.ready()
        self.assertEqual(self.page.evaluate('snapshotAllStores()'),old)
        self.page.evaluate('advance("T01",currentQuestion.id)');self.page.reload();self.ready();self.answer()
        data=self.page.evaluate('snapshotAllStores()')
        self.assertEqual(self.page.evaluate('getAvailableCoins()'),1)
        self.assertEqual(data['coinClaims'],[]);self.assertEqual(data['coinEvents'],[])
        self.assertEqual(len(data['reviewEvents']),1)

    def test_home_accessibility_layout_and_selection(self):
        evidence=Path('/tmp/table-coin-evidence');evidence.mkdir(exist_ok=True)
        metrics=[]
        for who in ['student','test']:
            self.page.evaluate('who=>navigateHome(who)',who)
            for scale in [100,200]:
                self.page.add_style_tag(content=f'html {{font-size:{scale}% !important}}')
                for width,height in SIZES:
                    self.page.set_viewport_size(dict(width=width,height=height))
                    rows=self.page.locator('#era-list > button').evaluate_all('''bs=>bs.map(b=>{
                      const r=b.getBoundingClientRect(),t=b.querySelector('strong').getBoundingClientRect(),c=b.querySelector('.table-coin-reward'),i=c.querySelector('img'),cr=c.getBoundingClientRect();
                      return {label:c.getAttribute('aria-label'),text:c.textContent,src:i.getAttribute('src'),alt:i.alt,hidden:i.getAttribute('aria-hidden'),image:i.getBoundingClientRect().width,
                        fits:b.scrollWidth<=b.clientWidth&&cr.right<=r.right&&cr.left>=r.left,overlap:!(t.right<=cr.left||t.bottom<=cr.top||cr.bottom<=t.top),touch:r.height>=44,
                        progress:!!b.querySelector('.track'),count:b.querySelector('.era-total').textContent,rank:b.querySelector('.rank-pill').textContent};})''')
                    self.assertEqual(len(rows),9)
                    for n,(row,amount) in enumerate(zip(rows,[1,1,3,3,3,4,4,5,5]),1):
                        self.assertEqual(row['label'],f'正解でコイン{amount}枚');self.assertEqual(row['text'],f'{amount}枚')
                        self.assertEqual(row['src'],'assets/coins/crown-gold.webp');self.assertEqual(row['alt'],'');self.assertEqual(row['hidden'],'true')
                        self.assertEqual(row['image'],17);self.assertTrue(row['fits'],(who,scale,width,height,n,row));self.assertFalse(row['overlap']);self.assertTrue(row['touch']);self.assertTrue(row['progress'])
                        self.assertIn('/ 9問 習得',row['count']);self.assertEqual(row['rank'],'れんしゅうスタート')
                    self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                    metrics.append(dict(profile=who,scale=scale,width=width,height=height,rows=rows))
                    if who=='student' and (width,height) in [(320,568),(1024,768),(507,768)]:
                        self.page.locator('#era-list').screenshot(path=str(evidence/f'home-{width}x{height}-{scale}.png'))
            self.assertIn('正解でコイン3枚',self.page.locator('#era-list button').nth(2).aria_snapshot())
            self.page.locator('#era-list button').nth(2).click();self.page.wait_for_function('quizReady&&phase==="question"')
            self.assertEqual(self.page.evaluate('currentQuestion.left'),3)
        (evidence/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))
        self.assertEqual(self.errors,[])
