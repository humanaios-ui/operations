from copy import deepcopy
from datetime import datetime, timezone
import json
import unittest
import tempfile
from pathlib import Path
from resource_system.contracts import ValidationError
from resource_system.contracts import ROOT, validate
from resource_system.adapters.resource_miner_adapter import ingest
from resource_system.adapters.entitlement_navigator_adapter import investigate
from resource_system.controller.portfolio_sweep import sweep, convergence, routing_from_outcomes
from resource_system.runtime.scheduler import tick, execute_external, LocalRuntime
from resource_system.runtime.state_store import StateStore
from resource_system.gateway import ClaimGateway
from resource_system.artifacts import build_artifact
from resource_system.manager.inventory import Inventory

TODAY = '2026-10-10'
NOW = datetime(2026, 10, 10, tzinfo=timezone.utc)

def resource(rid='RM-002'):
    return dict(schema_version='1.0', id=rid, source_url='https://example.org/spec',
                action_url='https://example.org/apply', source_handoff_id='rm:' + rid,
                eligibility='UNASSESSED', state='DISCOVERED', resource_types=['EMPLOYMENT'], requirements=['capability'])

def evidence(eid='e1', value=True, classification='GLOBAL'):
    return dict(schema_version='1.0', id=eid, predicate='capability', value=value,
                classification=classification, material=True, resource_ids=['RM-002'],
                source_url='urn:synthetic:repository', provenance_type='REPOSITORY', observed_on=TODAY)

def rule(rid='RM-002'):
    return dict(schema_version='1.0', id='rules:' + rid, resource_id=rid, authoritative=True,
                source_url='https://example.org/spec', verified_on=TODAY, valid_until='2026-10-31', predicates=['capability'])

def auth(operation='ARTIFACT'):
    return dict(schema_version='1.0', id='a1', resource_id='RM-002', purpose='PREPARE',
                recipient='https://example.org/apply', operation=operation, state='GRANTED',
                human_authorized=True, expires_at='2026-10-11T00:00:00Z')

def activity(state='CLICKED'):
    return dict(schema_version='1.0', id='activity1', resource_id='RM-002', state=state,
                actor='HUMAN', source_url='https://example.org/spec', action_url='https://example.org/apply',
                artifact_ids=[], outcome='UNKNOWN', material=False, purpose='PREPARE',
                authorization_id=None, next_operation='CHECK_IN')

class ResourceSystemTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def test_material_rescan_batch_and_replay(self):
        resources = [resource(), resource('second')]
        rules = {r['id']: rule(r['id']) for r in resources}
        initial = sweep(resources, [], rules, TODAY)
        assert initial['questions'] == {'capability': ['RM-002', 'second']}
        updated = tick(resources, [evidence()], rules, TODAY, changed_evidence=evidence())
        assert updated['rescan_ids'] == ['RM-002', 'second']
        assert updated['questions'] == {}
        assert all(b['warrant'] and b['authority_effect'] == 'NONE' for b in updated['branches'].values())
        replay = tick(resources, [evidence()], rules, TODAY, logic_changed=True)
        assert replay['rescan_ids'] == ['RM-002', 'second'] and not replay['questions']
        local = tick(resources, [evidence(classification='LOCAL')], rules, TODAY, changed_evidence=evidence(classification='LOCAL'))
        assert local['rescan_ids'] == ['RM-002'] and local['questions'] == {'capability': ['second']}

    def test_frontier_expansion_and_external_boundary(self):
        result = tick([], [], {}, TODAY, frontier=['new-domain'], exhausted=True)
        assert result['scan_queue'] == ['new-domain'] and not result['scan_executed']
        assert not result['external_execution_enabled']
        with self.assertRaises(PermissionError):
            execute_external()

    def test_currentness_contradiction_and_disqualifier(self):
        r, rules = resource(), {'RM-002': rule()}
        assert not sweep([r], [evidence()], rules, '2026-11-01')['branches']['RM-002']['warrant']
        for nodes in [[evidence(), evidence('e2', False)], [evidence(classification='DISQUALIFYING')], [evidence(classification='CONTRADICTORY')]]:
            assert sweep([r], nodes, rules, TODAY)['branches']['RM-002']['eligibility'] == 'BLOCKED'
        assert not sweep([r], [evidence()], {}, TODAY)['branches']['RM-002']['warrant']

    def test_miner_handoff_preserves_boundary(self):
        candidate = dict(resource_id='rm1', eligibility_assessed=False, eligibility_status='UNASSESSED',
                         canonical_url='https://example.org/spec', resource_types=['GRANT'], need_matches=['high'])
        result = ingest(candidate)
        validate('resource', result)
        assert result['eligibility'] == 'UNASSESSED'
        assert investigate(candidate)['authority_effect'] == 'NONE'
        with self.assertRaises(ValueError):
            ingest({**candidate, 'eligibility_assessed': True})

    def test_pii_minimum_disclosure_and_receipt(self):
        tmp_path = Path(self.directory.name)
        store, gateway = StateStore(tmp_path / 'events.jsonl'), ClaimGateway()
        gateway.put('identity', 'SYNTHETIC PRIVATE VALUE')
        claim = gateway.claim('claim1', 'capability', True, 'e1')
        store.append('claim', claim)
        with self.assertRaises(PermissionError):
            gateway.disclose('identity', 'RM-002', 'PREPARE', 'https://example.org/apply', [], store, NOW)
        granted = auth('DISCLOSE')
        assert gateway.disclose('identity', 'RM-002', 'PREPARE', granted['recipient'], [granted], store, NOW) == 'SYNTHETIC PRIVATE VALUE'
        receipt = store.events()[-1]['record']
        assert receipt['authorization_id'] == 'a1' and receipt['purpose'] == 'PREPARE' and receipt['action_url'] == granted['recipient']
        assert 'SYNTHETIC PRIVATE VALUE' not in store.path.read_text()
        revoked = {**granted, 'id': 'a2', 'state': 'REVOKED'}
        for authorities in [[granted, revoked], [{**granted, 'recipient': 'https://other.example/'}], [{**granted, 'expires_at': '2026-10-09T00:00:00Z'}]]:
            with self.assertRaises(PermissionError):
                gateway.disclose('identity', 'RM-002', 'PREPARE', granted['recipient'], authorities, store, NOW)
        with self.assertRaises(ValidationError):
            store.append('claim', {**claim, 'raw_identity': 'private'})

    def test_rm002_artifact_traceability_and_activity(self):
        tmp_path = Path(self.directory.name)
        r, nodes = resource(), [evidence()]
        branch = sweep([r], nodes, {'RM-002': rule()}, TODAY)['branches']['RM-002']
        claims = [dict(predicate='capability', value=True, evidence_id='e1')]
        artifact = build_artifact('resume:v1', r, branch, nodes, claims, [auth()], NOW)
        assert artifact['state'] == 'UNDER_REVIEW' and artifact['evidence_snapshot'] == ['e1']
        for bad_claims in [[{**claims[0], 'evidence_id': 'absent'}], [{**claims[0], 'value': False}], []]:
            with self.assertRaises(ValueError):
                build_artifact('bad', r, branch, nodes, bad_claims, [auth()], NOW)
        with self.assertRaises(PermissionError):
            build_artifact('bad', r, branch, nodes, claims, [], NOW)
        with self.assertRaises(ValueError):
            build_artifact('resume:v2', r, branch, nodes, claims, [auth()], NOW, prior=artifact)
        reused = build_artifact('resume:v2', r, branch, nodes, claims, [auth()], NOW, prior=artifact, overlap=['capability'], delta=[])
        store = StateStore(tmp_path / 'ledger.jsonl')
        for kind, record in [('resource', r), ('evidence', nodes[0]), ('authorization', auth()), ('artifact', artifact), ('artifact', reused), ('activity', activity())]:
            if kind == 'artifact':
                store.append(kind, record, now=NOW)
            else:
                store.append(kind, record)
        assert store.events()[-1]['record']['state'] == 'CLICKED'
        assert r['state'] == 'DISCOVERED'
        with self.assertRaises(ValueError):
            store.append('artifact', artifact)
        assert StateStore(store.path).events() == store.events()

    def test_ledger_rejects_invalid_artifact_authorization_and_trace(self):
        tmp_path = Path(self.directory.name)
        store = StateStore(tmp_path / 'ledger.jsonl')
        r, nodes = resource(), [evidence()]
        branch = sweep([r], nodes, {'RM-002': rule()}, TODAY)['branches']['RM-002']
        claims = [dict(predicate='capability', value=True, evidence_id='e1')]
        artifact = build_artifact('resume:direct', r, branch, nodes, claims, [auth()], NOW)
        for kind, record in [('resource', r), ('evidence', nodes[0]), ('authorization', auth())]:
            store.append(kind, record)
        store.append('artifact', artifact, now=NOW)

        expired = {**auth(), 'id': 'a-expired', 'expires_at': '2026-10-09T00:00:00Z'}
        mismatched = {**auth(), 'id': 'a-mismatch', 'recipient': 'https://other.example/apply'}
        revoked = {**auth(), 'id': 'a-revoked', 'state': 'REVOKED'}
        for authorization in [expired, mismatched, revoked]:
            store.append('authorization', authorization)

        def bad_artifact(identifier, authorization_id='a1', **changes):
            return {**artifact, 'id': identifier, 'authorization_id': authorization_id,
                    'prior_artifact_id': None, 'overlap': [], 'delta': [], **changes}

        expired_artifact = bad_artifact('bad-expired', 'a-expired')
        mismatched_artifact = bad_artifact('bad-recipient', 'a-mismatch')
        revoked_artifact = bad_artifact('bad-revoked', 'a1')
        with self.assertRaises(PermissionError):
            store.append('artifact', expired_artifact, now=NOW)
        with self.assertRaises(PermissionError):
            store.append('artifact', mismatched_artifact, now=NOW)
        with self.assertRaises(PermissionError):
            store.append('artifact', revoked_artifact, now=NOW)
        with self.assertRaises(ValueError):
            store.append('artifact', bad_artifact('bad-no-time'), now=None)

        store.append('resource', {**r, 'requirements': ['capability', 'security']})
        current = {**auth(), 'id': 'a-current'}
        store.append('authorization', current)
        incomplete = bad_artifact('bad-requirements', 'a-current')
        with self.assertRaises(ValueError):
            store.append('artifact', incomplete, now=NOW)

        contradictory = evidence('e2', False, 'CONTRADICTORY')
        store.append('evidence', contradictory)
        contradictory_claims = [
            claims[0],
            dict(predicate='security', value=False, evidence_id='e2'),
        ]
        contradictory_artifact = bad_artifact(
            'bad-contradictory',
            'a-current',
            claims=contradictory_claims,
            evidence_snapshot=['e1', 'e2'],
        )
        with self.assertRaises(ValueError):
            store.append('artifact', contradictory_artifact, now=NOW)
        assert len(store.events()) == 10

    def test_azure_resource_conversion_and_expiration(self):
        r = {**resource('azure'), 'state': 'ACQUIRED', 'resource_types': ['INFRASTRUCTURE']}
        value = dict(schema_version='1.0', id='azure-value', resource_id='azure', value_type='RESTRICTED_INFRASTRUCTURE',
                     nominal_value=5000, cash_value=0, usable_value=5000, acquisition_cost=0, friction_cost=0,
                     restriction_level='RESTRICTED', expiration_risk=0.5, conversion_potential=1, dependency_value=0,
                     realized_value=0, expires_on='2027-01-01', allowed_workloads=['legitimate-workload'])
        inventory = Inventory(r, value)
        with self.assertRaises(ValidationError):
            Inventory(r, {**value, 'cash_value': 5000})
        for workload, amount in [('unapproved', 10), ('legitimate-workload', 6000), ('legitimate-workload', -1)]:
            with self.assertRaises(ValueError):
                inventory.allocate(workload, amount, TODAY)
        inventory.allocate('legitimate-workload', 1000, TODAY)
        inventory.consume('legitimate-workload', 500, TODAY)
        assert inventory.value['realized_value'] == 0 and inventory.value['cash_value'] == 0
        observation = {**evidence('observed-gain'), 'resource_ids': ['downstream-resource']}
        edge = inventory.conversion('downstream-resource', 200, observation)
        assert edge['source'] == 'azure' and inventory.value['realized_value'] == 200
        with self.assertRaises(ValueError):
            inventory.conversion('downstream-resource', 200, observation)
        assert inventory.lifecycle('2027-01-01') == 'EXPIRED'
        with self.assertRaises(ValueError):
            inventory.consume('legitimate-workload', 10, '2027-01-01')

    def test_convergence_and_material_outcome_routing(self):
        branches = {'a': {'eligibility': 'VERIFIED'}, 'b': {'eligibility': 'VERIFIED'}, 'c': {'eligibility': 'UNASSESSED'}}
        actions = [{'id': 'single', 'yields': {'a': ['EMPLOYMENT']}}, {'id': 'multi', 'yields': {'a': ['EMPLOYMENT'], 'b': ['CREDENTIAL']}}]
        assert convergence(actions, branches)[0]['id'] == 'multi'
        assert routing_from_outcomes([activity()]) == {}
        assert routing_from_outcomes([{**activity('OUTCOME'), 'material': True, 'outcome': 'FAILURE'}]) == {'RM-002': -1}

    def test_schema_versions_and_strict_ui_contract(self):
        for directory in ['schemas', 'ui_contract']:
            for path in (ROOT / directory).glob('*.json'):
                schema = json.loads(path.read_text())
                assert schema['$schema'] == 'https://json-schema.org/draft/2020-12/schema'
                assert schema['additionalProperties'] is False
        validate('checkin', dict(schema_version='1.0', id='check1', resource_id='RM-002', actor='HUMAN',
                                observed_state='CLICKED', evidence_id='e1', next_operation='VERIFY_SUBMISSION'))

    def test_runtime_restart_and_resource_history(self):
        store = StateStore(Path(self.directory.name) / 'runtime.jsonl')
        for kind, record in [('resource', resource()), ('evidence', evidence()), ('trust_rule', rule())]:
            store.append(kind, record)
        result = LocalRuntime(store).run(TODAY)
        assert result['branches']['RM-002']['warrant'] and not result['questions']
        count = len(store.events())
        assert not LocalRuntime(StateStore(store.path)).run(TODAY)['questions']
        assert len(store.events()) == count
        store.append('resource', {**resource(), 'state': 'ACQUIRED'})
        assert store.latest('resource')['RM-002']['state'] == 'ACQUIRED'
        assert store.events()[0]['record']['state'] == 'DISCOVERED'

    def test_ledger_rejects_orphan_artifact_and_invalid_contract_values(self):
        store = StateStore(Path(self.directory.name) / 'ledger.jsonl')
        branch = sweep([resource()], [evidence()], {'RM-002': rule()}, TODAY)['branches']['RM-002']
        artifact = build_artifact('resume:v1', resource(), branch, [evidence()],
                                  [dict(predicate='capability', value=True, evidence_id='e1')], [auth()], NOW)
        with self.assertRaises(ValueError):
            store.append('artifact', artifact)
        for bad in [{**evidence(), 'value': 1}, {**evidence(), 'observed_on': 'yesterday'},
                    {**evidence(), 'id': 'raw identity with spaces'}, {**evidence(), 'source_url': 'relative'}]:
            with self.assertRaises(ValidationError):
                validate('evidence', bad)

    def test_artifact_rejects_omitted_contradictory_evidence_on_builder_and_ledger(self):
        store = StateStore(Path(self.directory.name) / 'omitted.jsonl')
        r, positive = resource(), evidence('e1')
        contradictory = evidence('e2', False, 'CONTRADICTORY')
        claims = [dict(predicate='capability', value=True, evidence_id='e1')]
        branch = sweep([r], [positive], {'RM-002': rule()}, TODAY)['branches']['RM-002']
        # Builder path: branch snapshot silently drops the recorded contradiction.
        with self.assertRaisesRegex(ValueError, 'applicable contradictory evidence'):
            build_artifact('omit:builder', r, branch, [positive, contradictory], claims, [auth()], NOW)
        # Ledger path: a record that omits the contradiction is refused on direct append.
        omitted = build_artifact('omit:ledger', r, branch, [positive], claims, [auth()], NOW)
        for kind, record in [('resource', r), ('evidence', positive), ('evidence', contradictory), ('authorization', auth())]:
            store.append(kind, record)
        with self.assertRaisesRegex(ValueError, 'applicable contradictory evidence'):
            store.append('artifact', omitted, now=NOW)
        assert all(event['record']['id'] != 'omit:ledger' for event in store.events())
        # Positive control: a snapshot that carries the contradiction is accepted on both paths.
        complete = {**branch, 'evidence_snapshot': ['e1', 'e2']}
        accepted = build_artifact('omit:complete', r, complete, [positive, contradictory], claims, [auth()], NOW)
        assert accepted['evidence_snapshot'] == ['e1', 'e2']
        store.append('artifact', accepted, now=NOW)
        assert store.events()[-1]['record']['id'] == 'omit:complete'

    def test_artifact_rejects_prior_from_another_resource_on_builder_and_ledger(self):
        store = StateStore(Path(self.directory.name) / 'cross.jsonl')
        r2, e1 = resource('RM-002'), evidence('e1')
        r3, e3 = resource('RM-003'), {**evidence('e3'), 'resource_ids': ['RM-003']}
        auth3 = {**auth(), 'id': 'a3', 'resource_id': 'RM-003'}
        claims2 = [dict(predicate='capability', value=True, evidence_id='e1')]
        claims3 = [dict(predicate='capability', value=True, evidence_id='e3')]
        branch2 = sweep([r2], [e1], {'RM-002': rule()}, TODAY)['branches']['RM-002']
        branch3 = sweep([r3], [e3], {'RM-003': rule('RM-003')}, TODAY)['branches']['RM-003']
        prior = build_artifact('rm2:v1', r2, branch2, [e1], claims2, [auth()], NOW)
        # Builder path: RM-003 cannot reuse RM-002's history, even with matching predicates.
        with self.assertRaisesRegex(ValueError, 'same resource'):
            build_artifact('rm3:builder', r3, branch3, [e3], claims3, [auth3], NOW,
                           prior=prior, overlap=['capability'], delta=[])
        # Ledger path: the same forged predecessor link is refused on direct append.
        standalone = build_artifact('rm3:ledger', r3, branch3, [e3], claims3, [auth3], NOW)
        forged = {**standalone, 'prior_artifact_id': prior['id'], 'overlap': ['capability'], 'delta': []}
        for kind, record in [('resource', r2), ('resource', r3), ('evidence', e1), ('evidence', e3),
                             ('authorization', auth()), ('authorization', auth3)]:
            store.append(kind, record)
        store.append('artifact', prior, now=NOW)
        with self.assertRaisesRegex(ValueError, 'same resource'):
            store.append('artifact', forged, now=NOW)
        assert [event['record']['id'] for event in store.events() if event['kind'] == 'artifact'] == ['rm2:v1']

if __name__ == "__main__":
    unittest.main()
