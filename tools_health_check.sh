#!/bin/bash

# Tools Health Check — Run all 5 tools basic functionality tests
# Usage: bash operations/tools_health_check.sh
# Output: Health status report to stdout + exit code

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "=========================================="
echo "TOOLS HEALTH CHECK"
echo "Date: $(date)"
echo "=========================================="
echo ""

# Change to project root for relative imports to work
cd "$PROJECT_ROOT"

PASSED=0
FAILED=0

# Test each tool
echo "1. acat_observability_bridge.py"
if python3 tools/acat_observability_bridge.py > /dev/null 2>&1; then
    echo "   ✅ PASS"
    ((PASSED++))
else
    echo "   ❌ FAIL"
    ((FAILED++))
fi

echo "2. acat_corpus_session.py"
if python3 tools/acat_corpus_session.py > /dev/null 2>&1; then
    echo "   ✅ PASS"
    ((PASSED++))
else
    echo "   ❌ FAIL"
    ((FAILED++))
fi

echo "3. acat_rec2_session_init.py"
if python3 hooks/acat_rec2_session_init.py > /dev/null 2>&1; then
    echo "   ✅ PASS"
    ((PASSED++))
else
    echo "   ❌ FAIL"
    ((FAILED++))
fi

echo "4. acat_rec3_preflight_reminder.py"
if python3 hooks/acat_rec3_preflight_reminder.py > /dev/null 2>&1; then
    echo "   ✅ PASS"
    ((PASSED++))
else
    echo "   ❌ FAIL"
    ((FAILED++))
fi

echo "5. acat_rec4_postflight_verifier.py"
if python3 hooks/acat_rec4_postflight_verifier.py > /dev/null 2>&1; then
    echo "   ✅ PASS (Note: verifier is currently stubbed)"
    ((PASSED++))
else
    echo "   ❌ FAIL"
    ((FAILED++))
fi

echo ""
echo "=========================================="
echo "SUMMARY: $PASSED passed, $FAILED failed"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
