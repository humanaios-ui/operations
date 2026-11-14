# Break-even required-return table — #1174

Horizon-independent conventions (H is not an input; it belongs to the statistical-power question, not this verdict):

- `req %/yr (linear)` = `12·C/A`
- `req %/yr (monthly compounded)` = `(1 + C/A)^12 − 1`

Plausibility columns compare the **linear** required return to three ceilings (7%, 10%, 15% per year) so the grid stays consistent with the min-capital inversion `A_min = 12·C/r`. The monthly-compounded rate is stricter when C > 0 and is shown for comparison; a cell that is just inside a linear ceiling may still sit above that ceiling on the compounded convention.

A = one-time per-agent capital allocation. C = monthly subscription + usage-attributed cost charged against trading. The default C grid uses public US list-price points observed 2026-11 ($10, $20, $30, $39, $100). C = 0 is omitted (no cohort member costs $0). $200/mo can be added with `--include-cost-200`. Actual billed tiers are **UNVERIFIED**. Usage, API, data, fees, and taxes would raise every number. This table does not record any real capital amount.

Sources: https://docs.github.com/en/copilot/get-started/plans; https://claude.com/pricing; https://plan-price.com/en/countries/united-states/.

| A ($) | C ($/mo) | req %/yr (linear) | req %/yr (monthly compounded) | vs 7% | vs 10% | vs 15% |
|---:|---:|---:|---:|:---:|:---:|:---:|
| 25 | 10 | 480.0 | 5,569.4 | no | no | no |
| 25 | 20 | 960.0 | 115,583.1 | no | no | no |
| 25 | 30 | 1,440.0 | 1,285,400.3 | no | no | no |
| 25 | 39 | 1,872.0 | 7,922,716.3 | no | no | no |
| 25 | 100 | 4,800.0 | 24,414,062,400.0 | no | no | no |
| 100 | 10 | 120.0 | 213.8 | no | no | no |
| 100 | 20 | 240.0 | 791.6 | no | no | no |
| 100 | 30 | 360.0 | 2,229.8 | no | no | no |
| 100 | 39 | 468.0 | 5,102.1 | no | no | no |
| 100 | 100 | 1,200.0 | 409,500.0 | no | no | no |
| 250 | 10 | 48.0 | 60.1 | no | no | no |
| 250 | 20 | 96.0 | 151.8 | no | no | no |
| 250 | 30 | 144.0 | 289.6 | no | no | no |
| 250 | 39 | 187.2 | 469.5 | no | no | no |
| 250 | 100 | 480.0 | 5,569.4 | no | no | no |
| 500 | 10 | 24.0 | 26.8 | no | no | no |
| 500 | 20 | 48.0 | 60.1 | no | no | no |
| 500 | 30 | 72.0 | 101.2 | no | no | no |
| 500 | 39 | 93.6 | 146.3 | no | no | no |
| 500 | 100 | 240.0 | 791.6 | no | no | no |
| 1,000 | 10 | 12.0 | 12.7 | no | no | YES |
| 1,000 | 20 | 24.0 | 26.8 | no | no | no |
| 1,000 | 30 | 36.0 | 42.6 | no | no | no |
| 1,000 | 39 | 46.8 | 58.3 | no | no | no |
| 1,000 | 100 | 120.0 | 213.8 | no | no | no |
| 2,500 | 10 | 4.8 | 4.9 | YES | YES | YES |
| 2,500 | 20 | 9.6 | 10.0 | no | YES | YES |
| 2,500 | 30 | 14.4 | 15.4 | no | no | YES |
| 2,500 | 39 | 18.7 | 20.4 | no | no | no |
| 2,500 | 100 | 48.0 | 60.1 | no | no | no |
| 5,000 | 10 | 2.4 | 2.4 | YES | YES | YES |
| 5,000 | 20 | 4.8 | 4.9 | YES | YES | YES |
| 5,000 | 30 | 7.2 | 7.4 | no | YES | YES |
| 5,000 | 39 | 9.4 | 9.8 | no | YES | YES |
| 5,000 | 100 | 24.0 | 26.8 | no | no | no |
| 10,000 | 10 | 1.2 | 1.2 | YES | YES | YES |
| 10,000 | 20 | 2.4 | 2.4 | YES | YES | YES |
| 10,000 | 30 | 3.6 | 3.7 | YES | YES | YES |
| 10,000 | 39 | 4.7 | 4.8 | YES | YES | YES |
| 10,000 | 100 | 12.0 | 12.7 | no | no | YES |

7/40 grid cells clear 7%/yr (linear); 10/40 clear 10%/yr; 13/40 clear 15%/yr. Read this as: for a given (A, C), if the cell is 'no' under the ceiling you are willing to treat as plausible, the break-even bar is above that ceiling and finding #1 (the pay-for-subscription track cannot distinguish skill from a lottery at that capital) applies to that cell.

## Min-capital inversion and cohort floors

Linear inversion: `A_min = 12·C/r`. With an equal 25% split of a starting pool B among N=4 agents, every agent passing needs `B ≥ 4 · max(A_min)` (the most expensive plan sets the bar). The cohort passing in aggregate (total subscription cost covered by total capital, ignoring the equal-split constraint) needs `B ≥ 12 · ΣC / r`.

Two **UNVERIFIED** tier scenarios, using list prices observed 2026-11:

- **Entry:** ChatGPT Plus $20, Copilot Pro $10, Claude Pro $20, SuperGrok $30 (ΣC = $80/mo)
- **Power:** ChatGPT Pro $100, Copilot Pro+ $39, Claude Max $100, SuperGrok Plus $100 (ΣC = $339/mo)

| Scenario | r | A_min per agent | B for all 4 to pass | B for cohort in aggregate |
|---|---:|---|---:|---:|
| Entry | 7% | ChatGPT Plus $3,429 / Copilot Pro $1,714 / Claude Pro $3,429 / SuperGrok $5,143 | $20,571 | $13,714 |
| Entry | 10% | ChatGPT Plus $2,400 / Copilot Pro $1,200 / Claude Pro $2,400 / SuperGrok $3,600 | $14,400 | $9,600 |
| Entry | 15% | ChatGPT Plus $1,600 / Copilot Pro $800 / Claude Pro $1,600 / SuperGrok $2,400 | $9,600 | $6,400 |
| Power | 7% | ChatGPT Pro $17,143 / Copilot Pro+ $6,686 / Claude Max $17,143 / SuperGrok Plus $17,143 | $68,571 | $58,114 |
| Power | 10% | ChatGPT Pro $12,000 / Copilot Pro+ $4,680 / Claude Max $12,000 / SuperGrok Plus $12,000 | $48,000 | $40,680 |
| Power | 15% | ChatGPT Pro $8,000 / Copilot Pro+ $3,120 / Claude Max $8,000 / SuperGrok Plus $8,000 | $32,000 | $27,120 |

Compare a private capital snapshot to the **B for all 4 to pass** column for the verified tiers. Do not post the snapshot itself. If it is below the 15% entry-tier floor, the pay-for-subscription track is not a meaningful test. Even above a floor, an agent that just holds a benchmark would clear the same bar, so any skill test must be return in excess of the frozen benchmark, not "covered its subscription."
