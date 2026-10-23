# CI Environment Assumptions & Graceful Degradation

**Updated:** 2026-10-02  
**Purpose:** Document external dependencies, CI environment capabilities, and graceful fallback patterns for contributors and tool authors.

---

## External Dependencies

| Tool | Dependency | CI Available? | Behavior | Fallback |
|------|:-----------|:---|:---|:---|
| ai_context_generator_v0_1 | GitHub CLI (gh) | ✓ (authenticated) | Fetches live issue/PR metadata via `gh issue view` / `gh pr view` | Returns fallback metadata (title/state/author set to "unknown") |
| repository_coordinator_v0_1 | GitHub API token (GITHUB_TOKEN) | ✓ (GitHub Actions env) | Queries repo, branches, CI runs, PR validation | N/A (required for gate) |
| intent_os_test_harness_v1_0 | Python 3.11+ | ✓ (setup-python action) | Runs baseline test enumeration, verifies workflow/harness sync | N/A |
| builder_compliance_scanner_v1_0 | BuilderMarker schema + tools-manifest.yaml | ✓ (in-repo) | Validates tool metadata registry, verifies builder v1.7 markers | N/A |
| repository_admission_gate | PR file reference validation | ✓ (via control-plane adapter) | Validates all file refs in PR body exist in main or PR diff | N/A (required for gate) |
| tool_manifest_renderer | .tool-control/render.py + tools-manifest.yaml | Manual (not automated) | Renders TOOLS_MANIFEST.md from source YAML; no CI integration yet | N/A |

---

## Graceful Degradation Patterns

### Pattern 1: GitHub CLI (gh)

When `gh` CLI unavailable, unauthed, or times out:

**ai_context_generator_v0_1 behavior:**
- Attempts `gh issue view <number>` or `gh pr view <number>` with 5s timeout
- On success: Returns live metadata (title, state, body, author from GitHub)
- On 404 / timeout / auth fail: Returns fallback object:
  ```python
  {
      "title": f"Issue #{number}",
      "state": "unknown",
      "body": "",
      "author": {"login": "unknown"},
  }
  ```
- For PRs, adds field: `"merged": False`

**Test behavior:**
- Tests decorated with `@unittest.skipUnless(has_gh_cli(), "GitHub CLI not available")`
- Skip count reported in pytest output (e.g., "7 passed, 3 skipped")
- No hard fail; test suite passes

**Template for new tools:**
```python
import subprocess

def has_gh_cli():
    """Check if GitHub CLI is available and authenticated."""
    try:
        result = subprocess.run(["gh", "--version"], capture_output=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def fetch_from_github(query):
    """Fetch data from GitHub; fall back gracefully."""
    try:
        result = subprocess.run(["gh", "..."], capture_output=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except Exception:
        pass
    # Return fallback (never raise)
    return {"status": "unknown", "data": {}}
```

**Outcome:** Smoke tests pass with skip count. Tools degrade gracefully instead of blocking CI.

### Pattern 2: External APIs (GitHub, Anthropic, etc.)

When API unavailable (timeout, 503, rate limit, auth fail):

- **Attempt:** Single call with 5s timeout
- **On fail:** Log error at WARNING level, return fallback object with sensible defaults
- **Never raise:** Always return valid schema (tools downstream depend on structure)
- **Telemetry:** Log attempt + failure reason in CI telemetry artifact

**Template:**
```python
def fetch_api(url, headers=None):
    """Fetch from external API; degrade gracefully."""
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        logging.warning(f"API timeout on {url}")
    except requests.HTTPError as e:
        logging.warning(f"API error {e.response.status_code} on {url}")
    except Exception as e:
        logging.warning(f"API error on {url}: {e}")
    
    # Return fallback (never raise)
    return {"status": "unavailable", "error": "external service unreachable"}
```

### Pattern 3: Optional Capabilities (Builder Markers, SMAG Predictions, etc.)

When builder metadata unavailable or SMAG service unreachable:

- **Report:** Advisory warning (non-blocking)
- **Continue:** Proceed with reduced capability set (skip that validation step)
- **Flag:** Include in CI telemetry artifact for investigation
- **Never block:** Advisory-only gates don't fail merge

**Template:**
```python
def validate_with_optional_capability(file_path):
    """Validate file; skip optional checks if capability unavailable."""
    result = {"valid": True, "warnings": []}
    
    # Core validation (always runs)
    if not is_valid_syntax(file_path):
        result["valid"] = False
        result["errors"] = ["syntax error"]
        return result
    
    # Optional: Builder marker validation
    try:
        markers = fetch_builder_metadata(file_path)
        if not validate_markers(markers):
            result["warnings"].append("builder markers invalid")
    except Exception as e:
        logging.warning(f"skipping builder check: {e}")
        result["warnings"].append("builder check skipped (service unavailable)")
    
    return result
```

---

## Testing Environment Limitations

| Limitation | Impact | Workaround |
|:-----------|:---|:---|
| `gh` CLI auth | Tests requiring live GitHub API skip gracefully | None needed (skip decorators in place) |
| Network (HTTPS via proxy) | Some third-party services may timeout or 403 | 5s timeout + fallback returns (see Pattern 2) |
| Disk (10 GB ephemeral) | Large clones may fail mid-session | Pre-populate large datasets; use sparse checkout for big repos |
| Python (3.11 only) | Tools requiring older versions fail | Pin Python 3.11 in tool requirements; no legacy support |
| GitHub token (Actions env) | Pull-only in CI; no git push without explicit step | Z3 executor handles push; CI validates only |

---

## Debugging Checklist

When CI fails unexpectedly:

1. **Local dry-run:**
   ```bash
   python3 -m pytest tools/tests/test_*.py -v
   ```
   - If local passes: Environment-specific issue (see step 2)
   - If local fails: Code issue (fix, commit, re-run)

2. **Environment-specific diagnostics:**
   ```bash
   # Check GitHub CLI
   gh --version
   gh auth status
   
   # Check network
   curl -sS https://api.github.com/octocat
   
   # Check disk
   df -h /
   
   # Check Python
   python3 --version
   ```

3. **Inspect telemetry artifact:**
   - Each CI run uploads `telemetry.json` (30-day retention)
   - Check `validation_result`, `error_message`, optional capability skips
   - Scan for patterns (repeated timeouts, auth failures, etc.)

4. **Verify fallback is in place:**
   - If optional API failed, did tool return fallback object (not raise)?
   - Check log output for WARNING-level "skipping" messages
   - Confirm schema matches expected type (not null or empty)

---

## Versioning & Stability

**Graceful degradation patterns are part of the contract.**

- Do not add hard-fail exceptions without Z2 (Night) ratification
- If degradation behavior changes, bump tool version
- Advisory-only failures (Pattern 3) never block merge
- Skip decorators (Pattern 1) reduce flake in test suites

**Updating a Tool:**
When modifying external dependency handling:
1. Run local tests with dependency unavailable (e.g., `gh --version` fails)
2. Verify fallback object is returned (not exception)
3. Confirm downstream consumers accept fallback schema
4. Update this document if new pattern introduced
5. Emit H/IC candidate if pattern affects multiple tools

---

## Implementation Checklist

For tool authors implementing a new external dependency:

- [ ] Add entry to "External Dependencies" table (this doc)
- [ ] Implement graceful degradation (pick pattern 1/2/3 above)
- [ ] Test with dependency unavailable (`@unittest.skipUnless` or equivalent)
- [ ] Log at WARNING level on fallback (not ERROR or CRITICAL)
- [ ] Return valid schema on fallback (never raise, never return null)
- [ ] Update tool version number if adding new dependency
- [ ] Add telemetry signal for skipped/unavailable capability
- [ ] Document expected fallback behavior in tool docstring

---

## CI/CD Integration

**Current status:**
- Graceful degradation patterns in place for `ai_context_generator_v0_1`
- Test enumeration harness validates coverage (Phase 2)
- Tool manifest sync gate planned (Phase 2)
- SMAG advisory warnings operational (Phase 1B)

**Future roadmap:**
- Automated API availability pre-flight check (Phase 3)
- Fallback telemetry dashboard (Phase 3)
- Dynamic capability negotiation via INTENT-OS (Phase 3)

---

## Related Files

- **CLAUDE.md:** Authority & governance, commit discipline
- **.github/workflows/quality-baseline.yml:** Quality gate definition (runs pytest baseline suites)
- **tools/intent_os_test_harness_v1_0.py:** Baseline test enumeration
- **tools/ai_context_generator_v0_1.py:** Reference implementation of Pattern 1 (GitHub CLI graceful degradation)
- **tools/repository_coordinator_v0_1.py:** Uses Pattern 2 (API graceful degradation)
