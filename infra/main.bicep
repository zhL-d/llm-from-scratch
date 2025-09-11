param namePrefix string = 'bpe'
param location string = resourceGroup().location

// The email address that will receive the job completion notifications.
param alertEmailAddress string

// // The name of the Container App Job to monitor.
// param containerAppJobName string = 'bpe-train'

// Existing resources you already created
@description('Existing ACR name (e.g., zhlacr). We do NOT create ACR here.')
param acrName string

@description('Existing Storage Account name for Files+Blob (e.g., transformer336zhl)')
param storageAccountName string

// Storage Account key is resolved at deploy time via listKeys; not passed via params.

@description('Azure Files share name for training data.')
param fileShareName string = 'cs336zhl'

@description('Blob containers for artifacts')
// param datasetsContainer string = 'datasets'
param artifactsContainer string = 'bpe-artifacts'

// Optional: workload profile name (Dedicated). Leave empty to use default.
@description('Container Apps workload profile name (Dedicated). Leave empty for default.')
param workloadProfileName string = ''

// Defaults (can be overridden at runtime/CI)
@description('Initial image repo and tag; runtime pipeline will update tag.')
param imageRepo string = 'cs336-bpe'
param imageTag string = 'latest'
@description('Initial CPU and Memory for the job (update later via pipeline).')
param cpu int = 4
param memory string = '16Gi'
@description('Initial training params.')
param trainDataPath string = '/data/tokenizer/corpus.en'
param vocabSize string = '500'

// ----- Existing resources -----
resource acr 'Microsoft.ContainerRegistry/registries@2025-04-01' existing = {
  name: acrName
}
resource stg 'Microsoft.Storage/storageAccounts@2025-01-01' existing = {
  name: storageAccountName
}

// ----- Log Analytics + Container Apps Env -----
resource law 'Microsoft.OperationalInsights/workspaces@2025-02-01' = {
  name: '${namePrefix}-law'
  location: location
  properties: { retentionInDays: 30 }
}

resource cae 'Microsoft.App/managedEnvironments@2025-01-01' = {
  name: '${namePrefix}-cae'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: law.properties.customerId
        sharedKey: listKeys(law.id, '2020-08-01').primarySharedKey
      }
    }
  }
}

// ---- Notify ----
// --- Action Group ---
// Defines who to notify when an alert is triggered.

resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: '${namePrefix}-job-completion-ag'
  location: 'Global' // Action Groups are always global
  properties: {
    groupShortName: '${namePrefix}AG'
    enabled: true
    emailReceivers: [
      {
        name: 'JobAdmins'
        emailAddress: alertEmailAddress
        useCommonAlertSchema: true
      }
    ]
  }
}


resource metricAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${namePrefix}-job-exec-alert'
  // Metric alerts are global
  location: 'global'
  properties: {
    description: 'Notify when a job run completes (success or failure).'
    severity: 3
    enabled: true
    scopes: [ job.id ]
    evaluationFrequency: 'PT1M'
    windowSize: 'PT5M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          // REQUIRED for each condition:
          criterionType: 'StaticThresholdCriterion'
          name: 'Job executions increased'
          metricNamespace: 'microsoft.app/jobs'
          metricName: 'Executions'
          timeAggregation: 'Total'
          operator: 'GreaterThan'
          threshold: 0
          // dimensions: []  // optional
        }
      ]
    }
    actions: [
      {
        actionGroupId: actionGroup.id
      }
    ]
    autoMitigate: true // optional
  }
}


// ----- UAMI + RBAC: AcrPull + Blob Data Contributor -----
resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: '${namePrefix}-uami'
  location: location
}

var acrPullRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
var blobDataContributor = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')

resource raAcr 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, uami.id, 'acr-pull')
  scope: acr
  properties: {
    roleDefinitionId: acrPullRole
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource raBlob 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(stg.id, uami.id, 'blob-w')
  scope: stg
  properties: {
    roleDefinitionId: blobDataContributor
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ----- Blob containers: datasets + artifacts -----
resource blobSvc 'Microsoft.Storage/storageAccounts/blobServices@2025-01-01' existing = {
  parent: stg
  name: 'default'
}

// resource datasets 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
//   name: datasetsContainer
//   parent: blobSvc
//   properties: { publicAccess: 'None' }
// }
resource artifacts 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01' = {
  name: artifactsContainer
  parent: blobSvc
  properties: { publicAccess: 'None' }
}

// ----- Azure Files: register storage with CAE (uses account key) -----
resource envStorage 'Microsoft.App/managedEnvironments/storages@2025-01-01' = {
  parent: cae
  name: '${storageAccountName}-files'
  properties: {
    azureFile: {
      accountName: storageAccountName
      // Resolve the key at deploy time to avoid handling secrets in CI
      accountKey: listKeys(stg.id, '2024-01-01').keys[0].value
      shareName: fileShareName
      accessMode: 'ReadOnly'
    }
  }
}

// ----- ACA Job (manual trigger) -----
resource job 'Microsoft.App/jobs@2025-01-01' = {
  name: '${namePrefix}-train'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uami.id}': {}
    }
  }
  properties: {
    environmentId: cae.id
    workloadProfileName: empty(workloadProfileName) ? null : workloadProfileName
    configuration: {
      registries: [
        {
          server: acr.properties.loginServer
          identity: uami.id
        }
      ]
      replicaTimeout: 86400
      replicaRetryLimit: 0
      manualTriggerConfig: {
        replicaCompletionCount: 1
        parallelism: 1
      }
      secrets: []
      triggerType: 'Manual'
    }
    template: {
      containers: [
        {
          image: '${acr.properties.loginServer}/${imageRepo}:${imageTag}'
          name: 'trainer'
          resources: {
            cpu: cpu
            memory: memory
          }
          env: [
            { name: 'LOG_DIR', value: 'cs336_basics/outputs' }, { name: 'TRAINDATA_PATH', value: trainDataPath }, { name: 'VOCAB_SIZE', value: vocabSize }, { name: 'RUN_CONTEXT', value: 'AZURE' }
          ]
          volumeMounts: [
            { mountPath: '/data', volumeName: 'dataset' }
          ]
        }
      ]
      volumes: [
        {
          name: 'dataset'
          storageType: 'AzureFile'
          storageName: envStorage.name
        }
      ]
    }
  }
  tags: {
    app: 'bpe'
    env: 'test'
    purpose: 'tokenizer'
  }
}

output containerAppsEnvName string = cae.name
output jobName string = job.name
output uamiId string = uami.id
output acrLoginServer string = acr.properties.loginServer
output storageName string = stg.name
