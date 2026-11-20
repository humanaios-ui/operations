#!/usr/bin/env python3
"""
break_even_table.py — required-return sensitivity table for #1174
(fixed-cash autonomous agent trading economics proposal).

The issue's red-team review (finding #1) asked for the annualized return
a fixed one-time allocation A would need, net of subscription/usage cost
C, just to break even. A later follow-up (issue comment 6812392277)
corrected three presentation problems in the first version of this table:

  * The H-dependent "compounded" form (1 + C*H/A)^(12/H) - 1 mixed
    compounding conventions as the horizon changed, so the plausibility
    verdict moved with H even though the monthly hurdle C/A is constant.
    Horizon H belongs to the statistical-power question, not this
    break-even verdict, and is not an input to the grid.
  * C = 0 rows do not correspond to any cohort member and are omitted
    from the default cost grid.
  * A single 15%/yr ceiling is generous. Plausibility is reported
    against 7%, 10%, and 15% per year.

Two horizon-independent conventions are reported side by side:

  required_annual_return_linear              = 12 * C / A
  required_annual_return_monthly_compounded  = (1 + C / A) ** 12 - 1

The first is simple annualization of the monthly cost draw. The second
is the return required if that cost is drawn from capital each month
and the leftover must still compound to a break-even year. The second
is strictly larger when C > 0. Plausibility columns use the linear
convention so they stay consistent with the min-capital inversion
A_min = 12 * C / r.

This tool does not set A, C, or r for a live experiment, and it does
not record any real capital amount. Actual billed tiers remain
UNVERIFIED. It is not financial advice.

Usage:
  python3 break_even_table.py                 # default grid + cohort section
  python3 break_even_table.py --include-cost-200
  python3 break_even_table.py --smoke-test    # self-check, no file writes
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CAPITAL = [25, 100, 250, 500, 1_000, 2_500, 5_000, 10_000]
DEFAULT_COST = [10, 20, 30, 39, 100]  # list-price points; no cohort member is $0
OPTIONAL_COST_200 = 200
DEFAULT_CEILINGS = (0.07, 0.10, 0.15)

# Public US list prices observed 2026-11 (monthly billing, before tax).
# Actual billed tiers are UNVERIFIED.
PRICE_SOURCES = (
    "https://docs.github.com/en/copilot/get-started/plans",
    "https://claude.com/pricing",
    "https://plan-price.com/en/countries/united-states/",
)
TIER_SCENARIOS: dict[str, dict[str, float]] = {
    "Entry": {
        "ChatGPT Plus": 20,
        "Copilot Pro": 10,
        "Claude Pro": 20,
        "SuperGrok": 30,
    },
    "Power": {
        "ChatGPT Pro": 100,
        "Copilot Pro+": 39,
        "Claude Max": 100,
        "SuperGrok Plus": 100,
    },
}


@dataclass(frozen=True)
class Row:
    capital: float
    monthly_cost: float
    required_annual_linear_pct: float
    required_annual_monthly_compounded_pct: float
    plausible_vs_7: bool
    plausible_vs_10: bool
    plausible_vs_15: bool


@dataclass(frozen=True)
class AgentMinCapital:
    name: str
    monthly_cost: float
    r: float
    a_min: float


@dataclass(frozen=True)
class CohortRequirement:
    scenario: str
    r: float
    sum_c: float
    per_agent: tuple[AgentMinCapital, ...]
    b_all_four: float
    b_aggregate: float


def required_annual_linear(capital: float, monthly_cost: float) -> float:
    """12*C/A, as a fraction. Horizon-independent.

    Matches the review's worked example (A=500, C=20 -> 0.48;
    A=500, C=200 -> 4.80).
    """
    if capital <= 0:
        return float("inf")
    return 12.0 * monthly_cost / capital


def required_annual_monthly_compounded(capital: float, monthly_cost: float) -> float:
    """(1 + C/A)^12 - 1, as a fraction.

    Required annual return if the monthly cost is drawn from capital
    each month. Horizon-independent. For A=500, C=20 this is
    (1.04)^12 - 1 ≈ 0.6010.
    """
    if capital <= 0:
        return float("inf")
    return (1.0 + monthly_cost / capital) ** 12.0 - 1.0


def min_capital(monthly_cost: float, r: float) -> float:
    """A_min = 12*C/r. Linear inversion of required_annual_linear.

    Returns +inf when r <= 0.
    """
    if r <= 0:
        return float("inf")
    return 12.0 * monthly_cost / r


def cohort_requirement(scenario: str, costs: dict[str, float], r: float) -> CohortRequirement:
    per_agent = tuple(
        AgentMinCapital(name=name, monthly_cost=cost, r=r, a_min=min_capital(cost, r))
        for name, cost in costs.items()
    )
    sum_c = sum(costs.values())
    return CohortRequirement(
        scenario=scenario,
        r=r,
        sum_c=sum_c,
        per_agent=per_agent,
        b_all_four=4.0 * max(p.a_min for p in per_agent),
        b_aggregate=12.0 * sum_c / r if r > 0 else float("inf"),
    )


def build_cohort_table(ceilings: tuple[float, ...] = DEFAULT_CEILINGS) -> list[CohortRequirement]:
    rows: list[CohortRequirement] = []
    for scenario, costs in TIER_SCENARIOS.items():
        for r in ceilings:
            rows.append(cohort_requirement(scenario, costs, r))
    return rows


def _plausible(required_fraction: float, ceiling: float) -> bool:
    if not math.isfinite(required_fraction):
        return False
    return required_fraction <= ceiling


def build_grid(
    capitals: list[float],
    costs: list[float],
    ceilings: tuple[float, ...] = DEFAULT_CEILINGS,
) -> list[Row]:
    if len(ceilings) != 3:
        raise ValueError("exactly three plausibility ceilings are required")
    c7, c10, c15 = ceilings
    rows: list[Row] = []
    for capital in capitals:
        for cost in costs:
            lin = required_annual_linear(capital, cost)
            comp = required_annual_monthly_compounded(capital, cost)
            rows.append(
                Row(
                    capital=capital,
                    monthly_cost=cost,
                    required_annual_linear_pct=lin * 100.0,
                    required_annual_monthly_compounded_pct=comp * 100.0,
                    plausible_vs_7=_plausible(lin, c7),
                    plausible_vs_10=_plausible(lin, c10),
                    plausible_vs_15=_plausible(lin, c15),
                )
            )
    return rows


def _fmt_money(value: float) -> str:
    if not math.isfinite(value):
        return "inf"
    if abs(value - round(value)) < 1e-9:
        return f"${value:,.0f}"
    return f"${value:,.0f}"


def _fmt_pct(value: float) -> str:
    if not math.isfinite(value):
        return "inf"
    return f"{value:,.1f}"


def render_markdown(rows: list[Row], cohort: list[CohortRequirement]) -> str:
    lines = [
        "# Break-even required-return table — #1174",
        "",
        "Horizon-independent conventions (H is not an input; it belongs to "
        "the statistical-power question, not this verdict):",
        "",
        "- `req %/yr (linear)` = `12·C/A`",
        "- `req %/yr (monthly compounded)` = `(1 + C/A)^12 − 1`",
        "",
        "Plausibility columns compare the **linear** required return to "
        "three ceilings (7%, 10%, 15% per year) so the grid stays consistent "
        "with the min-capital inversion `A_min = 12·C/r`. The monthly-compounded "
        "rate is stricter when C > 0 and is shown for comparison; a cell that "
        "is just inside a linear ceiling may still sit above that ceiling on "
        "the compounded convention.",
        "",
        "A = one-time per-agent capital allocation. C = monthly subscription "
        "+ usage-attributed cost charged against trading. The default C grid "
        "uses public US list-price points observed 2026-11 "
        "($10, $20, $30, $39, $100). C = 0 is omitted (no cohort member costs "
        "$0). $200/mo can be added with `--include-cost-200`. Actual billed "
        "tiers are **UNVERIFIED**. Usage, API, data, fees, and taxes would "
        "raise every number. This table does not record any real capital amount.",
        "",
        "Sources: "
        + "; ".join(PRICE_SOURCES)
        + ".",
        "",
        "| A ($) | C ($/mo) | req %/yr (linear) | req %/yr (monthly compounded) | vs 7% | vs 10% | vs 15% |",
        "|---:|---:|---:|---:|:---:|:---:|:---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r.capital:,.0f} | {r.monthly_cost:,.0f} | "
            f"{_fmt_pct(r.required_annual_linear_pct)} | "
            f"{_fmt_pct(r.required_annual_monthly_compounded_pct)} | "
            f"{'YES' if r.plausible_vs_7 else 'no'} | "
            f"{'YES' if r.plausible_vs_10 else 'no'} | "
            f"{'YES' if r.plausible_vs_15 else 'no'} |"
        )

    def _count(attr: str) -> int:
        return sum(1 for r in rows if getattr(r, attr))

    lines += [
        "",
        f"{_count('plausible_vs_7')}/{len(rows)} grid cells clear 7%/yr (linear); "
        f"{_count('plausible_vs_10')}/{len(rows)} clear 10%/yr; "
        f"{_count('plausible_vs_15')}/{len(rows)} clear 15%/yr. "
        "Read this as: for a given (A, C), if the cell is 'no' under the "
        "ceiling you are willing to treat as plausible, the break-even bar "
        "is above that ceiling and finding #1 (the pay-for-subscription "
        "track cannot distinguish skill from a lottery at that capital) "
        "applies to that cell.",
        "",
        "## Min-capital inversion and cohort floors",
        "",
        "Linear inversion: `A_min = 12·C/r`. With an equal 25% split of a "
        "starting pool B among N=4 agents, every agent passing needs "
        "`B ≥ 4 · max(A_min)` (the most expensive plan sets the bar). "
        "The cohort passing in aggregate (total subscription cost covered "
        "by total capital, ignoring the equal-split constraint) needs "
        "`B ≥ 12 · ΣC / r`.",
        "",
        "Two **UNVERIFIED** tier scenarios, using list prices observed "
        "2026-11:",
        "",
        "- **Entry:** ChatGPT Plus $20, Copilot Pro $10, Claude Pro $20, SuperGrok $30 (ΣC = $80/mo)",
        "- **Power:** ChatGPT Pro $100, Copilot Pro+ $39, Claude Max $100, SuperGrok Plus $100 (ΣC = $339/mo)",
        "",
        "| Scenario | r | A_min per agent | B for all 4 to pass | B for cohort in aggregate |",
        "|---|---:|---|---:|---:|",
    ]
    for req in cohort:
        per = " / ".join(
            f"{p.name} {_fmt_money(p.a_min)}" for p in req.per_agent
        )
        lines.append(
            f"| {req.scenario} | {req.r:.0%} | {per} | "
            f"{_fmt_money(req.b_all_four)} | {_fmt_money(req.b_aggregate)} |"
        )
    lines += [
        "",
        "Compare a private capital snapshot to the **B for all 4 to pass** "
        "column for the verified tiers. Do not post the snapshot itself. "
        "If it is below the 15% entry-tier floor, the pay-for-subscription "
        "track is not a meaningful test. Even above a floor, an agent that "
        "just holds a benchmark would clear the same bar, so any skill test "
        "must be return in excess of the frozen benchmark, not \"covered "
        "its subscription.\"",
    ]
    return "\n".join(lines)


def write_csv(rows: list[Row], cohort: list[CohortRequirement], path: Path) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "section",
                "capital_usd",
                "monthly_cost_usd",
                "required_annual_pct_linear",
                "required_annual_pct_monthly_compounded",
                "plausible_vs_7",
                "plausible_vs_10",
                "plausible_vs_15",
                "scenario",
                "rate",
                "agent",
                "a_min_usd",
                "b_all_four_usd",
                "b_aggregate_usd",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    "grid",
                    r.capital,
                    r.monthly_cost,
                    f"{r.required_annual_linear_pct:.4f}",
                    f"{r.required_annual_monthly_compounded_pct:.4f}",
                    r.plausible_vs_7,
                    r.plausible_vs_10,
                    r.plausible_vs_15,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )
        for req in cohort:
            for p in req.per_agent:
                writer.writerow(
                    [
                        "cohort",
                        "",
                        p.monthly_cost,
                        "",
                        "",
                        "",
                        "",
                        "",
                        req.scenario,
                        req.r,
                        p.name,
                        f"{p.a_min:.4f}",
                        f"{req.b_all_four:.4f}",
                        f"{req.b_aggregate:.4f}",
                    ]
                )


def run_smoke_test() -> int:
    print("break_even_table smoke test")
    checks = 0
    failures = 0

    def check(label: str, cond: bool) -> None:
        nonlocal checks, failures
        checks += 1
        status = "ok" if cond else "FAIL"
        if not cond:
            failures += 1
        print(f"  [{status}] {label}")

    lin_1 = required_annual_linear(500, 20)
    check("A=500,C=20 linear == 0.48", abs(lin_1 - 0.48) < 1e-12)

    lin_2 = required_annual_linear(500, 200)
    check("A=500,C=200 linear == 4.80", abs(lin_2 - 4.80) < 1e-12)

    comp_1 = required_annual_monthly_compounded(500, 20)
    expected_comp = (1.04) ** 12 - 1
    check(
        "A=500,C=20 monthly-compounded == (1.04)^12-1 ≈ 0.601",
        abs(comp_1 - expected_comp) < 1e-12 and abs(comp_1 - 0.601) < 5e-4,
    )
    check(
        "monthly-compounded > linear when C>0",
        comp_1 > lin_1,
    )

    a_min = min_capital(30, 0.15)
    check("A_min(C=30,r=0.15) == 2400", abs(a_min - 2400.0) < 1e-12)

    # List-price tier figures through cohort_requirement (A_min = 12*C/r).
    entry_15 = cohort_requirement("Entry", TIER_SCENARIOS["Entry"], 0.15)
    entry_15_a = {p.name: p.a_min for p in entry_15.per_agent}
    check("entry/15%: ChatGPT A_min = $1,600", abs(entry_15_a["ChatGPT Plus"] - 1600) < 1.0)
    check("entry/15%: Copilot A_min = $800", abs(entry_15_a["Copilot Pro"] - 800) < 1.0)
    check("entry/15%: SuperGrok A_min = $2,400", abs(entry_15_a["SuperGrok"] - 2400) < 1.0)
    check("entry/15%: B for all 4 to pass = $9,600", abs(entry_15.b_all_four - 9600) < 1.0)
    check(
        "entry/15%: B for cohort in aggregate = $6,400",
        abs(entry_15.b_aggregate - 6400) < 1.0,
    )

    entry_10 = cohort_requirement("Entry", TIER_SCENARIOS["Entry"], 0.10)
    check("entry/10%: B for all 4 to pass = $14,400", abs(entry_10.b_all_four - 14400) < 1.0)

    entry_7 = cohort_requirement("Entry", TIER_SCENARIOS["Entry"], 0.07)
    check("entry/7%: B for all 4 to pass ~= $20,571", abs(entry_7.b_all_four - 20571) < 1.0)

    power_15 = cohort_requirement("Power", TIER_SCENARIOS["Power"], 0.15)
    power_15_a = {p.name: p.a_min for p in power_15.per_agent}
    check("power/15%: Copilot Pro+ A_min = $3,120", abs(power_15_a["Copilot Pro+"] - 3120) < 1.0)
    check("power/15%: B for all 4 to pass = $32,000", abs(power_15.b_all_four - 32000) < 1.0)
    check(
        "power/15%: B for cohort in aggregate = $27,120",
        abs(power_15.b_aggregate - 27120) < 1.0,
    )

    power_7 = cohort_requirement("Power", TIER_SCENARIOS["Power"], 0.07)
    check("power/7%: B for all 4 to pass ~= $68,571", abs(power_7.b_all_four - 68571) < 1.0)

    check("zero capital -> inf, not an exception", required_annual_linear(0, 20) == float("inf"))
    check(
        "zero capital compounded -> inf, not an exception",
        required_annual_monthly_compounded(0, 20) == float("inf"),
    )
    check("r<=0 -> A_min inf", min_capital(30, 0) == float("inf"))

    grid = build_grid(DEFAULT_CAPITAL, DEFAULT_COST)
    check(
        "default grid size matches capital*cost product (no H dimension)",
        len(grid) == len(DEFAULT_CAPITAL) * len(DEFAULT_COST),
    )
    check("default capital grid starts at 25", DEFAULT_CAPITAL[0] == 25)
    check("default cost grid has no C=0", 0 not in DEFAULT_COST)
    check(
        "default cost grid is the list-price points 10,20,30,39,100",
        DEFAULT_COST == [10, 20, 30, 39, 100],
    )
    # A=2400 is not in the default grid; A=2500, C=30 is linear 14.4% ->
    # fails 7% and 10%, clears 15%.
    boundary = next(r for r in grid if r.capital == 2500 and r.monthly_cost == 30)
    check(
        "A=2500,C=30 linear 14.4%: no vs 7%, no vs 10%, YES vs 15%",
        (not boundary.plausible_vs_7)
        and (not boundary.plausible_vs_10)
        and boundary.plausible_vs_15
        and abs(boundary.required_annual_linear_pct - 14.4) < 1e-9,
    )
    smallest = next(
        r
        for r in grid
        if r.capital == min(DEFAULT_CAPITAL) and r.monthly_cost == max(DEFAULT_COST)
    )
    check(
        "smallest-capital, largest-cost row fails all three ceilings",
        (not smallest.plausible_vs_7)
        and (not smallest.plausible_vs_10)
        and (not smallest.plausible_vs_15),
    )

    print(f"{checks - failures}/{checks} checks passed")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capital", type=float, nargs="*", default=None, help="override capital (A) grid, $")
    parser.add_argument("--cost", type=float, nargs="*", default=None, help="override monthly cost (C) grid, $")
    parser.add_argument(
        "--include-cost-200",
        action="store_true",
        help="append $200/mo to the default cost grid (not a current list-price point)",
    )
    parser.add_argument("--out-md", type=Path, default=Path(__file__).with_name("break_even_table.md"))
    parser.add_argument("--out-csv", type=Path, default=Path(__file__).with_name("break_even_table.csv"))
    parser.add_argument("--smoke-test", action="store_true", help="self-check on fixtures; no file writes")
    args = parser.parse_args()

    if args.smoke_test:
        return run_smoke_test()

    costs = list(args.cost or DEFAULT_COST)
    if args.include_cost_200 and OPTIONAL_COST_200 not in costs:
        costs.append(OPTIONAL_COST_200)
    rows = build_grid(args.capital or DEFAULT_CAPITAL, costs)
    cohort = build_cohort_table()
    md = render_markdown(rows, cohort)
    args.out_md.write_text(md + "\n")
    write_csv(rows, cohort, args.out_csv)
    print(md)
    print(f"\nwrote {args.out_md} and {args.out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
