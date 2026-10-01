// Azure Container Apps deployment for resource-miner (humanaios-funding-pipeline).
//
// Scaffolding only — written without Azure access from this session, so it has not
// been deployed or validated against a real subscription. Review before applying.
//
// Prerequisites:
//   1. Build and push the image (from humanaios-funding-pipeline/):
//        docker build -f Dockerfile.resource-miner -t <registry>/resource-miner:<tag> .
//        docker push <registry>/resource-miner:<tag>
//   2. Deploy:
//        az deployment group create \
//          --resource-group <rg> \
//          --template-file infra/resource-miner-containerapp.bicep \
//          --parameters containerImage=<registry>/resource-miner:<tag> \
//                       registryServer=<registry> \
//                       registryUsername=<user> \
//                       registryPassword=<token-or-password>
//
// resource-miner itself needs no secrets (stdlib-only, reads checked-in JSON files) —
// registryServer/Username/Password are only for pulling the image if the registry is
// private (e.g. Azure Container Registry). Omit all three for a public image.

@description('Azure region for all resources. Defaults to the resource group\'s region.')
param location string = resourceGroup().location

@description('Container Apps Environment name. Shared if other funding-pipeline services are added later.')
param environmentName string = 'humanaios-funding-pipeline-env'

@description('Container App name.')
param containerAppName string = 'resource-miner'

@description('Fully qualified image reference, e.g. myregistry.azurecr.io/resource-miner:latest.')
param containerImage string

@description('Login server of the container registry hosting containerImage, e.g. myregistry.azurecr.io. Leave empty for a public image needing no auth.')
param registryServer string = ''

@description('Registry username. Leave empty for a public image.')
param registryUsername string = ''

@secure()
@description('Registry password or token. Leave empty for a public image.')
param registryPassword string = ''

@description('vCPU for the single container. Must pair with memorySize at one of Container Apps\' valid combinations (0.25/0.5Gi is the smallest).')
param cpuCores string = '0.25'

@description('Memory for the single container.')
param memorySize string = '0.5Gi'

@description('Minimum replica count. 1 keeps the app always warm; 0 allows scale-to-zero between requests but means idle gaps in the Milestone 3 60-day sustained-usage window.')
@minValue(0)
@maxValue(1)
param minReplicas int = 1

@description('Maximum replica count.')
param maxReplicas int = 2

var hasRegistry = !empty(registryServer)

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

resource resourceMinerApp 'Microsoft.App/containerApps@2024-03-01' = {
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
      secrets: hasRegistry ? [
        {
          name: 'registry-password'
          value: registryPassword
        }
      ] : []
    }
    template: {
      containers: [
        {
          name: containerAppName
          image: containerImage
          resources: {
            cpu: json(cpuCores)
            memory: memorySize
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/api/health'
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

@description('Public URL of the deployed resource-miner service.')
output resourceMinerUrl string = 'https://${resourceMinerApp.properties.configuration.ingress.fqdn}'
