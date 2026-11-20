import json
import math
import unittest
from pathlib import Path
import digital_evolution_e0 as d

class TestExperiment(unittest.TestCase):
    def test_metrics_is_deterministic(self):
        self.assertEqual(d.metrics((.3,.5,.7)),d.metrics((.3,.5,.7)))
    def test_metrics_bounds(self):
        for p in ((0,0,0),(1,1,1),(.4,.6,.7)):
            x=d.metrics(p)
            self.assertTrue(0<=x['accuracy']<=1)
            self.assertTrue(0<=x['violation']<=1)
            self.assertTrue(x['throughput']>0)
    def test_more_gaming_increases_proxy_but_reduces_verified(self):
        a=d.metrics((.5,.5,0));b=d.metrics((.5,.5,1))
        self.assertGreater(b['proxy'],a['proxy'])
        self.assertLess(b['verified_utility'],a['verified_utility'])
    def test_more_verification_reduces_violations(self):
        self.assertLess(d.metrics((.9,.5,.5))['violation'],d.metrics((.1,.5,.5))['violation'])
    def test_control_shift_is_stricter(self):
        a=d.metrics((.5,.5,.5));b=d.metrics((.5,.5,.5),shift=True)
        self.assertLess(b['accuracy'],a['accuracy'])
        self.assertGreater(b['violation'],a['violation'])
    def test_uniform_without_human_selection(self):
        p=d.choose_deployment(d.make_initial(42),False,__import__('random').Random(123))
        self.assertEqual(len(p),d.N)
        self.assertTrue(all(abs(x-1/d.N)<1e-12 for x in p))
    def test_audited_human_selection_nonuniform(self):
        p=d.choose_deployment(d.make_initial(42),True,__import__('random').Random(123))
        self.assertGreater(max(p)-min(p),.0001)
        self.assertAlmostEqual(sum(p),1)
    def test_offline_no_models(self):
        agents=d.make_initial(42)
        self.assertEqual(len(agents),d.N)
        self.assertTrue(all(len(x)==3 and all(isinstance(v,float) for v in x) for x in agents))
    def test_same_seed_replays(self):
        self.assertEqual(d.run_arm(1234,True,True,True),d.run_arm(1234,True,True,True))
    def test_different_selection_pressure_changes_result(self):
        x=d.run_arm(1234,False,False,False)
        y=d.run_arm(1234,True,False,False)
        self.assertNotEqual(x['verified_utility_normal'],y['verified_utility_normal'])
    def test_training_only_does_not_require_evolution(self):
        x=d.run_arm(1234,False,False,False)
        y=d.run_arm(1234,False,True,False)
        self.assertNotEqual(x['gaming_normal'],y['gaming_normal'])
    def test_evolution_only_does_not_require_training(self):
        x=d.run_arm(1234,False,False,False)
        y=d.run_arm(1234,False,False,True)
        self.assertNotEqual(x['gaming_normal'],y['gaming_normal'])
    def test_reward_type_must_be_explicit(self):
        with self.assertRaises(ValueError):
            d.run_arm(42,True,True,True,training_objective='secret')
    def test_eight_arms(self):
        o=json.loads((Path(__file__).parent/'results.json').read_text())
        self.assertEqual(set(o['summary']),set(o['arms']))
        self.assertEqual(len(o['arms']),8)
    def test_no_unearned_hypothesis_pass(self):
        o=json.loads((Path(__file__).parent/'results.json').read_text())
        self.assertFalse(o['hypothesis_supported_in_this_toy_world'])
        self.assertFalse(o['predefined_gates']['beats_best_two_force_by_002'])
    def test_no_authority_in_output(self):
        o=json.loads((Path(__file__).parent/'results.json').read_text())
        self.assertEqual(o['authority_effect'],'NONE')
        self.assertEqual(o['state'],'SIMULATED_ONLY')
    def test_original_replicates_checksum(self):
        import hashlib
        data=(Path(__file__).parent/'replicates.csv').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         'c9da2a292f34c3a261baffe9fd0a9ad4411131418891b3dc5756e0d4b9db32cf')

if __name__=='__main__':
    unittest.main(verbosity=2)
