from __future__ import annotations

import argparse
import json
from pathlib import Path

from .claim_state_machine import reconcile_claim_event_ledger
from .miner import enrich
from .mines import load_mines, receipts_to_jsonl, resolve_mines
from .opportunity_claim import claims_from_propositions, write_claims_jsonl
from .proposition import propositions_from_candidates, write_propositions_jsonl
from .planning import load_resource_plan, miner_requirements_from_plan, resolve_resource_plan
from .reconcile import reconcile_snapshot
from .policy_adjudication import adjudicate_ranked_candidate
from .security_authorization import TestingMode
from .security_capability import profile_from_machine_graph, unknown_capability_profile
from .security_scope import fetch_scope_graph
from .store import write_jsonl
from .sources import devto, funding_pipeline, github, hackerone, rss

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HumanAIOS Resource Miner")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Discover, normalize, map, and route resource candidates")
    scan.add_argument("--source", action="append", choices=["funding", "devto", "github", "hackerone", "rss"], default=[])
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
    scan.add_argument("--hackerone-handle", action="append", default=[])
    scan.add_argument("--hackerone-page-size", type=int, default=100)
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
    resolve.add_argument("--events-ledger", default=str(DEFAULT_CLAIM_EVENTS))
    resolve.add_argument("--dry-run", action="store_true")

    profile = sub.add_parser(
        "portfolio-check",
        help="Read-only controlled profile resource drift check (local, approval-gated)",
    )
    profile.add_argument("--personal-projection", required=True)
    profile.add_argument("--business-anchor", required=True)
    profile.add_argument("--consumer-snapshot", required=True)
    profile.add_argument("--prior-revisions")

    local_profile = sub.add_parser(
        "connect-private-profile",
        help="On-demand owner-approved read from three local git checkouts",
    )
    local_profile.add_argument("--private-checkout", required=True)
    local_profile.add_argument("--operations-checkout", required=True)
    local_profile.add_argument("--consumer-checkout", required=True)
    local_profile.add_argument("--owner-approved", action="store_true")
    local_profile.add_argument("--prior-revisions")

    app = sub.add_parser(
        "render-private-application",
        help="Build a review-only DOCX using the private master and local style template",
    )
    app.add_argument("--private-checkout", required=True)
    app.add_argument("--template", required=True)
    app.add_argument("--output", required=True)
    app.add_argument("--target", default="")
    app.add_argument("--max-projects", type=int, default=5)
    app.add_argument("--owner-approved", action="store_true")
    app.add_argument("--operations-checkout")

    presence = sub.add_parser(
        "profile-presence",
        help="Owner-approved, read-only public profile inventory and review",
    )
    presence.add_argument("--private-checkout", required=True)
    presence.add_argument("--candidate-observations", help="Local Resource Miner public-result snapshot JSON")
    presence.add_argument("--probe-public", action="store_true",
                          help="Contact only fixed public GitHub/ORCID read APIs")
    presence.add_argument("--owner-approved", action="store_true")
    presence.add_argument("--github-alias", help="Explicit owner-selected public alias to search GitHub once")

    plan = sub.add_parser("plan", help="Validate and resolve a Resource Plan graph")
    plan.add_argument("--file", required=True)
    plan.add_argument(
        "--miner-requirements",
        action="store_true",
        help="Emit only externally mineable Resource Requirement Objects",
    )

    reconcile = sub.add_parser("reconcile", help="Reconcile durable resource state against receipts")
    reconcile.add_argument("--snapshot", default=str(ROOT / "data" / "resources.snapshot.jsonl"))
    reconcile.add_argument("--receipts", default=str(ROOT / "data" / "resource_state.receipts.jsonl"))
    reconcile.add_argument("--out", default=None, help="Defaults to rewriting --snapshot in place")
    reconcile.add_argument("--audit-out", default=None)
    return parser


def _plan_requirements(paths: list[str]) -> list[dict]:
    requirements: list[dict] = []
    for path in paths:
        requirements.extend(miner_requirements_from_plan(load_resource_plan(path)))
    return requirements


def _safe_reason(exc: BaseException) -> str:
    """Short, fixed-vocabulary reason; never echo parser or file contents."""
    if isinstance(exc, (ValueError, RuntimeError, PermissionError, FileExistsError)):
        return str(exc)[:120]
    return "local file or git access failed"


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "profile-presence":
        from .private_profile_bridge import load_private_master
        from .profile_presence import observe_owner_presence
        if not args.owner_approved:
            raise SystemExit("owner approval required: supply --owner-approved")
        try:
            master, revision = load_private_master(args.private_checkout)
        except (ValueError, RuntimeError, PermissionError, OSError) as exc:
            raise SystemExit(f"profile-presence failed: {_safe_reason(exc)}") from None
        observations = (
            json.loads(Path(args.candidate_observations).read_text(encoding="utf-8"))
            if args.candidate_observations else []
        )
        if args.github_alias:
            from .profile_presence import search_github_alias
            search_result = search_github_alias(args.github_alias, owner_approved=True)
            observations = observations + search_result["observations"]
        else:
            search_result = {"state": "NOT_REQUESTED", "observations": []}
        report = observe_owner_presence(
            master, owner_approved=True, observations=observations,
            probe_public=args.probe_public,
        )
        report["search_state"] = search_result["state"]
        report["private_source_revision"] = revision
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    if args.command == "render-private-application":
        from .application_portfolio import build_application
        if not args.owner_approved:
            raise SystemExit("owner approval required: supply --owner-approved")
        if not (1 <= args.max_projects <= 12):
            raise SystemExit("--max-projects must be between 1 and 12")
        protected = (
            (Path(args.operations_checkout).expanduser().resolve(),)
            if args.operations_checkout else ()
        )
        try:
            receipt = build_application(
                args.private_checkout, args.template, args.output,
                target=args.target, max_projects=args.max_projects,
                forbidden_checkouts=protected,
            )
        except (ValueError, RuntimeError, PermissionError, OSError) as exc:
            raise SystemExit(f"render-private-application failed: {_safe_reason(exc)}") from None
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return

    if args.command == "connect-private-profile":
        from .private_profile_bridge import read_local_portfolio
        if not args.owner_approved:
            raise SystemExit("owner approval required: supply --owner-approved")
        prior = (
            json.loads(Path(args.prior_revisions).read_text(encoding="utf-8"))
            if args.prior_revisions else None
        )
        try:
            report = read_local_portfolio(
                args.private_checkout,
                args.operations_checkout,
                args.consumer_checkout,
                owner_approved=True,
                prior=prior,
            )
        except (ValueError, RuntimeError, PermissionError, OSError) as exc:
            raise SystemExit(f"connect-private-profile failed: {_safe_reason(exc)}") from None
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    if args.command == "portfolio-check":
        from .portfolio_maintainer import observe_portfolio

        def read_local(path: str) -> dict:
            return json.loads(Path(path).read_text(encoding="utf-8"))

        report = observe_portfolio(
            read_local(args.personal_projection),
            read_local(args.business_anchor),
            read_local(args.consumer_snapshot),
            prior=read_local(args.prior_revisions) if args.prior_revisions else None,
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    if args.command == "reconcile":
        audit = reconcile_snapshot(args.snapshot, args.receipts, args.out, args.audit_out)
        print(json.dumps(audit, indent=2, ensure_ascii=False))
        return

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
        claims = claims_from_propositions(resources, propositions)
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "mines": [mine.to_dict() for mine in mines],
                        "opportunities": [row.to_dict() for row in resources],
                        "propositions": [row.to_dict() for row in propositions],
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
            write_claims_jsonl(args.claims_out, claims)
            appended_events = reconcile_claim_event_ledger(
                args.events_ledger,
                claims,
                actor_id="resource-miner",
                method="scheduled_mine_resolution",
            )
            print(
                f"resolved {len(mines)} mines -> {len(resources)} opportunities, "
                f"{len(propositions)} propositions, and {len(claims)} claims; "
                f"appended {len(appended_events)} claim events; wrote {args.out}, "
                f"{args.receipts_out}, {args.propositions_out}, {args.claims_out}, "
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
    if "hackerone" in sources:
        discovered.extend(
            hackerone.discover(
                args.hackerone_handle or None,
                page_size=args.hackerone_page_size,
            )
        )
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
