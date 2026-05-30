#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${1:-https://operations-production-bd55.up.railway.app}"
echo "==> Smoke test target: ${BASE_URL}"
echo
echo "==> [1/3] GET /"
curl -sS -i "${BASE_URL}/"
echo
echo
echo "==> [2/3] GET /api/v1/acat/health"
curl -sS -i "${BASE_URL}/api/v1/acat/health"
echo
echo
ASSESSMENT_ID="railway-smoke-$(date +%s)"
SESSION_ID="railway-smoke-session-$(date +%s)"
echo "==> [3/3] POST /api/v1/acat/intake/phase1"
curl -sS -i \
 -X POST "${BASE_URL}/api/v1/acat/intake/phase1" \
 -H "Content-Type: application/json" \
 -d "{
 \"assessment_id\": \"${ASSESSMENT_ID}\",
 \"session_id\": \"${SESSION_ID}\",
 \"agent_name\": \"Claude\",
 \"provider\": \"anthropic\",
 \"phase\": \"phase1\",
 \"submission_purity\": \"agent_self_only\",
 \"scores\": {
 \"truth\": 80,
 \"service\": 80,
 \"harm\": 80,
 \"autonomy\": 80,
 \"value\": 80,
 \"humility\": 80
 }
 }"
echo
echo
echo "Smoke test complete."
echo "assessment_id=${ASSESSMENT_ID}"
echo "session_id=${SESSION_ID}"

