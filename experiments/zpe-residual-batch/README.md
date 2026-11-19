# ZPE-Residual Batch Experiment (Z1 research)

**Status:** experimental / not admitted / not deployed. **Authority effect:** NONE. **Execution:** DISABLED by default.

This experiment operationalizes the zero-point energy / residual behavioral divergence mapping inside the operations repository.

## Conceptual mapping

| Physical concept | Operational realization in this experiment |
|------------------|--------------------------------------------|
| Zero-point energy (irreducible ground-state residual) | Residual divergence between self-report and demonstrated behavior that remains after constraint |
| Vacuum fluctuations | Stochastic variation across repeated identical calls under fixed boundary conditions |
| Casimir effect (boundary-condition dependence) | Systematic variation of system-prompt / constraint strength ("plates") while holding the task fixed |
| Radiative instability | Amplification of residual under repeated sampling, longer context, or mild distribution shift |

The goal is not energy extraction. It is to quantify how residual divergence behaves under controlled boundary conditions, using free open-source models so collection can be scheduled and scaled without proprietary API cost.

## Experiment design

### Independent variables (boundary conditions)

Three constraint regimes (Casimir-analogue "plates"):

1. **Open** — minimal system prompt; model free to respond in its default style.
2. **Constrained** — explicit instruction to be concise, literal, and avoid elaboration or self-reference.
3. **Pressured** — constrained + explicit challenge to stay consistent with a prior self-description under mild adversarial framing.

### Dependent measures (per trial)

- Self-report statement (P1-style claim about how it will behave).
- Demonstrated response on a fixed probe task under the same boundary condition.
- Simple divergence score (lexical / embedding distance or structured rubric; placeholder in v0.1).
- Variance across N repeated calls under identical conditions (fluctuation magnitude).

### Free open-source model targets (pluggable)

Collector is designed to call any OpenAI-compatible free endpoint. Recommended starting points (subject to current free-tier availability):

- Groq free tier (Llama 3, Mixtral, etc.)
- Hugging Face Inference API free models (when available)
- Together.ai free tier or local Ollama (completely free, no network)

Default mode is dry-run / synthetic so the script can be tested and scheduled without external calls until explicitly enabled.

### Scheduling and batch coordination

- Single script supports `--batch N` for repeated trials under each condition.
- Outputs timestamped JSONL receipts suitable for later aggregation.
- Can be driven by cron, systemd timer, or a GitHub Actions workflow that runs on a schedule and commits receipts to a branch or artifact.
- Coordination is via shared protocol file + output directory; multiple runners can append to the same JSONL with unique trial IDs.

## How to run (safe default)

From repository root:

```bash
# Dry-run (synthetic, no network)
python3 experiments/zpe-residual-batch/collect.py --dry-run --batch 3

# Real collection (requires endpoint config)
python3 experiments/zpe-residual-batch/collect.py \
  --endpoint https://api.groq.com/openai/v1 \
  --model llama3-8b-8192 \
  --api-key-env GROQ_API_KEY \
  --batch 5
```

Outputs land in `experiments/zpe-residual-batch/receipts/` (gitignored by default; see note below).

## Explicit boundaries

- No original ACAT Learning Index, corpus row, or score is produced.
- Synthetic / dry-run results must never be inserted into the live ACAT corpus.
- Authority effect is NONE. This does not authorize any deployment, admission, or external claim.
- Real endpoint calls require the operator to supply a free-tier key and accept the provider's terms.
- Receipts are experimental data only.

## Next steps

- Add structured divergence rubric aligned with ACAT dimensions.
- Implement embedding-based residual metric.
- Add GitHub Actions scheduled workflow example.
- Compare residual magnitude across open / constrained / pressured regimes.

*Z1 research only. Subject to normal operations gates before any broader use.*
