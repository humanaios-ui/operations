#!/usr/bin/env python3
"""
pre_submit.py — run the PR pre-submission checks in one command.

    python3 scripts/pre_submit.py                     # print the report
    python3 scripts/pre_submit.py --body-out DRAFT.md # also write a PR body draft
    python3 scripts/pre_submit.py --body FILLED.md    # lint a body you have filled in

Checks, in order:
  1. Branch     not on the default branch; has commits ahead of the base.
  2. No-op      the branch changes at least one file (mirrors no-op-pr-guard).
  3. Readiness  scripts/verify_pr_readiness.sh (tool manifest, document control).
  4. Workflows  changed .github/workflows/*.yml parse, with no duplicate keys.
  5. Secrets    added lines contain no private keys or GitHub/AWS token formats.
  6. Molt tier  the committed diff is measured with the CI classifier (info only).

Checks 1-5 block (exit 1). Everything else is reported and does not block.
Environment problems (no base ref, not a git repo) exit 2.

The prediction fields are never filled in for you. smag_p and molt_tier_claimed
are the author's hypothesis; CI measures the diff and records the gap. A
pre-filled claim would always match the measurement and erase that signal. The
draft instead shows the measured tier beside the empty field.

This script is advisory tooling, not a gate. CI remains the authority.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / ".github" / "PULL_REQUEST_TEMPLATE.md"
VERIFY = REPO / "scripts" / "verify_pr_readiness.sh"
CLASSIFIER = REPO / "tools" / "molting_protocol_diff_v1_0.py"
DEFAULT_BRANCHES = ("main", "master")

# Deliberately high-precision. A false positive here blocks a push, so only
# formats with a fixed shape are listed. gitleaks in CI is the full scanner.
# The private-key header is split so this file does not match itself.
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN [A-Z ]*" + "PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}

# Governance files that CLAUDE.md lists as requiring a Z2 signature.
Z2_FILES = {
    "REGISTERED.md", "PRIORITY_QUEUE.md", "ZONE_REGISTRY.md", "PLANNED_REPOS.md",
    "CLAUDE.md", "GOVERNANCE.md", "MOLT_STATE.md", "system_graph.json",
}
Z3_PATTERN = re.compile(r"(^|/)(\.env|secrets?|deploy|billing)", re.IGNORECASE)

MARK = {"pass": "✓", "info": "·", "warn": "⚠", "fail": "✗"}
MOLT_LINE = re.compile(r"^\*\*molt_tier_claimed:\*\*.*$", re.MULTILINE)


@dataclass
class Check:
    name: str
    status: str  # "pass" | "info" | "warn" | "fail"
    detail: str = ""


# ---------------------------------------------------------------- git helpers

def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout


def ref_exists(ref: str) -> bool:
    return subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=REPO, capture_output=True,
    ).returncode == 0


def resolve_base() -> str:
    for ref in ("origin/main", "main"):
        if ref_exists(ref):
            return ref
    raise RuntimeError("neither origin/main nor main exists; fetch the default branch first")


def changed_files(base: str) -> list[str]:
    out = git("diff", "--name-only", "--diff-filter=ACMRD", f"{base}...HEAD")
    return [line for line in out.splitlines() if line]


# --------------------------------------------------------------- claim parsing

def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def claimed_tier(body: str) -> int | None:
    """A filled-in claim is a bare digit 0-2. The unfilled `[0 | 1 | 2]` is not one.

    The digit must not be followed by another digit or `|`, so `10` never reads
    as a claim of Tier 1.
    """
    match = re.search(r"molt_tier_claimed:\*{0,2}[\s`\[]*([0-2])(?!\s*[\d|])", strip_comments(body))
    return int(match.group(1)) if match else None


def smag_prediction(body: str) -> float | None:
    match = re.search(r"smag_p:\s*(\d?\.\d+)", strip_comments(body))
    return float(match.group(1)) if match else None


def zone_ticked(body: str) -> bool:
    return bool(re.search(r"- \[[xX]\] \*\*Z[123]\*\*", strip_comments(body)))


# ----------------------------------------------------------------- the checks

def check_branch(base: str) -> list[Check]:
    out = []
    branch = git("branch", "--show-current").strip()
    if not branch or branch in DEFAULT_BRANCHES:
        out.append(Check("Branch", "fail",
                         f"on '{branch or 'detached HEAD'}'; create a feature branch first"))
    else:
        out.append(Check("Branch", "pass", f"'{branch}'"))
    ahead = int(git("rev-list", "--count", f"{base}..HEAD").strip())
    if ahead == 0:
        out.append(Check("Commits", "fail", f"no commits ahead of {base}; nothing to submit"))
    else:
        out.append(Check("Commits", "pass", f"{ahead} commit(s) ahead of {base}"))
    if git("status", "--porcelain").strip():
        out.append(Check("Working tree", "warn", "uncommitted changes will not be in the PR"))
    return out


def check_noop(files: list[str], base: str) -> Check:
    if not files:
        return Check("No-op", "fail",
                     f"0 files differ from {base}; no-op-pr-guard rejects empty PRs")
    return Check("No-op", "pass", f"{len(files)} file(s) changed vs {base}")


def check_readiness() -> Check:
    proc = subprocess.run(["bash", str(VERIFY)], cwd=REPO, capture_output=True, text=True)
    if proc.returncode == 0:
        return Check("Readiness", "pass", "verify_pr_readiness.sh passed")
    lines = proc.stdout.splitlines()
    failures = [line.strip() for line in lines if "✗" in line] or lines[-5:]
    return Check("Readiness", "fail",
                 f"verify_pr_readiness.sh exited {proc.returncode}: " + "; ".join(failures))


def _strict_loader(yaml):
    """GitHub rejects duplicate mapping keys; PyYAML silently keeps the last one."""
    class Strict(yaml.SafeLoader):
        pass

    def no_duplicate_keys(loader, node, deep=False):
        out = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=True)
            if key in out:
                raise yaml.constructor.ConstructorError(
                    None, None, f"duplicate key {key!r}", key_node.start_mark)
            out[key] = loader.construct_object(value_node, deep=True)
        return out

    Strict.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, no_duplicate_keys)
    return Strict


def check_workflows(files: list[str]) -> Check:
    paths = [f for f in files
             if f.startswith(".github/workflows/") and f.endswith((".yml", ".yaml"))]
    if not paths:
        return Check("Workflows", "pass", "no workflow files changed")
    try:
        import yaml
    except ImportError:
        return Check("Workflows", "warn", "PyYAML not installed; workflow parse skipped")
    loader = _strict_loader(yaml)
    bad = []
    for rel in paths:
        path = REPO / rel
        if not path.exists():  # deleted in this branch
            continue
        try:
            doc = yaml.load(path.read_text(encoding="utf-8"), Loader=loader)
        except Exception as exc:  # any parse failure is a zero-job run on GitHub
            bad.append(f"{rel}: {str(exc).splitlines()[0]}")
            continue
        # PyYAML reads a bare `on:` key as the boolean True.
        if not isinstance(doc, dict) or (True not in doc and "on" not in doc):
            bad.append(f"{rel}: no `on:` trigger, so it can never fire")
    if bad:
        return Check("Workflows", "fail", "; ".join(bad))
    return Check("Workflows", "pass", f"{len(paths)} changed workflow file(s) parse")


def secret_labels(line: str) -> list[str]:
    return [label for label, pattern in SECRET_PATTERNS.items() if pattern.search(line)]


def check_secrets(base: str) -> Check:
    diff = git("diff", "--unified=0", "--no-color", f"{base}...HEAD")
    hits, current = set(), ""
    for line in diff.splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else line[4:]
            continue
        if not line.startswith("+"):
            continue
        for label in secret_labels(line[1:]):
            hits.add(f"{current}: {label}")
    if hits:
        # Report the location and the kind of match, never the matched value.
        return Check("Secrets", "fail",
                     "possible secret in added lines (value not shown): " + "; ".join(sorted(hits)))
    return Check("Secrets", "pass", "no private keys or known token formats in added lines")


def load_classifier():
    spec = importlib.util.spec_from_file_location("molt_protocol_diff", CLASSIFIER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_molt(files: list[str], classifier) -> tuple[Check, int, list]:
    tier = classifier.classify_molt_tier(files)
    evidence = classifier.tier_evidence(files)
    detail = f"measured {classifier.TIER_NAMES[tier]}"
    return Check("Molt tier", "info", detail), tier, evidence


def suggest_zone(tier: int, files: list[str]) -> tuple[str, str]:
    """A suggestion for the author to confirm. Ticking the box stays a human act."""
    if any(Z3_PATTERN.search(f) for f in files):
        return "Z3", "touches a path that looks credential-bearing or deploy-related"
    if any(Path(f).name in Z2_FILES for f in files) or tier >= 1:
        return "Z2", f"measured Tier {tier}, or a governance file changed; ratification needed"
    return "Z1", "no constants, gates, governance files, or credential-bearing paths touched"


# ------------------------------------------------------------- body handling

def build_draft(template: str, tier: int, evidence: list, zone: tuple[str, str],
                files: list[str], checks: list[Check]) -> str:
    """Fill what is mechanical and leave the rest for the author.

    The molt placeholder stays in place. A comment beside it shows the measured
    tier, so the author writes their own claim and can see the gap.
    """
    note = (f"<!-- pre_submit measured Tier {tier} for this diff. "
            f"Write your own claim above; the measurement is for reference. -->")
    body = MOLT_LINE.sub(lambda m: m.group(0) + "\n" + note, template)

    report = [
        "", "<details>", "<summary>Pre-submission report</summary>", "",
        f"- Files changed: {len(files)}",
        f"- Measured molt tier: {tier} — {TIER_LABEL[tier]}",
        f"- Suggested zone: {zone[0]} — {zone[1]} (tick it yourself)",
        "- Checks:",
    ]
    report += [f"  - {MARK[c.status]} {c.name}: {c.detail.splitlines()[0]}" for c in checks]
    if evidence:
        report.append("- Tier evidence:")
        report += [f"  - `{row['path']}` → Tier {row['tier']} ({', '.join(row['matched'])})"
                   for row in evidence]
    report += [
        "- Still open for the author: `smag_p`, `molt_tier_claimed`, the zone box, "
        "and the checklist.",
        "", "</details>", "",
    ]
    return body.rstrip() + "\n" + "\n".join(report)


TIER_LABEL = {
    0: "no constants or gates touched",
    1: "constants touched; needs molt_id, prediction and window",
    2: "gates touched; needs registry entry and ADV run",
}


def lint_body(path: Path, tier: int) -> list[Check]:
    body = path.read_text(encoding="utf-8")
    out = []
    claim = claimed_tier(body)
    if claim is None:
        out.append(Check("Body: molt claim", "warn",
                         "molt_tier_claimed is not filled in; CI will record no claim"))
    elif claim != tier:
        out.append(Check("Body: molt claim", "info",
                         f"claimed Tier {claim}, measured Tier {tier}; CI records the gap "
                         "as audit data, not a block"))
    else:
        out.append(Check("Body: molt claim", "pass", f"claimed Tier {claim} matches measurement"))
    if smag_prediction(body) is None:
        out.append(Check("Body: smag_p", "warn",
                         "smag_p is not filled in; an omitted prediction is VOID, not scored"))
    else:
        out.append(Check("Body: smag_p", "pass", f"smag_p {smag_prediction(body)}"))
    if zone_ticked(body):
        out.append(Check("Body: zone", "pass", "a zone box is ticked"))
    else:
        out.append(Check("Body: zone", "warn", "no zone box ticked"))
    unchecked = len(re.findall(r"- \[ \]", strip_comments(body)))
    if unchecked:
        out.append(Check("Body: checklist", "info", f"{unchecked} item(s) still unchecked"))
    return out


# ------------------------------------------------------------------- output

def print_report(checks: list[Check]) -> None:
    print("pre-submission report")
    for c in checks:
        print(f"  {MARK[c.status]} {c.name}: {c.detail}")
    blocking = sum(c.status == "fail" for c in checks)
    advisory = sum(c.status == "warn" for c in checks)
    print()
    if blocking:
        print(f"✗ {blocking} blocking issue(s); fix them and re-run")
    elif advisory:
        print(f"✓ ready to submit ({advisory} advisory note(s))")
    else:
        print("✓ ready to submit")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", help="base ref to compare against (default: origin/main, then main)")
    parser.add_argument("--body-out", type=Path, help="write a PR body draft to this path")
    parser.add_argument("--body", type=Path, help="lint a filled-in PR body before submitting")
    args = parser.parse_args(argv)

    if not TEMPLATE.exists():
        print(f"pre_submit: missing PR template at {TEMPLATE}", file=sys.stderr)
        return 2
    try:
        base = args.base or resolve_base()
        checks = check_branch(base)
        files = changed_files(base)
        checks.append(check_noop(files, base))
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"pre_submit: environment error: {exc}", file=sys.stderr)
        return 2

    checks.append(check_readiness())
    checks.append(check_workflows(files))
    checks.append(check_secrets(base))
    molt_check, tier, evidence = check_molt(files, load_classifier())
    checks.append(molt_check)

    if args.body_out:
        draft = build_draft(TEMPLATE.read_text(encoding="utf-8"), tier, evidence,
                            suggest_zone(tier, files), files, checks)
        args.body_out.write_text(draft, encoding="utf-8")
        checks.append(Check("Draft", "info", f"PR body written to {args.body_out}"))
    if args.body:
        checks.extend(lint_body(args.body, tier))

    print_report(checks)
    return 1 if any(c.status == "fail" for c in checks) else 0


if __name__ == "__main__":
    sys.exit(main())
