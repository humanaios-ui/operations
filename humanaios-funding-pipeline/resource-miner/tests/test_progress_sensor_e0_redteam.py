"""Red-team round on the E0 progress sensor. Synthetic only. Written BEFORE the fixes (author-run)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from resource_miner.progress_sensor_e0 import evaluate_progress, main
from tests.test_progress_sensor_e0 import sample, signal, ID, URL


def keys(result, kind):
    return [t["dedupe_key"] for t in result["trigger_candidates"] if t["type"] == kind]


class OutOfRangeTimesFailClosedAsValueError(unittest.TestCase):
    """Every rejection must be a ValueError so callers can fail closed with one handler."""

    def test_deadline_that_overflows_utc_conversion_is_value_error(self):
        x = sample(); x["source_observations"][0]["deadline_at"] = "0001-01-01T00:00:00+14:00"
        with self.assertRaises(ValueError):
            evaluate_progress(x)

    def test_ancient_utc_deadline_is_value_error_not_overflow_in_local_time(self):
        x = sample(); x["source_observations"][0]["deadline_at"] = "0001-01-01T00:00:00Z"
        with self.assertRaises(ValueError):
            evaluate_progress(x)

    def test_absurd_future_deadline_is_value_error(self):
        x = sample(); x["source_observations"][0]["deadline_at"] = "9999-12-31T23:59:00Z"
        with self.assertRaises(ValueError):
            evaluate_progress(x)

    def test_real_deadlines_still_work(self):
        self.assertEqual(evaluate_progress(sample())["deadline_state"], "NEAR")


class SourceUrlIsPlainAscii(unittest.TestCase):
    """The canonical URL is echoed into the private digest, so it must not carry hidden characters."""

    def bad(self, url):
        x = sample(); x["canonical_url"] = url
        for row in x["source_observations"]:
            row["canonical_url"] = url
        with self.assertRaises(ValueError):
            evaluate_progress(x)

    def test_right_to_left_override_rejected(self):
        self.bad("https://apartresearch.com/sprints/swarm‮-alignment-2026")

    def test_zero_width_character_rejected(self):
        self.bad("https://apartresearch.com/sprints/swarm​-alignment-2026")

    def test_nul_and_control_characters_rejected(self):
        self.bad("https://apartresearch.com/sprints/swarm\x00alignment")
        self.bad("https://apartresearch.com/sprints/swarm\x1balignment")

    def test_backslash_rejected(self):
        self.bad("https://apartresearch.com\\sprints/swarm-alignment-2026")

    def test_non_ascii_host_rejected(self):
        self.bad("https://apаrtresearch.com/sprints/swarm-alignment-2026")  # Cyrillic a


class RecurringConditionsGetANewKey(unittest.TestCase):
    """A dedupe key must stay stable inside one episode of a condition and change when a new episode starts."""

    def stale(self, checked, as_of, revision="public-brief-v1"):
        x = sample()
        x["source_observations"][0].update(checked_at=checked, source_revision=revision)
        x["signals"] = []
        x["as_of"] = as_of
        return evaluate_progress(x)

    def test_stale_alert_is_stable_across_days_inside_one_episode(self):
        a = self.stale("2026-11-01T00:00:00Z", "2026-11-05T00:00:00Z")
        b = self.stale("2026-11-01T00:00:00Z", "2026-11-06T00:00:00Z")
        self.assertEqual(keys(a, "SOURCE_STALE_RECHECK"), keys(b, "SOURCE_STALE_RECHECK"))
        self.assertEqual(len(keys(a, "SOURCE_STALE_RECHECK")), 1)

    def test_stale_again_after_a_recheck_is_a_new_alert_even_with_same_revision(self):
        first = self.stale("2026-11-01T00:00:00Z", "2026-11-05T00:00:00Z")
        later = self.stale("2026-11-08T00:00:00Z", "2026-11-12T00:00:00Z")  # rechecked, unchanged page, stale again
        self.assertNotEqual(keys(first, "SOURCE_STALE_RECHECK"), keys(later, "SOURCE_STALE_RECHECK"))
        # and the replay of the FIRST key must not mute the second episode
        x = sample(); x["source_observations"][0].update(checked_at="2026-11-08T00:00:00Z")
        x["signals"] = []; x["as_of"] = "2026-11-12T00:00:00Z"
        x["prior_dedupe_keys"] = keys(first, "SOURCE_STALE_RECHECK")
        states = [t["emission_state"] for t in evaluate_progress(x)["trigger_candidates"] if t["type"] == "SOURCE_STALE_RECHECK"]
        self.assertEqual(states, ["NEW_CANDIDATE"])

    def conflict(self, deadline_b, rev_b="other"):
        x = sample()
        x["source_observations"].append(dict(x["source_observations"][0], source_revision=rev_b, deadline_at=deadline_b))
        return evaluate_progress(x)

    def test_same_conflict_keeps_its_key(self):
        self.assertEqual(keys(self.conflict("2026-11-10T23:59:00-12:00"), "SOURCE_CONFLICT_HOLD"),
                         keys(self.conflict("2026-11-10T23:59:00-12:00"), "SOURCE_CONFLICT_HOLD"))

    def test_a_different_conflict_is_not_muted_by_the_first(self):
        a = self.conflict("2026-11-10T23:59:00-12:00")
        b = self.conflict("2026-11-12T23:59:00-12:00", rev_b="another")
        self.assertNotEqual(keys(a, "SOURCE_CONFLICT_HOLD"), keys(b, "SOURCE_CONFLICT_HOLD"))


class DigestNeverEchoesOpaqueEvidence(unittest.TestCase):
    """Privacy: the projection may name kinds and counts, never the caller's opaque references or observation ids."""

    def test_output_contains_no_evidence_ref_or_observation_id(self):
        x = sample()
        x["signals"] = [dict(signal("INTERNAL_WORK_LINKED", "obs-SECRETISH-1"), evidence_ref="ref-SECRETISH-A"),
                        dict(signal("BLOCKER_OBSERVED", "obs-SECRETISH-2"), evidence_ref="ref-SECRETISH-B"),
                        dict(signal("PROVIDER_RECEIPT_OBSERVED", "obs-SECRETISH-3"), evidence_ref="ref-SECRETISH-C")]
        blob = json.dumps(evaluate_progress(x))
        self.assertNotIn("SECRETISH", blob)

    def test_dedupe_keys_do_not_change_when_only_opaque_refs_change(self):
        a, b = sample(), sample()
        b["signals"][0]["evidence_ref"] = "a-completely-different-ref"
        self.assertEqual(evaluate_progress(a)["trigger_candidates"], evaluate_progress(b)["trigger_candidates"])


class CliFailsClosedAndCleanly(unittest.TestCase):
    def run_cli(self, text):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "in.json"; p.write_text(text, encoding="utf-8")
            with self.assertRaises(SystemExit) as ctx:
                main(["--input", str(p)])
            return ctx.exception.code

    def test_duplicate_object_key_is_refused(self):
        good = json.dumps(sample())
        # the repeated key is itself a perfectly valid value, so ONLY duplicate-key detection can refuse it
        dup = good[:-1] + ', "prior_dedupe_keys": []}'
        self.assertEqual(self.run_cli(dup), 2)

    def test_invalid_envelope_exits_2_without_a_traceback(self):
        self.assertEqual(self.run_cli(json.dumps({"schema": "nope"})), 2)

    def test_not_json_exits_2(self):
        self.assertEqual(self.run_cli("not json"), 2)

    def test_valid_input_still_prints_a_projection(self):
        import contextlib, io
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "in.json"; p.write_text(json.dumps(sample()), encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                main(["--input", str(p)])
        self.assertEqual(json.loads(out.getvalue())["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
