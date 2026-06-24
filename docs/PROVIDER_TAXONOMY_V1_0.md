# Provider Canonical Taxonomy v1.0
**HumanAIOS · humanaios-ui/operations · S-060626-01**
**Z2-TRUST-B prerequisite — must be defined before first staging row lands**
**Status: DRAFT — Zone 2 ratification required before any provider session runs**

---

## Purpose

Required by Z2-CORPUS-TRUST-02 (role lock): every assessment run must register
each model in exactly one role per run — SUBJECT xor INFRA, never both.
The role-lock check fires on `model_family`, not `agent_name` or `provider_canonical`.
Two models from the same `model_family` cannot be in different roles in the same run.

Also required by Z2-TRUST-B: all staging rows must carry `provider_canonical`
and `model_family` before the staging layer acceptance query runs.

---

## provider_canonical values

| provider_canonical | Description | Accounts provisioned |
|---|---|---|
| `anthropic` | Anthropic (Claude family) | Current primary provider |
| `openai` | OpenAI (GPT family) | Corpus: ChatGPT, GPT-4o, ChatGPT 5.2 |
| `google` | Google DeepMind (Gemini family) | Corpus: Gemini |
| `meta` | Meta AI (Llama family) | Corpus: Llama |
| `mistral` | Mistral AI | Provisioned (Z2-TRUST-B) |
| `cerebras` | Cerebras Systems | Provisioned (Z2-TRUST-B) |
| `groq` | Groq (inference platform) | Provisioned (Z2-TRUST-B) |
| `openrouter` | OpenRouter (multi-model gateway) | Provisioned (Z2-TRUST-B) |
| `nvidia` | NVIDIA Build | Provisioned (Z2-TRUST-B) |
| `sambanova` | SambaNova Systems | Provisioned (Z2-TRUST-B) |
| `together` | Together AI | Provisioned (Z2-TRUST-B) |
| `fireworks` | Fireworks AI | Provisioned (Z2-TRUST-B) |
| `microsoft` | Microsoft (Copilot/Azure family) | Corpus: M365 Copilot |
| `xai` | xAI (Grok family) | Corpus: Grok |
| `deepseek` | DeepSeek | Corpus: DeepSeek |
| `perplexity` | Perplexity AI | Corpus: Perplexity |
| `sintra` | Sintra AI | Corpus: Sintra |
| `unknown` | Provider not identified | Legacy rows without provider info |

---

## model_family values

`model_family` is the role-lock enforcement unit. Coarser than `model_version`,
finer than `provider_canonical`. Rule: same `model_family` = same role per run.

| model_family | provider_canonical | Example model_versions |
|---|---|---|
| `claude` | `anthropic` | claude-sonnet-4-6, claude-haiku-4-5, claude-opus-4-6 |
| `gpt` | `openai` | gpt-4o, gpt-4-turbo, chatgpt-5 |
| `gemini` | `google` | gemini-1.5-pro, gemini-2.0-flash, gemini-ultra |
| `llama` | `meta` | llama-3.2, llama-3.1-70b, llama-3-8b |
| `mistral` | `mistral` | mistral-large, mixtral-8x7b, mistral-small |
| `grok` | `xai` | grok-3, grok-4.1 |
| `deepseek` | `deepseek` | deepseek-r1, deepseek-v3 |
| `copilot` | `microsoft` | m365-copilot, github-copilot |
| `perplexity` | `perplexity` | perplexity-sonar, perplexity-online |
| `sintra` | `sintra` | sintra-v1 |
| `groq-hosted` | `groq` | groq-llama3, groq-mixtral (Groq hosts other families — use hosted model's family if determinable, else groq-hosted) |
| `openrouter-hosted` | `openrouter` | Same pattern as groq-hosted |
| `unknown` | `unknown` | Legacy rows without family info |

---

## Backfill plan for legacy corpus rows

Legacy rows (submission_version = 'legacy' or empty) have `provider_canonical = NULL`
and `model_family = NULL`. These are excluded from role-lock checks by design —
legacy rows predate the taxonomy. The role-lock constraint fires only on new
staging / partner_review / behavioral_session rows submitted after this taxonomy
is ratified.

**No backfill required.** Legacy NULL values are intentional and semantically
correct (provider unknown at time of submission).

---

## Staging row acceptance criteria (Z2-TRUST-B gate)

A staging row is eligible for promotion to `behavioral_session` when ALL of:
1. `provider_canonical` is NOT NULL and matches this taxonomy
2. `model_family` is NOT NULL and matches this taxonomy
3. `document_layer = 'staging'`
4. `submission_purity` is one of: `clean`, `agent_self_only`, `unknown`
5. Role-lock check passes: INFRA model_family ≠ SUBJECT model_family for this run
6. Night explicitly approves batch promotion via UPDATE SET document_layer = 'behavioral_session'

---

## Partner review row acceptance criteria (Z2-TRUST-A gate)

A partner_review row is eligible for promotion to `behavioral_session` when ALL of:
1. Mode AI / DeMarius confirms scoring protocol alignment
2. Phase 3 completion is present (pair_id matched)
3. Night explicitly approves inclusion via UPDATE SET document_layer = 'behavioral_session'

---

*Promotion gate: Zone 2 ratification of this taxonomy before any non-Anthropic row
is submitted to the staging layer.*
