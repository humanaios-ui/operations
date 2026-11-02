"""Offline contract tests for read-only, non-authoritative containment projection."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXED = '2026-10-22T12:31:00-05:00'  # fixture time, not a claimed observation
SCRIPT = ROOT / 'research/agent_containment/phase0/containment_evidence_adapter.py'
SOURCE_NAMES = ('EVIDENCE_GRAPH.json',
                'research/agent_containment/phase0/scenario.json',
                'research/agent_containment/phase0/trial_receipt.json')

spec = importlib.util.spec_from_file_location('containment_evidence_adapter', SCRIPT)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for source in SOURCE_NAMES:
            dst = self.root / source
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / source, dst)
        self.prior = (self.root / 'EVIDENCE_GRAPH.json').read_bytes()

    def doc(self, name):
        return json.loads((self.root / name).read_text())

    def replace(self, name, payload):
        (self.root / name).write_text(json.dumps(payload))

    def test_synthetic_model_replay_matches_declared_receipt(self):
        model = ROOT / 'research/agent_containment/phase0/phase0_sim.py'
        mod_spec = importlib.util.spec_from_file_location('phase0_sim', model)
        mod = importlib.util.module_from_spec(mod_spec)
        mod_spec.loader.exec_module(mod)
        sim, results = mod.trial()
        declared = self.doc(SOURCE_NAMES[2])
        self.assertEqual(declared['trial_results'], results)
        self.assertTrue(mod.SimBoard.verify(sim.replay()))
        self.assertEqual(declared['events'], len(sim.events))
        self.assertEqual(declared['head_hash'], sim.events[-1]['hash'])
        self.assertEqual(declared['quarantined_events'], sum(e['event_type'] == 'containment_event' for e in sim.events))
        # This is same-model replay, not independent verification of a live runtime.

    def test_projection_non_authoritative_and_linked(self):
        graph = adapter.project(self.root, FIXED)
        self.assertEqual(graph['source']['system'], 'evidence_graph')
        self.assertEqual(graph['source']['visibility'], 'internal')
        self.assertEqual(graph['schema_version'], 'humanaios.graph.observation_projection.v0')
        self.assertTrue(graph['source']['revision'].startswith('sha256:'))
        nodes = {n['id']: n for n in graph['nodes']}
        self.assertIn('eg.CT1', nodes)
        self.assertIn('eg.CT2', nodes)
        self.assertIn('eg.C1', nodes)
        self.assertEqual(len([n for n in nodes if n.startswith('sim.trial.')]), 12)
        self.assertEqual(nodes['sim.receipt']['evidence']['state'], 'unresolved')
        self.assertTrue(all(nodes[f'sim.trial.T{i:02}']['evidence']['state'] == 'unresolved'
                            for i in range(1, 13)))
        self.assertIn(('sim.trial.T06', 'eg.CT1'),
                      {(e['from'], e['to']) for e in graph['edges']})
        self.assertTrue(all(e['evidence']['state'] == 'inferred'
                            for e in graph['edges'] if e['id'].startswith('sim.edge.crosswalk.')))
        self.assertFalse(any('authoriz' in e['relation'].lower() or 'ratif' in e['relation'].lower()
                             for e in graph['edges']))

    def test_empty_relation_fails_closed(self):
        graph = self.doc(SOURCE_NAMES[0])
        graph['edges'][0]['relation'] = ''
        self.replace(SOURCE_NAMES[0], graph)
        with self.assertRaisesRegex(adapter.ProjectionError, 'invalid graph edge'):
            adapter.project(self.root, FIXED)

    def test_required_crosswalk_cannot_be_silently_lost(self):
        scenario = self.doc(SOURCE_NAMES[1])
        receipt = self.doc(SOURCE_NAMES[2])
        for row in scenario['trial']:
            if row['id'] == 'T06':
                row['id'] = 'MISSING_CROSSWALK'
        for row in receipt['trial_results']:
            if row['id'] == 'T06':
                row['id'] = 'MISSING_CROSSWALK'
        self.replace(SOURCE_NAMES[1], scenario)
        self.replace(SOURCE_NAMES[2], receipt)
        with self.assertRaisesRegex(adapter.ProjectionError, 'crosswalk trials missing'):
            adapter.project(self.root, FIXED)

    def test_trial_id_length_rejected(self):
        scenario = self.doc(SOURCE_NAMES[1])
        receipt = self.doc(SOURCE_NAMES[2])
        long_id = 'A' * 106
        scenario['trial'][0]['id'] = long_id
        receipt['trial_results'][0]['id'] = long_id
        self.replace(SOURCE_NAMES[1], scenario)
        self.replace(SOURCE_NAMES[2], receipt)
        with self.assertRaisesRegex(adapter.ProjectionError, 'mismatched trial ID'):
            adapter.project(self.root, FIXED)

    def test_trial_id_maximum_accepted_and_schema_valid(self):
        from jsonschema import Draft202012Validator, FormatChecker
        scenario = self.doc(SOURCE_NAMES[1])
        receipt = self.doc(SOURCE_NAMES[2])
        max_id = 'A' * 105
        scenario['trial'][0]['id'] = max_id
        receipt['trial_results'][0]['id'] = max_id
        self.replace(SOURCE_NAMES[1], scenario)
        self.replace(SOURCE_NAMES[2], receipt)
        output = adapter.project(self.root, FIXED)
        self.assertTrue(all(len(n['id']) <= 128 for n in output['nodes']))
        self.assertTrue(all(len(e['id']) <= 128 for e in output['edges']))
        schema = json.loads((ROOT / 'docs/graph_integration/observation_projection_v0.schema.json').read_text())
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(output)

    def test_space_separated_date_normalized_to_iso(self):
        output = adapter.project(self.root, '2026-10-22 12:31:00-05:00')
        self.assertEqual(output['source']['observed_at'], FIXED)

    def test_source_graph_not_changed(self):
        adapter.project(self.root, FIXED)
        self.assertEqual((self.root / 'EVIDENCE_GRAPH.json').read_bytes(), self.prior)
        self.assertEqual(sorted(p.relative_to(self.root).as_posix()
                                for p in self.root.rglob('*') if p.is_file()), sorted(SOURCE_NAMES))

    def test_determinism(self):
        self.assertEqual(adapter.project(self.root, FIXED), adapter.project(self.root, FIXED))

    def test_nonzero_production_effect_rejected(self):
        name = SOURCE_NAMES[2]
        r = self.doc(name)
        r['production_receipts'] = 1
        self.replace(name, r)
        with self.assertRaisesRegex(adapter.ProjectionError, 'zero production effects'):
            adapter.project(self.root, FIXED)

    def test_mismatched_scenario_rejected(self):
        name = SOURCE_NAMES[2]
        r = self.doc(name)
        r['scenario_id'] = 'ANOTHER-SCENARIO'
        self.replace(name, r)
        with self.assertRaisesRegex(adapter.ProjectionError, 'ID mismatch'):
            adapter.project(self.root, FIXED)

    def test_mismatched_quarantine_count_rejected(self):
        name = SOURCE_NAMES[2]
        r = self.doc(name)
        r['quarantined_events'] = 0
        self.replace(name, r)
        with self.assertRaisesRegex(adapter.ProjectionError, 'quarantine count'):
            adapter.project(self.root, FIXED)

    def test_duplicate_trial_rejected(self):
        name = SOURCE_NAMES[2]
        r = self.doc(name)
        r['trial_results'][1]['id'] = 'T01'
        self.replace(name, r)
        with self.assertRaisesRegex(adapter.ProjectionError, 'duplicate/out-of-order'):
            adapter.project(self.root, FIXED)

    def test_missing_anchor_rejected(self):
        name = SOURCE_NAMES[0]
        graph = self.doc(name)
        graph['nodes'] = [n for n in graph['nodes'] if n['id'] != 'CT1']
        graph['edges'] = [e for e in graph['edges'] if e['to'] != 'CT1' and e['from'] != 'CT1']
        self.replace(name, graph)
        with self.assertRaisesRegex(adapter.ProjectionError, 'anchors missing'):
            adapter.project(self.root, FIXED)

    def test_cannot_read_outside_repository(self):
        with self.assertRaisesRegex(adapter.ProjectionError, 'outside repository'):
            adapter.load_json(self.root, '../anywhere.json')

    def test_naive_timestamp_rejected(self):
        with self.assertRaisesRegex(adapter.ProjectionError, 'timezone'):
            adapter.project(self.root, '2026-10-22T12:31:00')

    def test_schema_contract(self):
        # A missing contract dependency must fail, not silently skip validation.
        from jsonschema import Draft202012Validator, FormatChecker
        schema = json.loads((ROOT / 'docs/graph_integration/observation_projection_v0.schema.json').read_text())
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(adapter.project(self.root, FIXED))

    def test_cli_check_no_write(self):
        before = {name: (self.root / name).read_bytes() for name in SOURCE_NAMES}
        result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root),
                                 '--observed-at', FIXED, '--check'],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('PASS:', result.stdout)
        self.assertEqual(before, {name: (self.root / name).read_bytes() for name in SOURCE_NAMES})


if __name__ == '__main__':
    unittest.main()
