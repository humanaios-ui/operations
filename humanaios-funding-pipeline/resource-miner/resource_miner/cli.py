from __future__ import annotations

import argparse
import json
from pathlib import Path

from .miner import enrich
from .planning import load_resource_plan, miner_requirements_from_plan, resolve_resource_plan
from .store import write_jsonl
from .sources import devto, funding_pipeline, github, rss

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NEEDS = ROOT / "data" / "needs.seed.json"
DEFAULT_REQUIREMENTS = ROOT / "data" / "resource_requirements.seed.json"
DEFAULT_OUT = ROOT / "data" / "resources.jsonl"
DEFAULT_FUNDING = ROOT.parent / "data" / "sources.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HumanAIOS Resource Miner")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Discover, normalize, map, and route resource candidates")
    scan.add_argument("--source", action="append", choices=["funding", "devto", "github", "rss"], default=[])
    scan.add_argument("--needs", default=str(DEFAULT_NEEDS))
    scan.add_argument("--requirements", default=str(DEFAULT_REQUIREMENTS))
    scan.add_argument(
        "--resource-plan",
        action="append",
        default=[],
        help="Add externally mineable deficits derived from a local Resource Plan JSON file",
    )
    scan.add_argument("--out", default=str(DEFAULT_OUT))
    scan.add_argument("--funding-data", default=str(DEFAULT_FUNDING))
    scan.add_argument("--dev-tag", action="append", default=[])
    scan.add_argument("--github-query", action="append", default=[])
    scan.add_argument("--rss", action="append", default=[])
    scan.add_argument("--dry-run", action="store_true")

    plan = sub.add_parser("plan", help="Validate and resolve a Resource Plan graph")
    plan.add_argument("--file", required=True)
    plan.add_argument(
        "--miner-requirements",
        action="store_true",
        help="Emit only externally mineable Resource Requirement Objects",
    )
    return parser


def _plan_requirements(paths: list[str]) -> list[dict]:
    requirements: list[dict] = []
    for path in paths:
        requirements.extend(miner_requirements_from_plan(load_resource_plan(path)))
    return requirements


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "plan":
        plan = load_resource_plan(args.file)
        data = miner_requirements_from_plan(plan) if args.miner_requirements else resolve_resource_plan(plan)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    sources = args.source or ["funding", "devto"]
    discovered = []
    if "funding" in sources:
        discovered.extend(funding_pipeline.discover(args.funding_data))
    if "devto" in sources:
        discovered.extend(devto.discover(args.dev_tag or ["devchallenge"]))
    if "github" in sources:
        queries = args.github_query or ["is:issue is:open label:bounty", 'is:issue is:open "cash prize"']
        discovered.extend(github.discover(queries))
    if "rss" in sources:
        discovered.extend(rss.discover(args.rss))

    extra_requirements = _plan_requirements(args.resource_plan)
    resources = enrich(discovered, args.needs, args.requirements, extra_requirements)
    if args.dry_run:
        print(json.dumps([x.to_dict() for x in resources], indent=2, ensure_ascii=False))
    else:
        write_jsonl(args.out, resources)
        print(f"wrote {len(resources)} resources to {args.out}")


if __name__ == "__main__":
    main()
