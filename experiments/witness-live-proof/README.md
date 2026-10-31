# Existing Witness: one genuine operator-side MCP interaction (issue #1090)

**Target**: the *already installed* macOS service at \`127.0.0.1:8768/mcp\`; **not** the candidate spawned in the synthetic E2/E3 tests. **State**: no real interaction proven until an operator executes the probe and supplies a redacted receipt.

## Run on the operator Mac

Before running, review that the existing installed Witness's three local context snapshots are suitable for provider transmission. A real \`haios_talk\` call sends those snapshots to Anthropic under the configured provider terms; it is **not air-gapped**. The operator must explicitly opt in.

Use the Python interpreter already installed with the HumanAIOS MCP service:

\`\`\`sh
"$HOME/Library/Application Support/HumanAIOS/mcp/.venv/bin/python" \
  experiments/witness-live-proof/prove_existing_witness.py --allow-model-call
\`\`\`

Run from a checkout containing this branch, or supply the absolute path to the script. Do not install or restart the service just to make this proof green. If the service is not running, the result is \`NOT_PROVEN\`. Do not paste API keys, bearer tokens, \`session_id\`, model response text, or private user data in issues.

## Acceptance

1. Client reaches the existing loopback service; no-token and wrong-token requests return HTTP 401.
2. Mac Keychain supplies the existing bearer privately; MCP initializes and lists \`haios_status\`, \`haios_talk\`.
3. Authenticated \`haios_status\` states \`authority=NONE\`.
4. Exactly one \`haios_talk\` model request carries a random fresh 32-hex nonce and an explicitly synthetic prompt.
5. Response echoes \`WITNESS_ACK:<nonce>\`, is complete, states \`authority=NONE\`, returns three source manifest entries with SHA-256 and truncation fields, and has a matching model response digest if provided.
6. Output prints an **unsigned operator-side JSON receipt** (nonce, content hashes, version, timestamp, manifest). The script does not print raw answer, credentials or session handles.
7. If the installed v0.1.1 nonstreaming call fails, **report NOT_PROVEN**. This is an important failing result, not permission to hot-reinstall or silently switch to the v0.2 candidate.

## Boundaries

A successful nonce response is sufficient to show the local client reached an authenticated MCP tool and received model-generated text. It is **not** a trusted third-party attestation, current-GitHub verification, user benefit proof, a signed audit, or permission to deploy. It also does **not** show a private browser↔ChatGPT tunnel works.

For offline synthetic regressions (no provider calls):

\`\`\`sh
python3 -m unittest tests.test_witness_existing_live_proof -v
\`\`\`

The operator can attach only the redacted JSON receipt to issue #1090. Preserve the installed-service version and hash metadata; do not promote an unsigned receipt into Z2 authority. PR #1078 remains draft. PR #1012 remains a separate candidate service update.
