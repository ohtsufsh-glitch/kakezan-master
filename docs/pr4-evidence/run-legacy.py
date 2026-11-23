import unittest,sys,json,time,pathlib
sys.path.insert(0,'tests')
modules=['question_feedback_test','quiz_coin_display_test','study_coin_integration_test','study_modes_test','ui_cleanup_test']
print('MODULES',json.dumps(modules),flush=True)
class Result(unittest.TextTestResult):
 def record(self,test,status,detail=''):
  with open('/tmp/pr4-legacy-results.jsonl','a') as f:f.write(json.dumps(dict(test=test.id(),status=status,detail=detail))+'\n')
 def addSuccess(self,test):super().addSuccess(test);self.record(test,'pass')
 def addFailure(self,test,err):super().addFailure(test,err);self.record(test,'fail',self._exc_info_to_string(err,test))
 def addError(self,test,err):super().addError(test,err);self.record(test,'error',self._exc_info_to_string(err,test))
 def addSubTest(self,test,subtest,err):
  super().addSubTest(test,subtest,err)
  if err:self.record(subtest,'subtest-fail',self._exc_info_to_string(err,test))
pathlib.Path('/tmp/pr4-legacy-results.jsonl').write_text('')
s=unittest.defaultTestLoader.loadTestsFromNames(modules)
r=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(s)
sys.exit(not r.wasSuccessful())
