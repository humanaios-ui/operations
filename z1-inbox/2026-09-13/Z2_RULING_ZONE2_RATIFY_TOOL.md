# Z2 Ruling — 2026-09-13

Ratification of one Zone 2 tool declaration.

## Ruling: `.z1-control/ratify.py` Zone 2 — RATIFIED

Hash: `z1-ratify-zone2-approved-20260913`

**Decision by:** Night (Z2 / Admiral)
**Given:** 2026-09-13, in session `016hAX9tLuggZumWsrPKYc5L`, in response to the Z2 item raised
in `Q-TOOLCONTROL-03.md` ("Addendum — surfaced by the #308 merge").
**Recorded by:** Claude (Z1), as transcription of Z2's decision. Z1 did not make this call.

`tools/.z1-control/ratify.py` declares `TOOL_ZONE = 2`. The declaration is ratified: the tool
records a Z2 decision on a candidate block and is run by the ratifier, so ratify-level authority
is the correct zone for it.

**Effect on the tool manifest:**

- `HAIOS-TOOL-153` gains `ratified_by: "z1-ratify-zone2-approved-20260913"`.
- `pending_ratification` is removed — it is no longer an open item.
- The path is removed from `UNRATIFIED_ZONE_CLAIMS` in `.tool-control/validate.py`.

`tools/message_calibration_v1_0.py` (`HAIOS-TOOL-088`) is **not** covered by this ruling and
remains an open Z2 item.

---

## Gap noted while recording this

`.z1-control/ratify.py` computes a real sha256 signature, but only for **candidate blocks**
(`q_id`). A tool's Zone 2/3 claim has no equivalent: `ratified_by` in `tools-manifest.yaml` is a
free-text field that the validator checks for *presence*, not for a signature that verifies.

So this ruling's hash is a human-readable slug in the style of `Z2_RULINGS_2026-09-08.md`, not a
content-pinned sha256, and nothing recomputes it. A later pass could extend `ratify.py` to sign
tool-zone rulings the way it signs candidate blocks, at which point this entry should be re-pinned.

Recorded as an observation, not fixed here — extending the signing machinery is its own change and
was not what Z2 was asked to decide.
