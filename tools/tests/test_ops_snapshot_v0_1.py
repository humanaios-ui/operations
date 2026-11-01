#!/usr/bin/env python3
"""Regression tests for tools/ops_snapshot_v0_1.py (pure layer only; no network)."""
from __future__ import annotations

import json
import os
import sys

import pytest
from datetime import UTC, datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import ops_snapshot_v0_1 as ops

NOW = datetime(2026, 10, 24, tzinfo=UTC)


def snap(raw=None):
    return ops.build_snapshot(raw or ops._fixture(), NOW)


def test_smoke_test_passes():
    assert ops.run_smoke_test()


def test_same_input_same_output():
    assert json.dumps(snap(), sort_keys=True) == json.dumps(snap(), sort_keys=True)


def test_main_failure_is_blocker():
    items = [b for b in snap()["blockers"]["items"] if b["rule"] == "MAIN_CHECK_FAILED"]
    assert [b["detail"] for b in items] == ["security-gates"]
    assert items[0]["ref"] == "main@m1"


def test_draft_prs_never_produce_blockers():
    assert not [b for b in snap()["blockers"]["items"] if b["ref"].startswith("#3")]


def test_stale_threshold():
    stale = [b["ref"] for b in snap()["blockers"]["items"] if b["rule"] == "PR_STALE"]
    assert stale == ["#1"]


def test_duplicate_blocker_issues_counted_once():
    raw = ops._fixture()
    raw["blocker_issues"] = raw["blocker_issues"] * 2
    assert snap(raw)["blockers"]["by_rule"]["ISSUE_LABELED_BLOCKER"] == 1


def test_api_errors_downgrade_tag():
    raw = ops._fixture()
    raw["api_errors"] = [{"path": "/x", "status": 403}]
    s = snap(raw)
    assert s["epistemic_tag"] == "OBSERVED_PARTIAL"
    assert s["coverage"]["api_errors"] == [{"path": "/x", "status": 403}]


def test_missing_main_sha_does_not_crash():
    raw = ops._fixture()
    raw["main_sha"] = None
    s = snap(raw)
    assert s["main"]["checks"]["total"] is None
    assert not [b for b in s["blockers"]["items"] if b["rule"] == "MAIN_CHECK_FAILED"]


def test_authority_boundary_and_not_collected_are_explicit():
    s = snap()
    assert s["authority_effect"] == "NONE"
    assert "unresolved_review_threads" in s["coverage"]["not_collected"]


@pytest.mark.parametrize("main,pulls", [(False, True), (True, False), (False, False)])
def test_failed_fetch_reads_unknown_not_zero(main, pulls):
    raw = ops._fixture()
    raw["observed"]["main"] = main
    raw["observed"]["pulls"] = pulls
    s = snap(raw)
    assert s["epistemic_tag"] == "UNOBSERVED"
    for name in ("open_count", "draft_count", "with_failing_checks"):
        assert s["pull_requests"][name] is None
    assert s["main"]["checks"]["total"] is None if not main else s["main"]["checks"]["total"] == 2
    assert s["blockers"]["count"] is None
    assert "- blockers: unknown" in ops.markdown_summary(s)
    assert "0 checks, 0 failing" not in ops.markdown_summary(s) if not main else True


def test_missing_observation_provenance_fails_closed():
    raw = ops._fixture()
    raw.pop("observed")
    s = snap(raw)
    assert s["epistemic_tag"] == "UNOBSERVED"
    assert s["blockers"]["count"] is None


def test_incomplete_check_and_issue_collections_have_unknown_blocker_totals():
    for missing in ("checks", "blocker_issues"):
        raw = ops._fixture()
        if missing == "checks":
            raw["check_observed_by_sha"]["p2"] = False
        else:
            raw["observed"]["blocker_issues"] = False
        s = snap(raw)
        assert s["epistemic_tag"] == "OBSERVED_PARTIAL"
        assert s["blockers"]["count"] is None
        if missing == "checks":
            assert s["pull_requests"]["with_failing_checks"] is None
            assert next(p for p in s["pull_requests"]["items"] if p["number"] == 2)["checks"]["total"] is None


def test_paginate_checks_and_issues_beyond_first_page():
    class FakeGitHub:
        def __init__(self):
            self.errors = []
            self.calls = 0

        def get(self, path, params=None):
            self.calls += 1
            page = (params or {}).get("page", 1)
            if path == "/repos/o/r":
                return {"default_branch": "main"}
            if path == "/repos/o/r/commits/main":
                return {"sha": "m1"}
            if path == "/repos/o/r/pulls":
                return []
            if path == "/repos/o/r/commits/m1/check-runs":
                if page == 1:
                    return {"total_count": 101, "check_runs": [
                        {"name": f"ok-{i}", "conclusion": "success"} for i in range(100)]}
                return {"total_count": 101, "check_runs": [
                    {"name": "page-two-failure", "conclusion": "failure", "html_url": "check/101"}]}
            if path == "/repos/o/r/issues":
                if page == 1:
                    return ([{"number": 500, "pull_request": {"url": "pr/500"}}]
                            + [{"number": i, "title": f"issue {i}", "html_url": f"issue/{i}"}
                               for i in range(1, 100)])
                return [{"number": 100, "title": "issue 100", "html_url": "issue/100"}]
            raise AssertionError((path, params))

    gh = FakeGitHub()
    raw = ops.fetch_raw(gh, "o/r", ("blocker",))
    out = ops.build_snapshot(raw, NOW)
    assert raw["observed"]["checks"] is True
    assert raw["observed"]["blocker_issues"] is True
    assert len(raw["check_runs"]["m1"]) == 101
    assert len(raw["blocker_issues"]) == 100
    assert out["epistemic_tag"] == "OBSERVED"
    assert out["main"]["checks"]["total"] == 101
    assert out["blockers"]["by_rule"]["MAIN_CHECK_FAILED"] == 1
    assert out["blockers"]["by_rule"]["ISSUE_LABELED_BLOCKER"] == 100


def test_second_page_failure_fails_closed_without_dropping_first_page():
    class BrokenGitHub:
        errors = []
        calls = 0

        def get(self, path, params=None):
            self.calls += 1
            page = (params or {}).get("page", 1)
            if path == "/repos/o/r":
                return {"default_branch": "main"}
            if path == "/repos/o/r/commits/main":
                return {"sha": "m1"}
            if path == "/repos/o/r/pulls":
                return []
            if path.endswith("/check-runs"):
                if page == 1:
                    return {"total_count": 101, "check_runs": [
                        {"name": f"pass-{i}", "conclusion": "success"} for i in range(100)]}
                self.errors.append({"path": path, "status": 503})
                return None
            if path == "/repos/o/r/issues":
                return []
            raise AssertionError(path)

    gh = BrokenGitHub()
    raw = ops.fetch_raw(gh, "o/r", ("blocker",))
    out = ops.build_snapshot(raw, NOW)
    assert out["epistemic_tag"] == "OBSERVED_PARTIAL"
    assert out["main"]["checks"]["total"] is None
    assert len(raw["check_runs"]["m1"]) == 100
    assert out["blockers"]["count"] is None
    assert out["coverage"]["api_errors"][0]["status"] == 503


def test_replay_uses_pinned_source_observation_time(tmp_path, monkeypatch):
    raw = ops._fixture()
    raw["observed_at"] = "2026-10-24T00:00:00Z"
    source = tmp_path / "raw.json"
    source.write_text(json.dumps(raw), encoding="utf-8")
    copies = []
    for index in range(2):
        path = tmp_path / f"out-{index}.json"
        monkeypatch.setattr(sys, "argv", ["ops-snapshot", "--from-raw", str(source), "--out", str(path)])
        assert ops.main() == 0
        copies.append(json.loads(path.read_text(encoding="utf-8")))
    assert copies[0] == copies[1]
    assert copies[0]["generated_at"] == "2026-10-24T00:00:00Z"


def test_replay_without_pinned_clock_is_refused(tmp_path, monkeypatch):
    raw = ops._fixture()
    raw.pop("observed_at")
    source = tmp_path / "raw.json"
    source.write_text(json.dumps(raw), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["ops-snapshot", "--from-raw", str(source)])
    with pytest.raises(SystemExit) as err:
        ops.main()
    assert err.value.code == 2


def test_explicit_utc_clock_override(tmp_path, monkeypatch):
    raw = ops._fixture()
    source = tmp_path / "raw.json"
    source.write_text(json.dumps(raw), encoding="utf-8")
    dest = tmp_path / "out.json"
    monkeypatch.setattr(sys, "argv", ["ops-snapshot", "--from-raw", str(source),
                                     "--now", "2026-10-25T00:00:00Z", "--out", str(dest)])
    assert ops.main() == 0
    assert json.loads(dest.read_text())["generated_at"] == "2026-10-25T00:00:00Z"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
