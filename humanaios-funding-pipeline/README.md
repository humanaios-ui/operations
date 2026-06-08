# 🏛️ HumanAIOS Funding & Resource Pipeline

> **Cherokee Nation · AI Safety / Behavioral Observability · TRL 2–3 · Solo LLC**

A self-refreshing, structured database and automation pipeline for tracking funding opportunities, free AI infrastructure, and income sources — purpose-built for an Indigenous (Cherokee Nation) solo research founder building open AI behavioral observability infrastructure at pre-revenue stage.

**Live outputs:**
- [`reports/OPPORTUNITIES.md`](reports/OPPORTUNITIES.md) — sortable Markdown table (auto-generated weekly)
- [`reports/index.html`](reports/index.html) — dark-themed filterable HTML dashboard (open locally)
- [`data/sources.json`](data/sources.json) — machine-readable canonical dataset (auto-updated)

**GitHub Actions:**
| Workflow | Trigger | What it does |
|----------|---------|--------------|
| [🔄 Weekly Refresh](.github/workflows/refresh.yml) | Every Monday 09:00 UTC | Checks all URLs, scrapes deadlines, regenerates reports, commits, opens issue on alerts |
| [📥 Import](.github/workflows/import.yml) | Manual / push to `data/incoming/` | Merges new sources from CSV, JSON, URL, grants.gov, or SAM.gov |
| [✅ Validate](.github/workflows/validate.yml) | Every PR touching `data/` or `src/` | Schema check, duplicate detection, unit tests |

---

## Quick start

### 1 — Clone and install

```bash
git clone https://github.com/humanaios-ui/humanaios-funding-pipeline.git
cd humanaios-funding-pipeline
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Optional: install as a package so the CLI is on PATH
pip install -e .
```

### 2 — Open the dashboard

```bash
# Regenerate HTML and open it
python scripts/generate_html.py
open reports/index.html          # macOS
xdg-open reports/index.html      # Linux
start reports/index.html         # Windows
```

### 3 — Query via CLI

```bash
# Summary stats
python -m src.humanaios_funding.cli --summary

# Native-eligible + AI-safety (highest-priority intersection)
python -m src.humanaios_funding.cli --native --ai-safety

# Deadlines within 45 days — sort by deadline
python -m src.humanaios_funding.cli --deadline-soon 45 --sort-by deadline

# All compute credits
python -m src.humanaios_funding.cli --category compute_credit

# Rolling AI-safety grants — output as JSON for piping
python -m src.humanaios_funding.cli --category ai_safety --status rolling --format json

# Search by keyword
python -m src.humanaios_funding.cli --search "cherokee"

# Just the URLs (for curl/wget batching)
python -m src.humanaios_funding.cli --native --format urls

# If installed as package:
haios-funding --summary
```

**All CLI flags:**

| Flag | Type | Description |
|------|------|-------------|
| `--data` | path | Data file to query (default: `data/sources.json`) |
| `--category` | enum | Filter by category (see Categories below) |
| `--native` | flag | Only native_eligible opportunities |
| `--ai-safety` | flag | Only ai_safety_relevant opportunities |
| `--status` | enum | `active`, `rolling`, `closed`, `upcoming`, `uncertain` |
| `--deadline-soon` | int | Deadline within N days |
| `--trl` | str | TRL tag substring match (e.g. `TRL2-3`) |
| `--tag` | str | Eligibility tag substring match |
| `--search` | str | Case-insensitive name/notes search |
| `--summary` | flag | Print summary stats and exit |
| `--format` | enum | `table` (default), `json`, `csv`, `urls` |
| `--sort-by` | enum | `priority` (default), `name`, `deadline` |

---

## Import sources

### From a local file

```bash
# Merge a CSV of new opportunities
python scripts/import_sources.py --from-csv path/to/new_grants.csv

# Merge a JSON array
python scripts/import_sources.py --from-json path/to/extra.json

# Preview without writing
python scripts/import_sources.py --from-csv new.csv --dry-run
```

### From a remote URL

```bash
# Fetch and import a remote JSON/CSV
python scripts/import_sources.py --from-url https://example.org/opportunities.json
```

### From grants.gov (live search)

```bash
# Search and import matching federal grants
python scripts/import_sources.py --from-grants-gov "AI safety behavioral observability"
python scripts/import_sources.py --from-grants-gov "native american technology"
```

### From SAM.gov (live search)

```bash
python scripts/import_sources.py --from-sam "AI evaluation research"
```

### Via GitHub Actions (manual dispatch)

Go to **Actions → 📥 Import Opportunities → Run workflow**, then choose:
- **source**: `csv`, `json`, `url`, `grants_gov`, or `sam_gov`
- **value**: the file path, URL, or search query
- **dry_run**: `true` to preview without committing

### Auto-import via `data/incoming/`

Drop any `.csv` or `.json` file into `data/incoming/` and push to `main`. The import workflow fires automatically, merges the data, and commits the result.

---

## Add a source manually

Add a row to `data/sources.json` (JSON array) or `data/sources.csv`:

**Required fields:** `name`, `category`, `sponsor`, `url`

**All fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Full display name of the opportunity |
| `category` | enum | See Categories table below |
| `sponsor` | str | Organisation providing the opportunity |
| `url` | str | Must start with `https://` |
| `eligibility_tags` | list[str] | Pipe-separated in CSV; e.g. `["cherokee_citizen","llc"]` |
| `award_size` | str\|null | Human-readable, e.g. `"up to $305,000"` |
| `deadline` | str\|null | ISO date `YYYY-MM-DD`, or null |
| `deadline_cadence` | str\|null | `"rolling"`, `"annual"`, `"monthly"`, etc. |
| `native_eligible` | bool | True if Cherokee Nation / Native American citizens eligible |
| `ai_safety_relevant` | bool | True if directly relevant to AI safety / behavioral observability |
| `trl_fit` | str | `"TRL2-3"`, `"TRL2-4"`, `"any"`, etc. |
| `status` | enum | `active`, `rolling`, `closed`, `upcoming`, `uncertain` |
| `last_checked` | str\|null | ISO date; set automatically by checker |
| `url_ok` | bool\|null | Set automatically by checker |
| `notes` | str\|null | Internal notes (contact, caveats, eligibility details) |
| `source` | str\|null | Attribution domain, e.g. `"nsf.gov"` |

**Categories:**

| Value | Description |
|-------|-------------|
| `native` | Cherokee Nation / Indigenous / Native American programs |
| `ai_safety` | AI safety / alignment / x-risk funding |
| `research_grant` | General research grants (NSF, foundations, etc.) |
| `contest` | Hackathons, prizes, red-team competitions |
| `compute_credit` | Cloud / GPU / compute credit programs |
| `fellowship` | Stipended fellowships and programs |
| `paid_work` | Gig work, eval contracting, maintainer funding |
| `publishing` | Open-access publishing, preprint servers |
| `free_api` | Free LLM API tiers |
| `free_infra` | Free databases, observability, orchestration tools |

---

## Run URL checker manually

```bash
# Check all URLs, scrape deadline hints, update sources.json in place
python -m src.humanaios_funding.checker data/sources.json data/sources.json

# Check only, don't write
python -m src.humanaios_funding.checker data/sources.json
```

The checker:
1. Pings every URL with retry + exponential backoff
2. Scrapes the page for deadline keywords and extracts dates
3. Stamps `last_checked` (today) and `url_ok` (true/false) on every record
4. Prints a report: dead links, deadline hints, imminent/soon deadlines
5. Exits with code `1` if any dead links or deadlines ≤7 days exist (CI-friendly)

---

## Regenerate reports manually

```bash
# Markdown report
python -m src.humanaios_funding.report
# → reports/OPPORTUNITIES.md

# HTML dashboard
python scripts/generate_html.py
# → reports/index.html

# Both at once
python -m src.humanaios_funding.report && python scripts/generate_html.py
```

---

## Run tests

```bash
python -m pytest tests/ -v

# With coverage (requires pytest-cov)
pip install pytest-cov
python -m pytest tests/ --cov=src/humanaios_funding --cov-report=term-missing
```

18 tests covering schema validation, URL validation, deadline countdown, JSON/CSV round-trips, deduplication, and summary stats.

---

## GitHub Actions setup

The three workflows in `.github/workflows/` are ready to use as-is. They require no secrets for the core pipeline.

**Optional: add a `GITHUB_TOKEN` for higher API rate limits**
This is auto-provided by GitHub Actions — no configuration needed.

**Optional: label setup**
The refresh workflow labels alert issues with `funding-alert`. Create this label in your repo Settings → Labels, or remove the `labels:` line from `refresh.yml`.

**Weekly schedule:** Monday 09:00 UTC. Edit `cron: "0 9 * * 1"` in `refresh.yml` to change.

**Manual run:** Go to Actions → any workflow → Run workflow.

---

## Repo structure

```
humanaios-funding-pipeline/
├── .github/
│   └── workflows/
│       ├── refresh.yml       ← weekly auto-sync (Monday)
│       ├── import.yml        ← on-demand import (manual / incoming/)
│       └── validate.yml      ← PR validation (schema + tests)
│
├── data/
│   ├── sources.json          ← canonical dataset (45 seed records)
│   ├── sources.csv           ← CSV mirror (optional; auto-generated)
│   └── incoming/             ← drop files here to trigger auto-import
│
├── reports/
│   ├── OPPORTUNITIES.md      ← human-readable Markdown (auto-generated)
│   └── index.html            ← dark-theme HTML dashboard (auto-generated)
│
├── scripts/
│   ├── import_sources.py     ← bulk importer (CSV/JSON/URL/grants.gov/SAM)
│   └── generate_html.py      ← HTML report generator
│
├── src/
│   └── humanaios_funding/
│       ├── __init__.py
│       ├── schema.py         ← Pydantic v2 Opportunity model
│       ├── loader.py         ← CSV/JSON I/O
│       ├── checker.py        ← URL pinger + deadline scraper
│       ├── cli.py            ← argparse query CLI
│       └── report.py         ← Markdown report generator
│
├── tests/
│   └── test_schema.py        ← 18 unit tests (18/18 passing)
│
├── requirements.txt
├── setup.py
└── README.md
```

---

## Profile context

This pipeline is calibrated for the following founder profile. The `native_eligible` and `ai_safety_relevant` flags on each record reflect eligibility under this profile:

- **Entity:** HumanAIOS LLC (FL single-member LLC, EIN 41-5367995)
- **Founder:** Cherokee Nation citizen, US-based (Florida), solo
- **Research domain:** AI behavioral observability / calibration / alignment; ACAT (AI Calibration Assessment Tool); behavioral telemetry measuring gap between AI self-reported vs demonstrated behavior
- **Stage:** Pre-revenue, TRL 2–3, open research, arXiv preprints, GitHub/HuggingFace data
- **Contact:** aioshuman@gmail.com | (448) 243-3992

**Priority funding stack (as of June 2026):**

1. **This week:** Set up free AI stack (Cerebras + Groq + Gemini Flash + Ollama) → eliminate $4/day. Enter Gray Swan Arena next wave.
2. **This month:** BlueDot Rapid Grants, LTFF, Manifund, AIAF, Foresight, IFP (all rolling). Cherokee Nation SBAC intake.
3. **Next 1-3 months:** NSF SBIR Project Pitch (reopens June 2, 2026) → up to $305k equity-free. Emergent Ventures.
4. **Ongoing:** Mercor gig income ($50-$111/hr), Apart Research monthly hackathons, Gray Swan bounties.

---

## Governance note

This tool is **Zone 1 infrastructure** (Unit Zero executes). The data it produces is informational. All decisions about which opportunities to pursue require **Zone 2 ratification** per HumanAIOS governance (humanaios-ui/operations). No opportunity is applied for, committed to, or distributed based solely on this pipeline without operator (Night) review.

---

*Wado.*

<!-- Last updated: 2026-06-02 -->
