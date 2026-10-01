// Azure Container Apps deployment for the ACAT API (acat/api/app.py) — already live on
// Railway at api.humanaios.ai. This adds an Azure deployment target alongside it.
//
// Scaffolding only — written without Azure access from this session, so it has not
// been deployed or validated against a real subscription. Review before applying.
//
// Prerequisites:
//   1. Build and push the image (from the repo root):
//        docker build -f Dockerfile.acat-api -t <registry>/acat-api:<tag> .
//        docker push <registry>/acat-api:<tag>
//   2. Deploy (only containerImage and acatWriteToken are required; the rest have
//      empty defaults and the routes that use them degrade gracefully if unset —
//      see each param's description for exactly where it's read):
//        az deployment group create \
//          --resource-group <rg> \
//          --template-file infra/acat-api-containerapp.bicep \
//          --parameters containerImage=<registry>/acat-api:<tag> \
//                       acatWriteToken=<token> \
//                       registryServer=<registry> registryUsername=<user> registryPassword=<token>
//
// Deliberately NOT a parameter here: an Anthropic API key. acat/api/services/
// elicitation_service.py reads `api_key` from each request's own JSON payload
// (bring-your-own-key), not a server-side env var — there is nothing to configure.

@description('Azure region for all resources. Defaults to the resource group\'s region.')
param location string = resourceGroup().location

@description('Container Apps Environment name. Shared if other funding-pipeline/ACAT services are added later.')
param environmentName string = 'humanaios-acat-env'

@description('Container App name.')
param containerAppName string = 'acat-api'

@description('Fully qualified image reference, e.g. myregistry.azurecr.io/acat-api:latest.')
param containerImage string

@description('Login server of the container registry hosting containerImage. Leave empty for a public image needing no auth.')
param registryServer string = ''

@description('Registry username. Leave empty for a public image.')
param registryUsername string = ''

@secure()
@description('Registry password or token. Leave empty for a public image.')
param registryPassword string = ''

@secure()
@description('acat/api/security.py::require_write_token — gates every mutating endpoint (assess, intake, human-score writes). Required: unset means the API fails closed with 503 on all writes (by design, not a bug). Read (GET) endpoints are not gated.')
param acatWriteToken string

@secure()
@description('DATABASE_URL — acat/api/db.py, used by guidance_router.py and findings_router.py for Postgres access via psycopg2. Note: psycopg2 is not in requirements.txt, so unless the image is rebuilt with it added, db.py silently falls back to an in-memory mock connection (empty reads, no-op writes) rather than failing — confirm this is still true of the Railway deployment before assuming this needs a real value here.')
param databaseUrl string = ''

@secure()
@description('SUPABASE_URL — acat/api/services/ingest_service.py, scoring_service.py, routes/human_score_route.py.')
param supabaseUrl string = ''

@secure()
@description('SUPABASE_KEY — same call sites as supabaseUrl.')
param supabaseKey string = ''

@secure()
@description('SUPABASE_ANON_KEY — acat/api/services/scoring_service.py.')
param supabaseAnonKey string = ''

@secure()
@description('SUPABASE_SERVICE_ROLE_KEY — acat/api/services/ingest_service.py, routes/human_score_route.py. Privileged — scope access to this deployment only.')
param supabaseServiceRoleKey string = ''

@secure()
@description('QDRANT_URL — acat/api/routes/findings_router.py.')
param qdrantUrl string = ''

@secure()
@description('ORIGINSTAMP_API_KEY — acat/api/routes/human_score_route.py.')
param originstampApiKey string = ''

@description('vCPU for the single container.')
param cpuCores string = '0.25'

@description('Memory for the single container.')
param memorySize string = '0.5Gi'

@description('Minimum replica count.')
@minValue(0)
@maxValue(1)
param minReplicas int = 1

@description('Maximum replica count.')
param maxReplicas int = 2

var hasRegistry = !empty(registryServer)

// Secrets are declared unconditionally (Container Apps allows an unused secret
// definition), but env vars only reference the ones with real values — an empty
// secure param becomes an empty string, and the affected route degrades the same
// way it already does on Railway when that variable is unset, per each param's
// description above. envFor() below filters those out rather than passing empties.
var allSecrets = [
  { name: 'acat-write-token', value: acatWriteToken }
  { name: 'database-url', value: databaseUrl }
  { name: 'supabase-url', value: supabaseUrl }
  { name: 'supabase-key', value: supabaseKey }
  { name: 'supabase-anon-key', value: supabaseAnonKey }
  { name: 'supabase-service-role-key', value: supabaseServiceRoleKey }
  { name: 'qdrant-url', value: qdrantUrl }
  { name: 'originstamp-api-key', value: originstampApiKey }
]
var definedSecrets = [for s in allSecrets: { name: s.name, value: s.value }]

var envMap = [
  { name: 'ACAT_WRITE_TOKEN', secretRef: 'acat-write-token', has: !empty(acatWriteToken) }
  { name: 'DATABASE_URL', secretRef: 'database-url', has: !empty(databaseUrl) }
  { name: 'SUPABASE_URL', secretRef: 'supabase-url', has: !empty(supabaseUrl) }
  { name: 'SUPABASE_KEY', secretRef: 'supabase-key', has: !empty(supabaseKey) }
  { name: 'SUPABASE_ANON_KEY', secretRef: 'supabase-anon-key', has: !empty(supabaseAnonKey) }
  { name: 'SUPABASE_SERVICE_ROLE_KEY', secretRef: 'supabase-service-role-key', has: !empty(supabaseServiceRoleKey) }
  { name: 'QDRANT_URL', secretRef: 'qdrant-url', has: !empty(qdrantUrl) }
  { name: 'ORIGINSTAMP_API_KEY', secretRef: 'originstamp-api-key', has: !empty(originstampApiKey) }
]
var envVars = [for e in filter(envMap, m => m.has): { name: e.name, secretRef: e.secretRef }]

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${environmentName}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource acatApiApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8080
        transport: 'http'
        allowInsecure: false
      }
      registries: hasRegistry ? [
        {
          server: registryServer
          username: registryUsername
          passwordSecretRef: 'registry-password'
        }
      ] : []
      secrets: concat(
        definedSecrets,
        hasRegistry ? [{ name: 'registry-password', value: registryPassword }] : []
      )
    }
    template: {
      containers: [
        {
          name: containerAppName
          image: containerImage
          env: envVars
          resources: {
            cpu: json(cpuCores)
            memory: memorySize
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8080
              }
              initialDelaySeconds: 5
              periodSeconds: 30
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
      }
    }
  }
}

@description('Public URL of the deployed ACAT API.')
output acatApiUrl string = 'https://${acatApiApp.properties.configuration.ingress.fqdn}'
