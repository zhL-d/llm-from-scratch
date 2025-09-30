#!/bin/bash
# Upload training data to Azure ML workspace

set -e

RG_NAME="${RG_NAME:-bpe-rg}"
WORKSPACE_NAME="${WORKSPACE_NAME:-bpe-workspace}"
DATA_DIR="${DATA_DIR:-./data}"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║           Upload Training Data to Azure ML               ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Configuration:"
echo "  Workspace:     $WORKSPACE_NAME"
echo "  Resource Group: $RG_NAME"
echo "  Data Directory: $DATA_DIR"
echo ""

# Check if data directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo "❌ Error: Data directory '$DATA_DIR' not found"
    echo ""
    echo "Please download data first:"
    echo "  mkdir -p data && cd data"
    echo "  wget https://huggingface.co/datasets/roneneldan/TinyStories/resolve/main/TinyStoriesV2-GPT4-train.txt"
    echo "  wget https://huggingface.co/datasets/stanford-cs336/owt-sample/resolve/main/owt_train.txt.gz"
    echo "  gunzip owt_train.txt.gz"
    exit 1
fi

echo "📂 Files to upload:"
ls -lh "$DATA_DIR" | grep -E '\.(txt|gz)$' || echo "  (no .txt or .gz files found)"
echo ""

# Get default datastore (automatic blob storage created with workspace)
echo "🔍 Getting workspace datastore..."
DATASTORE_NAME=$(az ml datastore show \
    --name workspaceblobstore \
    --workspace-name "$WORKSPACE_NAME" \
    --resource-group "$RG_NAME" \
    --query name -o tsv 2>/dev/null || echo "workspaceblobstore")

echo "✅ Using datastore: $DATASTORE_NAME"

# Upload data
echo ""
echo "⬆️  Uploading data to Azure ML..."
az ml data create \
    --name bpe-training-data \
    --version 1 \
    --type uri_folder \
    --path "$DATA_DIR" \
    --workspace-name "$WORKSPACE_NAME" \
    --resource-group "$RG_NAME" 2>&1 | grep -v "Warning" || true

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                  Upload Complete ✅                       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Data uploaded to: azureml://datastores/$DATASTORE_NAME/paths/LocalUpload/"
echo ""
echo "Next step: Submit training job"
echo "  az ml job create --file aml-job.yml -g $RG_NAME -w $WORKSPACE_NAME"
echo ""