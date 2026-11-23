// Run from repository root: node docs/pr4-evidence/runner-unattended.mjs
import * as m from '../../runner/game.js';
const rows=[];
for(const version of [1,7])for(const id of ['shiba','sloth','goldfish','salamander','bear']) {
  const s=m.createRunnerState(m.getStage('S06',version),id);s.mode='running';
  for(let frame=0;frame<120*120&&s.mode==='running';frame++)m.updateRunner(s,1/120);
  rows.push({version,id,score:s.score,distance:s.distance,reason:s.reason,lives:s.lives});
}
console.log(JSON.stringify(rows,null,2));
