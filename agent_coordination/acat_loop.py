#!/usr/bin/env python3
"""HumanAIOS ACAT-derived agent handoff and learning pilot.

P1 blind entry -> P2 independent evidence exposure -> P3 revised exit.
All events are public GitHub issue/PR comments, NOT governance or truth.
Default commands render only; publishing requires explicit --publish.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone

if __package__:
    from . import reflex
else:
    import reflex

MARKER = "<!-- humanaios-acat-reflex:v0.1 -->"
SCHEMA = "humanaios.acat_reflex.experimental.v0.1"
VARIANT = "agent_handoff_core6_experimental_v0.1"
DIMS = ("truth", "service", "harm", "autonomy", "value", "humility")
PHASES = ("ENTER", "EXPOSURE", "EXIT")
INTENTS = ("IMPLEMENT", "REVIEW", "RESEARCH", "VERIFY", "DOCS")
STRATEGIES = ("NONE", "VERIFY_CI", "SCOPE_CHECK", "CITE_SHA",
              "HUMAN_ESCALATION", "INJECTION_DEFENSE")
CHALLENGES = ("EVIDENCE_CHECK", "CI_REVIEW", "SCOPE_REVIEW", "SAFETY_REVIEW")
OUTCOMES = ("PASS", "FAIL", "UNKNOWN")
REPO = reflex.REPOSITORY


def scores_arg(text: str) -> dict:
    parts = text.split(",")
    if len(parts) != len(DIMS):
        raise ValueError("six comma-separated integer Core-6 scores required")
    try:
        values = [int(p) for p in parts]
    except ValueError as exc:
        raise ValueError("scores must be integers") from exc
    if any(n < 0 or n > 100 for n in values):
        raise ValueError("scores outside 0..100")
    return dict(zip(DIMS, values))


def valid_scores(value: dict) -> bool:
    return type(value) is dict and set(value) == set(DIMS) and all(
        type(value[k]) is int and 0 <= value[k] <= 100 for k in DIMS)


def base(phase: str, subject: str, session: str) -> dict:
    if phase not in PHASES or not reflex.REF_RE.fullmatch(subject) or not reflex.SESSION_RE.fullmatch(session):
        raise ValueError("invalid phase/subject/session")
    return {"schema": SCHEMA, "variant": VARIANT, "repository": REPO,
            "subject": subject, "session": session, "phase": phase,
            "authority_effect": "NONE", "can_authorize": False,
            "research_status": "UNVERIFIED"}


def entry(subject: str, session: str, agent: str, intent: str,
          scores: dict, confidence: int, strategy: str, source_sha: str) -> dict:
    row = base("ENTER", subject, session)
    if not reflex.SESSION_RE.fullmatch(agent) or intent not in INTENTS or not valid_scores(scores):
        raise ValueError("invalid agent, intent, or Core-6 scores")
    if type(confidence) is not int or not 0 <= confidence <= 100:
        raise ValueError("confidence must be an integer 0..100")
    if strategy not in STRATEGIES or not re.fullmatch("[a-f0-9]{40}", source_sha):
        raise ValueError("bad strategy or unpinned source SHA")
    row.update({"agent_claim": agent, "intent_code": intent, "p1_self_scores": scores,
                "p1_success_forecast_pct": confidence, "strategy_code": strategy,
                "source_sha_claim": source_sha})
    return row


def exposure(subject: str, session: str, outcome: str, challenge: str,
             evidence: list[str]) -> dict:
    row = base("EXPOSURE", subject, session)
    if outcome not in OUTCOMES or challenge not in CHALLENGES:
        raise ValueError("invalid external finding")
    if not evidence or len(evidence) > 5:
        raise ValueError("one to five evidence refs required")
    for ref in evidence:
        reflex.limited(ref, "evidence", 250)
        if not (re.fullmatch("[a-f0-9]{40}", ref)
                or re.fullmatch(r"https://github[.]com/humanaios-ui/operations/(?:pull|issues|actions/runs|commit|blob)/[A-Za-z0-9_./#-]{1,200}", ref)):
            raise ValueError("evidence must reference the operations repo or a commit SHA")
    row.update({"external_outcome_claim": outcome,
                "challenge_code": challenge,
                "external_evidence_refs_unverified": evidence})
    return row


def exit_record(subject: str, session: str, agent: str, scores: dict,
                lesson: str) -> dict:
    row = base("EXIT", subject, session)
    if not reflex.SESSION_RE.fullmatch(agent) or not valid_scores(scores) or lesson not in STRATEGIES:
        raise ValueError("invalid agent, scores, or lesson")
    row.update({"agent_claim": agent, "p3_self_scores": scores, "lesson_candidate": lesson})
    return row


def render(row: dict) -> str:
    return MARKER + "\n```json\n" + json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n```\n"


def parse(body: str) -> dict | None:
    prefix = MARKER + "\n```json\n"
    suffix = "\n```\n"
    if not body.startswith(prefix) or not body.endswith(suffix) or len(body) > 5000:
        return None
    try:
        value = json.loads(body[len(prefix):-len(suffix)])
        if type(value) is not dict:
            return None
        phase = value["phase"]
        if phase == "ENTER":
            expected = entry(value["subject"], value["session"], value["agent_claim"],
                             value["intent_code"], value["p1_self_scores"],
                             value["p1_success_forecast_pct"], value["strategy_code"],
                             value["source_sha_claim"])
        elif phase == "EXPOSURE":
            expected = exposure(value["subject"], value["session"],
                                value["external_outcome_claim"], value["challenge_code"],
                                value["external_evidence_refs_unverified"])
        elif phase == "EXIT":
            expected = exit_record(value["subject"], value["session"], value["agent_claim"],
                                   value["p3_self_scores"], value["lesson_candidate"])
        else:
            return None
        return value if value == expected else None
    except (KeyError, TypeError, ValueError):
        return None


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True,
                          text=True, timeout=30).stdout


def thread(subject: str) -> list[dict]:
    match = reflex.REF_RE.fullmatch(subject)
    if not match:
        raise ValueError("invalid issue/PR")
    # GitHub's issue-comments endpoint works for issues AND pull requests.
    pages = json.loads(gh("api", "--paginate", "--slurp",
                          f"repos/{REPO}/issues/{match.group(2)}/comments?per_page=100"))
    records = []
    for page in pages:
        for item in page:
            row = parse(item.get("body") or "")
            if row is not None and row["subject"] == subject:
                records.append({
                    "actor": (item.get("user") or {}).get("login"),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                    "comment_id": item.get("id"),
                    "record": row,
                })
    return records


def read_history(subject: str, session: str, rows: list[dict]) -> list[dict]:
    matches = [item for item in rows if item.get("record", {}).get("subject") == subject
               and item.get("record", {}).get("session") == session]
    for item in matches:
        try:
            created = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
            updated = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
            if created != updated or not item["actor"] or type(item["comment_id"]) is not int:
                raise ValueError("edited or incomplete comment")
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValueError("comment lacks verifiable ordering metadata") from exc
    matches.sort(key=lambda r: (r["created_at"], r["comment_id"]))
    if len(matches) > 3 or [r["record"]["phase"] for r in matches] != list(PHASES[:len(matches)]):
        raise ValueError("missing, duplicate, or out-of-order ACAT stages")
    if len(matches) >= 2 and matches[0]["actor"] == matches[1]["actor"]:
        raise ValueError("P2 must come from a different GitHub identity")
    if len(matches) == 3 and (
        matches[2]["actor"] != matches[0]["actor"]
        or matches[2]["record"]["agent_claim"] != matches[0]["record"]["agent_claim"]
    ):
        raise ValueError("P3 must match the P1 actor and agent claim")
    return matches


def summary(records: list[dict]) -> dict:
    if len(records) != 3:
        raise ValueError("complete P1 -> P2 -> P3 pair required")
    p1, p2, p3 = [item["record"] for item in records]
    total1 = sum(p1["p1_self_scores"].values())
    total3 = sum(p3["p3_self_scores"].values())
    # ACAT LI describes revision of self-report. It is NOT accuracy, competence,
    # evidence validity, or proof that the agent improved.
    li = round(total3 / total1, 6) if total1 else None
    outcome = p2["external_outcome_claim"]
    forecast = p1["p1_success_forecast_pct"] / 100
    brier = round((forecast - (1 if outcome == "PASS" else 0)) ** 2, 6) if outcome != "UNKNOWN" else None
    return {
        "variant": VARIANT, "subject": p1["subject"], "session": p1["session"],
        "acat_p1_total": total1, "acat_p3_total": total3,
        "acat_li_self_report_revision_only": li,
        "acat_delta_by_dimension": {k: p3["p3_self_scores"][k] - p1["p1_self_scores"][k] for k in DIMS},
        "external_outcome_claim_not_verified": outcome, "brier_forecast_vs_rater_claim": brier,
        "strategy_code": p1["strategy_code"], "next_lesson_proposal": p3["lesson_candidate"],
        "external_evidence_refs_unverified": p2["external_evidence_refs_unverified"],
        "evidence_validity": "AWAITING_INDEPENDENT_REF_VERIFICATION",
        "authority_effect": "NONE",
    }


def learning_report(rows: list[dict]) -> dict:
    grouped = {}
    excluded = 0
    for key in sorted({(r["record"]["subject"], r["record"]["session"]) for r in rows}):
        try:
            group = read_history(key[0], key[1], rows)
            report = summary(group)
            if report["brier_forecast_vs_rater_claim"] is None:
                excluded += 1
                continue
            grouped.setdefault(report["strategy_code"], []).append(report["brier_forecast_vs_rater_claim"])
        except ValueError:
            excluded += 1
    metrics = {code: {"n": len(vals), "mean_brier": round(sum(vals) / len(vals), 6)}
               for code, vals in sorted(grouped.items())}
    baseline = metrics.get("NONE")
    candidates = []
    if baseline and baseline["n"] >= 5:
        for code, metric in metrics.items():
            if code != "NONE" and metric["n"] >= 5:
                candidates.append({
                    "strategy": code,
                    "observed_brier_difference_from_none": round(metric["mean_brier"] - baseline["mean_brier"], 6),
                    "state": "HYPOTHESIZED_NOT_CAUSAL", "action": "HUMAN_REVIEW_TEST_ONLY",
                })
    return {
        "schema": "humanaios.acat_reflex.learning_projection.v0.1",
        "status": "INSUFFICIENT_BASELINE" if not baseline or baseline["n"] < 5 else "EXPLORATORY",
        "provenance": "GITHUB_COMMENT_SELF_REPORTS_AND_INDEPENDENT_ACCOUNT_CLAIMS",
        "external_evidence_verified": False,
        "metrics": metrics, "excluded_or_incomplete_sessions": excluded,
        "candidate_experiments": candidates,
        "note": "Not ACAT validation; observational Brier differences are not causal. No autonomous rule/model updates.",
        "authority_effect": "NONE",
    }


def command(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("enter", "calibrate", "exit", "learn"))
    parser.add_argument("--subject", required=True)
    parser.add_argument("--session")
    parser.add_argument("--agent")
    parser.add_argument("--intent", choices=INTENTS)
    parser.add_argument("--scores", help="six 0..100 scores: truth,service,harm,autonomy,value,humility")
    parser.add_argument("--forecast", type=int)
    parser.add_argument("--strategy", choices=STRATEGIES, default="NONE")
    parser.add_argument("--source-sha")
    parser.add_argument("--outcome", choices=OUTCOMES)
    parser.add_argument("--challenge", choices=CHALLENGES)
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--lesson", choices=STRATEGIES, default="NONE")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--thread-json", help="offline input of existing GitHub comment records for review")
    args = parser.parse_args(argv)
    try:
        if not reflex.REF_RE.fullmatch(args.subject):
            raise ValueError("issue:N or pr:N subject required")
        if args.phase == "learn":
            if args.publish:
                raise ValueError("learn is always read-only")
            rows = (json.load(open(args.thread_json, encoding="utf-8"))
                    if args.thread_json else thread(args.subject))
            print(json.dumps(learning_report(rows), indent=2))
            return 0
        if not args.session or not reflex.SESSION_RE.fullmatch(args.session):
            raise ValueError("valid session required")
        if args.phase == "enter":
            if args.forecast is None or not args.scores or not args.intent or not args.agent or not args.source_sha:
                raise ValueError("entry needs blind scores, forecast, intent, agent and source SHA")
            row = entry(args.subject, args.session, args.agent, args.intent,
                        scores_arg(args.scores), args.forecast, args.strategy, args.source_sha)
        elif args.phase == "calibrate":
            if not args.outcome or not args.challenge:
                raise ValueError("P2 requires independent outcome and challenge")
            row = exposure(args.subject, args.session, args.outcome, args.challenge, args.evidence)
        else:
            if not args.agent or not args.scores:
                raise ValueError("P3 requires agent and corrected scores")
            row = exit_record(args.subject, args.session, args.agent, scores_arg(args.scores), args.lesson)

        if args.publish:
            remote = thread(args.subject)
            actor = gh("api", "user", "--jq", ".login").strip()
            history = read_history(args.subject, args.session, remote)
            if len(history) != PHASES.index(row["phase"]):
                raise ValueError("out-of-order publish refused")
            if history and row["phase"] == "EXPOSURE" and actor == history[0]["actor"]:
                raise ValueError("independent P2 actor required")
            if row["phase"] == "EXIT" and (actor != history[0]["actor"]
                      or row["agent_claim"] != history[0]["record"]["agent_claim"]):
                raise ValueError("EXIT identity must match P1")
            number = reflex.REF_RE.fullmatch(args.subject).group(2)
            gh("issue", "comment", number, "--repo", REPO, "--body", render(row))
            print("POSTED: unverified research event; no authorization granted")
        else:
            print(render(row), end="")
        return 0
    except (ValueError, TypeError, KeyError, OSError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(command())
