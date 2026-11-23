import unittest,sys,json,time,pathlib
sys.path.insert(0,'tests')
legacy={'admin_menu_hierarchy','coin_wording','era_question_weight','history_navigation','improvement_request','question_editor','question_feedback','quiz_coin_display','study_coin_integration','study_modes','ui_cleanup'}
modules=[p.stem for p in sorted(pathlib.Path('tests').glob('*_test.py')) if p.stem.removesuffix('_test') not in legacy]
print('MODULES',json.dumps(modules),flush=True)
class Result(unittest.TextTestResult):
 def record(self,test,status,detail=''):
  with open('/tmp/pr4-current-results.jsonl','a') as f:f.write(json.dumps(dict(test=test.id(),status=status,detail=detail))+'\n')
 def addSuccess(self,test):super().addSuccess(test);self.record(test,'pass')
 def addFailure(self,test,err):super().addFailure(test,err);self.record(test,'fail',self._exc_info_to_string(err,test))
 def addError(self,test,err):super().addError(test,err);self.record(test,'error',self._exc_info_to_string(err,test))
 def addSubTest(self,test,subtest,err):
  super().addSubTest(test,subtest,err)
  if err:self.record(subtest,'subtest-fail',self._exc_info_to_string(err,test))
pathlib.Path('/tmp/pr4-current-results.jsonl').write_text('')
s=unittest.defaultTestLoader.loadTestsFromNames(modules)
r=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(s)
sys.exit(not r.wasSuccessful())
