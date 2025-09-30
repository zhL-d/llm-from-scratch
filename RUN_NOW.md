# 🚀 Ready to Run: BPE Training on Azure ML

**Everything is prepared. Follow these exact steps.**

---

## Prerequisites Check

Before starting, ensure you have:

```bash
# 1. Azure CLI installed
az --version
# Should show version 2.x.x or higher

# 2. Logged into Azure
az login
# Opens browser for authentication

# 3. Correct subscription active
az account show --query name -o tsv
# Should show your subscription name

# 4. Training data downloaded
ls -lh data/
# Should show owt_train.txt or TinyStoriesV2-GPT4-train.txt
```

---

## Step 1: Create Azure ML Workspace (5 minutes)

```bash
# Make script executable
chmod +x azure-ml-setup.sh

# Run setup
bash azure-ml-setup.sh
```

**Expected output:**
```
╔══════════════════════════════════════════════════════════╗
║     Azure ML Setup for BPE Training (Regular Instances)  ║
╚══════════════════════════════════════════════════════════╝

📦 Creating resource group...
✅ Resource group created

🔧 Installing Azure ML CLI extension...
✅ Azure ML CLI ready

🏗️  Creating Azure ML workspace...
✅ Workspace created

⚙️  Creating compute cluster...
✅ Compute cluster created

╔══════════════════════════════════════════════════════════╗
║                    Setup Complete ✅                      ║
╚══════════════════════════════════════════════════════════╝
```

**What was created:**
- Resource group: `bpe-rg`
- Workspace: `bpe-workspace`
- Compute: `cpu-cluster` (D32: 32 vCPU, 128 GiB RAM)

**Cost:** $0 (compute is scaled to 0)

---

## Step 2: Upload Training Data (5-10 minutes)

```bash
# Make script executable
chmod +x upload-data.sh

# Upload data
bash upload-data.sh
```

**Expected output:**
```
╔══════════════════════════════════════════════════════════╗
║           Upload Training Data to Azure ML               ║
╚══════════════════════════════════════════════════════════╝

📂 Files to upload:
-rw-r--r-- 1 user staff 2.1G owt_train.txt
-rw-r--r-- 1 user staff 327M TinyStoriesV2-GPT4-train.txt

🔍 Getting workspace datastore...
✅ Using datastore: workspaceblobstore

⬆️  Uploading data to Azure ML...
✅ Upload complete

╔══════════════════════════════════════════════════════════╗
║                  Upload Complete ✅                       ║
╚══════════════════════════════════════════════════════════╝
```

**What happened:**
- Data uploaded to workspace blob storage
- Dataset registered as `bpe-training-data:1`

**Cost:** ~$0.10/month storage

---

## Step 3: Submit Training Job (30 seconds)

### **Option A: Quick Test (5 minutes, $0.10)**

Test with small dataset first:

```bash
az ml job create \
  --file aml-job.yml \
  --set display_name=bpe-test-tinystories \
  --set environment_variables.TRAINDATA_PATH='${{inputs.training_data}}/TinyStoriesV2-GPT4-train.txt' \
  --set environment_variables.VOCAB_SIZE=1000 \
  --resource-group bpe-rg \
  --workspace-name bpe-workspace
```

### **Option B: Full Training (10 hours, $12)**

Full OpenWebText training:

```bash
az ml job create \
  --file aml-job.yml \
  --resource-group bpe-rg \
  --workspace-name bpe-workspace
```

**Expected output:**
```
Command job created. Job name: happy_tree_abc123

View job in Azure ML Studio:
https://ml.azure.com/runs/happy_tree_abc123?wsid=...
```

**Save this job name!** You'll need it for monitoring.

---

## Step 4: Monitor Training

### **Method 1: Azure ML Studio (Recommended)**

Click the URL from step 3, or:

1. Go to https://ml.azure.com
2. Click **Jobs** in left sidebar
3. Click your job name (e.g., `happy_tree_abc123`)
4. Click **Metrics** tab

**What you'll see:**

**System Overview:**
- CPU Utilization: Real-time graph (should spike to ~3200% during pretokenization)
- Memory Used: Growing during pair counting (should reach ~40-60 GB)
- Memory Percent: Should stay below 90%

**Process Details:**
- Process Count: Should show 33 during pretokenization phase
- CPU per Process: Each worker using ~100% CPU
- Memory per Process: Main process highest, workers moderate

**Expected timeline:**
```
0-10s:       Initialization
10s-1h:      Pretokenization (CPU spike to 3200%)
1h-1.5h:     Build pair counts (memory grows)
1.5h-10h:    BPE merge loop (steady CPU ~600%)
10h:         Save results
```

### **Method 2: Terminal Logs**

Stream logs in real-time:

```bash
# Replace with your job name
az ml job stream \
  --name happy_tree_abc123 \
  --resource-group bpe-rg \
  --workspace-name bpe-workspace
```

**Expected output:**
```
2025-09-30 10:00:00 - INFO - Starting BPE training...
2025-09-30 10:00:05 - INFO - Pretokenization phase...
2025-09-30 10:30:42 - INFO - Phase complete: 1,234,567 pretokens
2025-09-30 10:30:45 - INFO - Building pair counts...
2025-09-30 11:00:12 - INFO - Starting BPE merge loop...
...
```

Press `Ctrl+C` to stop streaming (job continues running).

### **Method 3: Check Status**

Quick status check:

```bash
az ml job show \
  --name happy_tree_abc123 \
  --resource-group bpe-rg \
  --workspace-name bpe-workspace \
  --query status -o tsv
```

**Possible statuses:**
- `Preparing`: Scaling up compute, pulling Docker image
- `Running`: Training in progress ✅
- `Completed`: Success! 🎉
- `Failed`: Check logs

---

## Step 5: Download Results

After job completes:

```bash
# Download all outputs
az ml job download \
  --name happy_tree_abc123 \
  --resource-group bpe-rg \
  --workspace-name bpe-workspace \
  --download-path ./trained-model
```

**Files downloaded:**
```
trained-model/
├── named-outputs/
│   └── model/
│       ├── owt_train_serialization_vocab_20250930_123456.json
│       └── owt_train_serialization_merge_20250930_123456.json
└── user_logs/
    └── std_log.txt
```

**Verify results:**
```bash
# Check vocabulary size
python -c "import json; print(len(json.load(open('trained-model/named-outputs/model/*_vocab_*.json'))))"
# Should output: 32000

# Check merge count
python -c "import json; print(len(json.load(open('trained-model/named-outputs/model/*_merge_*.json'))))"
# Should output: 31744 (32000 - 256 base bytes)
```

---

## Monitoring Checklist

While training is running, verify:

### **During Pretokenization (first 1 hour):**
- [ ] CPU spikes to ~3200% (32 cores × 100%)
- [ ] Process count shows 33 (1 main + 32 workers)
- [ ] Memory grows steadily (~100 MB → 5 GB)
- [ ] Disk read activity high
- [ ] Logs show "Pretokenization phase..."

### **During Pair Counting (1-1.5 hours):**
- [ ] CPU drops to ~400%
- [ ] Process count back to 1 (workers terminated)
- [ ] Memory grows rapidly (~5 GB → 40 GB)
- [ ] Logs show "Building pair counts..."

### **During Merge Loop (1.5-10 hours):**
- [ ] CPU steady at ~600%
- [ ] Memory stable (~50 GB)
- [ ] Process count stays at 1
- [ ] Logs show periodic progress (if you added logging)

### **Signs of Problems:**

**❌ CPU never spikes above 500%:**
- Multiprocessing not enabled
- Check `PRETOKEN_PROCS` in `aml-job.yml`

**❌ Memory exceeds 90%:**
- Risk of OOM
- Consider switching to D64 (256 GiB RAM)

**❌ Job stuck in "Preparing" > 10 minutes:**
- Quota issue
- Check: `az ml compute list-usage -l switzerlandnorth`

**❌ Job fails immediately:**
- Check logs: `az ml job stream --name <job-name> -g bpe-rg -w bpe-workspace`
- Common issues: wrong data path, missing config file

---

## Cost Tracking

Monitor costs in Azure Portal:

1. Go to https://portal.azure.com
2. Search for "Cost Management"
3. Click "Cost analysis"
4. Filter by resource group: `bpe-rg`

**Expected costs:**
```
First hour:    ~$1.20 (pretokenization)
Hours 2-10:    ~$10.80 (merge loop)
Total:         ~$12.00 per training run
Storage:       ~$0.10/month
```

**Cost alerts (optional):**
```bash
az consumption budget create \
  --budget-name bpe-training-alert \
  --amount 50 \
  --category cost \
  --time-grain monthly \
  --start-date 2025-09-01 \
  --resource-group bpe-rg
```

---

## After Training Completes

### **Success! Now what?**

1. **Download results** (step 5 above)

2. **Validate vocabulary:**
   ```bash
   # Check files exist
   ls -lh trained-model/named-outputs/model/

   # Inspect first few vocab entries
   python -c "
   import json
   vocab = json.load(open('trained-model/named-outputs/model/*_vocab_*.json'))
   print(list(vocab.items())[:10])
   "
   ```

3. **Compare with reference:**
   ```bash
   # If you have GPT-2 vocab for comparison
   # Your vocab should have similar structure
   ```

4. **Review monitoring data:**
   - Azure ML Studio → Jobs → Your job → Metrics
   - Look for anomalies, optimization opportunities

5. **Clean up (optional):**
   ```bash
   # Compute auto-scales to 0 (no cleanup needed)
   # Storage costs ~$0.10/month (keep data for future runs)

   # To delete everything:
   az ml workspace delete --name bpe-workspace -g bpe-rg --yes
   az group delete --name bpe-rg --yes
   ```

---

## Troubleshooting Commands

### **Job won't start:**
```bash
# Check compute status
az ml compute show --name cpu-cluster -w bpe-workspace -g bpe-rg

# Check quota
az ml compute list-usage -l switzerlandnorth
```

### **Job failed:**
```bash
# View error logs
az ml job stream --name <job-name> -g bpe-rg -w bpe-workspace

# Download all logs for inspection
az ml job download --name <job-name> -g bpe-rg -w bpe-workspace --logs
```

### **Can't find job:**
```bash
# List all jobs
az ml job list -w bpe-workspace -g bpe-rg --output table

# Show recent jobs
az ml job list -w bpe-workspace -g bpe-rg --query "[?status=='Running']"
```

### **Cancel job:**
```bash
az ml job cancel --name <job-name> -g bpe-rg -w bpe-workspace
```

---

## Summary: Your 3 Commands

```bash
# 1. Setup (one-time)
bash azure-ml-setup.sh

# 2. Upload data (one-time)
bash upload-data.sh

# 3. Train (repeat as needed)
az ml job create --file aml-job.yml -g bpe-rg -w bpe-workspace
```

**Monitoring:** Automatic in Azure ML Studio!

---

## Ready? Let's Go! 🚀

```bash
# Run all three now:
bash azure-ml-setup.sh && \
bash upload-data.sh && \
az ml job create --file aml-job.yml -g bpe-rg -w bpe-workspace
```

**Then:** Open Azure ML Studio and watch your training in real-time!

**Questions?** Check [AZURE_ML_QUICKSTART.md](./AZURE_ML_QUICKSTART.md) or [MONITORING_GUIDE.md](./MONITORING_GUIDE.md)