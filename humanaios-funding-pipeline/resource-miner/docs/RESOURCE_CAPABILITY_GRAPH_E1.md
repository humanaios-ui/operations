# Resource-to-Capability Graph E1 — local, bounded extension

**State:** Z1 DRAFT / REVIEW ONLY. Authority NONE. Execution DISABLED.
Related: operations #588 (Resource System), #1091 (resource classifications),
#1143 (ratified product-first baseline), #979 (Opportunity Journeys),
#1002 (controlled source correction), and #928 (measured user benefit).

## Why this is an extension, not another platform

E1 adds a small graph panel to the already-existing local `/pathways` page.
The main `/intent-os` page exposes a link only when local `/pathways`
responds successfully. The graph reuses the existing `/api/pathways` response,
existing seven `need_id` values, existing source/evidence boundaries, and
stored/public refresh buttons. It adds **no** endpoint, separate graph database,
profile import, action queue, network adapter, agent activation, credential use,
GitHub write path, or permission expansion.

The only server-side data addition is `resource_types`, strictly limited to
declared public mechanism vocabulary. It is not guessed from a title and is
never a claim of eligibility, legitimacy, control, or current availability.

## Bounded behavior

Four hard-coded, **synthetic** public capability examples map to subsets of
already-established *resource needs*. This is a proposed preparation map,
**not a judgment that any person has that skill**.

For each example, E1 reads candidate records that carry an explicit Miner
`need_matches[].need_id` edge, groups candidates only by machine-readable
`resource_types`, and displays at most 11, round-robin across categories.
Resource candidates without explicit matching needs cannot appear on that
path. Empty results mean a bounded source observation was empty, not that the
user has no entitlement or that there are no opportunities.

The graphic displays four stages:

```
SYNTHETIC CAPABILITY --HYPOTHESIS--> EXISTING NEED
EXISTING NEED --MINER RELEVANCE--> SOURCE OBSERVATION
SOURCE OBSERVATION --NOT EARNED--> POSSIBLE PORTFOLIO PROOF
```

All edges are dashed; source date and human verification gate remain visible.
No market-growth prediction, current opening, program eligibility, accepted
application, grant award, credit transfer, certification, or earnings is asserted.
`source_url` comes from the existing Pathways URL checker; E1 additionally
withholds query/fragment URLs from its outbound hyperlink.

## Privacy and approval

The synthetic examples do **not** read real transcripts, tribal documents,
resume contents, private claim YAML, email, authentication, browser storage or
user account data. A public repository change must never include them.

The pre-existing loopback+peer+Host+Origin control still guards `/pathways`
and `/api/pathways`. E1 has no submission/export or write control. Keeping
the user-specific proof in the owner's private approved evidence store is a
*separate future decision*, not implicitly admitted by this patch.

## Acceptance and falsification

1. Re-run `python -m unittest tests.test_resource_capability_graph_e1`
   from the resource-miner root and existing pathway/UI tests.
2. Check exact-head CI. Separate inherited ACAT-R six regressions from new
   E1 failures; a red full suite is a merge hold, even if E1 cases pass.
3. Open `/intent-os` on permitted local loopback; follow the guarded
   "Capability paths E1" link. It must be absent on public/hosted bind.
4. On `/pathways#capabilityE1`, switch four synthetic capability examples
   and stored/public modes. Check explicit need matches, real source
   links, type diversity, source dates, and evidence gaps.
5. Falsifiers: source title alone invents category; stale link appears verified;
   candidate implies the operator possesses a capability; secret in JSON/DOM;
   host bypasses local gate; any graph interaction creates or updates state.
6. A follow-up five-session comparison against manual research must measure
   elapsed time, relevant candidates, incorrect eligibility claims, review
   effort, and human-approved **verified** benefits. Do not claim E1 helps
   users until those observations exist.

## Operational boundary

The existing daily Resource Miner Scan remains blocked by ACAT-R test failures
at inspection time (2026-11-18). E1 must not quietly heal, suppress or bypass
that workstream. This branch is for independent review; no merge or deployment.

## Philosophy-to-evidence interpretation (human-directed)

The optional **Witness interpretation lens** is an attributed analogy, not a scientific, personal-belief, eligibility or market-growth determination. See [research note](../../../docs/research/MENTALISM_INTENT_ACTION_E0.md) for the 1908 `Kybalion` source and disputed historical framing.

- **BELIEF / ATTRIBUTED PHILOSOPHY:** `The Kybalion` presents Mentalism; we make no assertion that thought creates external outcomes.
- **HYPOTHESIS:** A synthetic existing capability might connect to an observed opportunity via an explicit Resource Miner need match. No person has been assessed.
- **ACTION / PROPOSED:** A human may choose to verify a provider's terms. E1 has no execution endpoint.
- **OBSERVED RESULT / NOT ESTABLISHED:** A source candidate can be observed while any benefit, award, completed task, grant, credential, or client outcome remains unverified.

This is deterministic UI text, not a Witness model invocation. It adds no data capture or scoring rules. The conditions in this section do not approve implementation, admission or live deployment.
