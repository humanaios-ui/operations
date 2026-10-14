# Cerebras SDK → Langfuse tracing, bounded pilot

Upstream skill installed in `.agents/skills/langfuse` from
`langfuse/skills@b86532b77f16f1e27c7cffa32bb632aa3cd9a352`.
Read `SKILL.md` and `references/instrumentation.md` before changing tracing.
The code uses **Langfuse Python SDK v5 / OpenTelemetry**, not the deprecated v2
trace/span API. For self-hosted Langfuse, verify server >= v4.59 first.

## Install dependencies (Python 3.11 or newer recommended)

From `humanaios-funding-pipeline/resource-miner`:

```bash
python3 -m pip install -e ".[observability]"
python3 -m resource_miner.traced_cerebras          # SAFE: prints missing key names only
python3 -m resource_miner.traced_cerebras --live   # ONE real public-prompt Cerebras request
```

The runtime needs environment variable **names** (put their values in Azure
Container App secrets or another approved secret store, never git or chat):

- `CEREBRAS_API_KEY`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_BASE_URL` (HTTPS US/EU/self-hosted endpoint as appropriate)

Optional `CEREBRAS_MODEL=qwen-3.8-27b` if the account model listing confirms
availability; no model is silently substituted. The provided question
"Why is fast inference important?" is the *only* allowed live prompt.
`max_completion_tokens<=128`, `max_retries=0`, 20-second timeout,
TCP-warming disabled, no external work unless `--live` passed.

## Trace layout

- root `resource-miner-public-inference-pilot` (span): fixed public task
  identifier, prompt hash, completion flag.
- child `cerebras-chat-completion` (generation): model, input/output token
  counts when provider reports them, latency, prompt/output hashes.

This captures **no raw prompt, generated text, customer identifiers,
credentials, or untrusted exception strings** in trace fields or JSON stdout.
Hashes are not confidentiality guarantees for a small public prompt; this
pilot explicitly uses public input. No automatic production data tracing.

`flush()` is called before process exit. A successful flush does not establish
the trace is visible or verified; the receipt explicitly says so. Fetch the
new trace by ID from the Langfuse *observations* API (modern v2), verify root
and generation parentage, model, usage and data masking, and preserve the
Langfuse URL or API receipt in the independent evidence graph.

## Azure runtime and authority

The repository **does not** run this code on GitHub Actions CI with credentials
or trigger a deployment automatically. To attribute this run to Azure, execute
it inside the user-owned Azure runtime and attach the Azure run/job identity
and deployment SHA as independent evidence. A GitHub-hosted runner is *not*
Azure compute even if it uses Azure credentials.

The granted subscription is not proof a specific runtime exists.
Any future deployment must stay under authorized human controls, bounded
spending, protection against secret exfiltration, and independent audit.

Model output quality is *not* scored by having a Langfuse trace. Complete M3
requires a real observed trace **and** an outcome rubric, single-resource
control arm, actual provider costs and measured execution times.
