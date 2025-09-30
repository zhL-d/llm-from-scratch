# Azure ML Quick Start Guide

Train BPE tokenizer on Azure ML with automatic monitoring (CPU, memory, multiprocessing).

## Prerequisites

1. **Azure CLI installed**
   ```bash
   # macOS
   brew install azure-cli

   # Or download from: https://aka.ms/installazurecliwindows
   ```

2. **Azure subscription with permissions**
   - Contributor role on subscription or resource group

3. **Training data downloaded** (if not already)
   ```bash
   mkdir -p data && cd data
   wget https://huggingface.co/datasets/roneneldan/TinyStories/resolve/main/TinyStoriesV2-GPT4-train.txt
   wget https://huggingface.co/datasets/stanford-cs336/owt-sample/resolve/main/owt_train.txt.gz
   gunzip owt_train.txt.gz
   cd ..
   ```

---

## Step-by-Step Setup

### **1. Login to Azure**

```bash
az login
```

If you have multiple subscriptions:
```bash
# List subscriptions
az account list --output table

# Set active subscription
az account set --subscription "<subscription-id>"
```

### **2. Run Setup Script (One-Time)**

This creates workspace and compute cluster:

```bash
bash azure-ml-setup.sh
```

**What it creates:**
- Resource group: `bpe-rg`
- Workspace: `bpe-workspace`
- Compute cluster: `cpu-cluster` (D32: 32 vCPU, 128 GiB RAM)
  - Auto-scales from 0 → 1 nodes
  - Cost: ~$1.20/hour when running
  - Auto-shuts down after 5 minutes idle

**Time:** ~3-5 minutes

### **3. Upload Training Data**

```bash
bash upload-data.sh
```

**What it does:**
- Uploads `./data` directory to workspace blob storage
- Creates versioned dataset: `bpe-training-data:1`

**Time:** ~2-10 minutes (depends on data size)

### **4. Submit Training Job**

```bash
az ml job create \
  --file aml-job.yml \
  --resource-group bpe-rg \
  --workspace-name bpe-workspace
```

**Expected output:**
```
Command job created. Job name: happy_tree_123456
```

**Cost:** ~$1.20/hour × training duration (estimate 10 hours = $12)

### **5. Monitor Job**

#### **Option A: Azure ML Studio (Recommended)**

Open the URL from setup output:
```
https://ml.azure.com/workspaces/<workspace-id>
```

**What you'll see:**
- 📊 Real-time CPU usage (per-core graphs)
- 💾 Real-time memory usage (RSS, available, %)
- 🔄 Multiprocessing workers (automatically tracked)
- 📝 Live log streaming
- 📈 Custom metrics (if you add mlflow.log_metric)

#### **Option B: Terminal Log Streaming**

```bash
# Replace with your job name from step 4
az ml job stream \
  --name happy_tree_123456 \
  --resource-group bpe-rg \
  --workspace-name bpe-workspace
```

#### **Option C: Check Job Status**

```bash
az ml job show \
  --name happy_tree_123456 \
  --resource-group bpe-rg \
  --workspace-name bpe-workspace \
  --query status -o tsv
```

**Statuses:**
- `Preparing`: Scaling up compute
- `Running`: Training in progress
- `Completed`: Success ✅
- `Failed`: Check logs

### **6. Download Results**

After job completes:

```bash
# Download all outputs
az ml job download \
  --name happy_tree_123456 \
  --resource-group bpe-rg \
  --workspace-name bpe-workspace \
  --output-name model \
  --download-path ./trained-model
```

**Files downloaded:**
- Vocabulary: `vocab_<timestamp>.json`
- Merges: `merges_<timestamp>.json`
- Logs: `training_<timestamp>.log` (if enabled)

---

## Customizing Training

### **Change Vocabulary Size**

Edit `aml-job.yml`:
```yaml
environment_variables:
  VOCAB_SIZE: "50000"  # Change here
```

Then resubmit:
```bash
az ml job create --file aml-job.yml -g bpe-rg -w bpe-workspace
```

### **Use Different Dataset**

Edit `aml-job.yml`:
```yaml
environment_variables:
  TRAINDATA_PATH: ${{inputs.training_data}}/TinyStoriesV2-GPT4-train.txt
```

### **Increase Compute Size (for larger memory needs)**

Edit compute size in `azure-ml-setup.sh`:
```bash
COMPUTE_SIZE="Standard_D64_v3"  # 64 vCPU, 256 GiB RAM
```

Then recreate compute:
```bash
az ml compute delete --name cpu-cluster -w bpe-workspace -g bpe-rg --yes
bash azure-ml-setup.sh
```

---

## Monitoring Deep Dive

### **What Azure ML Monitors Automatically**

**System Metrics (every 30 seconds):**
- ✅ CPU usage (total and per-core)
- ✅ Memory usage (used, available, %)
- ✅ Disk I/O (read/write MB/s)
- ✅ Network I/O (send/receive MB/s)

**Process Metrics:**
- ✅ Main Python process (PID, CPU, memory)
- ✅ Child processes (your multiprocessing workers!)
- ✅ Thread counts

**Multiprocessing Detection:**

Azure ML automatically detects your `ProcessPoolExecutor` workers:
```
Process Tree:
├── python train_bpe.py (main)
└── [python workers] × 32 (from ProcessPoolExecutor)
```

All are tracked individually in the monitoring dashboard.

### **Viewing Monitoring Dashboard**

1. Go to Azure ML Studio
2. Click **Jobs** → Your job name
3. Click **Metrics** tab

**Key charts:**
- **CPU Utilization**: Should spike to ~3200% (32 cores × 100%) during pretokenization
- **Memory**: Watch for steady growth during pair counting phase
- **Process Count**: Should show 33 (1 main + 32 workers)

### **Adding Custom Metrics (Optional)**

If you want to log custom metrics like training progress:

Edit `train_bpe.py`:
```python
import mlflow

# In your training loop
mlflow.log_metric("merge_step", i)
mlflow.log_metric("vocab_size", len(vocab))
```

These will appear in the Metrics tab automatically.

---

## Cost Management

### **Actual Costs**

| Resource | Cost | Duration | Total |
|----------|------|----------|-------|
| Storage (blob) | ~$0.02/GB/month | Always | ~$0.10/month |
| Compute idle | $0 | N/A | $0 |
| Compute running | $1.20/hour | 10 hours | $12.00 |
| **Total per training run** | | | **~$12** |

### **Cost Optimization Tips**

1. **Delete compute when not needed** (saves $0 since it auto-scales to 0)
   ```bash
   # Optional: Delete entire compute cluster
   az ml compute delete --name cpu-cluster -w bpe-workspace -g bpe-rg
   ```

2. **Use smaller datasets for testing**
   - Test with `TinyStories` first (~5 minutes, ~$0.10)
   - Scale to `owt_train.txt` for production

3. **Monitor job actively**
   - Cancel failed jobs early to avoid wasted compute:
   ```bash
   az ml job cancel --name <job-name> -g bpe-rg -w bpe-workspace
   ```

---

## Troubleshooting

### **Job Fails Immediately**

Check logs:
```bash
az ml job stream --name <job-name> -g bpe-rg -w bpe-workspace
```

**Common issues:**
- ❌ Data path incorrect → Check `TRAINDATA_PATH` in `aml-job.yml`
- ❌ Config file not found → Ensure `config_azure_trial.yaml` exists
- ❌ uv sync fails → Check `pyproject.toml` is valid

### **Out of Memory**

Increase compute size to D64 (256 GiB RAM):
```bash
az ml compute update \
  --name cpu-cluster \
  --size Standard_D64_v3 \
  -w bpe-workspace -g bpe-rg
```

### **Job Stuck in "Preparing"**

Quota issue. Check quota:
```bash
az ml compute list-usage -l switzerlandnorth --output table
```

Request increase: Azure Portal → Quotas → Machine Learning Service

---

## Comparison: Azure ML vs. Container Apps

| Aspect | Container Apps (Current) | Azure ML (New) |
|--------|-------------------------|----------------|
| **Setup complexity** | High (500+ lines Bicep) | Low (3 commands) |
| **Monitoring** | Manual (Logic Apps) | Automatic (built-in) |
| **Cost when idle** | $1.20/hour (dedicated) | $0 (auto-scale to 0) |
| **Multiprocess tracking** | No | Yes (automatic) |
| **Cleanup** | Manual (workflows) | Automatic (5 min idle) |
| **Industry standard** | For web apps | For ML training ✅ |
| **Lines of infra code** | ~800 | ~50 |

---

## Next Steps

1. ✅ **Run first training job** with small dataset (TinyStories)
2. ✅ **Validate monitoring** in Azure ML Studio
3. ✅ **Scale to full dataset** (owt_train.txt)
4. 🔄 **Iterate**: Experiment with different vocab sizes, datasets
5. 📊 **Optional**: Add custom metrics with MLflow

---

## Support

**Documentation:**
- Azure ML CLI: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-train-cli
- Monitoring Guide: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-log-view-metrics

**Your existing resources:**
- Setup script: `azure-ml-setup.sh`
- Job config: `aml-job.yml`
- Upload script: `upload-data.sh`

**Questions?** Check job logs first:
```bash
az ml job stream --name <job-name> -g bpe-rg -w bpe-workspace
```