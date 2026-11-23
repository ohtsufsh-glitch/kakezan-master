import sys,unittest,pathlib,re,json,csv,collections
sys.path.insert(0,'tests')

def flat(s):
 for t in s:
  if isinstance(t,unittest.TestSuite):yield from flat(t)
  else:yield t.id()

def json_results(path):
 out={}
 for line in pathlib.Path(path).read_text().splitlines():
  r=json.loads(line);key=r['test'].split(' (')[0]
  status='pass' if r['status']=='pass' else 'fail'
  if out.get(key)!='fail':out[key]=status
 return out

def text_results(path):
 out={};current=None
 for l in pathlib.Path(path).read_text().splitlines():
  m=re.match(r'^test_\S+ \(([^)]+)\) \.\.\.\s*(.*)$',l)
  if m:
   current=m[1]
   if m[2] in ['ok','FAIL','ERROR']:out[current]='pass' if m[2]=='ok' else 'fail'
  elif l.startswith('  test_') and current and re.search(r'\.\.\. (FAIL|ERROR)$',l):out[current]='fail'
 return out
old6={'admin_menu_hierarchy_test','coin_wording_test','era_question_weight_test','history_navigation_test','improvement_request_test','question_editor_test'}
explore=text_results('/tmp/pr4-discover.log');early={k:v for k,v in explore.items() if k.split('.')[0] in old6}
assert len(early)==108,len(early)
current=json_results('/tmp/pr4-current-results.jsonl');legacy=json_results('/tmp/pr4-legacy-results.jsonl');assert len(current)==421 and len(legacy)==106
retests={}
for p in ['pr4-backup-retest.log','pr4-crane-legacy-retest.log','pr4-version-expectations-retest.log','pr4-runner-controls-retest.log','pr4-hit-probe-retest.log','pr4-collision-retest.log']:
 retests.update(text_results('/tmp/'+p))
final_current={**current,**retests};final_legacy={**early,**legacy};final={**final_legacy,**final_current}
ids=set(flat(unittest.defaultTestLoader.discover('tests',pattern='*_test.py')))
assert set(final)==ids,(len(final),len(ids),ids-set(final),set(final)-ids)
with open('docs/pr4-evidence/test-results.csv','w') as f:
 w=csv.writer(f, lineterminator="\n");w.writerow(['test_id','group','exploration_old_6','current_batch','legacy_remainder','targeted_retest','last_observed'])
 for key in sorted(ids):w.writerow([key,'current' if key in current else 'historical_mixed',early.get(key,''),current.get(key,''),legacy.get(key,''),retests.get(key,''),final[key]])
summary={k:dict(collections.Counter(v.values())) for k,v in [('early_6',early),('current_initial',current),('legacy_remainder',legacy),('current_last',final_current),('legacy_last',final_legacy),('all_last',final)]}
summary['unique_coverage']=len(ids)
byfile={}
for mod in sorted({k.split('.')[0] for k in ids}):
 group={k:v for k,v in final.items() if k.split('.')[0]==mod};byfile[mod]=dict(collections.Counter(group.values()))
summary['by_file']=byfile
pathlib.Path('docs/pr4-evidence/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='by_file'},indent=2))
print('remaining current failures:');print('\n'.join(k for k,v in final_current.items() if v!='pass'))
