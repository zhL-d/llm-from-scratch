# Cross-Resource Group Bicep Solution

## Problem

Azure Bicep doesn't allow deploying resources with `scope` properties that differ from the deployment scope. This caused compilation errors when trying to reference resources (ACR, Storage) from a different resource group.

### Error Messages:
```
BCP139: A resource's scope must match the scope of the Bicep file for it to be deployable.
BCP165: A resource's computed scope must match that of the Bicep file for it to be deployable.
BCP181: This expression is being used in an argument of the function "listKeys", which requires a value that can be calculated at the start of the deployment.
```

## Solution Overview

The solution uses **manual resource ID construction** and **conditional resource declarations** instead of cross-scope resource references:

1. **Same-RG scenario (dev):** Reference resources directly using `existing` keyword
2. **Cross-RG scenario (prod):** Construct resource IDs manually using `resourceId()` function
3. **RBAC assignments:** Handle cross-RG RBAC in GitHub Actions workflow, not in Bicep

## Implementation Details

### 1. Resource References (main.bicep)

```bicep
// Only reference resources if in the same RG
resource acr 'Microsoft.ContainerRegistry/registries@2025-04-01' existing = if (empty(acrResourceGroup)) {
  name: acrName
}

resource stg 'Microsoft.Storage/storageAccounts@2025-01-01' existing = if (empty(storageResourceGroup)) {
  name: storageAccountName
}

// For cross-RG, build resource IDs manually
var acrResourceId = empty(acrResourceGroup)
  ? acr.id
  : resourceId(acrResourceGroup, 'Microsoft.ContainerRegistry/registries', acrName)

var stgResourceId = empty(storageResourceGroup)
  ? stg.id
  : resourceId(storageResourceGroup, 'Microsoft.Storage/storageAccounts', storageAccountName)

var acrLoginServer = empty(acrResourceGroup)
  ? acr.properties.loginServer
  : '${acrName}.azurecr.io'  // Construct login server from name
```

### 2. Runtime Operations (listKeys)

```bicep
// Works for both same-RG and cross-RG
accountKey: listKeys(stgResourceId, '2025-01-01').keys[0].value
```

The `listKeys()` function accepts manual resource IDs, so this works even when the storage account is in a different RG.

### 3. RBAC Assignments

**In Bicep (same-RG only):**
```bicep
resource raAcr 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (empty(acrResourceGroup)) {
  name: guid(acr.id, uami.id, 'acr-pull')
  scope: acr
  properties: {
    roleDefinitionId: acrPullRole
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}
```

**In GitHub Actions (cross-RG):**
```bash
# Get UAMI Principal ID from deployment output
UAMI_PRINCIPAL_ID=$(az deployment group show \
  --resource-group "$RG_PROD" \
  --name "$DEPLOYMENT_NAME" \
  --query properties.outputs.uamiPrincipalId.value -o tsv)

# Assign roles to shared resources
az role assignment create \
  --assignee "$UAMI_PRINCIPAL_ID" \
  --role "AcrPull" \
  --scope "/subscriptions/<sub-id>/resourceGroups/bpe-rg/providers/Microsoft.ContainerRegistry/registries/zhlacr"

az role assignment create \
  --assignee "$UAMI_PRINCIPAL_ID" \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/<sub-id>/resourceGroups/bpe-rg/providers/Microsoft.Storage/storageAccounts/transformer336zhl"
```

### 4. Blob Containers

**Same-RG (dev):** Created by Bicep
```bicep
resource artifacts 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01' = if (empty(storageResourceGroup)) {
  name: artifactsContainer
  parent: blobSvc
  properties: { publicAccess: 'None' }
}
```

**Cross-RG (prod):** Must exist before deployment
```bash
# One-time setup
az storage container create \
  --account-name transformer336zhl \
  --name bpe-artifacts \
  --auth-mode login
```

## Deployment Flow

### Dev Environment (Same RG)
```bash
az deployment group create \
  --resource-group bpe-rg \
  --template-file infra/main.bicep \
  --parameters @infra/dev.bicepparam
```

**What happens:**
1. ✅ References ACR and Storage in same RG using `existing` keyword
2. ✅ Creates blob container
3. ✅ Assigns RBAC roles in Bicep
4. ✅ Deploys Container Apps environment

### Prod Environment (Cross RG)
```bash
# 1. Create resource group
az group create -n rg-bpe-prod -l switzerlandnorth

# 2. Deploy infrastructure
az deployment group create \
  --resource-group rg-bpe-prod \
  --template-file infra/main.bicep \
  --parameters @infra/prod.bicepparam

# 3. Get UAMI Principal ID
UAMI_ID=$(az deployment group show \
  --resource-group rg-bpe-prod \
  --name <deployment-name> \
  --query properties.outputs.uamiPrincipalId.value -o tsv)

# 4. Assign RBAC roles manually
az role assignment create --assignee "$UAMI_ID" --role "AcrPull" --scope <acr-id>
az role assignment create --assignee "$UAMI_ID" --role "Storage Blob Data Contributor" --scope <storage-id>
```

**Or use GitHub Actions workflow** (handles steps 1-4 automatically):
```bash
gh workflow run deploy-dedicated.yml -f autoCleanup=true
```

## Why This Approach?

### ❌ Alternative: Bicep Modules

You could create a separate module deployed to the shared RG:
```bicep
module rbacAssignments './rbac-module.bicep' = {
  name: 'rbac-assignments'
  scope: resourceGroup('bpe-rg')
  params: {
    uamiPrincipalId: uami.properties.principalId
  }
}
```

**Problems:**
- Requires nested deployments
- More complex error handling
- Module file needs to know shared RG name

### ✅ Chosen Approach: Manual Resource IDs + Workflow RBAC

**Benefits:**
- ✅ Single Bicep file
- ✅ Clear separation: infrastructure in Bicep, cross-RG orchestration in workflow
- ✅ Easier to understand and debug
- ✅ No nested deployment complexity
- ✅ RBAC assignments idempotent (can rerun safely)

## Parameters Configuration

### dev.bicepparam (Same RG)
```bicep
param acrResourceGroup = ''  // Empty = same RG
param storageResourceGroup = ''  // Empty = same RG
```

### prod.bicepparam (Cross RG)
```bicep
param acrResourceGroup = 'bpe-rg'  // Shared RG
param storageResourceGroup = 'bpe-rg'  // Shared RG
```

## Prerequisites

Before deploying to production (cross-RG):

1. ✅ **Blob container must exist**
   ```bash
   az storage container create --account-name transformer336zhl --name bpe-artifacts --auth-mode login
   ```

2. ✅ **Azure Files share must exist**
   ```bash
   az storage share create --account-name transformer336zhl --name cs336zhl
   ```

3. ✅ **ACR and Storage Account must exist** in shared RG
   - ACR: `zhlacr`
   - Storage: `transformer336zhl`

## Verification

### Check Bicep compilation
```bash
az bicep build --file infra/main.bicep
# Should complete without errors
```

### Test dev deployment
```bash
az deployment group create \
  --resource-group bpe-rg \
  --template-file infra/main.bicep \
  --parameters @infra/dev.bicepparam \
  --what-if
```

### Test prod deployment
```bash
az deployment group create \
  --resource-group rg-bpe-prod \
  --template-file infra/main.bicep \
  --parameters @infra/prod.bicepparam \
  --what-if
```

## Troubleshooting

### Error: "Container not found"
**Solution:** Create blob container in shared storage account first:
```bash
az storage container create --account-name transformer336zhl --name bpe-artifacts --auth-mode login
```

### Error: "Insufficient permissions to pull image"
**Solution:** RBAC assignments may not have propagated. Wait 5 minutes or manually assign:
```bash
az role assignment create \
  --assignee <uami-principal-id> \
  --role "AcrPull" \
  --scope /subscriptions/<sub-id>/resourceGroups/bpe-rg/providers/Microsoft.ContainerRegistry/registries/zhlacr
```

### Error: "Forbidden" when accessing Azure Files
**Solution:** This uses Storage Account keys, not RBAC. Check that `listKeys()` is working:
```bash
az storage account keys list --account-name transformer336zhl --resource-group bpe-rg
```

## Summary

This solution successfully enables multi-environment deployments with shared resources across resource groups while maintaining Bicep best practices:

- ✅ No cross-scope resource declarations
- ✅ Works with both same-RG and cross-RG scenarios
- ✅ Clear separation of concerns
- ✅ Automated via GitHub Actions
- ✅ Idempotent and safe to rerun

The key insight: **Use manual resource ID construction for cross-RG references instead of trying to make Bicep handle cross-scope deployments.**