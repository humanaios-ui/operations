#!/bin/bash
# PR Readiness Verification — Run all validation checks in sequence
# Usage: ./scripts/verify_pr_readiness.sh [--verbose]
#
# Runs manifest and document integrity checks before merge.
# Exits on first failure; use --verbose for detailed output.

VERBOSE="${1:---quiet}"
FAILED=0
PASSED=0

log_check() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "▶ $1"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

check_pass() {
  echo "✓ $1"
  PASSED=$((PASSED+1))
}

check_fail() {
  echo "✗ $1"
  FAILED=$((FAILED+1))
}

# Tool Manifest Integrity
log_check "Tool Manifest Integrity"
if [[ "$VERBOSE" == "--verbose" ]]; then
  python3 .tool-control/scan.py --check || { check_fail "Manifest is stale"; exit 1; }
else
  python3 .tool-control/scan.py --check > /dev/null 2>&1 || { check_fail "Manifest is stale"; exit 1; }
fi
check_pass "Manifest matches working tree"

if [[ "$VERBOSE" == "--verbose" ]]; then
  python3 .tool-control/validate.py || { check_fail "Structural rule violations detected"; exit 1; }
else
  python3 .tool-control/validate.py > /dev/null 2>&1 || { check_fail "Structural rule violations detected"; exit 1; }
fi
check_pass "Structural rules pass"

if [[ "$VERBOSE" == "--verbose" ]]; then
  python3 .tool-control/render.py --check || { check_fail "TOOLS_MANIFEST.md is out of sync"; exit 1; }
else
  python3 .tool-control/render.py --check > /dev/null 2>&1 || { check_fail "TOOLS_MANIFEST.md is out of sync"; exit 1; }
fi
check_pass "TOOLS_MANIFEST.md is in sync"

# Document Control
log_check "Document Integrity"
if [[ "$VERBOSE" == "--verbose" ]]; then
  python3 .doc-control/validate.py || { check_fail "Document rule violations detected"; exit 1; }
else
  python3 .doc-control/validate.py > /dev/null 2>&1 || { check_fail "Document rule violations detected"; exit 1; }
fi
check_pass "Document rules pass"

if [[ "$VERBOSE" == "--verbose" ]]; then
  python3 .doc-control/render.py --check || { check_fail "TOOLS_MANIFEST.md is out of sync"; exit 1; }
else
  python3 .doc-control/render.py --check > /dev/null 2>&1 || { check_fail "TOOLS_MANIFEST.md is out of sync"; exit 1; }
fi
check_pass "Document registry is in sync"

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary: $PASSED passed, $FAILED failed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $FAILED -eq 0 ]; then
  echo "✓ PR is ready for review"
  exit 0
else
  echo "✗ Fix failures above before pushing"
  exit 1
fi
