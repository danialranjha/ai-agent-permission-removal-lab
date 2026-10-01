import itertools
import unittest
import experiment as e

class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.r = e.run()
        self.rows = {r['scenario']: r for r in self.r['scenarios']}

    def deletion(self, scenario, grant):
        return next(d for d in self.rows[scenario]['deletions'] if d['removed_grant'] == grant)

    def test_overlap_is_not_reduced_access(self):
        d = self.deletion('overlapping_file_directory','file_read')
        self.assertTrue(d['naive_witness']); self.assertFalse(d['strict_witness'])
        self.assertEqual(d['removed_operations'], [])
        self.assertTrue(d['branch']['probes']['read:sales'])
        self.assertEqual(d['branch']['output'], 'total=5\n')

    def test_genuine_optional_read_removal(self):
        d = self.deletion('optional_read','notes_read')
        self.assertTrue(d['strict_witness'])
        self.assertEqual(d['removed_operations'], ['read:notes'])
        self.assertFalse(d['branch']['probes']['read:notes'])
        self.assertEqual(d['branch']['output'],'total=5\n')

    def test_required_input_fails_task(self):
        d = self.deletion('required_input','sales_read')
        self.assertEqual(d['removed_operations'], ['read:sales'])
        self.assertFalse(d['branch']['accepted']); self.assertFalse(d['strict_witness'])
        self.assertIsNone(d['branch']['output'])

    def test_baseline_coverage_redundancy(self):
        d=self.deletion('baseline_overlap','notes_read')
        self.assertEqual(d['removed_operations'],[]); self.assertFalse(d['strict_witness'])

    def test_shared_dependency_kept(self):
        for d in self.rows['shared_dependency']['deletions']:
            self.assertIn('exec:runtime',d['branch']['authority'])
            self.assertIn('read:sales',d['branch']['authority'])
            self.assertTrue(d['strict_witness'])
            self.assertTrue(d['branch']['accepted'])

    def test_joint_removal_not_implied(self):
        self.assertTrue(all(d['strict_witness'] for d in self.rows['alternative_inputs']['deletions']))
        self.assertFalse(self.r['joint_removal_counterexample']['accepted'])
        self.assertIsNone(self.r['joint_removal_counterexample']['output'])

    def test_missing_baseline_oracle(self):
        d=self.deletion('missing_baseline_oracle','notes_read')
        self.assertTrue(d['naive_witness']); self.assertFalse(d['strict_witness'])

    def test_invalid_branch_oracle(self):
        d=self.deletion('invalid_branch_oracle','notes_read')
        self.assertTrue(d['branch']['task_output_matches'])
        self.assertFalse(d['naive_witness']);self.assertFalse(d['strict_witness'])

    def test_bad_baseline_output(self):
        row=self.rows['failed_baseline_task'];d=self.deletion('failed_baseline_task','notes_read')
        self.assertEqual(row['full']['output'],'total=6\n')
        self.assertTrue(d['branch']['accepted']);self.assertFalse(d['strict_witness'])

    def test_authority_all_subsets_independent_reachability_oracle(self):
        for s in e.scenarios():
            names=list(s.grants)
            subsets=[set(c) for n in range(len(names)+1) for c in itertools.combinations(names,n)]
            for sub in subsets:
                # Independent graph traversal from roots (compiler uses fixed-point union).
                todo=list(s.baseline)+[a for g in sub for a in s.grants[g]]
                seen=set()
                while todo:
                    a=todo.pop()
                    if a not in seen:
                        seen.add(a);todo.extend(s.dependencies.get(a,()))
                self.assertEqual(set(e.compile_authority(s,sub)),seen)
                for smaller in subsets:
                    if smaller<=sub:
                        self.assertLessEqual(e.compile_authority(s,smaller),e.compile_authority(s,sub))
        cycle=e.Scenario('cycle',{'g':{'tool:a'}},dependencies={'tool:a':{'tool:b'},'tool:b':{'tool:a'}})
        self.assertEqual(e.compile_authority(cycle,{'g'}),{'tool:a','tool:b','write:report'})

    def test_state_reset_probes_and_workload_oracle(self):
        expected=e.state_hash(e.RESOURCES)
        for row in self.r['scenarios']:
            for b in [row['full']]+[d['branch'] for d in row['deletions']]:
                self.assertEqual(b['initial_state_sha256'],expected)
                self.assertEqual(b['final_resource_sha256'],expected)
                self.assertEqual({op for op,ok in b['probes'].items() if ok},set(b['authority']))
                self.assertEqual(b['task_output_matches'],b['output']=='total=5\n')
        b=e.Broker(frozenset())
        with self.assertRaises(PermissionError):b.read('sales')
        with self.assertRaises(PermissionError):b.write_report('fake')
        self.assertEqual(b.sink,{})

    def test_reproducible_and_invalid_grants(self):
        self.assertEqual(self.r,e.run())
        with self.assertRaises(ValueError):e.compile_authority(e.scenarios()[0],{'unknown'})
        with self.assertRaises(ValueError):e.compile_authority(e.Scenario('bad',{'g':{'read:real'}}),{'g'})

if __name__=='__main__':unittest.main()
