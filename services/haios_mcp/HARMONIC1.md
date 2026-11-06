# HARMONIC-1 — Local CPU Inference Qualification (candidate-only)

**Status:** Z1 evaluation, not admitted. **Authority:** `NONE`. **Execution surface:** a separate, operator-started loopback-only `llama.cpp` compatible model server. No change to Witness MCP runtime, Coordinator, authorized tools or HARMONIC-0 routing policy. No automatic cloud request, API key access, model download, account connection, model training, resource allocation or deployment.

## Why this is not a production router

HARMONIC-0 runs a deterministic simulated local/cloud/unavailable policy. HARMONIC-1 is an **isolated test of the real LOCAL endpoint** only. It intentionally does not replace HARMONIC-0's fake endpoints in `harmonic0.py`, register a new MCP tool, or activate delegation. It checks HARMONIC-0's permitted LOCAL decision for each synthetic PUBLIC question, then issues a single local-only HTTP request per case. A local timeout or invalid response abstains; it **cannot** trigger real cloud fallback.

The local server binds only to `127.0.0.1` and the client connects to numeric IPv4 loopback using `http.client` directly. Host, path and protocol are fixed; there is no URL parameter, proxy discovery, redirect following, cookie, credential, tool call or arbitrary HTTP destination. The client accepts bounded `application/json` and an OpenAI-style `/v1/chat/completions` response. A loopback address alone **does not authenticate the process listening on the port**: the operator must verify the selected listener. There is no OS sandbox in this candidate. Send **only the bundled synthetic public prompts**.

## CPU candidate and constraints

An initial non-binding candidate for a memory-limited **Intel** Mac is a small 0.6B model in **GGUF Q4_K_M** format, such as Qwen3-0.6B. Quantized weights are about 0.48 GB, but resident memory includes context/KV cache, executable and operating system. Neither Mac compatibility, output quality, model licensing for the intended use, actual RSS nor acceptable latency is assumed by the test. Download/model selection is a separate explicit operator action; **nothing in this PR downloads model weights**.

Official serving documentation: https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md . Use a vetted local `llama-server` executable and a vetted GGUF file obtained separately. Example **after** reviewing local file integrity:

```sh
./llama-server --model '/absolute/path/to/your-reviewed-0.6b-Q4_K_M.gguf' \
  --alias local --host 127.0.0.1 --port 9931 --ctx-size 2048 --threads 2
```

No `0.0.0.0` binding. Ensure no unrelated listener owns port 9931. The benchmark client does not start or manage this server and does not require provider credentials. Hardware instructions and `llama-server` flags vary by build: inspect the locally installed binary's `--help` before starting it. On a higher-capacity Windows desktop, run the same contract with a Windows-built CPU server (the Python client is cross-platform except optional `/bin/ps` process RSS sampling).

## Run the controlled offline tests

From the root of the unmerged candidate worktree (Python 3.10+):

```sh
PYTHONPATH=services/haios_mcp/src python3 -m unittest -v \
  services/haios_mcp/tests/test_harmonic1.py
PYTHONPATH=services/haios_mcp/src python3 \
  services/haios_mcp/scripts/harmonic1_qualify.py --mode synthetic
```

This mode runs a scripted fake answer producer, not a model. Metrics from the synthetic example **must not** be presented as real speed, accuracy, calibration or model memory measurements.

## Opt-in local model evaluation

After separately starting the local-only model server:

```sh
PYTHONPATH=services/haios_mcp/src python3 \
  services/haios_mcp/scripts/harmonic1_qualify.py \
  --mode local --port 9931 --model local \
  --consent-to-send-public-fixtures-to-loopback \
  --report "$HOME/harmonic1-local-$(date +%Y%m%d%H%M%S).json"
```

The report is created with permission `0600` and refuses overwrite. It stores case IDs, deterministic lexical-rubric results, completion counts, wall-clock latency and optional sampled RSS **without prompts or raw model outputs**. Use `--model-pid N` to sample the local server's **RSS via `/bin/ps`**, not peak memory; omit on Windows. Model name comes from the local endpoint's self-assertion and is not verified. API cost is recorded as $0 for local calls, but power, device cost and model development are **unmeasured**, not free.

Every case is public and fixed. The CLI has no cloud mode. If the server is unavailable, the row records `LOCAL_UNAVAILABLE_ABSTAIN`. A benchmark can score poorly while the underlying model server functions normally. The test requires a **separate independent evaluator** for real accuracy/calibration; its lexical rubric is only a preliminary screening proxy.

## Offline Claude reference comparison (not a cloud call)

The tool accepts a **user-provided file containing only these PUBLIC case responses**; it never invokes Claude or asserts that the file was authored by Claude. Create a privately held JSON file mapping all eight `case_id` keys to plaintext answers, obtained in a **separately authorized** evaluation. Run with `--baseline-json /private/path/reference.json`. No API pricing, authenticated model identity, output provenance or latency is inferred from an imported file. Without it, the result is `NOT_PROVIDED_NO_CLOUD_CALL`.

## Recorded metrics and promotion gates

- **Completion/abstention:** number of valid local responses versus unavailable or invalid ones.
- **Heuristic quality:** eight fixed public source-and-governance cases, each graded with transparent `required_any` phrases. This is not a reliable judge of semantic accuracy, legal/medical suitability, safety, or ACAT P2; it has false positive and negative cases.
- **Latency:** median and maximum observed end-to-end HTTP round trip, plus a gross completion-tokens-per-wall-second approximation (includes input processing; not decoding throughput).
- **Memory:** optional snapshots of model PID resident memory; not peak or total system RSS.
- **Calibration:** request `CONFIDENCE: 0-100` and count compliant cases. No independent P2 reference means accuracy-calibration is `NOT_INDEPENDENTLY_EVALUATED`; do not compute self-certified LI or SAG from synthetic grades.
- **Cost:** local model API calls $0; actual electrical/hardware/maintenance cost unmeasured. Imported cloud baseline cost unavailable.
- **Authority:** `NONE`; human admission `PENDING`; cloud requests `0`; MCP calls `0`.

**Promotion to a real governed router remains blocked** until (1) local binary/model integrity and OS sandbox/permissions are verified on target hardware, (2) a real local run with measured memory and latency is repeated, (3) separately authorized cloud reference responses are evaluated on the identical fixed cases, (4) independently authenticated P2 reviewers challenge initial P1 answers and performance forecasts, (5) P3 corrections and held-out tests are evaluated without contaminating the data, and (6) separate human ratification/one-use cloud authorizations exist for any real fallback.

**No cloud inference or automatic switching is possible through this artifact.** Neither a passing CI job nor the harness's lexical rubric is admission evidence by itself.
