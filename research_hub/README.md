# Research Hub

A small MCP server. Any chatbot that can add a custom MCP connector (Grok, Claude, others) can call it.
It routes research questions between bots, keeps one shared graph, and exposes research data read-only.

**Status:** Z1 proposal, not ratified. Every result carries `authority_effect: NONE`.

## Tools

| Group | Tool | What it does |
|:--|:--|:--|
| route | `route_bots` | Bots, tags, model-judged reliability |
| route | `route_research` | Best bot answers; a **different** bot checks the claims |
| kg | `kg_summary`, `kg_query` | Read `kg/humanaios_kg_v0_1.json` |
| kg | `kg_propose_claim` | Stage a PROPOSAL (needs outside evidence and a falsifier) |
| kg | `kg_proposals` | List proposals; verify the hash chain |
| research | `research_datasets`, `research_dataset_read` | Read-only, 64 KB per call, no symlinks, no `..` |

## Rules the code enforces

- Proposals only. Nothing here writes `REGISTERED.md` or marks anything ratified. Z2 signs.
- A claim without a falsifier is rejected. Evidence from `hub:` ids (self-reference) is rejected.
- A bot never verifies its own claims. One bot configured means no verification, said plainly.
- Verification is an independent model judgement. Sources are not fetched. Scores are not ground truth.
- Spend caps: `max_calls` (hard max 8) per question and `HUB_MAX_CALLS_PER_HOUR` overall.
- Datasets: no write or delete tool exists. The research repo is never touched.
- No outbound webhooks. The loop reads `events.jsonl` (n8n can poll it).

## Run it

```bash
export HUB_TOKEN="$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')"
python3 -m research_hub                       # 127.0.0.1:8765, mock bots if nothing configured
python3 -m research_hub --host 0.0.0.0        # needs HUB_TOKEN (24+ chars); use behind HTTPS
```

Endpoints: `POST /mcp` (streamable HTTP), `GET /sse` + `POST /messages` (older SSE clients), `GET /healthz`.
Send `Authorization: Bearer <token>`.
If the connector form has no header field, set `HUB_ALLOW_URL_TOKEN=1` and add `?key=<token>` to the URL.
That puts the secret in the URL. Use a long random token and rotate it.

## Configure bots

`HUB_PROVIDERS` is a JSON list. A bot whose `key_env` variable is unset is skipped.

```json
[
  {"name": "claude", "kind": "anthropic", "model": "claude-opus-5-5",
   "key_env": "ANTHROPIC_API_KEY", "tags": ["long", "analysis"]},
  {"name": "grok", "kind": "openai_compat", "base_url": "https://api.x.ai/v1",
   "model": "<grok model id>", "key_env": "XAI_API_KEY", "tags": ["fresh", "web", "social"]}
]
```

Claude calls use the official `anthropic` SDK (`pip install anthropic`) with server-side refusal fallback on.
Other bots use plain HTTPS. Tags steer routing; after 5 judged samples, reliability breaks ties.

Other env: `HUB_STATE_DIR` (default `.hub_state`), `HUB_KG_PATH`, `HUB_DATASET_ROOT`, `HUB_ALLOWED_ORIGINS`.

## Falsifier

If two bots from the same pool agree on a claim that a source check later refutes more than 30% of
the time over 20+ judged claims, model verification adds no signal and the router should say so and stop
scoring bots on it.

## Not done

Live bot calls untested (no keys here). Whether Grok's connector wants `/mcp` or `/sse` is unconfirmed;
both are served. No rate limit per client. No TLS (put it behind Railway or a proxy).
