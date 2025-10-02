// Development environment - Consumption profile
// Deploy to: bpe-rg (existing, West Europe) with resources in Switzerland North
using './main.bicep'

param namePrefix = 'bpe'
param location = 'switzerlandnorth' // Resource location

// Reference existing shared resources (same RG currently)
param acrName = 'zhlacr'
param acrResourceGroup = '' // Same RG as deployment
param storageAccountName = 'transformer336zhl'
param storageResourceGroup = '' // Same RG as deployment

param fileShareName = 'cs336zhl'
param artifactsContainer = 'bpe-artifacts'

// Consumption profile (no workload profile)
param workloadProfileName = ''
param dedicatedProfileSku = ''

// Container image
param imageRepo = 'cs336-bpe'
param imageTag = 'latest'

// Resource allocation (consumption limits)
param cpu = 1
param memory = '2Gi'

// Training parameters
param trainDataPath = '/data/tokenizer/corpus.en'
param vocabSize = '500'

// Notifications
param alertEmailAddress = 'lucas.zeh.lu@gmail.com'