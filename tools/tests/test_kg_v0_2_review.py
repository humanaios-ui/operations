"""Offline negative controls for Z1 HumanAIOS KG v0.2 review; synthetic fixtures."""
import copy
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'kg_v0_2_review.py'
spec = importlib.util.spec_from_file_location('kg_v0_2_review', MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class GraphReviewTests(unittest.TestCase):
    def setUp(self):
        self.base = {
            'graph_id': 'humanaios-kg-v0.1', 'authority_effect': 'NONE',
            'nodes': [{'id': 'A01', 'label': 'ACAT'}],
            'edges': [{'id': 16, 'source': 'A01', 'target': 'A01'}],
        }
        self.p = {
            'extends': 'humanaios-kg-v0.1', 'authority_effect': 'NONE',
            'new_nodes': [{'id': 'C01', 'label': 'Test'}],
            'edges': [
                {'id': 17, 'source': 'C01', 'target': 'A01',
                 'relation': 'depends_on', 'link_state': 'recorded',
                 'status': 'unratified', 'basis': {'type': 'registry', 'ref': 'IC-031', 'note': 'Source claims connection'}},
                {'id': 18, 'source': 'C01', 'target': 'registry:H-RCO-01',
                 'relation': 'resulted_in', 'link_state': 'candidate',
                 'status': 'unratified', 'basis': {'type': 'inference', 'ref': '', 'note': 'Hypothesis only'}},
            ],
        }

    def check(self, p=None, base=None):
        return mod.check(base or self.base, p or self.p)

    def test_valid_proposal_is_structural_only(self):
        z = self.check()
        self.assertEqual(z['verdict'], 'PASS_STRUCTURE_ONLY')
        self.assertFalse(z['can_authorize'])
        self.assertEqual(z['counts']['verified_human_outcomes_by_this_checker'], 0)
        self.assertEqual(z['external_locator_manifest'][0]['resolution'], 'UNVERIFIED_BY_STRUCTURE_CHECK')

    def test_cannot_promote_candidate_inference(self):
        p = copy.deepcopy(self.p)
        p['edges'][1]['link_state'] = 'recorded'
        self.assertTrue(self.check(p)['blockers'])

    def test_cannot_claim_ratification(self):
        p = copy.deepcopy(self.p)
        p['edges'][0]['status'] = 'ratified'
        self.assertTrue(self.check(p)['blockers'])

    def test_missing_note_is_blocked(self):
        p = copy.deepcopy(self.p)
        p['edges'][0]['basis']['note'] = ''
        self.assertTrue(self.check(p)['blockers'])

    def test_unknown_internal_source_is_blocked(self):
        p = copy.deepcopy(self.p)
        p['edges'][0]['source'] = 'FORGED'
        self.assertTrue(self.check(p)['blockers'])

    def test_invalid_external_target_is_blocked(self):
        p = copy.deepcopy(self.p)
        p['edges'][0]['target'] = 'evidence:../../secrets'
        self.assertTrue(self.check(p)['blockers'])

    def test_undeclared_external_prefix_is_blocked(self):
        p = copy.deepcopy(self.p)
        p['edges'][0]['target'] = 'warrant:trust-me'
        self.assertTrue(self.check(p)['blockers'])

    def test_colliding_edge_ids_are_blocked(self):
        p = copy.deepcopy(self.p)
        p['edges'][1]['id'] = 17
        self.assertTrue(self.check(p)['blockers'])

    def test_node_id_collision_is_blocked(self):
        p = copy.deepcopy(self.p)
        p['new_nodes'][0]['id'] = 'A01'
        self.assertTrue(self.check(p)['blockers'])

    def test_graph_extension_mismatch_is_blocked(self):
        p = copy.deepcopy(self.p)
        p['extends'] = 'research-358'
        self.assertTrue(self.check(p)['blockers'])

    def test_authority_expansion_is_blocked(self):
        p = copy.deepcopy(self.p)
        p['authority_effect'] = 'APPROVED'
        self.assertTrue(self.check(p)['blockers'])

    def test_hypothesis_is_not_verified_outcome(self):
        z = self.check()
        self.assertTrue(any('not a verified measured outcome' in x for x in z['warnings']))
        self.assertEqual(z['counts']['outcome_edges_requiring_independent_proof'], 1)

    def test_empty_first_seen_is_allowed(self):
        p = copy.deepcopy(self.p)
        p['new_nodes'][0]['first_dated'] = ''
        self.assertEqual(self.check(p)['blockers'], [])

    def test_missing_external_ref_does_not_claim_verified(self):
        z = self.check()
        self.assertTrue(all(row['resolution'] == 'UNVERIFIED_BY_STRUCTURE_CHECK' for row in z['external_locator_manifest']))

    def test_repo_content_not_written_or_imported(self):
        z = self.check()
        self.assertEqual(z['separate_research_graph'], 'NOT_IMPORTED_NOT_JOINED')


if __name__ == '__main__':
    unittest.main()
