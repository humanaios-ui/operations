# Z2 Ruling — 2026-09-13

Ratification of one Zone 2 tool declaration.

## Ruling: `.z1-control/ratify.py` Zone 2 — RATIFIED

Hash: `z1-ratify-zone2-approved-20260913`

**Decision by:** Night (Z2 / Admiral)
**Given:** 2026-09-13, in session `016hAX9tLuggZumWsrPKYc5L`, in response to the Z2 item raised
in `Q-TOOLCONTROL-03.md` ("Addendum — surfaced by the #308 merge").
**Recorded by:** Claude (Z1), as transcription of Z2's decision. Z1 did not make this call.

`.z1-control/ratify.py` declares `TOOL_ZONE = 2`. The declaration is ratified: the tool
records a Z2 decision on a candidate block and is run by the ratifier, so ratify-level authority
is the correct zone for it.

**Effect on the tool manifest:**

- `HAIOS-TOOL-153` gains `ratified_by: "z1-ratify-zone2-approved-20260913"` and
  `ratification_ruling: z1-inbox/2026-09-13/Z2_RULING_ZONE2_RATIFY_TOOL.md` (this file).
- `pending_ratification` is removed — it is no longer an open item.
- The path is removed from `UNRATIFIED_ZONE_CLAIMS` in `.tool-control/validate.py`.

`tools/message_calibration_v1_0.py` (`HAIOS-TOOL-088`) is **not** covered by this ruling and
remains an open Z2 item.

---

## Gap noted while recording this

`.z1-control/ratify.py` computes a real sha256 signature, but only for **candidate blocks**
(`q_id`). A tool's Zone 2/3 claim has no equivalent, so this ruling's hash is a human-readable slug
in the style of `Z2_RULINGS_2026-09-08.md`, not a content-pinned sha256, and nothing recomputes it.

Recording that observation was not enough. As first written, the validator checked `ratified_by`
for *presence only* — and Z1 writes the manifest, so any typed string would have passed. That is
the same self-grant the rule exists to prevent, one field over. Review caught it.

So `verify_ratification` in `.tool-control/validate.py` now requires the hash to resolve:
a `ratification_ruling` path under `z1-inbox/` that exists and contains **both** the hash and the
tool's path. Not a signature — the repo has no Z2 key — but a claim a reviewer can read, and one
that costs a CODEOWNER-reviewed document to fabricate.

Still open: extending `ratify.py` to sign tool-zone rulings the way it signs candidate blocks, at
which point this entry should be re-pinned to a content hash and the check should recompute it. That
is its own change, and was not what Z2 was asked to decide.
