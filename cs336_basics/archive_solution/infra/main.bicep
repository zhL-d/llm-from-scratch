// ========================================
// PARAMETERS
// ========================================

param namePrefix string = 'bpe'
param location string = resourceGroup().location

// The email address that will receive the job completion notifications.
param alertEmailAddress string

// ========================================
// SHARED RESOURCE REFERENCES
// These resources typically live in a separate long-lived resource group
// ========================================

@description('Existing ACR name (e.g., zhlacr). We do NOT create ACR here.')
param acrName string

@description('Resource group containing the ACR. If empty, assumes same RG as this deployment.')
param acrResourceGroup string = ''

@description('Existing Storage Account name for Files+Blob (e.g., transformer336zhl)')
param storageAccountName string

@description('Resource group containing the Storage Account. If empty, assumes same RG.')
param storageResourceGroup string = ''

@description('Azure Files share name for training data.')
param fileShareName string = 'cs336zhl'

@description('Blob container for artifacts')
param artifactsContainer string = 'bpe-artifacts'

// Note: UAMI is created per environment for isolation and easier cleanup
// (Best practice for ephemeral dedicated environments)

// ========================================
// CONTAINER APPS ENVIRONMENT CONFIG
// ========================================

@description('Workload profile name for dedicated environments. Leave empty for consumption.')
param workloadProfileName string = ''

@description('Create dedicated workload profile (D4/D8/D16/D32). Leave empty to skip profile creation.')
@allowed(['', 'D4', 'D8', 'D16', 'D32'])
param dedicatedProfileSku string = ''

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

// ========================================
// SHARED RESOURCES (EXISTING)
// For cross-RG scenarios, we build resource IDs manually
// ========================================

// ACR - only reference if in same RG
resource acr 'Microsoft.ContainerRegistry/registries@2025-04-01' existing = if (empty(acrResourceGroup)) {
  name: acrName
}

// Storage Account - only reference if in same RG
resource stg 'Microsoft.Storage/storageAccounts@2025-01-01' existing = if (empty(storageResourceGroup)) {
  name: storageAccountName
}

// For cross-RG scenarios, build resource IDs manually
var acrResourceId = empty(acrResourceGroup)
  ? acr.id
  : resourceId(acrResourceGroup, 'Microsoft.ContainerRegistry/registries', acrName)

var stgResourceId = empty(storageResourceGroup)
  ? stg.id
  : resourceId(storageResourceGroup, 'Microsoft.Storage/storageAccounts', storageAccountName)

var acrLoginServer = empty(acrResourceGroup)
  ? acr.properties.loginServer
  : '${acrName}.azurecr.io'

// ========================================
// ENVIRONMENT-SPECIFIC RESOURCES
// These are created in this deployment's RG
// ========================================

// ----- Log Analytics -----
resource law 'Microsoft.OperationalInsights/workspaces@2025-02-01' = {
  name: '${namePrefix}-law'
  location: location
  properties: { retentionInDays: 30 }
}

// ----- Container Apps Environment -----
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
    // Add workload profiles for dedicated environments
    workloadProfiles: !empty(dedicatedProfileSku) ? [
      {
        name: workloadProfileName
        workloadProfileType: dedicatedProfileSku
        minimumCount: 1
        maximumCount: 1
      }
    ] : []
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


// ========================================
// MANAGED IDENTITY + RBAC
// Each environment gets its own UAMI for isolation
// ========================================

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: '${namePrefix}-uami'
  location: location
}

// Role definitions
var acrPullRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
var blobDataContributor = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')

// RBAC: ACR Pull (same RG only)
// For cross-RG RBAC, assign manually or use a separate deployment to the shared RG
resource raAcr 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (empty(acrResourceGroup)) {
  name: guid(acr.id, uami.id, 'acr-pull')
  scope: acr
  properties: {
    roleDefinitionId: acrPullRole
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// RBAC: Blob Data Contributor (same RG only)
// For cross-RG RBAC, assign manually or use a separate deployment to the shared RG
resource raBlob 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (empty(storageResourceGroup)) {
  name: guid(stg.id, uami.id, 'blob-w')
  scope: stg
  properties: {
    roleDefinitionId: blobDataContributor
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ----- Blob containers: datasets + artifacts -----
// Only create blob container if storage is in the same RG (dev scenario)
// For cross-RG deployments (prod), containers must already exist in the shared storage account
// Create manually if needed: az storage container create --account-name <storage> --name bpe-artifacts

resource blobSvc 'Microsoft.Storage/storageAccounts/blobServices@2025-01-01' existing = if (empty(storageResourceGroup)) {
  parent: stg
  name: 'default'
}

resource artifacts 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01' = if (empty(storageResourceGroup)) {
  name: artifactsContainer
  parent: blobSvc
  properties: { publicAccess: 'None' }
}

// Note: For cross-RG scenarios, we don't create or reference containers here.
// The Container Apps job will access containers directly using UAMI credentials.

// ----- Azure Files: register storage with CAE (uses account key) -----
resource envStorage 'Microsoft.App/managedEnvironments/storages@2025-01-01' = {
  parent: cae
  name: '${storageAccountName}-files'
  properties: {
    azureFile: {
      accountName: storageAccountName
      // Use listKeys with manually constructed resource ID for cross-RG scenario
      accountKey: listKeys(stgResourceId, '2025-01-01').keys[0].value
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
          server: acrLoginServer
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
          image: '${acrLoginServer}/${imageRepo}:${imageTag}'
          name: 'trainer'
          resources: {
            cpu: cpu
            memory: memory
          }
          env: [
            { name: 'LOG_DIR', value: 'cs336_basics/outputs' }, { name: 'TRAINDATA_PATH', value: trainDataPath }, { name: 'VOCAB_SIZE', value: vocabSize }, { name: 'RUN_CONTEXT', value: 'AZURE' }, { name: 'AZCOPY_MSI_CLIENT_ID', value: uami.properties.clientId }
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
output uamiPrincipalId string = uami.properties.principalId
output acrLoginServer string = acrLoginServer
output storageName string = storageAccountName
