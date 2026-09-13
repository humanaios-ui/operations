#!/usr/bin/env python3
"""Document review scheduler — record a review, derive the next one, triage the backlog.

The 39 overdue reviews are not 39 independent lapses. 35 of them share one
`review_due` (2026-08-01) and 4 share another (2026-08-15), because the
2026-07-02 seeding pass stamped the whole corpus with a single date. No
document has an `owner`, a `last_reviewed`, or an interval. So:

  - nothing can record that a review actually happened;
  - nothing can schedule the next one;
  - nobody is assigned; and
  - the whole corpus tips overdue on the same day, every time.

Bumping the 39 dates would clear the warnings and change none of that — and
setting a review date is the owner's act, the same no-self-grant rule
`document-registry.yaml` already states for approval. This tool supplies the
missing lifecycle instead:

  --record   a review HAPPENED: stamps last_reviewed/reviewed_by and DERIVES
             the next review_due from the interval. This is the only supported
             way a review_due moves forward.
  --queue    what is stale, by how much, and under whose name.
  --pull     the backlog as an ORDERED QUEUE with no dates — work the head when
             there is capacity. Prints; never writes.
  --check    CI mode: every document carrying last_reviewed has the review_due
             its interval implies (exit 1 otherwise).

Intervals come from `review_policy:` in the registry, by status, overridable
per document with `review_interval_days`.

Usage:
  python3 .doc-control/review.py --queue
  python3 .doc-control/review.py --record HAIOS-GOV-001 --by Night
  python3 .doc-control/review.py --pull --limit 10
  python3 .doc-control/review.py --check
  python3 .doc-control/review.py --smoke-test

Deps: PyYAML. No network. Writes document-registry.yaml only under --record.
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs it
    print("::error::PyYAML not installed (pip install pyyaml)")
    sys.exit(2)

TOOL_NAME = "doc_review_scheduler"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 1

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strict_yaml  # noqa: E402  (same directory; keeps one strict loader, not three)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "document-registry.yaml")

# Used only when the registry declares no review_policy of its own.
DEFAULT_POLICY = {"draft": 30, "review": 90, "approved": 180}
# A document that is obsolete on purpose is not on a review cadence.
NO_REVIEW = {"superseded", "retired"}


def as_date(value: object) -> datetime.date | None:
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def valid_interval(value: object) -> int | None:
    """A usable interval, or None. `True` is an int in Python; it is not an interval."""
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None


def interval_for(doc: dict, policy: dict) -> int | None:
    """Days between reviews: the per-document override, else the status default.

    Fails CLOSED on a present-but-invalid override. Falling back to the status
    policy would let `review_interval_days: "ninety"` silently stamp a 90-day
    date, which is the wrong interval presented as the right one.
    """
    # Status wins first: a `retired` document carrying review_interval_days: 30
    # would otherwise be treated as on-cadence, contradicting the rule that
    # superseded/retired documents are off it entirely.
    if doc.get("status") in NO_REVIEW:
        return None
    if "review_interval_days" in doc and doc.get("review_interval_days") is not None:
        return valid_interval(doc.get("review_interval_days"))
    return valid_interval(policy.get(doc.get("status")))


def next_due(doc: dict, policy: dict) -> datetime.date | None:
    """The review_due a document's own history implies, or None if unknowable."""
    last = as_date(doc.get("last_reviewed"))
    days = interval_for(doc, policy)
    if last is None or days is None:
        return None
    return last + datetime.timedelta(days=days)


def load() -> dict:
    """Parse the registry strictly.

    safe_load keeps the last of a duplicate key, so appending a second
    `review_baseline: {}` would make every freeze check read an empty mapping
    and pass — disabling the gate with one line and no error.
    """
    if not os.path.exists(REGISTRY):
        print(f"::error::missing {os.path.relpath(REGISTRY, ROOT)}")
        sys.exit(1)
    try:
        return strict_yaml.load_registry(REGISTRY)
    except yaml.YAMLError as exc:
        print(f"::error::document-registry.yaml does not parse: "
              f"{str(exc).splitlines()[-1].strip()}")
        sys.exit(1)


def policy_of(reg: dict) -> dict:
    declared = reg.get("review_policy")
    return declared if isinstance(declared, dict) and declared else dict(DEFAULT_POLICY)


def policy_errors(reg: dict) -> list[str]:
    """A declared policy must be usable. A broken one is a lifecycle that cannot run."""
    declared = reg.get("review_policy")
    if declared is None:
        return []
    if not isinstance(declared, dict) or not declared:
        return ["review_policy must be a non-empty mapping of status -> days"]
    out = []
    for status, days in sorted(declared.items(), key=lambda kv: str(kv[0])):
        if status in NO_REVIEW:
            out.append(f"review_policy.{status}: '{status}' is off the review cadence "
                       f"and must not carry an interval")
        elif valid_interval(days) is None:
            out.append(f"review_policy.{status}: interval must be a positive integer, "
                       f"got {days!r} — --record would fail with no interval")
    return out


def triage(reg: dict, today: datetime.date) -> dict:
    """Classify every document against today. Pure."""
    policy = policy_of(reg)
    rows = []
    for d in reg.get("documents") or []:
        status = d.get("status")
        if status in NO_REVIEW:
            continue
        due = as_date(d.get("review_due"))
        last = as_date(d.get("last_reviewed"))
        rows.append({
            "doc_id": d.get("doc_id"),
            "title": d.get("title"),
            "area": d.get("area"),
            "repo": d.get("canonical_repo"),
            "path": d.get("canonical_path"),
            "status": status,
            "owner": d.get("owner"),
            "review_due": due.isoformat() if due else None,
            "last_reviewed": last.isoformat() if last else None,
            "interval_days": interval_for(d, policy),
            "days_overdue": (today - due).days if due and due < today else 0,
            # The distinguishing fact about the backlog: never reviewed, so no
            # interval can place the next one.
            "never_reviewed": last is None,
        })
    overdue = [r for r in rows if r["days_overdue"] > 0]
    return {
        "generated": today.isoformat(),
        "policy": policy,
        "total": len(rows),
        "overdue": sorted(overdue, key=lambda r: (-r["days_overdue"], str(r["doc_id"]))),
        "unowned": [r for r in rows if not r["owner"]],
        "never_reviewed": [r for r in rows if r["never_reviewed"]],
        "rows": rows,
    }


def cmd_queue(reg: dict, today: datetime.date) -> int:
    t = triage(reg, today)
    print(f"Document review queue — {t['generated']}")
    print(f"  policy: {', '.join(f'{k}={v}d' for k, v in sorted(t['policy'].items()))}")
    print(f"  {t['total']} documents on a cadence · {len(t['overdue'])} overdue · "
          f"{len(t['unowned'])} unowned · {len(t['never_reviewed'])} never reviewed")
    if not t["overdue"]:
        print("\nNothing overdue.")
        return 0
    buckets: dict[str, list] = {}
    for r in t["overdue"]:
        buckets.setdefault(str(r["review_due"]), []).append(r)
    print("\nOverdue, grouped by the date they were stamped with:")
    for due in sorted(buckets):
        rows = buckets[due]
        print(f"\n  due {due} — {len(rows)} document(s), {rows[0]['days_overdue']}d late")
        for r in rows:
            owner = r["owner"] or "UNOWNED"
            print(f"    {r['doc_id']:<16} {owner:<10} {r['status']:<9} "
                  f"{r['repo']}/{r['path']}")
    print("\nA shared due date is a seeding artifact, not 39 independent lapses. "
          "Clear one with:\n  python3 .doc-control/review.py --record <DOC_ID> --by <owner>")
    return 0


def pull_order(reg: dict, today: datetime.date) -> list[dict]:
    """The backlog as an ORDERED QUEUE, with no dates attached.

    An earlier version of this emitted a staggered schedule — one document per
    weekday until the backlog "cleared" on a computed end date. That end date was
    invented. Nothing outside this system required the 39th document to be read
    by any particular day, so the schedule manufactured 39 deadlines and then
    reported progress against them, which is a way of generating failure that
    has nothing to do with the work.

    A date is only real here when something outside the system sets it. Those get
    a `regulatory_deadline` and must name their `regulatory_basis`; everything
    else is ordered by how stale it is and pulled when there is capacity to pull
    it. The queue has a head, not an end.
    """
    t = triage(reg, today)
    policy = policy_of(reg)
    by_id = {d.get("doc_id"): d for d in reg.get("documents") or []}

    rows = []
    for r in t["overdue"]:
        doc = by_id.get(r["doc_id"], {})
        interval = interval_for(doc, policy) or 1
        deadline = as_date(doc.get("regulatory_deadline"))
        rows.append({
            **r,
            "regulatory_deadline": deadline.isoformat() if deadline else None,
            "regulatory_basis": doc.get("regulatory_basis"),
            # How far past its own staleness threshold, as a multiple of that
            # threshold. Scale-free, so a 30-day draft and a 180-day approved
            # document compare honestly instead of by raw days late.
            "staleness": round(r["days_overdue"] / interval, 2),
        })

    # Externally-imposed dates first, nearest first. Then most stale.
    rows.sort(key=lambda r: (
        r["regulatory_deadline"] is None,
        r["regulatory_deadline"] or "",
        -r["staleness"],
        str(r["doc_id"]),
    ))
    return rows


def cmd_pull(reg: dict, today: datetime.date, limit: int) -> int:
    """Show the next N documents to review. No dates, no end date."""
    rows = pull_order(reg, today)
    if not rows:
        print("Nothing stale — the queue is empty.")
        return 0
    regulated = [r for r in rows if r["regulatory_deadline"]]
    print(f"Review queue — {len(rows)} document(s) past their staleness threshold, "
          f"ordered by pull priority (as of {today.isoformat()}).")
    print("No schedule and no end date: work the head of the queue when there is "
          "capacity, and the queue drains at whatever rate capacity allows.")
    if regulated:
        print(f"\n{len(regulated)} carry an externally-imposed deadline and sort first.")
    else:
        print("\nNo document carries a regulatory_deadline, so no date here is real.")
    print(f"\nNext {min(limit, len(rows))}:\n")
    print("| # | doc_id | staleness | owner | status | canonical path | deadline |")
    print("|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows[:limit], 1):
        print(f"| {i} | {r['doc_id']} | {r['staleness']}× | {r['owner'] or '—'} | "
              f"{r['status']} | `{r['repo']}/{r['path']}` | "
              f"{r['regulatory_deadline'] or '—'} |")
    if len(rows) > limit:
        print(f"\n…and {len(rows) - limit} behind them. Raise --limit to see more; "
              f"the order does not change.")
    print("\nClear the head with:\n"
          "  python3 .doc-control/review.py --record <DOC_ID> --by <owner>")
    return 0


def cmd_check(reg: dict, today: datetime.date | None = None) -> int:
    """review_due is derived where history exists, and frozen where it does not.

    Derivation alone left a hole: no document carries `last_reviewed` yet, so
    every one of the 39 seeded dates could be hand-edited to any future value
    and this check still returned 0 — the lifecycle would have been enforced
    only for documents that had already entered it. `review_baseline:` freezes
    the seeded dates, so a no-history document must keep the date it was seeded
    with until a review is actually recorded.
    """
    today = today or datetime.date.today()
    policy = policy_of(reg)
    errors = list(policy_errors(reg))
    baseline = reg.get("review_baseline")
    if baseline is not None and not isinstance(baseline, dict):
        errors.append("review_baseline must be a mapping of doc_id -> seeded ISO date")
        baseline = None

    # The freeze has to be total to be a freeze. Applying it only where an entry
    # happens to exist meant a PR could DELETE one baseline line and move that
    # document's date in the same commit, and the check would pass by omission —
    # the same shape as the bypass the baseline was added to close.
    if baseline is not None:
        known = {d.get("doc_id") for d in reg.get("documents") or []}
        for stray in sorted(k for k in baseline if k not in known):
            errors.append(f"review_baseline.{stray}: no such doc_id in the registry")
        for d in reg.get("documents") or []:
            did, st = d.get("doc_id"), d.get("status")
            if st in NO_REVIEW or d.get("last_reviewed") or not d.get("review_due"):
                continue
            if did not in baseline:
                errors.append(
                    f"{did}: has a review_due but no recorded review and no "
                    f"review_baseline entry — every un-reviewed date must be frozen, "
                    f"or removing a baseline line would silently unfreeze it")

    for d in reg.get("documents") or []:
        did = d.get("doc_id", "<missing>")
        last_raw = d.get("last_reviewed")
        if last_raw and as_date(last_raw) is None:
            errors.append(f"{did}: last_reviewed '{last_raw}' is not an ISO date")
            continue
        own = d.get("review_interval_days")
        if own is not None and valid_interval(own) is None:
            # valid_interval, not isinstance(own, int): YAML `true` IS an int in
            # Python, so a bare isinstance check let review_interval_days: true
            # through to expected=None and a silent pass.
            errors.append(f"{did}: review_interval_days must be a positive integer, got {own!r}")
            continue
        if d.get("status") in NO_REVIEW and own is not None:
            errors.append(f"{did}: status '{d.get('status')}' is off the review cadence "
                          f"and must not carry review_interval_days")
            continue
        # A date is only real when something outside this system imposes it.
        # Requiring the basis is what stops `regulatory_deadline` becoming a
        # place to launder invented urgency back into the registry.
        rd_raw = d.get("regulatory_deadline")
        if rd_raw:
            if as_date(rd_raw) is None:
                errors.append(f"{did}: regulatory_deadline '{rd_raw}' is not an ISO date")
            if not d.get("regulatory_basis"):
                errors.append(
                    f"{did}: regulatory_deadline without regulatory_basis — name the "
                    f"statute, contract or commitment that imposes it. A deadline with "
                    f"no external source is not a deadline.")
        elif d.get("regulatory_basis"):
            errors.append(f"{did}: regulatory_basis without regulatory_deadline")
        if d.get("last_reviewed") and not d.get("reviewed_by"):
            errors.append(f"{did}: last_reviewed without reviewed_by — a review is somebody's act")
        seen = as_date(last_raw)
        if seen and seen > today:
            # --record refuses a future date, but a direct registry edit does not
            # go through --record. Without this, "reviewed tomorrow" derives a
            # future review_due and clears an overdue item with no review.
            errors.append(f"{did}: last_reviewed {seen.isoformat()} is in the future — "
                          f"a review cannot have happened yet")
            continue
        actual = as_date(d.get("review_due"))
        expected = next_due(d, policy)
        if expected is not None:
            if actual != expected:
                errors.append(
                    f"{did}: review_due is derived from last_reviewed "
                    f"({d.get('last_reviewed')}) + {interval_for(d, policy)}d = "
                    f"{expected.isoformat()}; registry says {d.get('review_due')!r}. "
                    f"Run `--record` rather than editing the date.")
            continue
        # No recorded history: the seeded date is frozen until a review happens.
        # Missing coverage is reported above, so this only compares what exists.
        if baseline and did in baseline:
            frozen = as_date(baseline[did])
            if frozen is None:
                errors.append(f"review_baseline.{did}: "
                              f"{baseline[did]!r} is not an ISO date")
            elif actual != frozen:
                errors.append(
                    f"{did}: review_due {d.get('review_due')!r} was moved from its frozen "
                    f"baseline {frozen.isoformat()} without a recorded review. Run "
                    f"`--record --by <owner>`, or change the baseline as a ratified "
                    f"re-dating — not the date alone.")
    for e in errors:
        print(f"::error::{e}")
    if errors:
        print(f"\n{len(errors)} review-schedule violation(s).")
        return 1
    print("review schedule: OK — every recorded review derives its own next due date.")
    return 0


def cmd_record(reg: dict, doc_id: str, by: str, on: datetime.date) -> int:
    """Stamp a review and derive the next due date, editing the registry in place.

    Rewrites only the three affected lines via a targeted text edit: the registry
    carries comments and inline-flow blocks that a yaml.dump round-trip destroys.
    """
    docs = reg.get("documents") or []
    doc = next((d for d in docs if d.get("doc_id") == doc_id), None)
    if doc is None:
        print(f"::error::{doc_id} is not in the registry")
        return 1
    if doc.get("status") in NO_REVIEW:
        print(f"::error::{doc_id} is {doc.get('status')} — not on a review cadence")
        return 1
    policy = policy_of(reg)
    days = interval_for(doc, policy)
    if days is None:
        print(f"::error::{doc_id}: no interval for status '{doc.get('status')}' — "
              f"add review_interval_days or a review_policy entry")
        return 1
    last_seen = as_date(doc.get("last_reviewed"))
    if last_seen and on < last_seen:
        print(f"::error::{doc_id}: review date {on.isoformat()} precedes the recorded "
              f"last_reviewed {last_seen.isoformat()}")
        return 1
    # This command asserts a review HAPPENED. A future date would let the queue
    # be cleared by recording a review nobody has done yet.
    if on > datetime.date.today():
        print(f"::error::{doc_id}: review date {on.isoformat()} is in the future — "
              f"--record asserts a review that has already happened")
        return 1
    # `--by` is written into the registry. Serialize it as YAML rather than
    # interpolating it into a quoted scalar, where a quote or newline could
    # terminate the string and inject further fields into the document.
    by_scalar = yaml.safe_dump(by, default_flow_style=True, width=10**6).strip()
    if by_scalar.endswith("..."):
        by_scalar = by_scalar[:-3].strip()
    if "\n" in by_scalar or not by_scalar:
        print(f"::error::--by value cannot be represented as a single-line YAML scalar")
        return 1
    due = on + datetime.timedelta(days=days)

    text = open(REGISTRY, encoding="utf-8").read()
    block = re.search(rf"(^  - doc_id: {re.escape(doc_id)}\n)(.*?)(?=^  - doc_id: |\Z)",
                      text, re.MULTILINE | re.DOTALL)
    if not block:
        print(f"::error::{doc_id}: could not locate its block in {REGISTRY}")
        return 1
    head, body = block.group(1), block.group(2)

    def upsert(src: str, key: str, scalar: str) -> str:
        """Replace or append `key`, where `scalar` is already YAML-serialized."""
        line = f"    {key}: {scalar}\n"
        pattern = rf"^    {re.escape(key)}:.*\n"
        if re.search(pattern, src, re.MULTILINE):
            return re.sub(pattern, lambda _: line, src, count=1, flags=re.MULTILINE)
        return src + line

    body = upsert(body, "review_due", f'"{due.isoformat()}"')
    body = upsert(body, "last_reviewed", f'"{on.isoformat()}"')
    body = upsert(body, "reviewed_by", by_scalar)

    open(REGISTRY, "w", encoding="utf-8").write(text[:block.start()] + head + body
                                                + text[block.end():])
    print(f"{doc_id}: reviewed {on.isoformat()} by {by}; next review_due "
          f"{due.isoformat()} (+{days}d).")
    print("Commit document-registry.yaml. Approval remains a separate owner act.")
    return 0


def run_smoke_test() -> int:
    today = datetime.date(2026, 9, 13)
    reg = {
        "review_policy": {"draft": 30, "review": 90, "approved": 180},
        "documents": [
            # The seeded backlog shape: a shared due date and no history.
            {"doc_id": "HAIOS-A-001", "status": "review", "review_due": "2026-08-01"},
            {"doc_id": "HAIOS-A-002", "status": "review", "review_due": "2026-08-01"},
            # A document with a real history, correctly derived.
            {"doc_id": "HAIOS-B-001", "status": "approved", "last_reviewed": "2026-09-01",
             "reviewed_by": "Night", "review_due": "2027-02-28", "owner": "Night"},
            # Retired: off the cadence entirely.
            {"doc_id": "HAIOS-C-001", "status": "retired", "review_due": "2020-01-01"},
        ],
    }
    t = triage(reg, today)
    assert t["total"] == 3, t["total"]                      # retired excluded
    assert len(t["overdue"]) == 2, t["overdue"]
    assert t["overdue"][0]["days_overdue"] == 43, t["overdue"][0]
    assert len(t["never_reviewed"]) == 2, t["never_reviewed"]
    assert len(t["unowned"]) == 2, t["unowned"]

    import contextlib
    import io

    def quiet(fn, *args) -> int:
        """These commands report through stdout; swallow it so a pass looks like one."""
        with contextlib.redirect_stdout(io.StringIO()):
            return fn(*args)

    def quiet_check(registry: dict) -> int:
        return quiet(cmd_check, registry)

    # Derivation: last_reviewed + interval, and --check accepts a correct one.
    assert next_due(reg["documents"][2], reg["review_policy"]) == datetime.date(2027, 2, 28)
    assert quiet_check(reg) == 0

    # A hand-edited review_due that contradicts the history must be refused.
    bad = {**reg, "documents": [{**reg["documents"][2], "review_due": "2099-01-01"}]}
    assert quiet_check(bad) == 1

    # last_reviewed with nobody's name on it must be refused.
    anon = {**reg, "documents": [{"doc_id": "HAIOS-D-001", "status": "review",
                                  "last_reviewed": "2026-09-01", "review_due": "2026-11-30"}]}
    assert quiet_check(anon) == 1

    # A non-integer interval must be refused, not silently treated as absent.
    junk = {**reg, "documents": [{"doc_id": "HAIOS-E-001", "status": "review",
                                  "review_interval_days": "ninety"}]}
    assert quiet_check(junk) == 1
    # ...and must fail closed rather than borrowing the status default.
    assert interval_for({"status": "review", "review_interval_days": "ninety"},
                        reg["review_policy"]) is None
    assert interval_for({"status": "review", "review_interval_days": True},
                        reg["review_policy"]) is None

    # A broken policy is a lifecycle that cannot run; --check must say so even
    # when no document has history yet.
    assert quiet_check({**reg, "review_policy": {"review": 0}}) == 1
    assert quiet_check({**reg, "review_policy": {"retired": 30}}) == 1

    # A seeded date moved without a recorded review must be refused.
    seeded = {**reg, "review_baseline": {"HAIOS-A-001": "2026-08-01"},
              "documents": [{"doc_id": "HAIOS-A-001", "status": "review",
                             "review_due": "2027-08-01"}]}
    assert quiet_check(seeded) == 1
    kept = {**seeded, "documents": [{"doc_id": "HAIOS-A-001", "status": "review",
                                     "review_due": "2026-08-01"}]}
    assert quiet_check(kept) == 0

    # --record asserts a review that already happened.
    future = datetime.date.today() + datetime.timedelta(days=1)
    assert quiet(cmd_record, reg, "HAIOS-A-001", "Night", future) == 1

    # A reviewer name must be serialized, not interpolated: this would otherwise
    # close the quoted scalar and inject a field.
    injected = 'Night"\n    status: approved\n    x: "'
    scalar = yaml.safe_dump(injected, default_flow_style=True, width=10**6).strip()
    assert "\n" not in scalar, scalar
    assert yaml.safe_load(f"reviewed_by: {scalar}")["reviewed_by"] == injected

    # A retired document must not be dragged back on-cadence by an override.
    assert interval_for({"status": "retired", "review_interval_days": 30},
                        reg["review_policy"]) is None
    assert quiet_check({**reg, "documents": [{"doc_id": "HAIOS-F-001", "status": "retired",
                                              "review_interval_days": 30}]}) == 1

    # YAML `true` is an int in Python; --check must not let it through.
    assert quiet_check({**reg, "documents": [
        {"doc_id": "HAIOS-G-001", "status": "review", "review_interval_days": True,
         "last_reviewed": "2026-09-01", "reviewed_by": "Night",
         "review_due": "2026-11-30"}]}) == 1

    # A review cannot have happened tomorrow, however the date got there.
    tomorrow = (datetime.date(2026, 9, 13) + datetime.timedelta(days=1)).isoformat()
    assert quiet_check({**reg, "documents": [
        {"doc_id": "HAIOS-H-001", "status": "review", "last_reviewed": tomorrow,
         "reviewed_by": "Night", "review_due": "2026-12-13"}]},
        ) == 1

    # Deleting a baseline entry must not silently unfreeze that document.
    assert quiet_check({**reg, "review_baseline": {},
                        "documents": [{"doc_id": "HAIOS-A-001", "status": "review",
                                       "review_due": "2027-08-01"}]}) == 1
    # ...and a baseline naming a document that does not exist is an error.
    assert quiet_check({**reg, "review_baseline": {"HAIOS-GHOST-01": "2026-08-01"},
                        "documents": []}) == 1

    # A duplicate key must not be able to empty the freeze.
    dup = ("review_policy: {review: 90}\n"
           "review_baseline:\n  HAIOS-A-001: \"2026-08-01\"\n"
           "review_baseline: {}\n")
    try:
        strict_yaml.loads(dup)
        raise AssertionError("strict loader accepted a duplicate review_baseline")
    except yaml.YAMLError as exc:
        assert "duplicate key" in str(exc), exc

    # The queue is ORDERED and carries no invented dates.
    rows = pull_order(reg, today)
    assert rows, rows
    assert all("proposed_review_due" not in r for r in rows), \
        "the pull queue must not assign dates"
    assert all(r["regulatory_deadline"] is None for r in rows), rows
    # Staleness is scale-free: 43 days past a 90-day threshold is 0.48x.
    assert rows[0]["staleness"] == round(43 / 90, 2), rows[0]

    # An externally-imposed deadline sorts ahead of a staler document without one.
    regulated = {**reg,
                 "review_baseline": {"HAIOS-A-001": "2026-01-01",
                                     "HAIOS-A-002": "2026-08-01"},
                 "documents": [
        {"doc_id": "HAIOS-A-001", "status": "review", "review_due": "2026-01-01"},
        {"doc_id": "HAIOS-A-002", "status": "review", "review_due": "2026-08-01",
         "regulatory_deadline": "2026-10-01", "regulatory_basis": "EU AI Act Art. 12"}]}
    order = [r["doc_id"] for r in pull_order(regulated, today)]
    assert order[0] == "HAIOS-A-002", order  # deadline beats raw staleness

    # A deadline with no external source is refused — that is the whole point.
    assert quiet_check({**reg, "documents": [
        {"doc_id": "HAIOS-I-001", "status": "review",
         "regulatory_deadline": "2026-10-01"}]}) == 1
    assert quiet_check({**reg, "documents": [
        {"doc_id": "HAIOS-J-001", "status": "review",
         "regulatory_basis": "a feeling"}]}) == 1

    print("smoke-test OK — triages the seeded backlog, derives the next due date from "
          "recorded history, refuses hand-edited, anonymous, future and boolean-interval "
          "dates, refuses an unfrozen or ghost baseline entry and a duplicate "
          "review_baseline key, keeps retired documents off the cadence even with an "
          "override, orders the backlog as a dateless pull queue with externally-imposed "
          "deadlines first, and refuses a deadline that names no external source.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Document review scheduler")
    ap.add_argument("--queue", action="store_true", help="show the review backlog")
    ap.add_argument("--check", action="store_true", help="CI: derived review_due must match")
    ap.add_argument("--pull", action="store_true",
                    help="show the next documents to review, ordered — no dates")
    ap.add_argument("--record", metavar="DOC_ID", help="record that a review happened")
    ap.add_argument("--by", metavar="NAME", help="who reviewed it (required with --record)")
    ap.add_argument("--on", metavar="YYYY-MM-DD", help="review date (default: today)")
    ap.add_argument("--limit", type=int, default=10,
                    help="--pull: how many queue entries to show (default 10)")
    ap.add_argument("--smoke-test", action="store_true", help="self-test and exit")
    args = ap.parse_args()

    if args.smoke_test:
        return run_smoke_test()

    today = datetime.date.today()
    if args.on and as_date(args.on) is None:
        print(f"::error::--on '{args.on}' is not an ISO date")
        return 1
    if args.limit < 1:
        print(f"::error::--limit must be at least 1; got {args.limit}")
        return 1

    reg = load()
    if args.record:
        if not args.by:
            print("::error::--record requires --by (a review is somebody's act)")
            return 1
        return cmd_record(reg, args.record, args.by, as_date(args.on) or today)
    if args.check:
        return cmd_check(reg)
    if args.pull:
        return cmd_pull(reg, today, args.limit)
    return cmd_queue(reg, today)


if __name__ == "__main__":
    sys.exit(main())
