// Production environment - Dedicated profile for large-scale training
// Deploy to: rg-bpe-prod (ephemeral, delete after training)
using './main.bicep'

param namePrefix = 'bpeprod'
param location = 'switzerlandnorth'

// Reference shared resources from bpe-rg
param acrName = 'zhlacr'
param acrResourceGroup = 'bpe-rg' // Shared resource group
param storageAccountName = 'transformer336zhl'
param storageResourceGroup = 'bpe-rg' // Shared resource group

param fileShareName = 'cs336zhl'
param artifactsContainer = 'bpe-artifacts'

// Dedicated profile for high-memory training
// D16 = 16 vCPU, 64 GiB memory
// D32 = 32 vCPU, 128 GiB memory (for 100GB+ memory requirements)
param workloadProfileName = 'Dedicated'
param dedicatedProfileSku = 'D32' // 32 vCPU, 128 GiB

// Container image (updated by CI/CD)
param imageRepo = 'cs336-bpe'
param imageTag = 'latest'

// Job resource allocation (can use up to profile max)
param cpu = 32
param memory = '120Gi' // Leave headroom for system overhead

// Training parameters (override via workflow)
param trainDataPath = '/data/tokenizer/corpus.en'
param vocabSize = '500'

// Notifications
param alertEmailAddress = 'lucas.zeh.lu@gmail.com'
