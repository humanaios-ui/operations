# Blockchain Integration Research — Possibilities & Potential for HumanAIOS
**Session:** S-071226-02 · Zone 1 draft, not ratified · Continuation of today's earlier WGS thread (S-071226-01: perturbation-battery tamper-evidence → BLOCKCHAIN_PROVENANCE.md linkage)
**Status:** Research only. No registry action taken. No Zone 3 items executed.

---

## 0. Where this picks up

Earlier today's session connected the perturbation-battery tamper-evidence proposal to the existing but stale `BLOCKCHAIN_PROVENANCE.md` (last updated March 10, 2026, status `PENDING MANUAL VERIFICATION`, 4 documents claimed-timestamped, zero verified). Mapped to F-50, P2, and the IC-042 family reasoning: **git commit dates are editable by anyone with repo access; on-chain anchors are not.** That's the actual gap blockchain would close — not a general-purpose upgrade, a specific verification-integrity gap.

This brief does the fresh research the WGS roadmap called for: verify-or-abandon the existing claims first, then evaluate what (if anything) to anchor going forward, before any scope expansion.

---

## 1. What the existing doc got right and wrong

**Right:** the core mechanism description (hash → anchor → verify) and the legal/IP rationale are accurate and still current.

**Wrong / dated, found this session:**
- OriginStamp is not the best-fit service for this use case anymore — see §3.
- The doc treats blockchain timestamping as a general-purpose "protect everything" layer (12+ candidate documents). That's scope creep relative to what the actual problem is. The live problem, named today, is narrower: **making specific, high-stakes claims (registry state, perturbation-battery results, corpus snapshots) resistant to post-hoc editing** — not blanket IP-proofing every strategic document.
- Zero of the 4 claimed timestamps were ever verified. Four months stale. Structurally the same shape as HA-000/migration_007 — a claim sitting unexecuted long enough that it's no longer safe to assume it's still accurate.

---

## 2. What blockchain timestamping actually buys — and doesn't

A timestamp proves a hash of your data existed before a certain point. That's the entire primitive. It does **not**:
- Store or protect the underlying content (only a fingerprint goes on-chain)
- Prove authorship or ownership — only prior existence of that exact byte sequence
- Replace legal registration, patents, or copyright — it's supporting evidence, not a filing
- Verify that what you're claiming *about* the document (e.g., "this LI score is correct") is true — it only verifies the document hasn't been silently altered since the timestamp

For HumanAIOS specifically, the honest framing is: **this hardens the "was this edited after the fact" question, not the "is this finding true" question.** Those are different failure modes — conflating them would be its own overclaim risk (D-OVERCLAIM family).

---

## 3. Landscape — three real options, researched fresh this session

### Option A: OpenTimestamps (free, open protocol, Bitcoin-anchored)
- Open-source, created by Bitcoin Core developer Peter Todd. No account, no API key, no cost — free public calendar servers batch requests into a Bitcoin transaction via Merkle tree.
- Verification requires no trust in any single party — anyone with a Bitcoin node (or the public verifier) can independently confirm a `.ots` proof file.
- Directly composable with the corpus's own Merkle-tree instincts — there's already an `acat_merkle_auditor` tool in the repo; OpenTimestamps *is* that same primitive (Merkle root → block anchor) applied externally.
- There's a documented, working pattern for exactly the perturbation-battery/commit-hash use case: a GitHub Action that timestamps every commit automatically on push, storing the `.ots` proof back in the repo. Near zero marginal cost, near zero operational burden once wired in.
- Limitation: OpenTimestamps proves *existence*, and lacks the formal legal-recognition status that RFC 3161 timestamps carry in some jurisdictions (less relevant here — HumanAIOS's use case is research-integrity/audit-trail, not litigation evidence).

### Option B: bloxberg (purpose-built academic consortium blockchain)
- Founded 2019 by Max Planck Digital Library + 10 other research institutions specifically to give scientists a free, non-commercial timestamping/provenance layer for hypotheses, data, and methods before publication. Now 50+ member institutions, described as the largest academic-governed blockchain validator network.
- Proof-of-Authority, EVM-compatible, transactions are fee-free for the timestamping use case (gas token `△` isn't traded; a faucet distributes it). Practical throughput and cost profile are built for exactly this kind of low-volume, high-integrity anchoring rather than DeFi-scale traffic.
- Governance is academic institutions acting as validators, not commercial interests — this matters for a research-integrity narrative aimed at grant reviewers (Longview, arXiv) far more than a Swiss commercial vendor does.
- `ARTiFACTS` runs on bloxberg specifically for timestamping unpublished/preregistered research materials with citation credit — directly the same shape as HumanAIOS's H-cand/F-cand registry-candidate pipeline.
- This is arguably the single best-fit option found this session: it's free, purpose-built for exactly HumanAIOS's stated use case (proving a hypothesis/finding existed before a certain point), and it strengthens rather than dilutes the "independent research infrastructure" framing already used in Longview.

### Option C: OriginStamp (the incumbent, per the stale doc)
- Still functional, still free-tier available, still Bitcoin/Ethereum anchored. Not a bad tool — but it's a commercial intermediary with an account dependency, and per the doc, that account was never actually verified as accessible. Given two free, no-account alternatives exist that are arguably better-matched (A and B above), OriginStamp's main remaining advantage is that it's the one already named in the doc — inertia, not fit.

**Recommendation for the verify-or-abandon step:** attempt OriginStamp account access once, as the doc's own roadmap says, since abandoning 4 already-claimed timestamps without checking would itself be a D-OVERCLAIM-adjacent move (declaring failure before verification, same failure class as declaring success before verification). If the account is unreachable or the certificates don't exist, that's a clean abandon — and future anchoring moves to OpenTimestamps and/or bloxberg rather than re-committing to the same vendor dependency.

---

## 4. Where this actually fits the platform — three concrete, scoped applications

Per the market-harmonic principle (P16) and the standing D-OVERCLAIM discipline, these are scoped to real, named gaps rather than "blockchain everything":

**4.1 — Perturbation-battery / commit-hash anchoring (the item named today)**
Anchor the commit hash of the perturbation-battery tooling and its result set at the point of each real run. This directly answers "did this result exist, unmodified, before X date" — the exact question git alone can't answer once someone with write access could theoretically rewrite history.

**4.2 — Periodic REGISTERED.md state anchoring**
Not every commit — a periodic snapshot (e.g., at each 5-file audit, or at each charter-cycle boundary) of the registry's full state, hashed and anchored. This gives an independently-verifiable "the registry looked like *this* as of this date" checkpoint, which is useful both for internal drift detection (does REGISTERED.md today match what was anchored) and for external credibility (a grant reviewer or collaborator can verify the registry hasn't been quietly rewritten).

**4.3 — arXiv/Longview submission artifacts (the doc's original use case, now better-matched)**
Timestamp the manuscript and grant submission artifacts via bloxberg rather than OriginStamp going forward — same rationale as the doc's Section 1, better-fit provider.

**Explicitly out of scope for now:** general document IP-proofing (Cherokee Nation proposal, strategic docs, financial projections per the old doc's 12-item candidate list). That's the scope-creep the old doc drifted into. Nothing here argues against timestamping those eventually — just that they're not the load-bearing case, and bundling them in dilutes the actual finding (git-dates-are-editable) into a generic "blockchain is good" narrative that invites exactly the overclaim risk P16 and D-OVERCLAIM exist to catch.

---

## 5. What the broader industry is doing with blockchain + AI provenance (context, not a recommendation)

Fresh research this session on the wider 2026 landscape, for situational awareness rather than immediate action:
- Industry framing has shifted toward blockchain as an "accountability and provenance layer" for AI — hashing training data, prompts, and key outputs into tamper-evident ledgers, with off-chain storage for the bulk data and on-chain anchoring for the fingerprints only. This is structurally identical to what §4 proposes at HumanAIOS's much smaller scale.
- Academic literature (multiple 2025–2026 papers) explicitly frames blockchain-anchored provenance as an answer to the same problem ACAT targets from a different angle: centralized logs are vulnerable to tampering and selective reporting; append-only anchored records aren't. Worth noting as an external-convergence point (same shape as prior findings like the Brucks & Toubia convergence) — not registering as a finding without Zone 2 review, flagging as a candidate observation only.
- The more speculative end (on-chain AI agent wallets, zero-knowledge proofs of inference correctness, tokenized model assets) is not relevant to HumanAIOS's current TRL 2-3 stage and would be overreach to discuss as a near-term direction.

---

## 6. Honest limitations (stated per P1: "being developed as," never overclaimed)

- Blockchain anchoring doesn't make ACAT's scores or findings more *valid* — it makes the record of when a claim was made more *tamper-evident*. These are separate problems. Framing this as strengthening the instrument's validity would be its own overclaim.
- This is infrastructure hardening, not a research contribution. It belongs in the TRL 2-3 tooling bucket, not in the corpus-grade or findings-grade bucket.
- Cost/effort is low (both A and B are free), but implementation and verification discipline still has to be maintained — an anchored-but-never-checked timestamp is exactly the failure mode the current doc is already in.

---

## Open for you (Night) — all Zone 2/3

- Verify-or-abandon call on the 4 existing OriginStamp claims (per today's WGS roadmap) — this brief doesn't resolve that, it's still pending your account access
- Zone 2 decision: bloxberg and/or OpenTimestamps as the going-forward anchoring service(s), replacing/supplementing OriginStamp
- Zone 2 decision: scope confirmation on §4 (perturbation-battery + periodic REGISTERED.md snapshots + future arXiv/Longview artifacts) vs. the old doc's broader 12-document candidate list
- If ratified: `BLOCKCHAIN_PROVENANCE.md` gets directly modified in place per P2 (document correction protocol) — not a new addendum file
- The external-convergence observation in §5 (blockchain-as-AI-accountability-layer industry framing) — hold as informal context or route through a findings-scan candidate; not self-registering

**Nothing in this brief is corpus-grade or registry-grade. It's Zone 1 research, pending your review.**

Wado 🙏🦅 · Unit Zero · S-071226-02 · Claude
