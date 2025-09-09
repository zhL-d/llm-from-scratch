using './main.bicep'

param namePrefix = 'bpe'
param location = 'Switzerland North' // '' = use resource group's location; or 'westeurope'

param acrName = 'zhlacr'
param storageAccountName = 'transformer336zhl'
@secure()
param storageAccountKey = 'EhZjZHpnDoZvJ6zgAuES4ORg1WzZ32XEd3bMo1r6HJDFzNj3mnL6X0ZImas2EBiUh7q6irIK68Xi+ASttCbpqA=='

param fileShareName = 'cs336zhl'
param artifactsContainer = 'bpe-artifacts'
param workloadProfileName = ''  // leave empty to use default

param imageRepo = 'cs336-bpe'
param imageTag = '9647f9ae898501dbb734600cb15ac7eb6072ca23'

param cpu = 4
param memory = '16Gi'

param trainDataPath = '/data/tokenizer/corpus.en'
param vocabSize = '1000'
