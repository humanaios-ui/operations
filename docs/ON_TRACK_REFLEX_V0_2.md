# INTENT-OS × Resource Miner — On-Track v0.2 (stacked implementation)

**State:** PROPOSED, read-only. **Parent PR:** #929 / Issue #928. **Authority effect:** NONE.

## Measured human goal

> Can a human enter a real objective, receive public Resource Miner leads with source links and honest eligibility uncertainty, then make an informed decision?

This is the immediate usability target. Work linked to the goal is a *declaration* until independently tested, and a passing local HTTP test is not an observed human outcome.

## New implementation

- `resource_miner/on_track_execution.py` sends actual HTTP requests to a running local `app.py` process. It tests `GET /intent-os`, a positive `POST /api/intent` in **stored snapshot** mode, and a negative unrelated objective. It rejects unsafe/private source links, unexpected outcomes, authority claims, and false eligibility. It never follows redirects and never checks third-party sites. No write or account access.
- `resource_miner/on_track_progress.py` joins the existing v0.1 declared-goal report and the new loopback HTTP receipt, verifies both *unsigned digests for integrity only*, and produces `on_track_progress.json` plus an offline HTML progress card. Digests do **not** authenticate the issuer or grant authority.
- `/on-track` is a new **read-only page** on the existing Resource Miner service. It displays UNVERIFIED by default; the user can import a local progress JSON. It does not call GitHub, upload anything, or save the import. The Resource Miner `/intent-os` page links to it.
- `.github/workflows/on-track-reflex-execution.yml` starts the actual local service on loopback, captures HTTP findings, samples declared issue mappings, and publishes non-authorizing artifacts for inspection.

## Evidence state map

| Observation | Validated by | What it actually establishes |
|---|---|---|
| Declared issue goal link | Exact `on_track_target:` line or explicitly fixed pilot anchor | Declared association, **not** real progress |
| `GET /intent-os` and `POST /api/intent` | Independent Python HTTP client against running local app | Local API route works with committed snapshot under tested conditions |
| Safe candidate links and correct `NOT_ASSESSED` | Contract assertions over real API JSON | Visible source leads can be returned without eligibility or authorization claims |
| Public deployment and pinned deploy SHA | Not collected | **UNVERIFIED** |
| Human uses service and chooses a useful lead | Not collected | **UNVERIFIED** |
| App/grant/claim success or real value | Not collected | **UNVERIFIED** |

No green user success can result from a PR merge, a hash alone, a local test, a synthetic fixture, or a self-description.

## Reproducible usage

Run from `humanaios-funding-pipeline/resource-miner`:

```sh
python3 -m unittest discover -s tests -p 'test_on_track_*.py' -v
python3 app.py --host 127.0.0.1 --port 8766 &
miner_pid=$!
python3 -m resource_miner.on_track_execution \
  --origin http://127.0.0.1:8766 --output ../../outputs/on_track_execution.json
kill "$miner_pid"
```

To build the operator view, first produce the GitHub issue report using `resource_miner.on_track_reflex`, then:

```sh
python3 -m resource_miner.on_track_progress \
  --report ../../outputs/on_track_reflex.json \
  --receipt ../../outputs/on_track_execution.json \
  --template on-track.html \
  --json-out ../../outputs/on_track_progress.json \
  --html-out ../../outputs/on_track_progress.html
```

The Actions artifact contains the offline `on_track_progress.html` (preloaded with that run's evidence); open it directly in a browser. The service's `/on-track` page remains empty until a user imports the vetted report. **Neither page is a live GitHub connector or a production result.**

## Still required

1. Independent review and admission for parent #929 and this stacked PR.
2. Human-reviewed baseline on 30 cases to measure goal-mapping precision and misses.
3. Independently pinned exact-head CI evidence beyond an author-written PR body.
4. Independently established production origin and deployed SHA, then safe read-only production smoke with operator approval.
5. A real user task receipt demonstrating that the candidate links and uncertainty display were useful, with consent and no storing of private objectives.
6. Only after evidence warrants: a governed way to deliver a scrubbed on-track projection into the user-facing INTENT-OS view without import.

**Falsifier:** Any implementation states a human achieved the goal solely because a local HTTP request succeeded or because PR #822 was merged. Reject such a claim.
