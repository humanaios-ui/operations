# INTENT-OS × Resource Miner Capability Reflex E0 (Z1 draft)

Purpose: bounded read-only capability routing, graph observation projection and explicit Witness evidence gaps. No production wiring, graph authority, source mutation, execution or admission.

Run:
```
python3 -m unittest discover -s tests -p 'test_intent_os_capability_reflex_e0.py' -v
python3 tools/intent_os_capability_reflex_e0.py --input /tmp/reflex-input.json
```

Input example:
```json
{"objective":"Find a verified training opportunity","available":["resource_discovery"],"graphs":{"system":{"source_ref":"system_graph.json","revision":"PIN_EXACT_COMMIT_HERE"}},"claims":[{"state":"UNVERIFIED","source_ref":"source:example","revision":"snapshot-1"}]}
```

This pilot intentionally does not import optional Inspect AI, invoke Resource Miner, or parse canonical graph files. Its capability catalog lists intended adapters, **not verified executable availability**. Availability is caller-declared and must not be treated as an authenticated runtime result.

Next gates: (1) validate exact-head tests; (2) read-only real Resource Miner adapter using existing candidate types; (3) source-pinned graph adapters for #630/#835/#841 without mixing trust; (4) frozen Inspect AI evaluation, including prompt injection and false-verified controls; (5) compare 20 cases to baseline with a distinct reviewer; (6) record independently witnessed completed human objectives. No claims of human outcomes before receipts.

Related: #822, #928, #896, #1040, #1041, #1042, #821. Do not merge or deploy without Coordinator and human review.
