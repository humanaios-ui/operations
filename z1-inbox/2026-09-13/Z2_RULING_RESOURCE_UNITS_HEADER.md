# Z2 Ruling — 2026-09-13

Ratification of the `RESOURCE_UNITS.yaml` header correction, and the state of its hash.

## Ruling: `RESOURCE_UNITS.yaml` lines 3-4 — RATIFIED

**Decision by:** Night (Z2 / Admiral)
**Given:** 2026-09-13, in session `016hAX9tLuggZumWsrPKYc5L`, verbatim:
*"I ratify RESOURCE_UNITS.yaml:3-4 and submit hash, fix both properly in a separate PR"*
**Recorded by:** Claude (Z1), as transcription. Z1 did not make this call.

After `6a4a6c6` set `status: RATIFIED`, the file's own header still read:

> `# Status: CANDIDATE. Z1 proposes; Z2 ratifies (CLAUDE.md → Decision Routing).`
> `# Nothing in this file takes effect until` `ratification_hash` `is non-null.`

A ratified registry announcing itself as an inert candidate. The header is corrected to state
RATIFIED, and `test_header_comment_agrees_with_the_status_field` now fails if the header and the
`status:` field ever disagree again — so this particular drift cannot recur silently.

---

## The hash: what Z1 did NOT do, and why

Z2 also said "submit hash." **Z1 did not mint one**, and this section records the reason rather
than quietly doing it.

`.z1-control/ratify.py` states the rule in its own docstring:

> *"If Z1 wrote the ruling file, computed the hash, and set the status in one pass, it would satisfy
> all three while proving nothing — Copilot raised exactly this on PR #308 and the answer was that
> CI cannot authenticate Z2. So: you run it, the commit is yours."*

Computing the digest is mechanical; **running the command is the Z2 act, and the commit author is
the signature's provenance.** Z1 producing it would reproduce precisely the self-grant that PR #314
exists to close, one artifact over.

### What was found

The recorded hash verifies against nothing. Tested exhaustively:

| construction | result |
|:---|:---|
| `sha256` of file bytes | no match |
| `sha256` with `ratification_hash` nulled | no match |
| `sha256` of canonical YAML / canonical JSON | no match |
| `sha256` of the `units:` section alone | no match |
| `ratify.py`'s own `sha256(content \| by= \| at= \| decision=)` | no match |

`b6b8233dd06400f565e5e21286cc0fec65a71472adfa1ebb98045f2dfaeff2a2` is 64 hex characters that
resolve to no construction over this artifact — the same class of value as the 2026-09-08 slugs,
but harder to spot because it is shaped like a real digest.

### What was built instead

`ratify.py` gained artifact ratification, so a registry *can* now be signed and verified:

```
python3 .z1-control/ratify.py --artifact RESOURCE_UNITS.yaml --decision ACCEPT --by Night --apply
python3 .z1-control/ratify.py --verify-artifact RESOURCE_UNITS.yaml
```

The payload is the parsed document with the five ratification fields excluded, serialised
canonically. That exclusion is forced, not convenient: a hash covering `ratification_hash` could
never verify, because writing the digest into the file changes the content it was taken over.
Change a unit, a policy or a prior and the signature breaks; fix a comment and it does not.

`--verify-artifact` reports the current state honestly:

```
!! RESOURCE_UNITS.yaml: SIGNATURE MISMATCH
     recorded   b6b8233dd06400f565e5e21286cc0fec65a71472adfa1ebb98045f2dfaeff2a2
     recomputed be5358fa06864ce3461fc46932fa89ef07d199ecbc0f32e405a074803210d737
```

### The open item

`test_resource_economics.py` carries `UNVERIFIED_ARTIFACT_RATIFICATIONS`, holding exactly one entry:
`RESOURCE_UNITS.yaml`. It is in CODE, under review, for the same reason `UNRATIFIED_ZONE_CLAIMS` is
— an exemption an artifact could grant itself by setting a field is not an exemption.

**It removes itself by being decided.** When Z2 runs the command above, the hash verifies, and the
test then **fails** while the entry remains listed:

> `"RESOURCE_UNITS.yaml now verifies — remove it from UNVERIFIED_ARTIFACT_RATIFICATIONS so the
> exemption cannot outlive its cause"`

Every artifact ratified after this one must verify. This is a one-entry list that cannot grow
without a reviewed change to the gate, and cannot persist once its cause is gone.

---

## Also in this change

Two tests on `main` asserted the pre-ratification state and had been red since `6a4a6c6`,
blocking every open PR that merged main:

- `test_registry_parses_and_declares_itself_candidate` — `assert 'RATIFIED' == 'CANDIDATE'`
- `test_genesis_pins_the_units_registry_hash` — `assert 'b6b8233d…' is None`

The first is replaced by three tests that assert the ratified state, that the hash is a sha256
rather than a slug, and that it verifies. The original test's *name* carried a real guarantee —
that the registry had not self-ratified — and simply flipping the expected string would have
dropped it; asserting the signature verifies is the stronger form of the same claim, which is what
Z2 asked for.

The second now asserts genesis pins the ratification the registry actually carries, rather than
that it carries none.
