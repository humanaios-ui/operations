from __future__ import annotations

import argparse
import json
from pathlib import Path

from .dpp_asset_binding import bind_ready_assets_to_dpp_policy
from .hackerone_policy_screen import screen_program_policies
from .hackerone_portfolio import scan_portfolio
from .investigation_queue import build_ranked_queue
from .miner import enrich
from .planning import load_resource_plan, miner_requirements_from_plan, resolve_resource_plan
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

    h1_scope = sub.add_parser(
        "hackerone-scope",
        help="Fetch HackerOne program policy, structured scopes, and scope exclusions only",
    )
    h1_scope.add_argument("--handle", required=True)

    h1_policy_screen = sub.add_parser(
        "hackerone-policy-screen",
        help="Screen account-visible HackerOne program policy metadata for explicit passive/Data Protection language",
    )
    h1_policy_screen.add_argument("--page-size", type=int, default=100)
    h1_policy_screen.add_argument("--max-programs", type=int)
    h1_policy_screen.add_argument("--out", required=True, help="Local JSON evidence packet destination")

    h1_policy_hydrate = sub.add_parser(
        "hackerone-policy-hydrate",
        help="Hydrate structured scopes only for one matched program from a policy-screen packet",
    )
    h1_policy_hydrate.add_argument("--policy-screen", required=True)
    h1_policy_hydrate.add_argument("--candidate-index", type=int, default=1)
    h1_policy_hydrate.add_argument("--machine-graph")
    h1_policy_hydrate.add_argument("--page-size", type=int, default=100)
    h1_policy_hydrate.add_argument("--out", required=True)

    h1_dpp_bind = sub.add_parser(
        "hackerone-dpp-bind",
        help="Bind READY structured-scope assets to the Data Protection Program asset-tier list",
    )
    h1_dpp_bind.add_argument("--portfolio", required=True)
    h1_dpp_bind.add_argument("--out", required=True)

    h1_portfolio = sub.add_parser(
        "hackerone-portfolio",
        help="Build a metadata-only HackerOne portfolio and ranked review queue",
    )
    h1_portfolio.add_argument("--handle", action="append", default=[])
    h1_portfolio.add_argument("--page-size", type=int, default=100)
    h1_portfolio.add_argument("--max-programs", type=int)
    h1_portfolio.add_argument(
        "--machine-graph",
        help="Path to a HumanAIOS machine-substrate JSON snapshot; omitted means capability UNKNOWN",
    )
    h1_portfolio.add_argument("--out", help="Optional JSON output path")
    h1_portfolio.add_argument("--exclude-blocked", action="store_true")

    h1_adjudicate = sub.add_parser(
        "hackerone-adjudicate",
        help="Refresh policy/scope evidence for one ranked candidate and run the fail-closed authorization gate",
    )
    h1_adjudicate.add_argument("--portfolio", required=True, help="Path to a ranked HackerOne portfolio JSON")
    h1_adjudicate.add_argument("--rank", type=int, default=1, help="1-based rank among READY_FOR_POLICY_AND_METHOD_REVIEW entries")
    h1_adjudicate.add_argument(
        "--mode",
        choices=[mode.value for mode in TestingMode],
        default=TestingMode.PASSIVE_RECON.value,
    )
    h1_adjudicate.add_argument(
        "--method-allowed",
        choices=["unknown", "yes", "no"],
        default="unknown",
        help="Explicit reviewed-policy result; unknown fails closed",
    )
    h1_adjudicate.add_argument("--finding-category")
    h1_adjudicate.add_argument("--human-authorization-ref")
    h1_adjudicate.add_argument("--page-size", type=int, default=100)
    h1_adjudicate.add_argument("--out", required=True, help="Local JSON evidence packet destination")

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

    if args.command == "hackerone-scope":
        graph = fetch_scope_graph(hackerone.HackerOneClient(), args.handle)
        print(json.dumps(graph.to_dict(), indent=2, ensure_ascii=False))
        return

    if args.command == "hackerone-policy-screen":
        result = screen_program_policies(
            hackerone.HackerOneClient(),
            page_size=args.page_size,
            max_programs=args.max_programs,
        )
        payload = result.to_dict()
        out_path = Path(args.out).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        summary = payload["summary"]
        print(f"wrote HackerOne policy screen to {out_path}")
        print(f"programs_observed={summary['programs_observed']}")
        print(f"explicit_dpp_passive_matches={summary['explicit_dpp_passive_matches']}")
        print(f"other_passive_policy_signals={summary['other_passive_policy_signals']}")
        print("execution_capability=NONE")
        return

    if args.command == "hackerone-policy-hydrate":
        screen_path = Path(args.policy_screen).expanduser()
        screen_payload = json.loads(screen_path.read_text(encoding="utf-8"))
        matches = list(screen_payload.get("matches") or [])
        selected = [
            item for item in matches
            if int(item.get("candidate_index") or 0) == args.candidate_index
        ]
        if len(selected) != 1:
            raise ValueError(
                f"candidate index {args.candidate_index} is not uniquely present in policy screen"
            )
        handle = str(selected[0].get("program_handle") or "").strip()
        if not handle:
            raise ValueError("selected policy match is missing program_handle")

        client = hackerone.HackerOneClient()
        portfolio = scan_portfolio(
            client,
            handles=[handle],
            page_size=args.page_size,
        )
        if args.machine_graph:
            machine_path = Path(args.machine_graph).expanduser()
            machine_graph = json.loads(machine_path.read_text(encoding="utf-8"))
            capability_profile = profile_from_machine_graph(
                machine_graph,
                source=str(machine_path),
            )
        else:
            capability_profile = unknown_capability_profile()

        queue = build_ranked_queue(portfolio, capability_profile)
        payload = {
            "policy_match": {
                "candidate_index": args.candidate_index,
                "classification": selected[0].get("classification"),
                "matched_phrases": selected[0].get("matched_phrases") or [],
            },
            "portfolio": portfolio.to_dict(),
            "capability_profile": capability_profile.to_dict(),
            "ranked_queue": queue.to_dict(),
        }
        out_path = Path(args.out).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        summary = payload["ranked_queue"]["summary"]
        print(f"wrote targeted HackerOne policy-match hydration to {out_path}")
        print(f"programs_hydrated={len(payload['portfolio']['programs'])}")
        print(f"queue_entries={summary['entry_count']}")
        print(f"review_states={json.dumps(summary['review_state_counts'], sort_keys=True)}")
        print("authority_effect=NONE")
        print("execution_capability=NONE")
        return

    if args.command == "hackerone-dpp-bind":
        payload_path = Path(args.portfolio).expanduser()
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        result = bind_ready_assets_to_dpp_policy(payload)
        rendered = result.to_dict()
        out_path = Path(args.out).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(rendered, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        summary = rendered["summary"]
        print(f"wrote DPP asset binding packet to {out_path}")
        print(f"ready_entries={summary['ready_entries']}")
        print(f"dpp_policy_present={summary['dpp_policy_present']}")
        print(f"asset_tiers_heading_present={summary['asset_tiers_heading_present']}")
        print(f"scope_exclusions_heading_present={summary['scope_exclusions_heading_present']}")
        print(f"asset_tier_section_length={summary['asset_tier_section_length']}")
        print(f"extraction_state={summary['extraction_state']}")
        print(f"policy_asset_pattern_count={summary['policy_asset_pattern_count']}")
        print(f"dpp_asset_bound_entries={summary['dpp_asset_bound_entries']}")
        print(f"candidate_ready_ranks={summary['candidate_ready_ranks']}")
        print("authority_effect=NONE")
        print("execution_capability=NONE")
        return

    if args.command == "hackerone-adjudicate":
        payload_path = Path(args.portfolio).expanduser()
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        method_allowed = {"unknown": None, "yes": True, "no": False}[args.method_allowed]
        result = adjudicate_ranked_candidate(
            hackerone.HackerOneClient(),
            payload,
            rank=args.rank,
            mode=TestingMode(args.mode),
            method_allowed=method_allowed,
            requested_finding_category=args.finding_category,
            human_authorization_ref=args.human_authorization_ref,
            page_size=args.page_size,
        )
        out_path = Path(args.out).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        decision = result["authorization_decision"]
        binding = result["scope_binding"]
        print(f"wrote HackerOne adjudication packet to {out_path}")
        print(f"scope_binding_valid={binding['valid']}")
        print(f"authorization_state={decision['state']}")
        print("execution_capability=NONE")
        return

    if args.command == "hackerone-portfolio":
        client = hackerone.HackerOneClient()
        portfolio = scan_portfolio(
            client,
            handles=args.handle or None,
            page_size=args.page_size,
            max_programs=args.max_programs,
        )
        if args.machine_graph:
            machine_path = Path(args.machine_graph).expanduser()
            machine_graph = json.loads(machine_path.read_text(encoding="utf-8"))
            capability_profile = profile_from_machine_graph(
                machine_graph,
                source=str(machine_path),
            )
        else:
            capability_profile = unknown_capability_profile()
        queue = build_ranked_queue(
            portfolio,
            capability_profile,
            include_blocked=not args.exclude_blocked,
        )
        payload = {
            "portfolio": portfolio.to_dict(),
            "capability_profile": capability_profile.to_dict(),
            "ranked_queue": queue.to_dict(),
        }
        rendered = json.dumps(payload, indent=2, ensure_ascii=False)
        if args.out:
            out_path = Path(args.out).expanduser()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered + "\n", encoding="utf-8")
            print(f"wrote HackerOne portfolio queue to {out_path}")
        else:
            print(rendered)
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
