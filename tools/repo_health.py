#!/usr/bin/env python3
"""
repo_health.py — a basic, offline, deterministic self-diagnostic for a HumanAIOS repo.

Philosophy (see SYSTEM_HEALTH.md): the repository should be able to check its own
vitals with no network and no dependencies — the same way an organism's immune system
runs constant, local surveillance. This is the "learn from the basic level" layer; the
richer external stack (OpenSSF Scorecard, spbuilds/repohealth, actionlint, zizmor,
gitleaks) is the growth path documented in SYSTEM_HEALTH.md.

Checks group into five systems and produce a 0-100 vitality score. Stdlib only.

    python3 tools/repo_health.py            # human-readable report
    python3 tools/repo_health.py --markdown # markdown table (for SYSTEM_HEALTH.md)
    python3 tools/repo_health.py --json      # machine-readable
    python3 tools/repo_health.py --strict    # exit 1 if score < threshold (CI gate)
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THRESHOLD = 60  # --strict fails below this


def has(*names: str) -> bool:
    """True if any of the given paths exists at repo root."""
    return any((ROOT / n).exists() for n in names)


def immune_entries() -> int:
    """Count registered immune-memory entries (F/H/IC) in REGISTERED.md."""
    reg = ROOT / "REGISTERED.md"
    if not reg.exists():
        return -1
    text = reg.read_text(errors="ignore")
    return len(re.findall(r'(?m)^id:\s*["\']?(?:F-|H-|IC-)', text))


def workflows() -> list[str]:
    wf = ROOT / ".github" / "workflows"
    return sorted(p.name for p in wf.glob("*.yml")) if wf.is_dir() else []


def systems() -> list[dict]:
    """Return the five body systems, each with weighted checks."""
    wfs = workflows()
    ic = immune_entries()
    return [
        {"organ": "🧬 Genome & orientation", "checks": [
            ("README", has("README.md")),
            ("START_HERE front door", has("START_HERE.md")),
            ("SEED / identity", has("SEED.md", "docs/SEED.md")),
        ]},
        {"organ": "⚖️ Governance", "checks": [
            ("GOVERNANCE (Zones)", has("GOVERNANCE.md")),
            ("SESSION_RITUALS", has("SESSION_RITUALS.md")),
            ("CODEOWNERS", has("CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS")),
        ]},
        {"organ": "🛡️ Immune memory", "checks": [
            ("REGISTERED.md present", ic >= 0),
            (f"immune entries logged ({ic if ic>=0 else 0})", ic > 0),
            ("doc-control registry", has("document-registry.yaml")),
            ("doc-control validator", has(".doc-control/validate.py")),
        ]},
        {"organ": "⚡ Reflexes (CI)", "checks": [
            (f"workflows present ({len(wfs)})", len(wfs) > 0),
            ("doc-control gate active", "document-control.yml" in wfs),
        ]},
        {"organ": "🫀 Community & safety files", "checks": [
            ("LICENSE", has("LICENSE", "LICENSE.md", "LICENSE.txt")),
            ("SECURITY policy", has("SECURITY.md", ".github/SECURITY.md")),
            ("CONTRIBUTING", has("CONTRIBUTING.md", ".github/CONTRIBUTING.md")),
            (".gitignore", has(".gitignore")),
        ]},
    ]


def score(sys_list: list[dict]) -> tuple[int, list[dict]]:
    rows, got, tot = [], 0, 0
    for s in sys_list:
        passed = sum(1 for _, ok in s["checks"] if ok)
        n = len(s["checks"])
        got += passed
        tot += n
        rows.append({"organ": s["organ"], "passed": passed, "total": n,
                     "pct": round(100 * passed / n),
                     "detail": [{"check": c, "ok": ok} for c, ok in s["checks"]]})
    return (round(100 * got / tot) if tot else 0), rows


def verdict(pct: int) -> str:
    return ("🟢 healthy" if pct >= 80 else
            "🟡 functioning, gaps to close" if pct >= 60 else
            "🟠 needs attention" if pct >= 40 else "🔴 critical")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    total, rows = score(systems())

    if args.json:
        print(json.dumps({"repo": ROOT.name, "score": total,
                          "verdict": verdict(total), "systems": rows}, indent=2))
    elif args.markdown:
        print(f"**{ROOT.name}** — vitality **{total}/100** · {verdict(total)}\n")
        print("| System | Score | Checks |")
        print("|---|---|---|")
        for r in rows:
            det = " · ".join(("✅" if c["ok"] else "⬜") + c["check"] for c in r["detail"])
            print(f"| {r['organ']} | {r['pct']}% | {det} |")
    else:
        print(f"\n  {ROOT.name} — repository vitality: {total}/100  {verdict(total)}\n")
        for r in rows:
            print(f"  {r['organ']}  [{r['passed']}/{r['total']}]")
            for c in r["detail"]:
                print(f"      {'✅' if c['ok'] else '⬜'} {c['check']}")
        print()

    if args.strict and total < THRESHOLD:
        print(f"FAIL: vitality {total} < threshold {THRESHOLD}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
