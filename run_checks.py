"""Run real assertions against ordinary and deliberately weakened classifiers."""
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import experiment as e
import test_experiment

def suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(test_experiment.ExperimentTests)

def evaluate():
    r=unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite())
    return {'tests_run':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),
            'failed_tests':[t.id() for t,_ in r.failures+r.errors], 'passed':r.wasSuccessful()}

if __name__=='__main__':
    Path('artifacts').mkdir(exist_ok=True)
    normal=evaluate(); original=e.classify
    mutations=[]
    for name,kwargs in [('skip_strict_reduction',{'require_reduction':False}),
                        ('skip_baseline_acceptance',{'require_baseline':False})]:
        with patch.object(e,'classify',lambda f,b,k=kwargs:original(f,b,**k)):
            result=evaluate()
        mutations.append({'mutation':name,'detected':not result['passed'],**result})
    Path('artifacts/tests.json').write_text(json.dumps(normal,indent=2,sort_keys=True)+'\n')
    Path('artifacts/mutations.json').write_text(json.dumps(mutations,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'normal':normal,'mutations':mutations},sort_keys=True))
    if not normal['passed'] or not all(x['detected'] for x in mutations):raise SystemExit(1)
