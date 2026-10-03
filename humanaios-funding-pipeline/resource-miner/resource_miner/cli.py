from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adjudication import (
    adjudicate_resolution_sets,
    write_adjudications_jsonl,
    write_verification_frontier_jsonl,
)
from .claim_state_machine import reconcile_claim_event_ledger
from .miner import enrich
from .mines import load_mines, receipts_to_jsonl, resolve_mines
from .opportunity_claim import claims_from_propositions, write_claims_jsonl
from .proposition import propositions_from_candidates, write_propositions_jsonl
from .reconciliation import reconcile_propositions, write_resolution_sets_jsonl
from .source_standing import load_source_standing
from .work_queue import (
    compile_verification_work_queue,
    write_verification_work_queue_jsonl,
)
from .verification_routing import (
    compile_verification_routes,
    write_verification_routes_jsonl,
)
from .planning import load_resource_plan, miner_requirements_from_plan, resolve_resource_plan
from .store import write_jsonl
from .sources import devto, funding_pipeline, github, rss

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NEEDS = ROOT / "data" / "needs.seed.json"
DEFAULT_REQUIREMENTS = ROOT / "data" / "resource_requirements.seed.json"
DEFAULT_OUT = ROOT / "data" / "resources.jsonl"
DEFAULT_FUNDING = ROOT.parent / "data" / "sources.json"
DEFAULT_MINES = ROOT / "data" / "mines.seed.json"
DEFAULT_OPPORTUNITIES = ROOT / "data" / "opportunities.jsonl"
DEFAULT_MINE_RECEIPTS = ROOT / "data" / "mine-resolution.jsonl"
DEFAULT_OPPORTUNITY_CLAIMS = ROOT / "data" / "opportunity-claims.jsonl"
DEFAULT_CLAIM_EVENTS = ROOT / "data" / "opportunity-claim-events.jsonl"
DEFAULT_PROPOSITIONS = ROOT / "data" / "propositions.jsonl"
DEFAULT_PROPOSITION_RESOLUTIONS = ROOT / "data" / "proposition-resolutions.jsonl"
DEFAULT_SOURCE_STANDING = ROOT / "data" / "source-standing.seed.json"
DEFAULT_ADJUDICATIONS = ROOT / "data" / "proposition-adjudications.jsonl"
DEFAULT_VERIFICATION_FRONTIER = ROOT / "data" / "verification-frontier.jsonl"
DEFAULT_VERIFICATION_WORK_QUEUE = ROOT / "data" / "verification-work-queue.jsonl"
DEFAULT_VERIFICATION_ROUTES = ROOT / "data" / "verification-routes.jsonl"


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

    resolve = sub.add_parser(
        "resolve-mines",
        help="Re-observe persistent Mines and emit discrete Resource Opportunity tokens",
    )
    resolve.add_argument("--mines", default=str(DEFAULT_MINES))
    resolve.add_argument("--mine-id", action="append", default=[])
    resolve.add_argument("--needs", default=str(DEFAULT_NEEDS))
    resolve.add_argument("--requirements", default=str(DEFAULT_REQUIREMENTS))
    resolve.add_argument("--out", default=str(DEFAULT_OPPORTUNITIES))
    resolve.add_argument("--receipts-out", default=str(DEFAULT_MINE_RECEIPTS))
    resolve.add_argument("--claims-out", default=str(DEFAULT_OPPORTUNITY_CLAIMS))
    resolve.add_argument("--propositions-out", default=str(DEFAULT_PROPOSITIONS))
    resolve.add_argument("--resolutions-out", default=str(DEFAULT_PROPOSITION_RESOLUTIONS))
    resolve.add_argument("--source-standing", default=str(DEFAULT_SOURCE_STANDING))
    resolve.add_argument("--adjudications-out", default=str(DEFAULT_ADJUDICATIONS))
    resolve.add_argument("--verification-frontier-out", default=str(DEFAULT_VERIFICATION_FRONTIER))
    resolve.add_argument("--verification-work-queue-out", default=str(DEFAULT_VERIFICATION_WORK_QUEUE))
    resolve.add_argument("--verification-routes-out", default=str(DEFAULT_VERIFICATION_ROUTES))
    resolve.add_argument("--events-ledger", default=str(DEFAULT_CLAIM_EVENTS))
    resolve.add_argument("--dry-run", action="store_true")

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

    if args.command == "resolve-mines":
        mines = load_mines(args.mines)
        if args.mine_id:
            wanted = set(args.mine_id)
            mines = [mine for mine in mines if mine.mine_id in wanted]
        discovered, receipts = resolve_mines(mines)
        resources = enrich(discovered, args.needs, args.requirements)
        propositions = propositions_from_candidates(resources)
        resolutions = reconcile_propositions(propositions)
        standing_profiles = load_source_standing(args.source_standing)
        adjudications = adjudicate_resolution_sets(
            resolutions,
            propositions,
            standing_profiles,
        )
        verification_work_queue = compile_verification_work_queue(adjudications)
        verification_routes = compile_verification_routes(
            verification_work_queue,
            mines,
        )
        claims = claims_from_propositions(resources, propositions)
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "mines": [mine.to_dict() for mine in mines],
                        "opportunities": [row.to_dict() for row in resources],
                        "propositions": [row.to_dict() for row in propositions],
                        "resolutions": [row.to_dict() for row in resolutions],
                        "adjudications": [row.to_dict() for row in adjudications],
                        "verification_frontier": [
                            item.to_dict()
                            for row in adjudications
                            for item in row.verification_frontier
                        ],
                        "verification_work_queue": [
                            row.to_dict() for row in verification_work_queue
                        ],
                        "verification_routes": [
                            row.to_dict() for row in verification_routes
                        ],
                        "claims": [claim.to_dict() for claim in claims],
                        "receipts": [receipt.to_dict() for receipt in receipts],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            write_jsonl(args.out, resources)
            receipt_path = Path(args.receipts_out)
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(receipts_to_jsonl(receipts), encoding="utf-8")
            write_propositions_jsonl(args.propositions_out, propositions)
            write_resolution_sets_jsonl(args.resolutions_out, resolutions)
            write_adjudications_jsonl(args.adjudications_out, adjudications)
            write_verification_frontier_jsonl(
                args.verification_frontier_out,
                adjudications,
            )
            write_verification_work_queue_jsonl(
                args.verification_work_queue_out,
                verification_work_queue,
            )
            write_verification_routes_jsonl(
                args.verification_routes_out,
                verification_routes,
            )
            write_claims_jsonl(args.claims_out, claims)
            appended_events = reconcile_claim_event_ledger(
                args.events_ledger,
                claims,
                actor_id="resource-miner",
                method="scheduled_mine_resolution",
            )
            print(
                f"resolved {len(mines)} mines -> {len(resources)} opportunities, "
                f"{len(propositions)} propositions, {len(resolutions)} resolution sets, "
                f"{len(adjudications)} adjudications, and {len(claims)} claims; "
                f"appended {len(appended_events)} claim events; wrote {args.out}, "
                f"{args.receipts_out}, {args.propositions_out}, {args.resolutions_out}, "
                f"{args.adjudications_out}, {args.verification_frontier_out}, "
                f"{args.verification_work_queue_out}, {args.verification_routes_out}, "
                f"{args.claims_out}, "
                f"and reconciled {args.events_ledger}"
            )
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
