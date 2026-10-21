# INTENT-OS × Resource Miner: always-on Azure Container Apps (proposal)

**Status:** Candidate deployment readiness; **NOT DEPLOYED**. Production Azure spend, new role assignments, external ingress and cutover require separate **Z3 human execution** and explicit budget approval. No credentials or private Azure identifiers are committed.

## Reuse inventory before paying for another instance

Existing source:
- `humanaios-funding-pipeline/Dockerfile.resource-miner` builds the real stdlib `app.py` service (not a mock).
- `humanaios-funding-pipeline/infra/resource-miner-containerapp.bicep` has `minReplicas=1`, `targetPort=8080`, and a `/api/health` probe. **Do not run this template by default**: it creates a new Container Apps environment and Log Analytics workspace. On an existing Azure project, this can create duplicate billable infrastructure.
- An existing HumanAIOS ACR and separate ACAT Container Apps deployment scaffolding may be reusable. Check live Azure inventory first; repository Bicep alone is **not proof** that a Container Apps Environment is deployed.
- Existing Cloudflare `intent-os-board` has a verified-login `/collaborate` surface that can proxy the Resource Miner `POST /api/intent` path using `RESOURCE_MINER_ORIGIN`. That Worker is **not the Resource Miner server** and does not replace its runtime.

**Purpose:** host existing `/intent-os`, `/on-track`, `/api/health`, and bounded `POST /api/intent` on a provisioned Azure Container App, with no laptop dependency. This does not grant access to the first-user collaboration cockpit, authenticate participants or complete first-user qualification.

## Phase 0: zero-cost read-only discovery (Azure Cloud Shell)

Use the existing authorized subscription. Do **not** paste account IDs, secrets or unredacted Azure inventory into public issues. The following commands are read-only:

```sh
az account show --query "{subscription:name,state:state}" -o table
az acr list --query "[].{registry:name,resourceGroup:resourceGroup,sku:sku.name}" -o table
az containerapp env list --query "[].{environment:name,resourceGroup:resourceGroup,location:location}" -o table
az containerapp list --query "[].{app:name,resourceGroup:resourceGroup,revisionMode:properties.configuration.activeRevisionsMode,minReplicas:properties.template.scale.minReplicas}" -o table
az group list --query "[].{group:name,location:location}" -o table
```

Confirm (privately): correct subscription, already-existing ACR, *whether any Container Apps environment actually exists*, project region and resource group, selected container app name, current deployment state, remaining eligible credit and spending ceiling. If an environment is absent, **STOP** and obtain explicit authorization for provisioning and cost. An empty list is not evidence that the blueprint has already deployed.

Before accepting the selected existing ACR, check that it allows ARM-audience tokens for managed-identity image pulls:

```sh
az acr config authentication-as-arm show --registry <existing-acr> --query status -o tsv
```

Require `enabled`; if disabled or the setting cannot be verified, **STOP**. Enabling it with `az acr config authentication-as-arm update --registry <existing-acr> --status enabled` is a **separate approved Z3 write**, outside Phase 0. This setting and the managed identity's `AcrPull` permission (Phase 2, step 2) are both prerequisites.

## Phase 1: credential-free repository qualification

From the repo checkout:

```sh
cd humanaios-funding-pipeline
docker build -f Dockerfile.resource-miner -t resource-miner:preflight .
docker run --rm --publish 127.0.0.1:8766:8080 resource-miner:preflight
```

In a second terminal:

```sh
curl --fail http://127.0.0.1:8766/api/health
curl --fail http://127.0.0.1:8766/intent-os
curl --fail http://127.0.0.1:8766/on-track
curl --fail -X POST http://127.0.0.1:8766/api/intent \
  -H 'Content-Type: application/json' \
  --data '{"objective":"Find free research training","source_mode":"snapshot"}'
```

The **candidate** `.github/workflows/resource-miner-azure-readiness.yml` already tests a real container and asserts that uncredentialed `/api/resources`, `/api/scan`, and `/api/entitlement/handoff` fail with 403. CI needs independent review; passing a Docker run does not verify Azure deployment or production rate limiting.

## Phase 2: approved Azure deployment, **not yet executed**

Use an existing ACR, an existing Container Apps Environment, and the approved **immutable** image tag. Do **not** create a new ACR or log workspace on the assumption one is needed. Deploying the image and creating/updating a Container App incur usage charges and potentially permissions changes.

For an operator performing an explicitly approved deployment:

1. Select the approved ACR and **existing** Container Apps Environment from Phase 0. Capture their resource IDs privately. Set an approved maximum monthly Azure spending threshold/alerts and record existing credit status. Confirm the existing Container Apps workload profile (Consumption vs Dedicated).
2. Confirm the ACR's ARM-audience-token setting passed Phase 0 and an already-provisioned **user-assigned managed identity** has `AcrPull` permission on that ACR; avoid enabling the registry's admin user or pasting ACR passwords. If missing, stop; enable ARM-audience-token authentication, create the identity or grant a role only in a separate approved Z3 step.
3. Build and push the *approved commit* from `humanaios-funding-pipeline/` through the **existing** ACR (use `az acr build --registry <existing-acr> --image resource-miner:<approved-commit> --file Dockerfile.resource-miner .`). This is a **write** and is not part of the CI/no-spend phase.
4. Verify all selected values against actual subscription inventory, then choose the path for the selected app. **Do not execute a create command if the same app already exists.**
   - **Existing app:** before updating its image, use `az containerapp identity show --name <existing-app> --resource-group <app-resource-group>` and `az containerapp registry list --name <existing-app> --resource-group <app-resource-group>` to verify the selected user-assigned identity is attached and the selected ACR server is configured to use that identity's resource ID. If the identity is missing, attach it with `az containerapp identity assign --name <existing-app> --resource-group <app-resource-group> --user-assigned <identity-id>` as part of the approved deployment. If the registry binding is missing or differs, configure it with `az containerapp registry set --name <existing-app> --resource-group <app-resource-group> --server <acr>.azurecr.io --identity <identity-id>`. Recheck both bindings before running `az containerapp update --name <existing-app> --resource-group <app-resource-group> --image <acr>.azurecr.io/resource-miner:<approved-commit>`.
   - **New app:** create the **one** approved Container App in the existing Environment. `az containerapp create` accepts `--environment <existing-environment-id>`, `--image <acr>.azurecr.io/resource-miner:<approved-commit>`, `--ingress external`, `--target-port 8080`, `--cpu 0.25`, `--memory 0.5Gi`, `--min-replicas 1`, `--max-replicas 1`, `--user-assigned <identity-id>`, and `--registry-identity <identity-id>` with `--registry-server <acr>.azurecr.io` (also supply the approved `--name` and `--resource-group`).
5. Confirm image digest, revision readiness, `/api/health`, `/intent-os`, `/on-track`, and `POST /api/intent` via the assigned HTTPS FQDN. A health-only response is not sufficient: the original Dockerfile omitted both HTML files and the requirements seed.
6. Verify missing/weak admin token keeps administrative APIs denied; test Cloudflare Access/`/collaborate` and Resource Miner HTTPS origin *separately*. Add Azure origin to the existing Worker `RESOURCE_MINER_ORIGIN` **only after** approval and deployed-origin allowlisting. For first-user private use, add appropriate upstream access restrictions and abuse/rate limits before sharing the URL.
7. Record Azure **observed** revision SHA, billing meter/source, request-based smoke receipt, real browser screenshot/observation and external availability independently. Only then may status advance from `CODE_PRESENT` to `PRODUCTION_VERIFIED`; a real human outcome remains a separate control.

### Continuous availability and cost

Azure Container Apps **Consumption** with `minReplicas=1` keeps one instance warm while it runs and reduces cold starts. Consumption bills vCPU/GiB use and requests subject to Azure's shared per-subscription grants and idle rules. A dedicated profile bills differently. Additional ACR, logs, data transfer, private networking and other resources can incur charges. **No always-on option is guaranteed free or guarantees zero downtime.** Confirm actual Azure Price Calculator estimate and Cost Management alerts **before approval**, including what happens after promotional credit expiry.

Start with a **single 0.25 vCPU / 0.5Gi replica**, not five workloads to satisfy an unverified credit-program threshold. Scale later based on measured traffic, security needs and proven operator value.

### Fail-closed qualification

- `GET /api/health`: 200 with `ok=true`, not a generic platform 200.
- `GET /intent-os` and `/on-track`: actual HTML rendered, not an HTTP 500 or empty page.
- `POST /api/intent` snapshot mode: bounded public candidate response, `eligibility=NOT_ASSESSED`, `authority=NONE`, `execution=DISABLED`. Snapshot currentness not guaranteed.
- No anonymous access to administrative scan, resources or entitlement handoff. Real-user data and private Mines must not be exposed.
- Browser/Cloudflare login is **identity**, not authority to act for others.
- Independently verify repeated external requests and record uptime incidents; no uptime guarantee until monitoring proves it.
- No Azure provisioning/spend, access-control change, public cutover, auto-scan, credential change, or first-user qualification occurs solely from merging the candidate PR.

**Upstream docs:** https://learn.microsoft.com/azure/container-apps/billing ; https://learn.microsoft.com/en-us/cli/azure/containerapp ; https://learn.microsoft.com/azure/container-apps/managed-identity-image-pull.
