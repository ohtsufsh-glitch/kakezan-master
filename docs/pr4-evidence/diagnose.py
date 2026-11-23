# Executed during PR-4 as /tmp/pr4-diagnose.py; run from repository root.
import json,sys,time
sys.path.insert(0,'tests')
from arcade_board_test import ArcadeBoardTest
from runner_animation_test import RunnerAnimationTest

c=ArcadeBoardTest('test_crane_grip_and_lift_stay_together_across_widths_and_prize_sizes')
c.setUpClass()
rows=[]
try:
 c.setUp()
 original=c.page.evaluate
 def diagnostic(js,*args,**kw):
  if 'const stops={drop:' in js:
   js=js.replace('return {start,stops,frames,end:measure(),', '''const atReturn={opacity:getComputedStyle(toy).opacity, animations:toy.getAnimations().map(a=>({property:a.transitionProperty,state:a.playState,time:a.currentTime,timing:a.effect.getComputedTiming()}))};
           const before=performance.now();
           await Promise.all(toy.getAnimations().map(a=>a.finished));
           const settled={opacity:getComputedStyle(toy).opacity, animations:toy.getAnimations().length,elapsed:performance.now()-before};
           return {atReturn,settled,start,stops,frames,end:measure(),''')
  return original(js,*args,**kw)
 c.page.evaluate=diagnostic
 for width,height in [(375,812),(390,844),(430,932),(640,900),(641,900),(759,1000),(760,1000),(768,1024),(1024,768)]:
  for prize in ['star','secret_koryun']:
   c.page.set_viewport_size(dict(width=width,height=height));slots=['shiba','rabbit','shiba',prize,'bear','seal','cloud'];c.install(slots)
   a=c.sample_crane_animation('win');a.pop('frames');rows.append(dict(width=width,prize=prize,**a))
   print(json.dumps(rows[-1]),flush=True)
 c.tearDown()
finally:c.tearDownClass()
open('/tmp/pr4-evidence/crane-timings.json','w').write(json.dumps(rows,indent=2))
r=RunnerAnimationTest('test_delayed_and_failed_new_sprites_keep_input_and_same_character');r.setUpClass()
try:
 p,errors,requests=r.preview_runner()
 p.evaluate('window.pollProbe=false;setTimeout(()=>window.pollProbe=true,100)')
 results={}
 for polling in ['raf',50]:
  p.evaluate('window.pollProbe=false;setTimeout(()=>window.pollProbe=true,100)')
  start=time.monotonic()
  try:p.wait_for_function('window.pollProbe',polling=polling,timeout=700);result='pass'
  except Exception as e:result=type(e).__name__
  results[str(polling)]={'result':result,'elapsed':time.monotonic()-start,'flag':p.evaluate('pollProbe'),'pending':p.evaluate('runnerClock.snapshot().pending')}
 print('RUNNER_POLL_PROBE',json.dumps(results),flush=True)
 open('/tmp/pr4-evidence/runner-poll.json','w').write(json.dumps(results,indent=2))
finally:r.doCleanups();r.tearDownClass()
