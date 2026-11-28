# Witness × Buffer P1-B1 — independently recomputed Gmail message digests

**Status:** Z1 evidence packet / proposed; not admitted, merged, independently counter-signed, or public-release authority.
**Case:** WITNESS-X-20261109-P1B1
**Coordination:** [operations issue #1161](https://github.com/humanaios-ui/operations/issues/1161)
**Date of recomputation:** 2026-11-10
**Authority effect:** NONE.

## What was measured

During a private connected-Gmail read, a reviewer fetched each selected message through Gmail's message-read action with `include_raw_mime=true`. The provider returned a **raw RFC822 MIME Base64URL payload**. The reviewer decoded this payload to bytes *without text normalization or re-encoding*, and computed SHA-256 across the complete byte sequence. The SHA-256 implementation was checked against the standard known `abc` test vector (`ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad`).

Only source class, count, and cryptographic digest are committed here. The full private MIME, message IDs, account addresses, thread links, Buffer IDs, and source email text are **not** committed. The authenticated Gmail evidence mapping and detailed Buffer state remain in the private operator email branch.

| Private source class | Raw RFC822 byte count | SHA-256 (hex) |
| --- | ---: | --- |
| P1-B1 private email receipt | 18,739 | `804c34f9f31e56071ec0335e8a6fa094db3b493429e4975d276ee7bb8a0136d2` |
| Original private handoff branch message | 11,213 | `dcd389311dc6cd30afe5368e5dd08ebe476983db235f1d911372e0d80ba5db98` |
| November 9 Grok notification email | 31,127 | `1bef074b972aadb7a9ca5a03c1ac8a7b023fb0d7eb34761760bfe2fef180a3f6` |
| November 9 HumanAIOS Daily Digest email | 21,102 | `64d0ffc810ce7c6c7ad11cf072314e897b8641aeb1922e14e50bb745a2decd84` |

## Verification boundaries

- **Directly computed:** SHA-256 digests and byte lengths of Gmail-provided **email MIME** data. This is stronger than repeating a model's claimed digest, but it is not an independent trust anchor for the Gmail service itself.
- **Not computed:** Original Buffer draft bytes, post ID/provider write receipt, Grok's complete daily ten-story output beyond its notification email, or a Google Drive receipt. An email digest is not a Buffer digest.
- **Grok-reported, not independently tested in this session:** one synthetic Buffer X draft existed after the P1-B1 write, queue count 0, no reported scheduled post. Pre-write atomic baseline and complete sent history are missing. See issue #1161 and the private email branch.
- **No promotion:** These hashes are byte identity anchors, not proof that content is true, a model is ACAT-calibrated, or the public should see it.
- **Release gates:** P1-B1 remains provisionally passed on reported provider data. P2 evidence and ACAT/CIVIC checks HOLD. P3 scheduling/publication HOLD. No agent may use this file to authorize Buffer posting.

## Repeatability / falsifier

Given the same private original raw Gmail MIME bytes, any independent reviewer can recompute SHA-256 and compare to this table. Mismatch must be reported as `RECOMPUTE_MISMATCH`; do not silently normalize line endings, decode MIME text parts instead of the raw message, or overwrite this historical observation. Version a distinct observation if the provider later returns different bytes.

**Private next experiment:** write a minimal versioned Gmail→Drive receipt, read it back, confirm its access scope and exact content, reject a duplicate source-message identity, and reply inside the private email handoff thread. This document does **not** grant that workflow ongoing automation rights or public access.
