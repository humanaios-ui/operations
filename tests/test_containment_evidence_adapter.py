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
SCRIPT = ROOT / 'tools/containment_evidence_adapter.py'
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

    def test_schema_contract_if_jsonschema_available(self):
        try:
            from jsonschema import Draft202012Validator, FormatChecker
        except ImportError:
            self.skipTest('jsonschema missing; stdlib checks still run')
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
