# Azure inventory and readiness (#915)

Run from the repository root, after normal Azure CLI login:

```sh
python3 tools/azure_readiness.py --subscription f945ccaf-d3fb-42f9-8b35-a57bb8e0f299
```

The only Azure call is `az resource list` with an explicit subscription. The tool
does not deploy resources, switch accounts, call application endpoints or read
secrets. Stdout contains the scrubbed JSON report. Collection errors produce a
nonzero exit code, never an empty successful inventory.

For an existing private export:

```sh
python3 tools/azure_readiness.py --inventory /private/path/inventory.json
```

The standard `--input` option is an alias for `--inventory`.

Keep the export private. Output uses hashed resource IDs, service families,
resource types and SKU labels. It excludes raw names, IDs, tags, endpoints and
properties. Hashes are pseudonymous correlation references, not encryption or
proof of origin. Review output before sharing, including tenant-chosen SKU labels.

Generic inventory cannot prove deployed code revision, real database readiness,
successful human use or billing qualification. Those fields stay UNKNOWN or
NEEDS_EVIDENCE. A successful ARM provisioning state never becomes application
readiness. Missing billing days remain unknown; the qualifying-day count is null.
Candidate service families are planning groups, not Microsoft's qualifying count.
In particular AI_SERVICES does not establish an Azure OpenAI deployment.

## Backend proof and alerts

In the deployed API environment, with its normal DATABASE_URL and database driver:

```sh
python3 -c 'import json; from acat.api.db import check_database_readiness; print(json.dumps(check_database_readiness()))'
```

This explicit read-only probe distinguishes REAL, MOCK and UNAVAILABLE. It uses
SELECT 1 with connection and statement timeouts and closes its own connection.
REAL proves that configured endpoint answered a read; it does not prove application
schema correctness, staging persistence, a production cutover, or a live report
from this development environment. Existing HTTP health routes keep their behavior.

`infra/azure-research-budget.bicep` prepares resource-group email alerts at actual
50/80/100 percent and forecast 100 percent. Amount, billing-currency confirmation,
dates and recipients require explicit values. Deploying a budget remains a separate
authorized action; this template does not stop consumption or verify program rules.

`infra/metaculus-job.bicep` omits empty optional secrets. Its optional cron string
keeps Manual as the default. Enabling a cron schedule requires a fresh Railway
writer check and an approved handover. See the data and cutover review alongside
this document for the remaining field-classification and ownership decisions.

Next evidence: record the deployed image digest/source SHA; perform the existing
INTENT-OS Resource Miner smoke test; obtain explicit real-backend readiness and a
separately authorized staging persistence test; reconcile private daily billing
against written program rules. This report grants no authority.

Run regression tests with:

```sh
python3 -m unittest discover -s tests -p test_azure_readiness.py -v
```
