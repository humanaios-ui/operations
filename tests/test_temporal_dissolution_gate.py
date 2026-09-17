import unittest

from tools import temporal_dissolution_gate as gate


class TemporalDissolutionGateTests(unittest.TestCase):
    def evaluate(self, path, text, line_no=1):
        added = [gate.AddedLine(path=path, line_no=line_no, text=text.splitlines()[line_no - 1])]
        return gate.evaluate_added_lines(added, lambda _path: text)

    def test_internal_deadline_rejected(self):
        text = "complete_within: 48h\n"
        violations = self.evaluate("GOVERNANCE.md", text)
        self.assertEqual(len(violations), 1)
        self.assertIn("unclassified", violations[0].reason)

    def test_technical_safety_timer_allowed_when_classified(self):
        text = (
            "temporal_class: TECHNICAL_SAFETY\n"
            "respond_within: 30 seconds\n"
            "purpose: network dead-process detection only\n"
        )
        violations = self.evaluate(".github/healthcheck.yml", text, line_no=2)
        self.assertEqual(violations, [])

    def test_observational_timestamp_policy_allowed(self):
        text = (
            "temporal_class: OBSERVATIONAL\n"
            "due_at: 2026-09-17T18:00:00Z\n"
            "note: telemetry only; no scheduling authority\n"
        )
        violations = self.evaluate("schemas/example.yaml", text, line_no=2)
        self.assertEqual(violations, [])

    def test_regulatory_contract_allowed_when_complete(self):
        text = """external_constraint:
  type: REGULATORY_DEADLINE
  temporal_class: REGULATORY_EXTERNAL
  authority: Example Agency
  citation: Rule 42
  due_at: 2026-10-01T23:59:59Z
  evidence_ref: sha256:abc
  impact_if_missed: filing rejected
  z2_ratified: true
  ratification_ref: issue-comment:123
"""
        violations = self.evaluate("schemas/work.yaml", text, line_no=6)
        self.assertEqual(violations, [])

    def test_incomplete_regulatory_contract_rejected(self):
        text = """external_constraint:
  type: REGULATORY_DEADLINE
  temporal_class: REGULATORY_EXTERNAL
  due_at: 2026-10-01T23:59:59Z
  z2_ratified: true
"""
        violations = self.evaluate("schemas/work.yaml", text, line_no=4)
        self.assertEqual(len(violations), 1)
        self.assertIn("contract incomplete", violations[0].reason)

    def test_historical_record_allowed(self):
        text = (
            "temporal_class: HISTORICAL_RECORD\n"
            "deadline: 2026-07-31\n"
            "note: archival evidence only\n"
        )
        violations = self.evaluate("REGISTERED.md", text, line_no=2)
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
