# Tools Discovery — HumanAIOS Research Infrastructure

Scope: free/open tools that align with ACAT behavioral observability research, reproducible corpus operations, cooperative governance, and non-promotional public documentation.

## Psychometric analysis tools (open-source)

| Tool | Stack | Use in this program | URL |
|---|---|---|---|
| `psych` | R | Reliability analysis (including alpha) and factor-analysis workflows | https://cran.r-project.org/package=psych |
| `lavaan` | R | Confirmatory factor models and bi-factor model testing | https://cran.r-project.org/package=lavaan |
| `mirt` | R | Multidimensional IRT modeling for instrument diagnostics | https://cran.r-project.org/package=mirt |
| `pingouin` | Python | Reliability and inferential stats in Python workflows | https://pingouin-stats.org/ |
| `factor_analyzer` | Python | EFA/CFA-style exploratory workflows | https://github.com/EducationalTestingService/factor_analyzer |
| `semopy` | Python | Structural equation modeling for latent-variable validation | https://github.com/YoungjuneKwon/forked-semopy |

## Open corpus and dataset versioning (beyond Hugging Face)

| Tool/platform | Primary function | URL |
|---|---|---|
| DVC | Dataset/model versioning tied to Git workflows | https://dvc.org/ |
| Git LFS | Large file management in Git repos | https://git-lfs.com/ |
| Dataverse | Open data repository publishing and metadata | https://dataverse.org/ |
| CKAN | Open data catalog and API portal | https://ckan.org/ |
| Zenodo | DOI-backed archival for research artifacts | https://zenodo.org/ |
| OSF | Open science workflow and registration platform | https://osf.io/ |

## Collaborative annotation and peer review

| Tool | Function | URL |
|---|---|---|
| Label Studio | Multi-format annotation and review workflows | https://labelstud.io/ |
| Doccano | Lightweight NLP annotation | https://github.com/doccano/doccano |
| INCEpTION | Scholarly annotation with active learning support | https://inception-project.github.io/ |
| Hypothesis | Collaborative annotation on web documents | https://web.hypothes.is/ |
| OpenReview | Open peer review workflows | https://openreview.net/ |
| PREreview | Open manuscript review collaboration | https://prereview.org/ |

## Cooperative governance and transparent operations tooling

| Tool | Function | URL |
|---|---|---|
| Loomio | Participatory decision workflows | https://www.loomio.com/ |
| Decidim | Open participatory governance platform | https://decidim.org/ |
| Open Collective | Public budgeting and fiscal transparency | https://opencollective.com/ |
| CiviCRM | Membership/community operations management | https://civicrm.org/ |

## Behavioral data visualization (web-compatible)

| Tool | Function | URL |
|---|---|---|
| Apache Superset | SQL-first dashboards | https://superset.apache.org/ |
| Metabase | Internal analytics and dashboarding | https://www.metabase.com/ |
| Grafana OSS | Monitoring/time-series dashboarding | https://grafana.com/oss/grafana/ |
| Vega-Lite | Declarative statistical graphics | https://vega.github.io/vega-lite/ |
| D3.js | Custom web data visualizations | https://d3js.org/ |
| Apache ECharts | Interactive browser visualization | https://echarts.apache.org/ |

## Zone 2 decisions required

1. Baseline stack choice (R-first, Python-first, or mixed psychometric pipeline).
2. Corpus publication strategy (DVC + self-host, Dataverse/OSF, or split archive model).
3. Governance tooling adoption sequence (Loomio/Decidim/Open Collective integration order).
