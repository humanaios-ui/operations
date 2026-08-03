# Tool Development Standard — Template & Checklist

**Version:** 1.0  
**Effective:** Week 3 STANDARDIZE phase (2026-07-14)  
**Applies to:** All new tools in `tools/` directory

---

## What is a Tool?

A **tool** is a reusable Python module that performs a specific, focused function. Examples:
- `acat_observability_bridge.py` — real-time behavioral signature detection
- `acat_corpus_session.py` — ACAT session state management
- Integration hooks (Rec 2/3/4) — automated workflow triggers

Tools are **NOT** skills (skills are higher-level workflows that may orchestrate multiple tools).

---

## Tool Template (Checklist)

### Structure

```
tools/
├── <tool_name>.py           ← Main implementation
├── <tool_name>_spec.md      ← Technical specification (if complex)
└── README.md                ← Tools directory overview
```

### File: `<tool_name>.py`

**Required Elements:**

- [ ] **Module docstring** (top of file)
  ```python
  """
  <Tool Name> — <One-line purpose>
  Version: X.Y.Z (Zone: 1/2/3)
  
  <Brief description of what the tool does, when to use it, what it outputs>
  
  Author: <your-practice-name>
  Updated: <YYYY-MM-DD>
  """
  ```

- [ ] **Imports organized**
  - Standard library first
  - Third-party imports second
  - Local imports third
  - All with type annotations where used

- [ ] **Type hints on ALL functions**
  ```python
  def function_name(param1: str, param2: Optional[Path]) -> Dict[str, Any]:
      """Docstring."""
      pass
  ```

- [ ] **Docstrings on ALL classes and public methods**
  - Class-level docstring (what it does)
  - Method-level docstring (what it does + args + returns)
  - Example:
    ```python
    class MyClass:
        """Manages X with Y."""
        
        def method(self, arg: str) -> bool:
            """Check if arg is valid. Returns True if passes validation."""
            pass
    ```

- [ ] **Error handling**
  - Validate inputs (type, range, required fields)
  - Graceful degradation (return status dict with `ok: bool` + error message)
  - No silent failures (raise exception or return error status, never both)
  - Example:
    ```python
    def validate_scores(scores: Dict[str, float]) -> Tuple[bool, str]:
        """Validate ACAT scores are 0-100 with all 12 dimensions."""
        required = {"truth", "service", "harm", "autonomy", "value", "humility", 
                    "scheme", "power", "syc", "consist", "fair", "handoff"}
        
        missing = required - set(scores.keys())
        if missing:
            return False, f"Missing dimensions: {missing}"
        
        for dim, score in scores.items():
            if not isinstance(score, (int, float)) or not 0 <= score <= 100:
                return False, f"Invalid score for {dim}: {score} (must be 0-100)"
        
        return True, ""
    ```

- [ ] **Test stub in `if __name__ == "__main__"` block**
  - Demonstrate basic invocation
  - Show expected output format
  - Make it runnable: `python3 tools/<tool_name>.py`
  - Example:
    ```python
    if __name__ == "__main__":
        # Test: create session state
        result = create_tool_state()
        print(json.dumps(result, indent=2))
        assert result["ok"] == True, "Basic test failed"
    ```

- [ ] **Logging/Output**
  - Use structured output (dicts, JSON, dataclasses)
  - No print statements (except in test block)
  - Return status objects: `{"ok": bool, "data": ..., "error": str}`

### File: `<tool_name>_spec.md` (if complex)

**Required when:**
- Tool has >250 LOC, OR
- Tool integrates multiple sub-components, OR
- Tool has complex state management

**Contains:**
- Purpose (one sentence)
- Inputs (parameters, types, constraints)
- Outputs (structure, format examples)
- Error cases and handling
- Examples of usage
- Integration points (which hooks/skills call it)
- Known limitations

### Code Quality Checklist

- [ ] **Type hints:** 80%+ coverage (target: 100%)
- [ ] **Docstrings:** 100% on classes + public methods
- [ ] **Comments:** <10% of LOC (only WHY, not WHAT)
- [ ] **Linting:** Passes `ruff check` with zero errors
- [ ] **No hardcoded values:** Config should be parameterizable
- [ ] **No side effects:** Tool should not modify global state (only local files/state dicts)
- [ ] **Pure functions where possible:** Output depends only on inputs
- [ ] **Error handling:** No silent failures, always return status

---

## Zone Progression Checklist

### Zone 1 (Testable/Draft) → Zone 2 (Ratified)

Before moving tool from Zone 1 to Zone 2:

- [ ] Code quality passes all checks above
- [ ] Spec-code alignment verified (100%)
- [ ] Test stub runs without errors
- [ ] No FIXMEs or TODOs in code
- [ ] All dependencies documented
- [ ] Error cases tested (negative test cases)
- [ ] Integration path documented (which hooks/skills use this tool?)
- [ ] Review complete (peer or evaluator sign-off)

### Zone 2 (Ratified) → Zone 3 (Live)

Before moving tool from Zone 2 to Zone 3:

- [ ] Unit tests pass (70%+ coverage)
- [ ] Integration tests pass (end-to-end workflow)
- [ ] Performance benchmarks acceptable
- [ ] ACAT P1→P3 assessment completed (Learning Index documented)
- [ ] Production deployment plan defined
- [ ] Monitoring/health checks in place
- [ ] Documentation complete (README, examples, troubleshooting)

---

## Example: Minimal Tool (Zone 1 Draft)

```python
"""
Simple Data Validator — Validate and normalize input data
Version: 0.1.0 (Zone 1 draft)

Purpose: Accept messy input (dict, JSON, CSV), normalize to canonical form,
return status + validated data.

Author: empirica-foundation.carly.empirica-foundation-evaluator
Updated: 2026-07-14
"""

import json
from typing import Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validation."""
    ok: bool
    data: Dict[str, Any] = None
    error: str = None


def validate_input(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate input data structure.
    
    Args:
        data: Input dictionary with required keys.
    
    Returns:
        ValidationResult with ok=True + validated data, or ok=False + error message.
    """
    required_keys = {"name", "type", "value"}
    
    if not isinstance(data, dict):
        return ValidationResult(ok=False, error="Input must be a dictionary")
    
    missing = required_keys - set(data.keys())
    if missing:
        return ValidationResult(ok=False, error=f"Missing required keys: {missing}")
    
    # Normalize
    validated = {
        "name": str(data["name"]).strip(),
        "type": str(data["type"]).lower(),
        "value": data["value"],
    }
    
    return ValidationResult(ok=True, data=validated)


if __name__ == "__main__":
    # Test: valid input
    result = validate_input({"name": "test", "type": "STRING", "value": 123})
    assert result.ok == True
    assert result.data["type"] == "string"
    print("✅ Test passed")
```

---

## Deployment Checklist

Before merging a new tool:

- [ ] Tool file location: `tools/<tool_name>.py`
- [ ] Spec file (if needed): `tools/<tool_name>_spec.md`
- [ ] Tool added to `operations/TOOLS_MANIFEST.md`
- [ ] Zone status: Zone 1 (draft)
- [ ] Dependencies documented in manifest
- [ ] Integration point documented (which hooks/skills use it)
- [ ] ACAT assessment protocol defined (if applicable)
- [ ] Commit message includes: purpose, version, Zone, dependencies

---

## Anti-Patterns (Avoid These)

❌ **Silent failures**
```python
# Bad: no error handling
def process(data):
    return data.upper()  # Crashes if data is None
```

✅ **Explicit errors**
```python
# Good: validates input
def process(data: str) -> Tuple[bool, str]:
    if not isinstance(data, str):
        return False, f"Expected string, got {type(data)}"
    return True, data.upper()
```

---

❌ **Hardcoded magic numbers**
```python
# Bad: score range hardcoded everywhere
if score > 100:
    ...
```

✅ **Named constants**
```python
# Good: centralized, named
SCORE_MIN = 0
SCORE_MAX = 100
if not SCORE_MIN <= score <= SCORE_MAX:
    ...
```

---

❌ **Loose return types**
```python
# Bad: returns different types
def get_data():
    if error:
        return None  # or dict or list?
    return data
```

✅ **Structured returns**
```python
# Good: always structured
def get_data() -> Dict[str, Any]:
    return {"ok": bool, "data": ..., "error": str}
```

---

## Quality Gate: Before Zone 2

**Tool readiness score (checklist):**

```
Pass if: 90%+ of above items checked ✅
Then: Tool eligible for Zone 2 review
Then: Peer review → acceptance → merge → Zone 2 promotion
```

---

**Template Version:** 1.0  
**Next Review:** Week 4 (SUSTAIN phase)

