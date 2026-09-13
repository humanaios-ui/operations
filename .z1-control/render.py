#!/usr/bin/env python3
"""Render Z1_INBOX_INDEX.md from z1-inbox/INDEX.yaml.

The question this answers is "what does Z2 owe a decision on?" — which before
this file required opening 24 markdown files and reading a prose `**Status:**`
line that meant something different in each.

Usage:
  python3 .z1-control/render.py           # write Z1_INBOX_INDEX.md
  python3 .z1-control/render.py --check   # exit 1 if out of sync (CI mode)
  python3 .z1-control/render.py --smoke-test

Deps: PyYAML. No network; writes only Z1_INBOX_INDEX.md.
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

TOOL_NAME = "z1_inbox_renderer"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 1

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "z1-inbox", "INDEX.yaml")
OUTPUT = os.path.join(ROOT, "Z1_INBOX_INDEX.md")

STATUS_LABEL = {
    "awaiting_z2": "⏳ awaiting Z2",
    "ratified": "✅ ratified",
    "edit_requested": "✏️ edit requested",
    "rejected": "❌ rejected",
    "withdrawn": "↩️ withdrawn",
    "superseded": "⤴️ superseded",
}
# Statuses that represent a Z2 decision. Kept in step with validate.TERMINAL.
TERMINAL = {"ratified", "edit_requested", "rejected"}
# Closed without a Z2 decision — no signature to show.
CLOSED_UNDECIDED = {"withdrawn", "superseded"}


def _esc(text: object) -> str:
    return (str(text) if text is not None else "").replace("|", "\\|").replace("\n", " ").strip()


def _date(value: object) -> datetime.date | None:
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


CHECKLIST_HEADING = re.compile(r"^#{1,6}\s*Z2 Review Checklist\s*$", re.MULTILINE)
CHECKLIST_ITEM = re.compile(r"^- \[( |x|X)\]\s+(.*)$")


def open_questions(path: str, read) -> list[str]:
    """The unticked `- [ ]` lines under a candidate's '## Z2 Review Checklist'.

    The questions Z2 has to answer were only ever readable by opening each
    candidate block and scrolling to the bottom. Lifting them into the generated
    index is the difference between a queue you can act on and a queue you have
    to go looking for.
    """
    try:
        text = read(path)
    except Exception:
        return []
    m = CHECKLIST_HEADING.search(text)
    if not m:
        return []
    out: list[str] = []
    collecting = False
    for line in text[m.end():].split("\n"):
        if line.startswith("#"):
            break  # next section
        item = CHECKLIST_ITEM.match(line)
        if item:
            collecting = item.group(1) == " "
            if collecting:
                out.append(item.group(2).strip())
        elif collecting and line.strip() and line[:1].isspace():
            # A wrapped continuation line. Without this the item is cut off at
            # the first newline, which truncated questions mid-sentence.
            out[-1] += " " + line.strip()
        elif not line.strip():
            collecting = False
    return out


def render(index: dict, read=None) -> str:
    candidates = index.get("candidates") or []
    records = index.get("records") or []
    window = index.get("decision_window_days") or 0
    ratifiers = index.get("ratifiers") or []

    lines: list[str] = []
    add = lines.append

    add("# Z1 Inbox — Conversion Index")
    add("")
    add("Rendered from `z1-inbox/INDEX.yaml` (SSOT). **Do not hand-edit — edit the index** and "
        "run `python3 .z1-control/render.py`. CI runs `--check`, so the two cannot disagree.")
    add("")
    add(f"A **candidate** asks Z2 for a decision. A **record** reports, receipts or hands off "
        f"and asks for nothing. Z2's routine window is **{window} days** from submission "
        f"(CLAUDE.md); `decision_due` is derived from that, not hand-set. Signing is "
        f"{', '.join(f'**{r}**' for r in ratifiers)} — `.z1-control/validate.py` refuses any "
        f"other signature.")
    add("")

    counts: dict[str, int] = {}
    for c in candidates:
        key = str(c.get("status"))
        counts[key] = counts.get(key, 0) + 1
    summary = " · ".join(f"{STATUS_LABEL.get(k, k)} {v}" for k, v in sorted(counts.items()))
    add(f"**{len(candidates)} candidates** — {summary} · **{len(records)} records**")
    add("")

    # --- awaiting a decision ------------------------------------------------
    # Deliberately date-INDEPENDENT: no "overdue by N days" column, or --check
    # would start failing on a day nobody changed anything. `validate.py` makes
    # the is-it-late-today call, where a moving answer belongs.
    waiting = [c for c in candidates if c.get("status") == "awaiting_z2"]
    if waiting:
        add(f"## Awaiting Z2 ({len(waiting)})")
        add("")
        add("Earliest due first. Anything dated before today is past the window — "
            "`.z1-control/validate.py` flags those on every run, and CLAUDE.md routes a closed "
            "window to Admiral re-read.")
        add("")
        add("| decision due | candidate | what it asks | block |")
        add("|---|---|---|---|")
        for c in sorted(waiting, key=lambda x: (str(_date(x.get("submitted"))), str(x.get("q_id")))):
            sub = _date(c.get("submitted"))
            due = (sub + datetime.timedelta(days=window)).isoformat() if sub and window else "—"
            flag = " ⚠️ falsifier waived" if c.get("falsifier_waiver") else ""
            add(f"| {due} | **{_esc(c.get('q_id'))}**{flag} | {_esc(c.get('title'))} | "
                f"`{_esc(c.get('path'))}` |")
        add("")

    # --- decided ------------------------------------------------------------
    # TERMINAL only. `withdrawn` and `superseded` are in the validator's OPEN
    # set and carry no signature, so rendering them here would show a decision
    # with blank signer and ruling — a lifecycle state misstated as a ruling.
    decided = [c for c in candidates if c.get("status") in TERMINAL]
    if decided:
        add(f"## Decided ({len(decided)})")
        add("")
        add("| decision | candidate | signed by | on | ruling |")
        add("|---|---|---|---|---|")
        for c in sorted(decided, key=lambda x: (str(x.get("ratified_at")), str(x.get("q_id")))):
            ruling = c.get("z2_ruling")
            cite = f"`{_esc(ruling)}`" if ruling else "—"
            if c.get("z2_hash"):
                cite += f"<br>`{_esc(c.get('z2_hash'))}`"
            add(f"| {STATUS_LABEL.get(str(c.get('status')), _esc(c.get('status')))} | "
                f"**{_esc(c.get('q_id'))}** | {_esc(c.get('ratified_by')) or '—'} | "
                f"{_esc(c.get('ratified_at')) or '—'} | {cite} |")
        add("")

    # --- closed without a decision ------------------------------------------
    closed = [c for c in candidates if c.get("status") in CLOSED_UNDECIDED]
    if closed:
        add(f"## Closed without a Z2 decision ({len(closed)})")
        add("")
        add("Withdrawn or superseded by the proposer. No Z2 ruling was issued, so these carry "
            "no signature — they are not decisions.")
        add("")
        add("| state | candidate | what it asked | block |")
        add("|---|---|---|---|")
        for c in sorted(closed, key=lambda x: str(x.get("q_id"))):
            add(f"| {STATUS_LABEL.get(str(c.get('status')), _esc(c.get('status')))} | "
                f"**{_esc(c.get('q_id'))}** | {_esc(c.get('title'))} | "
                f"`{_esc(c.get('path'))}` |")
        add("")

    # --- waivers ------------------------------------------------------------
    waived = [c for c in candidates if c.get("falsifier_waiver")]
    if waived:
        add(f"## ⚠️ Falsifier waivers ({len(waived)}) — open for Z2")
        add("")
        add("A candidate with no falsifier. The waiver is the candidate's own claim that it "
            "predicts nothing, recorded so it cannot pass silently. Accepting or refusing it "
            "is Z2's act.")
        add("")
        add("| candidate | stated reason |")
        add("|---|---|")
        for c in sorted(waived, key=lambda x: str(x.get("q_id"))):
            add(f"| **{_esc(c.get('q_id'))}** | {_esc(c.get('falsifier_waiver'))} |")
        add("")

    # --- the questions themselves -------------------------------------------
    if read is not None:
        asked = [(c, open_questions(str(c.get("path")), read)) for c in waiting]
        asked = [(c, qs) for c, qs in asked if qs]
        if asked:
            total = sum(len(qs) for _, qs in asked)
            add(f"## Open questions for Z2 ({total})")
            add("")
            add("Every unticked item from the `## Z2 Review Checklist` of each candidate still "
                "awaiting a decision. Answer them in the block itself — ticking a box here does "
                "nothing, because this file is generated.")
            add("")
            for c, qs in sorted(asked, key=lambda x: str(x[0].get("q_id"))):
                add(f"### {_esc(c.get('q_id'))} ({len(qs)})")
                add("")
                add(f"`{_esc(c.get('path'))}`")
                add("")
                for q in qs:
                    add(f"- [ ] {q}")
                add("")

    # --- records ------------------------------------------------------------
    if records:
        add(f"## Records ({len(records)})")
        add("")
        add("No decision requested. Listed so the coverage rule cannot be satisfied by silence.")
        add("")
        add("| file | what it is |")
        add("|---|---|")
        for r in sorted(records, key=lambda x: str(x.get("path"))):
            add(f"| `{_esc(r.get('path'))}` | {_esc(r.get('title'))} |")
        add("")

    # --- excluded -----------------------------------------------------------
    # The validator accepts an `excluded:` path as satisfying coverage, so the
    # human-facing index must show it. Otherwise "explicitly excluded" becomes a
    # way to make a file disappear from the index while passing the gate.
    excluded = index.get("excluded") or []
    if excluded:
        add(f"## Excluded from the conversion record ({len(excluded)})")
        add("")
        add("Neither a candidate nor a record. Listed because an exclusion the index accepts "
            "must still be visible — silence is what the coverage rule exists to prevent.")
        add("")
        for path in sorted(str(p) for p in excluded):
            add(f"- `{_esc(path)}`")
        add("")

    add("---")
    add("")
    add("**Converting an inbox item to a Z2 decision:** add it to `z1-inbox/INDEX.yaml` under "
        "`candidates:` with `status: awaiting_z2` and a falsifier in the block itself, run "
        "`python3 .z1-control/render.py`, and commit both. An undecided candidate carries no "
        "signature fields at all.")
    add("")
    add("Z2 records the decision by setting `status`, `ratified_by`, `ratified_at`, a "
        "`z2_ruling` that resolves to a file **indexed under `records:`**, and a `z2_hash` "
        "that **appears in that ruling**. All five are required: the validator refuses a "
        "signature from anyone outside `ratifiers:`, and refuses a hash the cited ruling does "
        "not carry.")
    add("")
    return "\n".join(lines)


def run_smoke_test() -> int:
    sample = {
        "decision_window_days": 2,
        "ratifiers": ["Night"],
        "candidates": [
            {"q_id": "Q-OPEN-01", "title": "A|B", "path": "z1-inbox/x/a.md",
             "submitted": "2026-09-10", "status": "awaiting_z2"},
            {"q_id": "Q-WAIVED-01", "title": "no prediction", "path": "z1-inbox/x/b.md",
             "submitted": "2026-09-11", "status": "awaiting_z2",
             "falsifier_waiver": "reference architecture"},
            {"q_id": "Q-DONE-01", "title": "done", "path": "z1-inbox/x/c.md",
             "submitted": "2026-09-07", "status": "ratified", "ratified_by": "Night",
             "ratified_at": "2026-09-08", "z2_ruling": "z1-inbox/x/r.md", "z2_hash": "abc"},
        ],
        "records": [{"path": "z1-inbox/x/r.md", "title": "ruling"}],
    }
    out = render(sample)
    assert "3 candidates" in out, out
    assert "Open questions" not in out, "no reader supplied — must not invent questions"

    fs = {"z1-inbox/x/a.md": "# c\n## Z2 Review Checklist\n- [ ] decide the thing\n"
                             "      which wraps onto a second line\n"
                             "- [x] already done\n      and its wrap\n"
                             "\n## Summary\n- [ ] not a question\n"}
    out2 = render(sample, read=lambda p: fs[p])
    assert "Open questions for Z2 (1)" in out2, out2
    assert "decide the thing which wraps onto a second line" in out2, out2
    assert "and its wrap" not in out2, "a ticked item's continuation must not leak"
    assert "already done" not in out2, "ticked items must not be listed"
    assert "not a question" not in out2, "items past the next heading must not be listed"
    assert "Awaiting Z2 (2)" in out, out
    assert "Decided (1)" in out, out
    assert "Falsifier waivers (1)" in out, out
    assert "Records (1)" in out, out
    assert "A\\|B" in out, "pipe not escaped"
    # derived due date, not a stored one
    assert "| 2026-09-12 | **Q-OPEN-01**" in out, out
    # date-independence: rendering must not depend on today
    assert "overdue" not in out.lower(), "renderer leaked a moving value into a --check'd file"
    print("smoke-test OK — renders queue, decisions, waivers and records; derives due dates; "
          "escapes cells; lifts unticked Z2 checklist items; stays date-independent.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Render Z1_INBOX_INDEX.md from z1-inbox/INDEX.yaml")
    ap.add_argument("--check", action="store_true", help="exit 1 if Z1_INBOX_INDEX.md is out of sync")
    ap.add_argument("--smoke-test", action="store_true", help="self-test and exit")
    args = ap.parse_args()

    if args.smoke_test:
        return run_smoke_test()

    if not os.path.exists(INDEX):
        print(f"::error::missing {os.path.relpath(INDEX, ROOT)}")
        return 1

    # Same strict parse as the validator: a duplicate key must not silently
    # change what the rendered index claims.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from validate import load_index  # noqa: E402

    def read_repo_file(rel: str) -> str:
        return open(os.path.join(ROOT, rel), encoding="utf-8").read()

    try:
        out = render(load_index(INDEX), read=read_repo_file)
    except yaml.YAMLError as exc:
        print(f"::error::z1-inbox/INDEX.yaml does not parse: "
              f"{str(exc).splitlines()[-1].strip()}")
        return 1

    if args.check:
        current = open(OUTPUT, encoding="utf-8").read() if os.path.exists(OUTPUT) else ""
        if current != out:
            print("::error::Z1_INBOX_INDEX.md is out of sync with z1-inbox/INDEX.yaml — "
                  "run `python3 .z1-control/render.py` and commit.")
            return 1
        print("Z1_INBOX_INDEX.md: in sync with the index.")
        return 0

    with open(OUTPUT, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"wrote {os.path.relpath(OUTPUT, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
