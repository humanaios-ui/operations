# SKILL: humanaios-core-architecture-pattern

## ⚠️ DEPRECATED

**Status:** DEPRECATED  
**Deprecated in session:** S-061526  
**Deprecation ratified:** Z2 · June 15, 2026  
**Superseded by:** [`humanaios-dual-architecture`](../../humanaios-dual-architecture/SKILL.md) v1.3  

---

## Reason for Deprecation

`humanaios-core-architecture-pattern` has been superseded by `humanaios-dual-architecture` v1.3, which was Z2-ratified in session S-061526 as the canonical meta-spec for HAIOS system architecture. The dual-architecture skill incorporates all prior functionality with updated Zone system enforcement, EXEMPT self-compliance handling, and Z3 prohibition + impulse log structures that were absent from this skill.

Continuing to invoke `humanaios-core-architecture-pattern` risks:
- Stale Zone classification (pre-S-061526 schema)
- Missing Z3 prohibition enforcement
- Missing Impulse Audit Log structure
- Conflict with the ratified dual-architecture canonical spec

---

## Migration

**Do not invoke this skill.** Use instead:

```
humanaios-dual-architecture v1.3
```

Located at: `tools/skills/humanaios-dual-architecture/SKILL.md`

---

## Archive Note

This file is preserved in `tools/skills/deprecated/` for traceability and IC-class root cause analysis. It is not invocable and should not be updated.

**Source session:** S-061526 Close Note  
**Registry entry:** See `REGISTERED.md` — S-061526 Z2 ratification block  
**Carry count at deprecation:** 0 (clean deprecation — no unresolved carry items)
