# SKILL: elicitation_surface_scanner

## 1. Description

**What does this tool do?**
Scans known ACAT data-collection surfaces (MCP wrappers, corpus connectors, intake schemas, homepage prompts) and reports whether each agrees with the canonical 12-dimension schema and with each other. Distinguishes intentional legacy-schema surfaces (the frozen CSV archive) from drifted ones (a live-schema surface that's missing dimensions it should have).

---

## 2. Purpose

**Why does this tool exist?**
Every place the project collects ACAT data is an elicitation surface. If two surfaces disagree on dimension count, field names, or purity/variant tagging, the corpus silently accumulates non-equivalent rows (H-ELICIT-01 / F-52 territory) without anyone deciding that should happen. This tool turns that into something checked on every push instead of caught by chance in a chat session — see `workflows/haios_audit.yml`, step "A2 — Elicitation surface consistency."

---

## 3. Parameters and Inputs

| Parameter Name | Type | Required | Default Value | Description |
|---|---|---|---|---|
| `--scan` | `string[]` | No (required unless `--smoke-test`) | `None` | File paths to scan. |
| `--json` | `boolean` | No | `false` | Emit JSON instead of text. |
| `--smoke-test` | `boolean` | No | `false` | Run the 3 built-in self-test cases; verifies the tool's own classifier before trusting its output. |

---

## 4. Known limitations (read before extending)

- Extractors are pattern-specific, not a general parser. Three exist today: assess.html-style JS dim arrays, `p1_`/`p3_`-prefixed JSON/dict keys, and Python list-literal constants. A new surface type returns `NO_SURFACE_DETECTED` or `UNRECOGNIZED` — that result is the signal to add one more extractor, not a failure.
- `CANONICAL_DIMENSIONS` is a frozen snapshot (dated in the file header), not a live connection. `fetch_live_schema()` exists but is not called by default.
- Does not check JSON Schema contracts (`acat/contracts/*.schema.json`) — those define API-payload shape (nested `scores` object, unprefixed keys), which is a different and equally real failure mode found in this same session (see REGISTERED.md IC batch, S-062326). Schema-contract checking is the clear next extractor to write.

---

## 5. Run it

```bash
python tools/elicitation_surface_scanner_v1.py --scan tools/acat_mcp_full_wrapper_v1.2.py acat/mcp/wrappers/acat_mcp_wrapper.py tools/supabase_corpus_connector_v1_0.py tools/corpus_integrity_validator.py
python tools/elicitation_surface_scanner_v1.py --smoke-test
```
