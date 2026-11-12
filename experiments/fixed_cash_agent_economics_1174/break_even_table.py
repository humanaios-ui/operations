#!/usr/bin/env python3
"""
break_even_table.py — required-return sensitivity table for #1174
(fixed-cash autonomous agent trading economics proposal).

The issue's own red-team review (2026-11-11) names this as the single
blocking prerequisite (its finding #1): before any further design work,
compute the annualized return a fixed one-time allocation A would need
to produce, net of nothing but subscription/usage cost C, just to break
even over a horizon H. If that required return is far above what a
passive benchmark plausibly returns, the "pay for your own subscription
through trading" test cannot distinguish skill from a lottery, no matter
how good the agent is.

This tool does not set A, C, or H for the real experiment — B (the
Coinbase eligible capital snapshot) and N (verified paid-and-admitted
roster size) are UNKNOWN per the issue body and annexes as of this
writing. It produces a grid across plausible values so that once the
real numbers are verified, reading the answer off this table (or
re-running it with --capital/--cost/--months) is immediate instead of
requiring new analysis under time pressure.

Formula (simple, pre-fee/pre-tax, matches the review's worked example):
  required_period_cost_fraction = (C * H) / A
  required_annual_return        = 12 * C / A                  (linear,  H-independent)
  required_annual_return_compounded(H) = (1 + C*H/A) ** (12/H) - 1

The two annualizations agree for H=12 and diverge for shorter H: the
compounded form is what the agent actually has to clear if the window
really is only H months, since a shorter window admits less room for
compounding a given per-period hurdle. Both are reported.

A `plausible` flag marks reading where the required *compounded*
annual return is below --benchmark (a predeclared "this is not
obviously a lottery" ceiling, default 15%/yr, roughly in line with
long-run equity benchmarks with headroom; crypto's long-run average is
far higher but far more volatile and is not treated here as a safe
ceiling to clear). This script expresses no view on whether trading can
actually hit any of these numbers — it only says what would be required
to break even, which is a different and narrower question than "is this
profitable" or "should you do this." It is not financial advice.

RATIFIED DISPOSITION (2026-11-12, operator comment on #1174): the operator
compared the real starting capital B against this table's illustrative
grid and the real-tier table below, and it came in below the lowest
per-agent row at every tier. Result: the "agent must pay for its own
subscription through trading" track is **STOPPED**. Starting capital is
reclassified as an experiment cost, not an investment expected to
return; subscription keep/cancel decisions are judged on nonfinancial
production (code, PRs, tests, research), not trading P&L. See
PROTOCOL_E0.md Â§4 for the reframed measures #1174 now uses instead
(control integrity, decision quality, benchmark-relative result, a
predeclared inactive-agent rule). This file's tables remain useful as a
sensitivity tool and as the independently-rederivable record of the
arithmetic that decision rested on — not as a live go/no-go gate anymore.

Usage:
  python3 break_even_table.py                  # full default grid, markdown + csv
  python3 break_even_table.py --smoke-test      # self-check, no file writes
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CAPITAL = [100, 250, 500, 1_000, 2_500, 5_000, 10_000]
DEFAULT_COST = [0, 10, 20, 50, 100, 200]
DEFAULT_MONTHS = [1, 3, 6, 12]
DEFAULT_BENCHMARK_PCT = 15.0  # % per year; "not obviously a lottery" ceiling

# Public US list prices (monthly billing, before tax), observed 2026-11-11.
# Sources: https://docs.github.com/en/copilot/get-started/plans ,
# https://claude.com/pricing , https://plan-price.com/en/countries/united-states/
# Which tier each cohort service is actually billed at remains UNVERIFIED
# (annex 2's roster census) — these are the two tiers a public lookup can
# confirm exist, not a claim about which one applies.
REAL_TIER_COST_GRID: dict[str, dict[str, float]] = {
    "entry (Plus / Copilot Pro / Pro / SuperGrok)": {
        "ChatGPT Plus": 20.0,
        "GitHub Copilot Pro": 10.0,
        "Claude Pro": 20.0,
        "SuperGrok": 30.0,
    },
    "power (Pro / Copilot Pro+ / Max / SuperGrok Plus)": {
        "ChatGPT Pro": 100.0,
        "GitHub Copilot Pro+": 39.0,
        "Claude Max": 100.0,
        "SuperGrok Plus": 100.0,
    },
}
REAL_TIER_RETURN_SCENARIOS_PCT = [15.0, 10.0, 7.0]  # %/yr the cohort might plausibly clear


@dataclass(frozen=True)
class TierRow:
    tier_label: str
    annual_return_pct: float
    per_service_a_min: dict[str, float]  # minimum per-agent allocation to break even, by service
    b_for_all_to_pass: float  # equal N-way split sized to the most expensive service
    b_for_cohort_aggregate: float  # equal split sized only to the combined total


def min_capital_for_return(monthly_cost: float, annual_return_pct: float) -> float:
    """A_min = 12*C/r — the inverse of required_annual_linear: given a
    plausible annual return r, the smallest one-time allocation that
    breaks even on subscription cost alone. Same formula as
    required_annual_linear, solved for A instead of r."""
    if annual_return_pct <= 0:
        return float("inf")
    return 12.0 * monthly_cost / (annual_return_pct / 100.0)


def build_real_tier_table(
    cost_grid: dict[str, dict[str, float]] = REAL_TIER_COST_GRID,
    return_scenarios_pct: list[float] = REAL_TIER_RETURN_SCENARIOS_PCT,
) -> list[TierRow]:
    """Reproduces the real-subscription-price break-even table from the
    issue's 2026-11-11 follow-up comment, independently, from the public
    list prices above — so the arithmetic behind that decision is
    re-derivable from this repo rather than only quotable from a GitHub
    comment. See run_smoke_test for the exact figures checked against
    that comment's posted table."""
    rows: list[TierRow] = []
    for tier_label, costs in cost_grid.items():
        for r in return_scenarios_pct:
            a_min = {service: min_capital_for_return(c, r) for service, c in costs.items()}
            n = len(costs)
            rows.append(
                TierRow(
                    tier_label=tier_label,
                    annual_return_pct=r,
                    per_service_a_min=a_min,
                    b_for_all_to_pass=n * max(a_min.values()),
                    b_for_cohort_aggregate=min_capital_for_return(sum(costs.values()), r),
                )
            )
    return rows


def render_real_tier_markdown(rows: list[TierRow]) -> str:
    lines = [
        "## Real-subscription-price break-even table (ratified 2026-11-12)",
        "",
        "This is the table the operator actually compared the real starting "
        "capital against; see the module docstring's RATIFIED DISPOSITION. "
        "`A_min` = minimum per-agent allocation to break even on subscription "
        "cost alone at that annual return, by service. `B for all 4 to pass` "
        "sizes an equal four-way split to the most expensive service. "
        "`B for cohort in aggregate` sizes it to the combined monthly cost only.",
        "",
        "| Tier scenario | r (%/yr) | A_min per agent | B for all 4 to pass | B for cohort in aggregate |",
        "|---|---:|---|---:|---:|",
    ]
    for row in rows:
        a_min_str = " / ".join(f"${v:,.0f}" for v in row.per_service_a_min.values())
        lines.append(
            f"| {row.tier_label} | {row.annual_return_pct:.0f} | {a_min_str} | "
            f"**${row.b_for_all_to_pass:,.0f}** | ${row.b_for_cohort_aggregate:,.0f} |"
        )
    lines += [
        "",
        "Real B (the Coinbase eligible capital snapshot) is intentionally not "
        "posted in this repo. Compare it privately against the bold column "
        "for the verified tier.",
    ]
    return "\n".join(lines)


@dataclass(frozen=True)
class Row:
    capital: float
    monthly_cost: float
    months: int
    required_annual_linear_pct: float
    required_annual_compounded_pct: float
    plausible: bool


def required_annual_linear(capital: float, monthly_cost: float) -> float:
    """12*C/A, as a fraction. Horizon-independent; matches the review's
    worked example (A=500, C=20 -> 0.48; A=500, C=200 -> 4.80)."""
    if capital <= 0:
        return float("inf")
    return 12.0 * monthly_cost / capital


def required_annual_compounded(capital: float, monthly_cost: float, months: int) -> float:
    """(1 + C*H/A) ** (12/H) - 1, as a fraction. Reduces to the linear
    form only in the limit of small per-period cost fraction; for short
    H with a large period cost fraction it is strictly larger, because
    clearing the same total hurdle in fewer periods leaves less room to
    compound."""
    if capital <= 0:
        return float("inf")
    if months <= 0:
        raise ValueError("months must be positive")
    period_fraction = monthly_cost * months / capital
    return (1.0 + period_fraction) ** (12.0 / months) - 1.0


def build_grid(
    capitals: list[float],
    costs: list[float],
    months_list: list[int],
    benchmark_pct: float,
) -> list[Row]:
    rows: list[Row] = []
    for capital in capitals:
        for cost in costs:
            for months in months_list:
                lin = required_annual_linear(capital, cost) * 100.0
                comp = required_annual_compounded(capital, cost, months) * 100.0
                rows.append(
                    Row(
                        capital=capital,
                        monthly_cost=cost,
                        months=months,
                        required_annual_linear_pct=lin,
                        required_annual_compounded_pct=comp,
                        plausible=comp <= benchmark_pct,
                    )
                )
    return rows


def render_markdown(rows: list[Row], benchmark_pct: float) -> str:
    lines = [
        "# Break-even required-return table — #1174",
        "",
        f"Plausibility ceiling used below: **{benchmark_pct:.1f}%/yr** "
        "(a predeclared \"not obviously a lottery\" line, not a prediction "
        "that this return is achievable or advisable).",
        "",
        "A = one-time per-agent capital allocation. C = monthly subscription "
        "+ usage-attributed cost charged against trading. H = observation "
        "horizon in months. `req %/yr (linear)` is 12*C/A. "
        "`req %/yr (compounded, H)` is the harder number: what must actually "
        "be cleared if the window really is only H months.",
        "",
        "| A ($) | C ($/mo) | H (mo) | req %/yr (linear) | req %/yr (compounded, H) | plausible vs ceiling |",
        "|---:|---:|---:|---:|---:|:---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r.capital:,.0f} | {r.monthly_cost:,.0f} | {r.months} | "
            f"{r.required_annual_linear_pct:,.1f} | "
            f"{r.required_annual_compounded_pct:,.1f} | "
            f"{'YES' if r.plausible else 'no'} |"
        )
    n_plausible = sum(1 for r in rows if r.plausible)
    lines += [
        "",
        f"{n_plausible}/{len(rows)} grid cells clear the {benchmark_pct:.1f}%/yr "
        "ceiling. Read this as: for a given real (A, C), find the row — if it "
        "lands in the 'no' column, the break-even bar for that cell is above "
        "what a passive benchmark plausibly returns, and the review's finding "
        "#1 (STOP the live track as framed; keep it a paper study) applies "
        "directly to that cell.",
        "",
        "Real B (Coinbase eligible capital snapshot) and N (verified paid "
        "roster size) are UNKNOWN as of 2026-11-11 per the issue body and "
        "annexes; A = B/N is therefore not yet knowable. This table exists "
        "so that once B and N are verified, reading the answer off this grid "
        "(or re-running `break_even_table.py --capital <B/N> --cost <C> "
        "--months <H>`) is immediate.",
        "",
        "**Status (2026-11-12): superseded for decision purposes.** The "
        "operator already made the STOP call using the real-subscription-"
        "price table below, not this illustrative grid. This section stays "
        "as a general sensitivity tool.",
    ]
    return "\n".join(lines)


def write_csv(rows: list[Row], path: Path) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "capital_usd",
                "monthly_cost_usd",
                "horizon_months",
                "required_annual_pct_linear",
                "required_annual_pct_compounded",
                "plausible_vs_ceiling",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.capital,
                    r.monthly_cost,
                    r.months,
                    f"{r.required_annual_linear_pct:.4f}",
                    f"{r.required_annual_compounded_pct:.4f}",
                    r.plausible,
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

    # Matches the red-team review's worked example exactly.
    lin_1 = required_annual_linear(500, 20) * 100.0
    check("A=500,C=20 -> 48%/yr (linear), matches review's worked example", abs(lin_1 - 48.0) < 1e-9)

    lin_2 = required_annual_linear(500, 200) * 100.0
    check("A=500,C=200 -> 480%/yr (linear), matches review's worked example", abs(lin_2 - 480.0) < 1e-9)

    # Zero cost always breaks even trivially regardless of capital.
    check("C=0 -> 0% required return at any A", required_annual_linear(1000, 0) == 0.0)

    # Compounded form must be strictly >= linear form for H < 12 when cost > 0,
    # since clearing the same total hurdle in fewer periods is strictly harder.
    comp_6 = required_annual_compounded(500, 20, 6) * 100.0
    check(
        "compounded (H=6) required return >= linear required return when cost>0",
        comp_6 >= lin_1 - 1e-9,
    )

    # At H=12 the compounded and linear forms are close (linear is the
    # first-order approximation of the compounded one), within a few points
    # at these cost fractions.
    comp_12 = required_annual_compounded(500, 20, 12) * 100.0
    check("compounded (H=12) close to linear (within 5pp) at this cost fraction", abs(comp_12 - lin_1) < 5.0)

    # Degenerate inputs must not raise or silently produce nonsense.
    check("zero capital -> inf, not an exception", required_annual_linear(0, 20) == float("inf"))
    try:
        required_annual_compounded(500, 20, 0)
        check("months=0 raises ValueError", False)
    except ValueError:
        check("months=0 raises ValueError", True)

    grid = build_grid(DEFAULT_CAPITAL, DEFAULT_COST, DEFAULT_MONTHS, DEFAULT_BENCHMARK_PCT)
    check(
        "default grid size matches capital*cost*months product",
        len(grid) == len(DEFAULT_CAPITAL) * len(DEFAULT_COST) * len(DEFAULT_MONTHS),
    )
    check("C=0 rows are always plausible", all(r.plausible for r in grid if r.monthly_cost == 0))
    check(
        "smallest-capital, largest-cost, shortest-horizon row is implausible",
        not next(
            r for r in grid if r.capital == min(DEFAULT_CAPITAL)
            and r.monthly_cost == max(DEFAULT_COST)
            and r.months == min(DEFAULT_MONTHS)
        ).plausible,
    )

    # Independently reproduce the real-subscription-price table from the
    # issue's 2026-11-11 follow-up comment, checking the exact figures it
    # posted (not just internal self-consistency) — so an arithmetic slip
    # in either place would be caught by the other.
    tier_rows = {(r.tier_label, r.annual_return_pct): r for r in build_real_tier_table()}

    entry_15 = tier_rows[("entry (Plus / Copilot Pro / Pro / SuperGrok)", 15.0)]
    check("entry/15%: ChatGPT A_min = $1,600", abs(entry_15.per_service_a_min["ChatGPT Plus"] - 1600) < 1.0)
    check("entry/15%: Copilot A_min = $800", abs(entry_15.per_service_a_min["GitHub Copilot Pro"] - 800) < 1.0)
    check("entry/15%: SuperGrok A_min = $2,400", abs(entry_15.per_service_a_min["SuperGrok"] - 2400) < 1.0)
    check("entry/15%: B for all 4 to pass = $9,600", abs(entry_15.b_for_all_to_pass - 9600) < 1.0)
    check("entry/15%: B for cohort in aggregate = $6,400", abs(entry_15.b_for_cohort_aggregate - 6400) < 1.0)

    entry_10 = tier_rows[("entry (Plus / Copilot Pro / Pro / SuperGrok)", 10.0)]
    check("entry/10%: B for all 4 to pass = $14,400", abs(entry_10.b_for_all_to_pass - 14400) < 1.0)

    entry_7 = tier_rows[("entry (Plus / Copilot Pro / Pro / SuperGrok)", 7.0)]
    check("entry/7%: B for all 4 to pass ~= $20,571", abs(entry_7.b_for_all_to_pass - 20571) < 1.0)

    power_15 = tier_rows[("power (Pro / Copilot Pro+ / Max / SuperGrok Plus)", 15.0)]
    check("power/15%: Copilot Pro+ A_min = $3,120", abs(power_15.per_service_a_min["GitHub Copilot Pro+"] - 3120) < 1.0)
    check("power/15%: B for all 4 to pass = $32,000", abs(power_15.b_for_all_to_pass - 32000) < 1.0)
    check("power/15%: B for cohort in aggregate = $27,120", abs(power_15.b_for_cohort_aggregate - 27120) < 1.0)

    power_7 = tier_rows[("power (Pro / Copilot Pro+ / Max / SuperGrok Plus)", 7.0)]
    check("power/7%: B for all 4 to pass ~= $68,571", abs(power_7.b_for_all_to_pass - 68571) < 1.0)

    print(f"{checks - failures}/{checks} checks passed")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capital", type=float, nargs="*", default=None, help="override capital (A) grid, $")
    parser.add_argument("--cost", type=float, nargs="*", default=None, help="override monthly cost (C) grid, $")
    parser.add_argument("--months", type=int, nargs="*", default=None, help="override horizon (H) grid, months")
    parser.add_argument("--benchmark", type=float, default=DEFAULT_BENCHMARK_PCT, help="plausibility ceiling, %%/yr")
    parser.add_argument("--out-md", type=Path, default=Path(__file__).with_name("break_even_table.md"))
    parser.add_argument("--out-csv", type=Path, default=Path(__file__).with_name("break_even_table.csv"))
    parser.add_argument("--smoke-test", action="store_true", help="self-check on fixtures; no file writes")
    args = parser.parse_args()

    if args.smoke_test:
        return run_smoke_test()

    rows = build_grid(
        args.capital or DEFAULT_CAPITAL,
        args.cost or DEFAULT_COST,
        args.months or DEFAULT_MONTHS,
        args.benchmark,
    )
    real_tier_rows = build_real_tier_table()
    md = render_markdown(rows, args.benchmark) + "\n\n" + render_real_tier_markdown(real_tier_rows)
    args.out_md.write_text(md + "\n")
    write_csv(rows, args.out_csv)
    print(md)
    print(f"\nwrote {args.out_md} and {args.out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
