// Diagnostic executed as /tmp/pr4-motion-probe.mjs; only import path made portable.
import * as runnerModel from '../../runner/game.js';console.log(JSON.stringify((()=>{
          const m=runnerModel,results=[];
          const checkpoint=s=>JSON.stringify({...s,lives:null,invincibleRemaining:null,
            objects:s.objects.filter(o=>o.type!=='obstacle')});
          for(const phase of ['ground','ascending','descending','platform','landing'])for(const hz of [60,120]){
            const s=m.createRunnerState([{at:0,type:'star',height:120},
              {at:.03,type:'platform'}]);s.mode='running';s.score=20;
            if(phase==='ascending'||phase==='descending'){
              m.startJump(s);m.updateRunner(s,phase==='ascending'?.02:.88);
            }
            if(phase==='platform'||phase==='landing'){
              s.objects.push({id:'support',type:'platform',x:186,height:20});
              s.feetY=phase==='platform'?450:449.5;s.velocityY=phase==='platform'?0:100;
              s.supportId=phase==='platform'?'support':null;s.airAction=phase==='platform'?null:'jump';
            }
            const control=structuredClone(s);
            m.updateRunner(control,1/hz);
            const height=m.GROUND_Y-control.feetY+m.characterBob(control);
            // 同じサブステップにスターと複数の岩が接触する。
            s.objects.push({id:'earned-now',type:'star',x:186,height},
              {id:'future-star',type:'star',x:800,height:0});
            const expected=structuredClone(s);
            s.objects.push({id:'rock-a',type:'obstacle',x:186},
              {id:'rock-b',type:'obstacle',x:186});
            m.updateRunner(expected,1/hz);m.updateRunner(s,1/hz);
            const after={mode:s.mode,lives:s.lives,score:s.score,support:s.supportId,
              airAction:s.airAction,shield:s.invincibleRemaining,preserved:checkpoint(s)===checkpoint(expected),diff:Object.keys(s).filter(k=>JSON.stringify(s[k])!==JSON.stringify(expected[k])),
              uncollected:s.objects.some(o=>o.id==='future-star'),
              collected:!s.objects.some(o=>o.id==='earned-now'),nextSpawn:s.nextSpawn};
            const score=s.score;m.updateRunner(s,0);
            after.noDuplicate=s.score===score;results.push({phase,hz,...after});
          }
          return results;
        })(),null,2));