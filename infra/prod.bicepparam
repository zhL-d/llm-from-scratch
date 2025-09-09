using './main.bicep'

param namePrefix = 'bpe'
// param location = 'switzerlandnorth' // '' = use resource group's location; or 'westeurope'

param acrName = 'zhlacr'
param storageAccountName = 'transformer336zhl'
@secure()
param storageAccountKey = ''

param fileShareName = 'cs336zhl'
param artifactsContainer = 'bpe-artifacts'
param workloadProfileName = ''  // leave empty to use default

param imageRepo = 'cs336-bpe'
// Keep imageTag at module default ('latest'); workflow updates image out-of-band

param cpu = 4
param memory = '16Gi'

// param trainDataPath = '/data/corpus.en'
// param vocabSize = '500'
