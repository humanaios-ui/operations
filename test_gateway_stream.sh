#!/bin/bash
# Test streaming text generation through AI Gateway
# Requires: AI_GATEWAY_API_KEY environment variable

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for API key
if [ -z "${AI_GATEWAY_API_KEY:-}" ]; then
    echo "ERROR: AI_GATEWAY_API_KEY environment variable not set"
    echo ""
    echo "To test locally:"
    echo "  1. Get an API key: npx vercel ai-gateway api-keys create --name stream-test"
    echo "  2. Export it: export AI_GATEWAY_API_KEY='your-key-here'"
    echo "  3. Run this script"
    echo ""
    echo "In GitHub Actions: Add AI_GATEWAY_API_KEY to repo secrets"
    exit 1
fi

echo "═══════════════════════════════════════════════════════════"
echo "AI Gateway Streaming Text Generation Test"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Environment:"
echo "  Model: openai/gpt-6-astra"
echo "  Endpoint: https://ai-gateway.vercel.sh/v1"
echo "  API Key: ${AI_GATEWAY_API_KEY:0:20}..."
echo ""
echo "Running streaming request..."
echo ""

# Run the Python streaming script
python3 "$SCRIPT_DIR/stream_gateway_text.py"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Test Complete"
echo "═══════════════════════════════════════════════════════════"
