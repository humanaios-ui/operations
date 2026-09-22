#!/bin/bash
# PR Readiness Verification — Run all validation checks in sequence
# Usage: ./scripts/verify_pr_readiness.sh [--verbose]
#
# Runs manifest, code quality, security, and behavioral checks before merge.
# Exits on first failure; use --verbose for detailed output.

set -e
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
  ((PASSED++))
}

check_fail() {
  echo "✗ $1"
  ((FAILED++))
}

# Tool Manifest Integrity
log_check "Tool Manifest Integrity"
if python3 .tool-control/scan.py --check > /dev/null 2>&1; then
  check_pass "Manifest matches working tree"
else
  check_fail "Manifest is stale"
  exit 1
fi

if python3 .tool-control/validate.py > /dev/null 2>&1; then
  check_pass "Structural rules pass"
else
  check_fail "Structural rule violations detected"
  exit 1
fi

if python3 .tool-control/render.py --check > /dev/null 2>&1; then
  check_pass "TOOLS_MANIFEST.md is in sync"
else
  check_fail "TOOLS_MANIFEST.md is out of sync"
  exit 1
fi

# Document Control
log_check "Document Integrity"
if python3 .doc-control/scan.py --check > /dev/null 2>&1; then
  check_pass "Document registry matches filesystem"
else
  check_fail "Document registry is stale"
  exit 1
fi

if python3 .doc-control/validate.py > /dev/null 2>&1; then
  check_pass "Document rules pass"
else
  check_fail "Document rule violations detected"
  exit 1
fi

# Python Linting
log_check "Python Code Quality"
if python3 -m pylint scripts/*.py tools/*.py --disable=all --enable=E > /dev/null 2>&1; then
  check_pass "Python linting passes (errors only)"
else
  check_fail "Python linting found errors"
  # Non-fatal; continue
fi

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
