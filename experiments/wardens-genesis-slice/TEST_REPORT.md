# Genesis Slice — local test-launch evidence (2026-10-22/23 UTC)

**Scope:** Five-zone *new* browser prototype built from supplied art. It is not the hosted multiplayer game, the permanent Lineage service, an AI Witness model, or an Azure/Discord staging deployment.

## Checks actually executed

| Check | Outcome | Evidence |
|---|---|---|
| JavaScript parser | PASS | `node --check game.js` |
| Core state machine | PASS | `node tests/test_logic.mjs` |
| Genesis, explicit form choice | PASS | synthetic DOM Node harness |
| Three zones after Genesis; path record | PASS | synthetic DOM Node harness (Ember, Archive, Forge) |
| W1 defaults off, opt-in required | PASS | synthetic DOM Node harness |
| Read-only historical question cites event IDs | PASS | synthetic DOM Node harness |
| W1 unknown future refuses guidance | PASS | synthetic DOM Node harness |
| Human W2 contest separately appended | PASS | synthetic DOM Node harness |
| Calibration/uncertain claim path | PASS | synthetic DOM Node harness |
| Council proposal is only a local draft | PASS | synthetic DOM Node harness |
| Five-zone completion and state payload | PASS | synthetic DOM Node harness |
| Static HTTP index/CSS/JS/5 images | PASS | Python local `ThreadingHTTPServer` + urllib; **all eight endpoints HTTP 200** |
| Artwork files and unique DOM IDs | PASS | Verified 5 optimized WebP files exist; 33 DOM IDs unique |
| Chromium real-browser navigation / screenshots | **BLOCKED BY ENVIRONMENT** | Playwright Chrome returned `ERR_BLOCKED_BY_ADMINISTRATOR` on localhost and `file://` before any page script ran; five Playwright cases could not execute |
| Hosted game 33 regression checks | NOT RUN | Hosted game editable source absent from this repository |
| 2–8 co-op joins / synchronization | NOT RUN | Isolated static slice has no multiplayer server |
| Actual personal Witness / Discord / Azure | NOT RUN | Requires authenticated first-party game adapter, PostgreSQL production identity, and Azure #915 controls |

## Interpretation

Local scripted game-state behavior and asset delivery pass. **This is not a successful real-browser E2E test and not an internet-accessible launch.** A browser environment that permits localhost still needs to run `pytest tests/test_playable.py` and validate desktop/mobile screenshots and accessibility.

### Security and research boundaries

No network SDK/model, secrets, remote logging, hidden interrogation, personality inference, irreversible character evolution, or real Council votes. Witness output is deterministic and event-cited; its only output target is a status panel. All meaningful inputs are player-initiated. Browser localStorage is untrusted demo storage and must not be confused with the permanent, authenticated lineage service from merged PR #984.

### Test-launch release decision

**Local scripted smoke: PASS in five runs** (Seeker/Ember, Warden/Archive, Builder/Forge, Memory-Bearer/Archive, and W1 disabled). Browser E2E: BLOCKED. External staging/production: NOT LAUNCHED. The independent `.github/workflows/wardens-genesis-smoke.yml` adds a read-only CI harness and asset checks; CI status must be checked separately. Keep PR in draft pending CodeRabbit, complete real-browser validation, approved art publishing, and live game source access.
