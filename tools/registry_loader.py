"""
ACAT Registry Loader

Parses REGISTERED.md (the live, append-only findings registry) into
structured entries and computes the Validation funnel discussed in
S-061726 (Evidence-to-Advance / Validation Gate concept, mapped onto the
existing P21 / triage-gate / promotion_gate machinery rather than a new
biomedical-style pipeline).

This module is read-only with respect to REGISTERED.md. It does not write
findings, does not assign F/H/IC numbers, and does not modify the file.
It is the structural fix flagged two turns ago: REGISTRY_REFERENCE in
humility_audit_service.py was a hand-maintained, dated snapshot. This
module replaces that pattern with a parser run against the live document.

Three numbers, two of which are computable today from REGISTERED.md alone,
one of which requires the new acat_triage_log table (see
triage_log_service.py) to start accumulating rows:

- Advance Pass Rate    - NOT computable from REGISTERED.md. REGISTERED.md
  only contains observations that already passed
  the Q1-Q4 triage gate and were routed to Zone 2;
  per humanaios-triage-finding, anything that
  STOPped at triage goes to session notes, never
  to the registry. This number requires
  acat_triage_log to accumulate triage attempts
  going forward, including the STOPped ones.
  See triage_log_service.compute_advance_pass_rate().
- Validation Pass Rate - computable today: (REGISTERED + CONFIRMED) /
  (REGISTERED + CONFIRMED + CANDIDATE +
  PENDING_ZONE2), restricted to F/H classes.
  IC entries are always REGISTERED at registration
  time (error + fix both already happened by
  definition) and are reported separately, not
  folded into this ratio.
- Validation Collapse  - the complement of the above, plus a named list
  Rate                    of specific stale candidates (this is your CCI,
  applied to your own findings instead of a
  foreign domain): F/H entries sitting at
  CANDIDATE/PENDING_ZONE2 with their actual
  promotion_gate text and (where N>=X is
  parseable) the numeric target.

Real-document complications this parser was built and tested against
(REGISTERED.md is not a clean spec - see the verification pass before this
file was written):

- YAML frontmatter is sometimes inside a ``` fence, sometimes bare.
- Some entries (H-1, H-42, H-LE-02) are one-line pointers with no body -
  excluded as STUB_POINTER, not a parse failure.
- IC-038 uses an older bullet-style format ("- **Status:** REGISTERED")
  instead of YAML frontmatter, despite being dated after the 2026-05-08
  schema cutoff that the document's own header section says requires it
  - flagged as SCHEMA_COMPLIANCE_GAP, not silently parsed around.
- "### Entry header schema…" is the schema's own documentation section
  and contains a literal template entry (id: "F-XX") - excluded.
- H-APEX-DEFICIT-01 appears twice, verbatim, at two different line
  numbers - flagged as DUPLICATE_ID rather than silently double-counted
  or silently overwritten. (This is a real, previously-unflagged
  duplication in the live document, surfaced by writing this parser, not
  invented for the example.)
- Promotion criteria are not in the YAML; they're inline bold labels in
  the prose body ("**Promotion gate:**", "**Falsification design:**",
  "**Next gate:**") with no consistent position or bullet structure.
- Current-N for a given gate is NOT auto-extracted past a target. A naive
  "first N=<number> in the prose" approach was tested and produces wrong
  answers (F-48's gate is N>=3 independent datasets, but the first bare
  "N=" in its prose is the unrelated corpus size N=524 from a different
  sentence). Current N is therefore reported as None unless present in
  MANUALLY_VERIFIED_CURRENT_N below - entries I have actually read and
  confirmed by hand, with a citation, not regex-guessed.
  """
  from __future__ import annotations

import re
import ssl
from dataclasses import dataclass, field
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi

REGISTERED_MD_RAW_URL = (
"https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md"
)

SCHEMA_EFFECTIVE_DATE = "2026-05-08"  # per REGISTERED.md's own "Entry header schema" section

VALID_STATUSES = {
"CANDIDATE", "REGISTERED", "ACTIVE", "SUPERSEDED",
"CONFIRMED", "DISCONFIRMED", "PENDING_ZONE2",
}
VALIDATED_STATUSES = {"REGISTERED", "CONFIRMED"}
PENDING_STATUSES = {"CANDIDATE", "PENDING_ZONE2"}
RESOLVED_NEGATIVE_STATUSES = {"DISCONFIRMED"}  # P-RP-01's third gate state - a real outcome, not a gap
RETIRED_STATUSES = {"SUPERSEDED"}

FUNNEL_CLASSES = {"F", "H"}  # IC is always-REGISTERED by definition; reported separately, not in the ratio

# Entries verified by direct reading against REGISTERED.md (not regex-guessed)

# on the date noted. Re-verify whenever REGISTERED.md changes for these ids.

MANUALLY_VERIFIED_CURRENT_N = {
"F-49": {"current_n": 3, "verified_against_registered_md": "2026-06-17"},
"H-SELF-01": {"current_n": 1, "verified_against_registered_md": "2026-06-17"},
}

_HEADING_RE = re.compile(r"^### (.+)$", re.MULTILINE)
_YAML_BLOCK_RE = re.compile(r"-{3}\s*\n(.*?\n)-{3}", re.DOTALL)
_LEGACY_STATUS_RE = re.compile(r"(?:-\s*)?**Status:**\s*([A-Za-z*]+)")
_LEGACY_REGISTERED_DATE_RE = re.compile(r"(?:-\s*)?**Registered:**\s*([0-9]{4}-[0-9]{2}-[0-9]{2})")
_HONEST_GAP_RE = re.compile(r"(honest gap)", re.IGNORECASE)
_GATE_TARGET_RE = re.compile(r"N\s*(?:\u2265|>=)\s*(\d+)")
_GATE_TEXT_RE = re.compile(
r"**(Promotion gate|Falsification design|Next gate):**\s*(.+?)"
r"(?=**[A-Z][a-zA-Z ()]*:?**|\n\n|\Z)",
re.DOTALL,
)
_HEADING_ID_RE = re.compile(r"\b([A-Z]{1,2}(?:-[A-Z]+)?-[A-Z0-9]+(?:-\d+)?)\b")
_META_HEADING_PREFIXES = (
"Entry header schema",
"Document flow conventions",
"F-number registry quick index",
"Zone 2 --",
"Zone 2 -",
"P-IMPROVE class",
)

@dataclass
class RegistryEntry:
id: str
cls: Optional[str]
status: Optional[str]
date_registered: Optional[str]
schema_format: str  # "yaml" | "legacy_bullet"
gate_target_n: Optional[int]
gate_text: Optional[str]
raw_heading: str
line_no: Optional[int] = None

@dataclass
class ParseDiagnostics:
total_headings: int = 0
parsed_entries: int = 0
stub_pointers: list = field(default_factory=list)
intentional_voids: list = field(default_factory=list)
meta_sections_skipped: list = field(default_factory=list)
placeholder_skipped: list = field(default_factory=list)
schema_compliance_gaps: list = field(default_factory=list)
parse_failures: list = field(default_factory=list)
duplicate_ids: dict = field(default_factory=dict)

def _is_meta_heading(heading_text: str) -> bool:
return any(heading_text.startswith(p) for p in _META_HEADING_PREFIXES)

def _is_placeholder_id(id_value: str) -> bool:
# Template ids from the schema's own documentation section, e.g. "F-XX", "IC-XXX"
return "XX" in id_value

def _is_stub_pointer(body_after_heading: str) -> bool:
"""True if there's essentially nothing here but the heading line itself
(H-1, H-42, H-LE-02 style one-line cross-references)."""
stripped = body_after_heading.strip()
return len(stripped) < 5

def parse_registered_md(markdown_text: str) -> tuple[list[RegistryEntry], ParseDiagnostics]:
diagnostics = ParseDiagnostics()
entries: list[RegistryEntry] = []
seen_ids: dict[str, int] = {}

```
headings = [(m.start(), m.group(1)) for m in _HEADING_RE.finditer(markdown_text)]
diagnostics.total_headings = len(headings)

for i, (pos, heading_text) in enumerate(headings):
    end = headings[i + 1][0] if i + 1 < len(headings) else len(markdown_text)
    body = markdown_text[pos:end]
    line_no = markdown_text.count("\n", 0, pos) + 1

    if _is_meta_heading(heading_text):
        diagnostics.meta_sections_skipped.append(heading_text)
        continue

    body_after_heading = body[len(heading_text):]

    yaml_match = _YAML_BLOCK_RE.search(body)
    entry: Optional[RegistryEntry] = None

    if yaml_match:
        yaml_text = yaml_match.group(1)
        id_m = re.search(r'^id:\s*"?([^"\n]+)"?\s*$', yaml_text, re.MULTILINE)
        status_m = re.search(r"^status:\s*([A-Za-z_]+)", yaml_text, re.MULTILINE)
        class_m = re.search(r"^class:\s*([A-Za-z_]+)", yaml_text, re.MULTILINE)
        date_m = re.search(r'^date_registered:\s*"?([^"\n]+)"?\s*$', yaml_text, re.MULTILINE)

        if not id_m:
            diagnostics.parse_failures.append(
                {"heading": heading_text, "line": line_no, "reason": "YAML block present but no id field"}
            )
            continue

        id_value = id_m.group(1).strip()
        if _is_placeholder_id(id_value):
            diagnostics.placeholder_skipped.append(heading_text)
            continue

        prose = body[yaml_match.end():]
        gate_target_m = _GATE_TARGET_RE.search(prose)
        gate_text_m = _GATE_TEXT_RE.search(prose)

        entry = RegistryEntry(
            id=id_value,
            cls=class_m.group(1) if class_m else None,
            status=status_m.group(1) if status_m else None,
            date_registered=date_m.group(1).strip() if date_m else None,
            schema_format="yaml",
            gate_target_n=int(gate_target_m.group(1)) if gate_target_m else None,
            gate_text=re.sub(r"\s+", " ", gate_text_m.group(2)).strip() if gate_text_m else None,
            raw_heading=heading_text,
            line_no=line_no,
        )

    else:
        status_m = _LEGACY_STATUS_RE.search(body_after_heading)
        date_m = _LEGACY_REGISTERED_DATE_RE.search(body_after_heading)

        if status_m:
            id_m = _HEADING_ID_RE.search(heading_text)
            id_value = id_m.group(1) if id_m else heading_text.split(" ")[0]
            cls_guess = id_value.split("-")[0] if "-" in id_value else None
            entry = RegistryEntry(
                id=id_value,
                cls=cls_guess,
                status=status_m.group(1),
                date_registered=date_m.group(1) if date_m else None,
                schema_format="legacy_bullet",
                gate_target_n=None,
                gate_text=None,
                raw_heading=heading_text,
                line_no=line_no,
            )
            date_for_check = entry.date_registered or ""
            if date_for_check >= SCHEMA_EFFECTIVE_DATE:
                diagnostics.schema_compliance_gaps.append(
                    {
                        "id": id_value,
                        "heading": heading_text,
                        "line": line_no,
                        "reason": (
                            f"Dated {date_for_check} (after {SCHEMA_EFFECTIVE_DATE} schema "
                            "cutoff) but uses legacy bullet format, not the required YAML "
                            "frontmatter block."
                        ),
                    }
                )
        elif _is_stub_pointer(body_after_heading):
            diagnostics.stub_pointers.append(heading_text)
            continue
        elif _HONEST_GAP_RE.search(heading_text):
            diagnostics.intentional_voids.append(heading_text)
            continue
        else:
            diagnostics.parse_failures.append(
                {"heading": heading_text, "line": line_no, "reason": "No YAML block and no legacy status bullet found"}
            )
            continue

    if entry is None:
        continue

    if entry.id in seen_ids:
        diagnostics.duplicate_ids.setdefault(entry.id, [seen_ids[entry.id]]).append(line_no)
        continue  # keep first occurrence only; duplicate is flagged, not summed

    seen_ids[entry.id] = line_no
    entries.append(entry)
    diagnostics.parsed_entries += 1

return entries, diagnostics
```

def compute_validation_funnel(entries: list[RegistryEntry]) -> dict:
funnel_entries = [e for e in entries if e.cls in FUNNEL_CLASSES]
ic_entries = [e for e in entries if e.cls == "IC"]

```
validated = [e for e in funnel_entries if e.status in VALIDATED_STATUSES]
pending = [e for e in funnel_entries if e.status in PENDING_STATUSES]
disconfirmed = [e for e in funnel_entries if e.status in RESOLVED_NEGATIVE_STATUSES]
superseded = [e for e in funnel_entries if e.status in RETIRED_STATUSES]
active_steady_state = [e for e in funnel_entries if e.status == "ACTIVE"]
unknown_status = [e for e in funnel_entries if e.status not in VALID_STATUSES]

denom_pass_rate = len(validated) + len(pending)
validation_pass_rate = round(len(validated) / denom_pass_rate, 4) if denom_pass_rate else None
validation_collapse_rate = round(len(pending) / denom_pass_rate, 4) if denom_pass_rate else None

# Resolution rate counts BOTH confirmed and disconfirmed as "the gate reached
# a conclusion" (P-RP-01's three-state gate) -- distinct from pass rate,
# which only counts positive validation.
denom_resolution = len(validated) + len(disconfirmed) + len(pending)
validation_resolution_rate = (
    round((len(validated) + len(disconfirmed)) / denom_resolution, 4) if denom_resolution else None
)

stale_candidates = []
for e in sorted(pending, key=lambda x: x.id):
    verified = MANUALLY_VERIFIED_CURRENT_N.get(e.id)
    stale_candidates.append(
        {
            "id": e.id,
            "status": e.status,
            "gate_target_n": e.gate_target_n,
            "current_n": verified["current_n"] if verified else None,
            "current_n_source": (
                f"manually_verified ({verified['verified_against_registered_md']})"
                if verified
                else "not_extracted -- see gate_text"
            ),
            "gate_text": e.gate_text or "(no parseable promotion-gate sentence found in entry body)",
        }
    )

return {
    "validation_pass_rate": validation_pass_rate,
    "validation_collapse_rate": validation_collapse_rate,
    "validation_resolution_rate": validation_resolution_rate,
    "counts": {
        "validated": len(validated),
        "pending": len(pending),
        "disconfirmed": len(disconfirmed),
        "superseded": len(superseded),
        "active_steady_state": len(active_steady_state),
        "unknown_status": len(unknown_status),
        "f_h_total": len(funnel_entries),
        "ic_corrections_logged": len(ic_entries),
    },
    "stale_candidates": stale_candidates,
    "note": (
        "f_h_total excludes IC (always REGISTERED by definition -- reported "
        "separately) and excludes P-IMPROVE-class process carries (different "
        "lifecycle, not part of the F/H finding funnel). active_steady_state "
        "entries are reported but excluded from the pass/collapse ratio "
        "denominator since ACTIVE is a steady-state research thread, not a "
        "pending candidate awaiting a promotion gate."
    ),
}
```

def _ssl_context() -> ssl.SSLContext:
return ssl.create_default_context(cafile=certifi.where())

def fetch_registered_md_live(ref: str = "main") -> str:
"""Live fetch from GitHub raw - never cached. Matches the project's
standing instruction that REGISTERED.md is fetched live, not relied on
from project knowledge or a prior session's copy."""
url = REGISTERED_MD_RAW_URL.replace("/main/", f"/{ref}/")
request = Request(url, headers={"Accept": "text/plain"}, method="GET")
try:
with urlopen(request, timeout=15, context=_ssl_context()) as response:
return response.read().decode("utf-8")
except HTTPError as exc:
raise RuntimeError(f"REGISTERED.md fetch failed with HTTP {exc.code}") from exc
except URLError as exc:
raise RuntimeError(f"REGISTERED.md fetch connection failed: {exc}") from exc

def load_and_compute(markdown_text: Optional[str] = None) -> dict:
"""Top-level entry point. Pass markdown_text for testing against a local
copy; omit it to fetch REGISTERED.md live from GitHub."""
text = markdown_text if markdown_text is not None else fetch_registered_md_live()
entries, diagnostics = parse_registered_md(text)
funnel = compute_validation_funnel(entries)
return {
"funnel": funnel,
"diagnostics": {
"total_headings": diagnostics.total_headings,
"parsed_entries": diagnostics.parsed_entries,
"stub_pointers_excluded": diagnostics.stub_pointers,
"intentional_voids": diagnostics.intentional_voids,
"meta_sections_skipped": diagnostics.meta_sections_skipped,
"placeholder_entries_skipped": diagnostics.placeholder_skipped,
"schema_compliance_gaps": diagnostics.schema_compliance_gaps,
"parse_failures": diagnostics.parse_failures,
"duplicate_ids": diagnostics.duplicate_ids,
},
}

if __name__ == "__main__":
import json
import sys

```
path = sys.argv[1] if len(sys.argv) > 1 else None
text = open(path, encoding="utf-8").read() if path else None
result = load_and_compute(text)
print(json.dumps(result, indent=2))
```