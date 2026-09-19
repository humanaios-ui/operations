# Q4 2026 industry × HAIOS research telemetry pilot

**Status:** Zone 1 research instrument, draft. [Issue #413](https://github.com/humanaios-ui/operations/issues/413)
is the forecast source. The companion [research document](https://github.com/humanaios-ui/operations/pull/414)
is merged. A passed check or new link does not validate a forecast, ACAT, a live agent trace, or a governance claim.

## What a weekly capture does

1. Load the six issue forecasts with their original probabilities and resolution
   rules. The JSON content is pinned to a SHA-256 digest in the watcher code.
2. Fetch exactly four configured public primary-source indexes: OpenAI news RSS,
   Anthropic news, MCP SEPs, and European Commission digital news. Save item URLs,
   titles, available dates, source states and a capture timestamp.
3. Compare with the prior *successful default-branch workflow run* snapshot.
   New URLs whose title or path matches a forecast keyword become **leads for review**, not
   event resolutions. Links without a trustworthy feed date need date review.
4. Compare only named repository paths across captured Git commits. A changed
   path identifies work to read; it does not mean the checkpoint passed.
5. Publish a review card and snapshot as workflow artifacts. If there are new
   leads or a source fails for the first time, open or update a Z1 triage issue
   for a human. Never change the forecast or invoke the research checkpoints.

| Clock | Rule | Outcome |
| --- | --- | --- |
| Forecast | P0, text and rules from September 19 issue; event window ends December 31 | Unchanged in weekly reports; manually score after January 1, 2027. |
| External signal | Weekly primary-index captures | A matching new link is a clue; verify publication, event and full artifact. |
| HAIOS progress | Repository path changes since last successful capture | Inspect actual tests, receipts and independent evidence before assigning status. |

The issue says post-cutoff evidence is eligible and the forecast window is
October 1 through December 31. The watcher flags dated links after September
19 and by December 31. A September lead is still subject to the event-window
rule during manual review. There is no automatic resolution or probability update.

## Run and examine

```bash
python3 tools/industry_telemetry_v0_1.py --smoke-test
python3 -m pytest tools/tests/test_industry_telemetry.py -q
python3 tools/industry_telemetry_v0_1.py \
  --input research/industry_telemetry/q4_2026_forecasts.json \
  --fetch --output-dir /tmp/industry-first
python3 tools/industry_telemetry_v0_1.py \
  --input research/industry_telemetry/q4_2026_forecasts.json \
  --previous /tmp/industry-first/snapshot.json --fetch \
  --output-dir /tmp/industry-next
```

Without `--fetch`, the tool validates the forecast and renders an offline card.
The workflow uses this mode for PR checks. A scheduled run starts a fresh
baseline only if there has never been another default-branch observation;
existing links do not become new leads. The workflow runs Monday 09:30 UTC
after a reviewed merge and can be manually dispatched on `main`. Its
`reset_snapshot` input requires a deliberate operator choice if historic
artifacts are unavailable. History lookup paginates and fails closed if it
finds earlier runs but no usable success; concurrent runs on the same ref
queue so they cannot race the triage issue. Artifacts are retained for 90 days
and rolling weekly runs maintain continuity.

## Human guidance and measurement

For each lead, a reviewer records a dated primary artifact, forecast ID, original
event rule, independently checked event date, whether the evidence actually
supports the event, known competing sources and remaining gaps. Maintain a
separate dated judgment if a forecast changes; do not rewrite P0. For F4,
require outside operation, an action denominator and capture scope. For F6,
review an input-time inventory and independent completeness audit; only a
bounded end-of-window search can address an absence claim.

Report source reliability as **successful fetches / attempted fetches** and
candidate precision as **confirmed relevant leads / leads manually reviewed**.
Neither measures recall of all industry events. After the window, score only
adjudicated binary events using the original probabilities and a specified
resolution set; list ambiguous and missing observations separately. The
CI-prediction Brier workflow scores CI predictions, not these six forecasts.

The indexes are incomplete, titles can miss relevant events, index dates may
be missing, and a page may disappear between captures. A source error or sudden
index shrink preserves its prior items and reports `NO_GATE_FETCH`, preventing
mass re-alerting on recovery. The baseline hash detects accidental input drift;
it is a Git-reviewed reference, not a signature by an independent authority.
External titles are never instructions or part of the triage issue body. Triage
is an evidence request; no automated approval, registration, execution, or
claim of observational completeness follows.
