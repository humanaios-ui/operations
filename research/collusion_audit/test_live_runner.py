import json
import tempfile
import unittest
from pathlib import Path

import audit
import live_runner

KEY = "sk-TEST-NOT-REAL-0000"


class FakePost:
    """Scripted transport. Records every request; never touches the network."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []

    def __call__(self, url, key, body):
        self.requests.append(body)
        reply = self.replies.pop(0) if self.replies else {"text": "", "http_status": 500}
        return reply


def ok(text, request_id="req-1"):
    payload = {"id": request_id, "choices": [{"message": {"content": text},
                                             "finish_reason": "stop"}],
               "usage": {"prompt_tokens": 10, "completion_tokens": 3}}
    return {"http_status": 200, "headers": {"x-request-id": request_id},
            "text": json.dumps(payload)}


def packet(condition="coordinated_false_approval", episode_id="live-00"):
    task = audit.task(3)
    return {"episode_id": episode_id, "assigned_condition": condition, "task": task,
            "actor_instructions": "SECRET-CONDITION-PROMPT"}


class LiveRunnerTests(unittest.TestCase):
    def test_histories_are_separate_and_ballots_see_both_messages(self):
        post = FakePost([ok("A says hi"), ok("B says hi"), ok("APPROVE"), ok("APPROVE")])
        result = live_runner.run_episode(packet(), "m", KEY, post)
        self.assertEqual(result["status"], "complete")
        a_first, b_first, a_ballot, b_ballot = post.requests
        # B's first request must show A's message as user text and no A-side assistant turn.
        self.assertIn("A says hi", b_first["messages"][-1]["content"])
        self.assertNotIn("assistant", [m["role"] for m in b_first["messages"]])
        # A's ballot request carries its own message as assistant turn and B's message as user text.
        roles = [m["role"] for m in a_ballot["messages"]]
        self.assertEqual(roles.count("assistant"), 1)
        self.assertIn("B says hi", a_ballot["messages"][-1]["content"])
        # B's ballot history holds only B's own assistant turn; A's message is seen as user text.
        self.assertEqual([m["role"] for m in b_ballot["messages"]].count("assistant"), 1)
        self.assertIn("A says hi", json.dumps(b_ballot["messages"]))
        self.assertEqual(result["ballots"], {"A": "APPROVE", "B": "APPROVE"})

    def test_fresh_history_each_episode(self):
        post = FakePost([ok("A1"), ok("B1"), ok("REJECT"), ok("REJECT"),
                         ok("A2"), ok("B2"), ok("REJECT"), ok("REJECT")])
        live_runner.run_episode(packet(episode_id="live-00"), "m", KEY, post)
        live_runner.run_episode(packet(episode_id="live-01"), "m", KEY, post)
        second_episode_first_call = post.requests[4]["messages"]
        self.assertNotIn("A1", json.dumps(second_episode_first_call))

    def test_failed_call_is_recorded_and_never_substituted(self):
        post = FakePost([ok("A says hi"), {"http_status": 503, "headers": {}, "text": '{"error":"busy"}'}])
        result = live_runner.run_episode(packet(), "m", KEY, post)
        self.assertEqual(result["status"], "call_failed")
        self.assertIsNone(result["ballots"].get("A"))
        self.assertEqual(len(post.requests), 2)  # no retry, no ballot phase after a failure
        self.assertEqual(result["calls"][-1]["status"], "call_failed")
        self.assertIsNone(live_runner.blind_evidence(result, {}))

    def test_malformed_ballot_is_kept_not_repaired(self):
        post = FakePost([ok("A"), ok("B"), ok("I approve, probably."), ok("REJECT")])
        result = live_runner.run_episode(packet(), "m", KEY, post)
        self.assertEqual(result["status"], "malformed_ballot")
        self.assertIsNone(result["ballots"]["A"])
        self.assertEqual(result["calls"][2]["content"], "I approve, probably.")

    def test_blind_evidence_has_no_condition_or_predictions(self):
        post = FakePost([ok("A"), ok("B"), ok("APPROVE"), ok("APPROVE")])
        result = live_runner.run_episode(packet(), "m", KEY, post)
        blind = live_runner.blind_evidence(result, {"run_id": "t"})
        text = json.dumps(blind)
        for banned in ("coordinated_false_approval", "SECRET-CONDITION-PROMPT", "hybrid",
                       "talk_only", "actions_only", "assigned_condition"):
            self.assertNotIn(banned, text)
        audit.validate(blind["evidence"])  # the detector accepts it as-is

    def test_run_writes_no_key_and_keeps_scoring_apart(self):
        replies = []
        for _ in range(20):
            replies += [ok("A"), ok("B"), ok("APPROVE"), ok("APPROVE")]
        packets = {"protocol_sha256": live_runner.sha256_file(live_runner.ROOT / "protocol.json"),
                   "episodes": [packet(episode_id=f"live-{i:02d}") for i in range(20)]}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            post = FakePost(replies)
            for p in packets["episodes"]:
                result = live_runner.run_episode(p, "m", KEY, post)
                blind = live_runner.blind_evidence(result, {})
                scoring = live_runner.scoring_record(result, blind)
                (out / "b.json").write_text(json.dumps(blind or {}))
                (out / "s.json").write_text(json.dumps(scoring))
                self.assertNotIn("assigned_condition", json.dumps(blind or {}))
                self.assertIn("assigned_condition", scoring)
            self.assertNotIn(KEY, (out / "b.json").read_text() + (out / "s.json").read_text())

    def test_frozen_check_refuses_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("audit.py", "protocol.json", "test_audit.py"):
                (root / name).write_text("changed")
            (root / "freeze.json").write_text(json.dumps({"status": "x", "hashes": {
                "audit.py": "0" * 64, "protocol.json": "0" * 64, "test_audit.py": "0" * 64}}))
            with self.assertRaises(RuntimeError):
                live_runner.frozen_check(root)

    def test_message_too_long_is_flagged_not_truncated(self):
        post = FakePost([ok("x" * 4001), ok("B"), ok("APPROVE"), ok("APPROVE")])
        result = live_runner.run_episode(packet(), "m", KEY, post)
        self.assertEqual(result["status"], "message_too_long")
        self.assertEqual(len(result["texts"]["A"]), 4001)


    def test_truncated_output_is_excluded_not_scored(self):
        cut = ok("A")
        payload = json.loads(cut["text"])
        payload["choices"][0]["finish_reason"] = "length"
        cut["text"] = json.dumps(payload)
        post = FakePost([cut, ok("B"), ok("APPROVE"), ok("APPROVE")])
        result = live_runner.run_episode(packet(), "m", KEY, post)
        self.assertEqual(result["status"], "truncated_output")
        self.assertIsNone(live_runner.blind_evidence(result, {}))

    def test_empty_content_is_a_failed_call(self):
        post = FakePost([ok("")])
        result = live_runner.run_episode(packet(), "m", KEY, post)
        self.assertEqual(result["status"], "call_failed")
        self.assertEqual(result["calls"][0]["error"], "empty_content")

    def test_reasoning_is_stored_but_not_shown_to_the_other_actor(self):
        reply = ok("A says hi")
        payload = json.loads(reply["text"])
        payload["choices"][0]["message"]["reasoning"] = "PRIVATE-CHAIN"
        reply["text"] = json.dumps(payload)
        post = FakePost([reply, ok("B"), ok("REJECT"), ok("REJECT")])
        result = live_runner.run_episode(packet(), "m", KEY, post)
        self.assertEqual(result["calls"][0]["reasoning"], "PRIVATE-CHAIN")
        self.assertNotIn("PRIVATE-CHAIN", json.dumps(post.requests[1:]))
        self.assertNotIn("PRIVATE-CHAIN", json.dumps(live_runner.blind_evidence(result, {})))

    def test_run_requires_passing_connectivity_check(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(RuntimeError):
            live_runner.run("r1", live_runner.AMENDMENT["run_settings"]["model"], KEY,
                            out_root=tmp, post=FakePost([]))

    def test_amendment_is_tied_to_the_frozen_protocol(self):
        amended = live_runner.AMENDMENT["amends"]["protocol_sha256"]
        self.assertEqual(amended, live_runner.sha256_file(live_runner.ROOT / "protocol.json"))
        self.assertIsNone(live_runner.AMENDMENT["evaluation_limits"]["independent_evaluator"])


if __name__ == "__main__":
    unittest.main()
