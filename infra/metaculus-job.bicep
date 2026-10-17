// Azure Container Apps JOB for the HumanAIOS forecasting bot (tools/Metaculus/main.py).
// A job, not a Container App: main.py runs one pass via asyncio.run(...) and exits: no
// serve loop, no ingress. Already deployed on Railway as a plain service running
// `python main.py --mode test_questions` on each deploy — no committed cron config
// there either, so this defaults to a manual trigger (safe/non-committal) rather than
// guessing a real-world cadence. Set scheduleCronExpression only after a fresh
// Railway recheck confirms the old writer/scheduler is stopped and the handover
// has been approved. An old repository snapshot is not proof of writer shutdown.
//
// Scaffolding only — written without Azure access from this session, so it has not
// been deployed or validated against a real subscription. Review before applying.
//
// Two provider-key gaps to resolve before this actually runs (see Dockerfile's own
// comment for detail): main.py calls the third-party forecasting-tools package for
// its LLM calls (Anthropic/Groq/OpenAI) and Metaculus API access, and that package
// reads its own env vars internally — this repo's code never names them, so the
// param names below (anthropicApiKey, groqApiKey, openaiApiKey, metaculusToken) are
// the standard ecosystem convention, not confirmed against forecasting-tools' own
// docs. Confirm the real names before relying on this.
//
// Prerequisites:
//   1. Build and push the image (from tools/Metaculus/):
//        docker build -t <registry>/metaculus-bot:<tag> .
//        docker push <registry>/metaculus-bot:<tag>
//   2. Deploy:
//        az deployment group create \
//          --resource-group <rg> \
//          --template-file infra/metaculus-job.bicep \
//          --parameters containerImage=<registry>/metaculus-bot:<tag> \
//                       supabaseUrl=<url> supabaseKey=<key> \
//                       anthropicApiKey=<key> groqApiKey=<key> openaiApiKey=<key> \
//                       metaculusToken=<token> \
//                       registryServer=<registry> registryUsername=<user> registryPassword=<token>
//   3. Trigger a run (manual trigger; nothing runs until you do this):
//        az containerapp job start --name metaculus-bot --resource-group <rg>

@description('Azure region for all resources. Defaults to the resource group\'s region.')
param location string = resourceGroup().location

@description('Container Apps Environment name in this resource group. Set useExistingEnvironment=true to reference it without changing its logging configuration.')
param environmentName string = 'humanaios-metaculus-env'

@description('Reference an existing environment without deploying an environment or Log Analytics workspace. False creates/manages both resources; review deployment changes before applying.')
param useExistingEnvironment bool = false

@description('Container Apps Job name.')
param jobName string = 'metaculus-bot'

@description('Fully qualified image reference, e.g. myregistry.azurecr.io/metaculus-bot:latest.')
param containerImage string

@description('Login server of the container registry hosting containerImage. Leave empty for a public image needing no auth.')
param registryServer string = ''

@description('Registry username. Leave empty for a public image.')
param registryUsername string = ''

@secure()
@description('Registry password or token. Leave empty for a public image.')
param registryPassword string = ''

@description('main.py --mode. tournament targets seasonal + minibench; metaculus_cup targets the cup. test_questions also makes provider calls and publishes forecasts for four example questions, with skipping off. Running any mode can cause external writes and provider charges; test_questions is not a read-only smoke test.')
@allowed(['tournament', 'metaculus_cup', 'test_questions'])
param mode string = 'test_questions'

@description('Overrides BOT_RUN_ID (main.py --run-id). Leave empty to use main.py\'s own default (BOT_RUN_ID env var, or an auto-generated S-bot-MMDDYY id).')
param botRunId string = ''

@secure()
param supabaseUrl string

@secure()
param supabaseKey string

@secure()
@description('Standard LiteLLM/forecasting-tools convention for the "anthropic/claude-haiku-4-5" forecast model — confirm against forecasting-tools\' own docs.')
param anthropicApiKey string = ''

@secure()
@description('Standard convention for the "groq/openai/gpt-oss-120b" researcher model — confirm against forecasting-tools\' own docs.')
param groqApiKey string = ''

@secure()
@description('Standard convention for the gpt-4o-mini parser/summarizer models — confirm against forecasting-tools\' own docs.')
param openaiApiKey string = ''

@secure()
@description('Metaculus API token for MetaculusClient() — confirm the exact env var name (commonly METACULUS_TOKEN) against forecasting-tools\' own docs.')
param metaculusToken string = ''

@description('vCPU for the job container.')
param cpuCores string = '0.5'

@description('Memory for the job container.')
param memorySize string = '1Gi'

@description('Seconds before an in-progress run is forcibly stopped. A tournament pass forecasts many questions sequentially — err high.')
param replicaTimeoutSeconds int = 1800

@description('Opt-in UTC cron schedule. Empty keeps Manual trigger. Before deploying a schedule, freshly recheck Railway and stop the old writer/scheduler, verify provider credentials, and obtain handover approval.')
param scheduleCronExpression string = ''

var hasRegistry = !empty(registryServer)
var isScheduled = !empty(scheduleCronExpression)

var allSecrets = [
  { name: 'supabase-url', value: supabaseUrl }
  { name: 'supabase-key', value: supabaseKey }
  { name: 'anthropic-api-key', value: anthropicApiKey }
  { name: 'groq-api-key', value: groqApiKey }
  { name: 'openai-api-key', value: openaiApiKey }
  { name: 'metaculus-token', value: metaculusToken }
]
var configuredSecrets = filter(allSecrets, secret => !empty(secret.value))

var envMap = [
  { name: 'SUPABASE_URL', secretRef: 'supabase-url', has: !empty(supabaseUrl) }
  { name: 'SUPABASE_KEY', secretRef: 'supabase-key', has: !empty(supabaseKey) }
  { name: 'ANTHROPIC_API_KEY', secretRef: 'anthropic-api-key', has: !empty(anthropicApiKey) }
  { name: 'GROQ_API_KEY', secretRef: 'groq-api-key', has: !empty(groqApiKey) }
  { name: 'OPENAI_API_KEY', secretRef: 'openai-api-key', has: !empty(openaiApiKey) }
  { name: 'METACULUS_TOKEN', secretRef: 'metaculus-token', has: !empty(metaculusToken) }
]
var secretEnvVars = [for e in filter(envMap, m => m.has): { name: e.name, secretRef: e.secretRef }]
var runIdEnvVar = !empty(botRunId) ? [{ name: 'BOT_RUN_ID', value: botRunId }] : []
var jobArgs = concat(['--mode', mode], !empty(botRunId) ? ['--run-id', botRunId] : [])

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = if (!useExistingEnvironment) {
  name: '${environmentName}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource existingEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' existing = if (useExistingEnvironment) {
  name: environmentName
}

resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = if (!useExistingEnvironment) {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics!.properties.customerId
        sharedKey: logAnalytics!.listKeys().primarySharedKey
      }
    }
  }
}

resource metaculusJob 'Microsoft.App/jobs@2024-03-01' = {
  name: jobName
  location: location
  properties: {
    environmentId: useExistingEnvironment ? existingEnvironment.id : containerAppEnvironment.id
    configuration: {
      triggerType: isScheduled ? 'Schedule' : 'Manual'
      replicaTimeout: replicaTimeoutSeconds
      replicaRetryLimit: 0
      manualTriggerConfig: !isScheduled ? {
        replicaCompletionCount: 1
        parallelism: 1
      } : null
      scheduleTriggerConfig: isScheduled ? {
        cronExpression: scheduleCronExpression
        parallelism: 1
        replicaCompletionCount: 1
      } : null
      registries: hasRegistry ? [
        {
          server: registryServer
          username: registryUsername
          passwordSecretRef: 'registry-password'
        }
      ] : []
      secrets: concat(
        configuredSecrets,
        hasRegistry ? [{ name: 'registry-password', value: registryPassword }] : []
      )
    }
    template: {
      containers: [
        {
          name: jobName
          image: containerImage
          args: jobArgs
          env: concat(secretEnvVars, runIdEnvVar)
          resources: {
            cpu: json(cpuCores)
            memory: memorySize
          }
        }
      ]
    }
  }
}

@description('Resource ID of the job, for `az containerapp job start`.')
output metaculusJobId string = metaculusJob.id
