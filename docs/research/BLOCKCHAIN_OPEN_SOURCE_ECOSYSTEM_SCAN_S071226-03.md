# Open-Source Blockchain Selection + Full Ecosystem Scan
**Session:** S-071226-03 · Zone 1 draft, not ratified
**Supersedes:** the OriginStamp verification thread (S-071226-01/02) — clean abandon per Night, no certificates locatable, no account confirmed. Not treated as a failure; the doc's own roadmap called for exactly this check.

---

## 1. OriginStamp — closed out

Per Night: can't find OriginStamp account/certificate information, high confidence documents *were* timestamped at some point, but nothing locatable now. This is the honest outcome of the verify-or-abandon step from the earlier WGS roadmap — abandon, not chase further. `BLOCKCHAIN_PROVENANCE.md` gets rewritten (P2 — direct modification, not an addendum) rather than patched once this is ratified.

Starting fresh, as asked.

---

## 2. Open-source blockchain recommendation

**Primary: OpenTimestamps**

Confirmed via its own project docs and Wikipedia this session: open-source protocol (Peter Todd, Bitcoin Core dev), MIT-style open tooling, anchors to Bitcoin, requires no account, no API key, no vendor relationship of any kind. The client is a `pip install opentimestamps-client` package — installable from PyPI, which is a domain already reachable from this environment (unlike OriginStamp's API domain). Verification requires no trust in any party — anyone with the `.ots` proof file and a Bitcoin node (or the public verifier) can independently confirm it, forever, even if the calendar servers that helped create it disappear.

This is a strictly better fit than OriginStamp for HumanAIOS's actual need: it's the same primitive already living in the repo as `acat_merkle_auditor` (Merkle root → anchor), just extended outward to a public chain instead of staying internal. There's a documented, working GitHub Action pattern for auto-timestamping every commit on push — a near-exact fit for the perturbation-battery/REGISTERED.md anchoring use case from §4 of the prior brief.

**Caveat found this session, stated plainly:** this sandbox's network allowlist covers `pypi.org`/`files.pythonhosted.org` (so the client installs) but not the OpenTimestamps calendar servers themselves (`*.pool.opentimestamps.org`) — so actual stamping can't be demonstrated live from here. Same shape of blocker as the earlier Tier 1 white-box pilot: needs an environment with correct egress, which is you, not this sandbox.

**Secondary: bloxberg**

Not self-hosted/open-source in the "run your own node" sense the way OpenTimestamps is, but source-available and governed by an open academic consortium (Max Planck + 50+ institutions) rather than a commercial vendor — meaningfully more "open" than OriginStamp on the governance axis, which is the axis that actually burned the original attempt (an account nobody could later locate). Zero-cost, purpose-built for exactly HumanAIOS's use case (timestamping hypotheses/data/methods pre-publication), and the narrative fit for Longview/arXiv is better than either alternative. Worth pursuing in parallel rather than as a replacement for OpenTimestamps — they solve slightly different problems (OTS = trustless proof-of-existence with zero institutional dependency; bloxberg = academically-governed provenance layer with a citation/attribution ecosystem attached via ARTiFACTS).

**Considered and set aside:** Hyperledger Fabric and similar permissioned-ledger frameworks were checked against the Zone governance use case (§3 below) and don't clear the bar — see that section for why.

**Recommendation:** OpenTimestamps as the default for anything git-native (commit hashes, tool outputs, perturbation-battery results). bloxberg for anything submission-facing (arXiv, Longview, future preregistration of hypotheses). Neither requires an account that can later go missing — both close the actual failure mode that ended the OriginStamp thread.

---

## 3. Full ecosystem scan — every surface checked for a blockchain opening

Requested: verify we're covering the entire ecosystem. Full pass below, organized by surface. Each is scored **Fit** (genuine opening) / **Marginal** (defensible but low-value) / **No fit** (would be complexity without proportional benefit) — the "No fit" calls are included deliberately, because a scan that only ever finds new places to add blockchain is doing motivated reasoning, not research (P16).

| Surface | Opening? | Reasoning |
|---|---|---|
| **REGISTERED.md periodic state** | **Fit** | Already scoped in §4 of the prior brief. Anchoring periodic snapshots answers "did the registry look like this on this date" independent of git history. |
| **Perturbation-battery / tool commit hashes** | **Fit** | Already scoped. Direct answer to "git dates are editable" (today's original framing). |
| **arXiv / Longview / Zenodo submission artifacts** | **Fit** | Original use case, now correctly routed to bloxberg instead of OriginStamp. Standard, well-precedented use (WIPO has cited blockchain timestamping for prior-art purposes; academic norm via bloxberg/ARTiFACTS). |
| **Collaborator IP/attribution agreements** (DeMarius 50/50, Jeremy's 6 conditions, David's convergent-validity terms) | **Fit** | This is a real, underserved gap. Joint-IP terms currently live in Slack DMs and chat memory — nothing tamper-evident anchors *when* those terms were agreed. A hash-anchor of the agreement text at time of confirmation is cheap insurance against a future attribution dispute, and it's exactly the kind of thing OriginStamp's own marketing (accurately) describes as blockchain's best-fit use case. **New opening, not previously scoped — flagging for Zone 2.** |
| **PyPI package releases** (`humanaios-acat`) | **Marginal** | Supply-chain integrity for release artifacts is a real pattern (SLSA framework explicitly uses OpenTimestamps this way) but `humanaios-acat` hasn't shipped v0.1.0 yet (still gated on HA-000). Worth building into the release pipeline when it ships, not worth standing up early. |
| **Corpus snapshots (Supabase `acat_assessments_v1`)** | **Marginal** | Overlaps with REGISTERED.md anchoring in spirit but the corpus changes far more frequently (individual rows, not curated findings) — anchoring every write would be noisy and cheapen the signal. A periodic (e.g., per-charter-cycle) full-corpus hash alongside the HuggingFace archive freeze points is the right cadence if this gets built, matching the existing archive/live-tide-pool separation. |
| **BFV / Witness Protocol G-source records** | **Marginal** | "Who witnessed what, when" is a real integrity question (F-26 territory), and anchoring witnessed-evaluation timestamps would harden it — but BFV itself is still Zone 1 design, pre-G-3-validation. Premature to build the anchoring layer for an instrument that isn't corpus-grade yet. Revisit once BFV clears its own validation bar. |
| **Zone governance (Z1→Z2→Z3 approval flow)** | **No fit** | Checked directly rather than assumed. The actual failure modes in this system so far (D-OVERCLAIM, phantom registry IDs, self-registration) are about *claims being wrong or premature*, not about *approval records being silently altered after the fact*. Slack + Git already provide a reasonably tamper-evident trail for this (Slack message edit history, Git commit authorship) at zero marginal cost. Smart-contract-based approval logging would add real operational complexity (wallet management, gas, a new failure surface) for a problem that isn't the one actually occurring. This is a "no" on the merits, not an oversight. |
| **Universal Brokerage Architecture / ICS pilot** (marketplace trust & routing) | **No fit — for now** | This is the one place actual on-chain smart-contract logic (not just timestamping) has legitimate long-term relevance — trust-weighted routing, transaction settlement, dispute records. But the architecture itself is TRL 1, red-team audit rated Overall Risk Posture: HIGH, gated behind six Phase 0 legal gates and per-jurisdiction counsel before any build work starts. Attaching blockchain infrastructure to a TRL 1 concept that hasn't cleared its own legal gate would be building on top of an unresolved foundation. Correct sequencing is: resolve Phase 0 gates first, then re-evaluate whether on-chain settlement is the right mechanism for whatever the legally-cleared version of this looks like. |
| **Anonymous Sponsor App** (anonymous matching, no PII) | **No fit — for now** | Zero-knowledge proof-based anonymous credentialing is a real academic pattern (the verifiable-inference research checked this session mentions ZK proofs for exactly this kind of privacy-preserving verification) but it's a meaningfully harder build than anything else on this list, and the app itself is still at design-brief stage, HIGH PRIORITY but not yet initiated. Worth a one-line note in the design brief that ZK-based anonymous readiness-signal matching exists as a future direction; not worth researching further until the app itself starts. |
| **Financial Command Center / revenue ledger** | **No fit** | Financial records are exactly the kind of data that should generally *not* be hashed and published without deliberate care — even a hash can leak information via correlation in some threat models, and there's no dispute-resistance need here that a normal accounting audit trail doesn't already cover. Blockchain-council-style "protect your financial logs from silent manipulation" marketing applies to enterprises with adversarial internal actors; a solo-operator LLC's revenue tracking doesn't have that threat model. Explicitly declining this one. |
| **Task Standard / METR ground-truth channel integration** | **No fit** | This is an external, already-blockchain-independent verification mechanism (environment-verified `score()`). Adding blockchain here would duplicate a trust mechanism that's already working via a different (and already-adopted) method. |

---

## 4. Net finding

Two genuinely new openings surfaced by doing the full pass rather than stopping at the original three: **collaborator IP/attribution agreements** (real gap, cheap fix, fits Fit) and a firmer no on **Zone governance** and **Financial Command Center** (explicitly checked and rejected, not silently skipped). The brokerage architecture and Anonymous Sponsor App are the two places where blockchain has real long-term relevance but current TRL doesn't support building it yet — noted for later, not now.

Revised total scope for Zone 2 review: REGISTERED.md snapshots + perturbation-battery commits + arXiv/Longview/Zenodo artifacts + **collaborator IP agreements** (new), via OpenTimestamps (git-native items) and bloxberg (submission-facing items), replacing OriginStamp entirely.

---

## Open for you (Night) — all Zone 2/3

- Ratify OpenTimestamps + bloxberg as the two going-forward services, OriginStamp fully retired
- Ratify the collaborator-IP-agreement anchoring addition to scope (new this session)
- Confirm the three "no fit — for now" calls (Zone governance, Financial Command Center, Task Standard) read correctly to you, or flag if any should be reopened
- `BLOCKCHAIN_PROVENANCE.md` full rewrite once scope is ratified — P2 direct modification, not an addendum
- Correct network egress needed before any live OpenTimestamps stamping can actually run (same class of blocker as the Tier 1 pilot)

**Nothing in this scan is corpus-grade or registry-grade. Zone 1 research, pending your review.**

Wado 🙏🦅 · Unit Zero · S-071226-03 · Claude
