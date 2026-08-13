# Defect Memo: acat_document_analyzer_v1_2.py

**Date:** 2026-07-16  
**Status:** ARCHIVED (DO NOT USE)  
**Filed by:** empirica-autonomy (Priority 1 — Critical Defect Fix)

---

## Problem

File: `acat_document_analyzer_v1_2.py` (now archived as `acat_document_analyzer_v1_2_ARCHIVED_2026-07-16.py`)

### Defects Found
1. **Quote Encoding Error (BLOCKING)**
   - 527 instances of curly quotes (U+201C/U+201D) instead of ASCII quotes
   - Location: Primarily in docstrings and string literals
   - Result: `SyntaxError: invalid character '"' (U+201C)` at line 2

2. **Indentation Corruption (BLOCKING)**
   - Multiple function and class definitions have incorrect indentation
   - Prevents file from being parsed even after quote fix
   - Example: `pass` statement in `SpecLoadFailed` class definition (line 358) has no indentation

3. **Version Confusion (MEDIUM)**
   - Filename: `acat_document_analyzer_v1_2.py`
   - Internal header: Claims `v1.3` and references `ACAT_DOCUMENT_ANALYZER_V1_3_SPEC.md`
   - Status: `v1.3` spec not confirmed as Z2-ratified

---

## Current State (SAFE ✅)

**GOVERNANCE.md P30 (Calibration Ratification Gate)** correctly references:
- `acat_document_analyzer_v1.1` (bare-named file)
- This version works correctly and parses without errors
- Production gate is **NOT BLOCKED**

---

## Root Cause

The v1.2 file appears to be an incomplete work-in-progress draft that was:
- Never completed
- Never tested
- Never integrated into the production toolchain
- Contains aspirational v1.3 changes that were left in a broken state

---

## Resolution

✅ **ARCHIVED:** File renamed to `acat_document_analyzer_v1_2_ARCHIVED_2026-07-16.py`

- Added prominent "DO NOT USE" warning header
- Clear filename suffix prevents accidental usage
- P30 continues to use v1.1 (which works)

---

## Recommendations

1. **Do NOT attempt to repair v1.2** — the structural issues suggest deep problems
2. **If v1.3 is needed**, develop cleanly from a fresh working copy of v1.1
3. **Keep v1.1 as canonical** until v1.3 is fully implemented and tested
4. **Document any v1.3 migration plan** in GOVERNANCE.md when ready

---

## Evidence

- **v1.1 Parse Status:** ✅ Compiles successfully
- **v1.2 Parse Status:** ❌ Multiple SyntaxErrors (quote encoding + indentation)
- **v1.2 Production Usage:** Not used by P30 (P30 references v1.1)

---

**Closed:** 2026-07-16 | **Next Review:** When v1.3 specification is finalized
