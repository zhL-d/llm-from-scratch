using './main.bicep'

param namePrefix = 'bpe'
param location = 'switzerlandnorth' // '' = use resource group's location; or 'westeurope'

param acrName = 'zhlacr'
param storageAccountName = 'transformer336zhl'

param fileShareName = 'cs336zhl'
param artifactsContainer = 'bpe-artifacts'
param workloadProfileName = ''  // leave empty to use default

param imageRepo = 'cs336-bpe'
param imageTag = '9647f9ae898501dbb734600cb15ac7eb6072ca23'
// Keep imageTag at module default ('latest'); workflow updates image out-of-band

param cpu = 1
param memory = '2Gi'

// param trainDataPath = '/data/corpus.en'
// param vocabSize = '500'
