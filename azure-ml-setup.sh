#!/bin/bash
# Azure ML Setup Script for BPE Training
# Uses REGULAR (Dedicated) instances for reliability

set -e

# Configuration
RG_NAME="${RG_NAME:-bpe-rg}"
LOCATION="${LOCATION:-switzerlandnorth}"
WORKSPACE_NAME="${WORKSPACE_NAME:-bpe-workspace}"
COMPUTE_NAME="${COMPUTE_NAME:-cpu-cluster}"

# Compute size (can override for larger memory needs)
COMPUTE_SIZE="${COMPUTE_SIZE:-Standard_D32_v3}"  # 32 vCPU, 128 GiB RAM

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     Azure ML Setup for BPE Training (Regular Instances)  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Configuration:"
echo "  Resource Group:  $RG_NAME"
echo "  Location:        $LOCATION"
echo "  Workspace:       $WORKSPACE_NAME"
echo "  Compute:         $COMPUTE_NAME"
echo "  Size:            $COMPUTE_SIZE (32 vCPU, 128 GiB RAM)"
echo "  Tier:            Dedicated (regular pricing, guaranteed)"
echo ""

# Step 1: Create resource group
echo "📦 Creating resource group..."
if az group show --name "$RG_NAME" &>/dev/null; then
    echo "✅ Resource group already exists"
else
    az group create --name "$RG_NAME" --location "$LOCATION"
    echo "✅ Resource group created"
fi

# Step 2: Install Azure ML extension
echo ""
echo "🔧 Installing Azure ML CLI extension..."
az extension add --name ml --yes --only-show-errors 2>/dev/null || \
az extension update --name ml --only-show-errors 2>/dev/null
echo "✅ Azure ML CLI ready"

# Step 3: Create workspace
echo ""
echo "🏗️  Creating Azure ML workspace..."
if az ml workspace show --name "$WORKSPACE_NAME" -g "$RG_NAME" &>/dev/null; then
    echo "✅ Workspace already exists"
else
    az ml workspace create \
        --name "$WORKSPACE_NAME" \
        --resource-group "$RG_NAME" \
        --location "$LOCATION"
    echo "✅ Workspace created"
fi

# Step 4: Create compute cluster
echo ""
echo "⚙️  Creating compute cluster..."
if az ml compute show --name "$COMPUTE_NAME" -w "$WORKSPACE_NAME" -g "$RG_NAME" &>/dev/null; then
    echo "✅ Compute cluster already exists"
else
    az ml compute create \
        --name "$COMPUTE_NAME" \
        --type AmlCompute \
        --size "$COMPUTE_SIZE" \
        --min-instances 0 \
        --max-instances 1 \
        --tier Dedicated \
        --idle-time-before-scale-down 300 \
        --workspace-name "$WORKSPACE_NAME" \
        --resource-group "$RG_NAME"
    echo "✅ Compute cluster created"
fi

# Get workspace URL
WORKSPACE_ID=$(az ml workspace show \
    --name "$WORKSPACE_NAME" \
    -g "$RG_NAME" \
    --query id -o tsv)

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete ✅                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Compute Details:"
echo "  • Size: Standard_D32_v3 (32 vCPU, 128 GiB RAM)"
echo "  • Cost: ~\$1.20/hour (~\$12 for 10-hour training)"
echo "  • Scaling: Auto-scales from 0 → 1 nodes on demand"
echo "  • Auto-shutdown: 5 minutes after job completes"
echo ""
echo "Next Steps:"
echo ""
echo "1️⃣  Upload your training data:"
echo "   bash upload-data.sh"
echo ""
echo "2️⃣  Submit training job:"
echo "   az ml job create --file aml-job.yml -g $RG_NAME -w $WORKSPACE_NAME"
echo ""
echo "3️⃣  Monitor in Azure ML Studio (automatic dashboards):"
echo "   https://ml.azure.com/workspaces/$WORKSPACE_ID"
echo ""
echo "4️⃣  Stream logs in terminal:"
echo "   az ml job stream --name <job-name> -g $RG_NAME -w $WORKSPACE_NAME"
echo ""
echo "💡 Monitoring is automatic - Azure ML tracks CPU, memory,"
echo "   and multiprocessing workers without any code changes!"
echo ""