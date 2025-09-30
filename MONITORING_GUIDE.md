# Azure ML Monitoring Guide for Multiprocessing Training

Complete guide to monitoring your BPE tokenizer training with multiprocessing.

---

## What Azure ML Monitors Automatically

### **No Code Changes Required**

Azure ML automatically tracks all these metrics for your training job:

#### **1. System-Wide Metrics** (30-second intervals)

| Metric | Description | What to Watch |
|--------|-------------|---------------|
| **CPU %** | Total CPU utilization | Should reach ~3200% (32 cores × 100%) during pretokenization |
| **CPU per core** | Per-core utilization | All cores should be utilized during parallel phase |
| **Memory Used** | Physical RAM used (MB) | Grows during pair counting, peaks during merge phase |
| **Memory %** | Percentage of total RAM | Should stay < 90% to avoid OOM |
| **Memory Available** | Free RAM (MB) | Monitor to ensure headroom |
| **Disk Read** | Disk read throughput (MB/s) | Spikes during file loading |
| **Disk Write** | Disk write throughput (MB/s) | Activity during output saving |
| **Network Sent/Received** | Network I/O (MB/s) | Minimal for this workload |

#### **2. Process-Level Metrics**

| Metric | Description | Your Training |
|--------|-------------|---------------|
| **Process Count** | Number of active processes | 1 (main) + 32 (workers) = 33 during pretokenization |
| **Thread Count** | Threads per process | Varies by phase |
| **Process CPU** | CPU usage per process | Each worker should use ~100% CPU |
| **Process Memory** | Memory per process | Main process highest, workers moderate |

---

## Training Phases and Expected Patterns

### **Phase 1: Initialization (5-10 seconds)**

```
CPU:     Low (~5%)
Memory:  Low (~100 MB)
Processes: 1 (main only)
```

**What's happening:**
- Loading configuration
- Initializing tokenizer
- Reading vocabulary

### **Phase 2: Pretokenization (1-3 hours for large datasets)**

```
CPU:     High (~3200% = 32 cores at 100%)
Memory:  Growing (500 MB → 5 GB)
Processes: 33 (1 main + 32 workers)
Disk:    High read activity
```

**What's happening:**
- `ProcessPoolExecutor` spawns 32 workers
- File chunked by special token boundaries
- Each worker processes chunk independently
- Main process aggregates results

**Monitoring tips:**
- ✅ All CPU cores should be utilized (~100% each)
- ✅ Process count should jump to 33
- ⚠️ If CPU < 1000%, workers aren't starting correctly
- ⚠️ If memory spikes too fast, reduce `PRETOKEN_PROCS`

### **Phase 3: Build Pair Counts (10-30 minutes)**

```
CPU:     Low-Medium (~200-400%)
Memory:  High (grows to 20-40 GB)
Processes: 1 (workers terminated)
```

**What's happening:**
- Iterating over pretokens
- Building pair count dictionary
- Building reverse cache (pair → affected pretokens)

**Monitoring tips:**
- ✅ Memory should grow steadily (not spike)
- ⚠️ If memory exceeds 100 GB, increase compute size to D64

### **Phase 4: BPE Merge Loop (8-10 hours for 32k vocab)**

```
CPU:     Medium (~400-800%)
Memory:  Stable (40-60 GB)
Processes: 1
```

**What's happening:**
- Picking best pair from heap
- Merging best pair
- Updating pair counts and cache
- Repeating 32,000 times

**Monitoring tips:**
- ✅ CPU should be consistent (not idle)
- ✅ Memory should be stable (no leaks)
- ⚠️ If CPU drops to near 0%, job may be stuck

### **Phase 5: Saving Results (10-30 seconds)**

```
CPU:     Low (~50%)
Memory:  Stable
Disk:    High write activity
```

**What's happening:**
- Serializing vocabulary to JSON
- Serializing merges to JSON
- Uploading to Azure ML outputs

---

## How to Access Monitoring

### **Method 1: Azure ML Studio (Recommended)**

1. **Navigate to job:**
   ```
   https://ml.azure.com → Jobs → <your-job-name>
   ```

2. **View real-time metrics:**
   - Click **Metrics** tab
   - Charts update every 30 seconds
   - Can zoom, pan, compare runs

3. **Key charts to monitor:**

   **System Overview:**
   - CPU Utilization (%)
   - Memory Used (MB)
   - Memory Percent (%)

   **Process Details:**
   - Process Count (should show 33 during pretokenization)
   - CPU per Process
   - Memory per Process

4. **View logs:**
   - Click **Outputs + logs** tab
   - Navigate to `user_logs/std_log.txt`
   - Auto-refreshes every few seconds

### **Method 2: Azure CLI (Terminal)**

#### **Stream logs in real-time:**
```bash
az ml job stream \
  --name <job-name> \
  --resource-group bpe-rg \
  --workspace-name bpe-workspace
```

**Output:**
```
2025-09-30 10:30:15 - INFO - Starting BPE training...
2025-09-30 10:30:20 - INFO - Pretokenization phase...
2025-09-30 10:35:42 - INFO - Phase complete: 1,234,567 pretokens
...
```

#### **Check job status:**
```bash
az ml job show \
  --name <job-name> \
  --resource-group bpe-rg \
  --workspace-name bpe-workspace \
  --query "{status:status, startTime:properties.startTime, duration:properties.duration}" \
  --output table
```

#### **Get resource consumption summary:**
```bash
# After job completes
az ml job show \
  --name <job-name> \
  --resource-group bpe-rg \
  --workspace-name bpe-workspace \
  --query "properties.services.Tracking.properties.{cpuUsage:cpuUsage, memoryUsage:memoryUsage}"
```

### **Method 3: Azure Monitor (Advanced)**

For deeper analysis, export to Azure Monitor:

```bash
# Enable diagnostic logging
az monitor diagnostic-settings create \
  --name ml-diagnostics \
  --resource <workspace-resource-id> \
  --logs '[{"category":"AmlComputeJobEvent","enabled":true}]' \
  --metrics '[{"category":"AllMetrics","enabled":true}]' \
  --workspace <log-analytics-workspace-id>
```

Query with Kusto (KQL):
```kql
AmlComputeJobEvent
| where JobName == "<job-name>"
| where MetricName in ("CpuUtilization", "MemoryUtilization")
| project TimeGenerated, MetricName, MetricValue
| render timechart
```

---

## Interpreting Metrics for Multiprocessing

### **Expected CPU Pattern**

```
Phase 1 (Init):          ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  5%
Phase 2 (Pretokenize):   ████████████████████████████████ 3200% (32 cores!)
Phase 3 (Build Pairs):   ████████░░░░░░░░░░░░░░░░░░░░░░░░ 400%
Phase 4 (Merge):         ████████████░░░░░░░░░░░░░░░░░░░░ 600%
Phase 5 (Save):          ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 50%
```

### **Expected Memory Pattern**

```
Phase 1:  ▁          (~100 MB)
Phase 2:  ▁▂▃▄▅      (~5 GB, growing during aggregation)
Phase 3:  ▅▆▇█       (~40 GB, building data structures)
Phase 4:  ████       (~50 GB, stable)
Phase 5:  ████       (~50 GB, stable)
```

### **Expected Process Count Pattern**

```
Phase 1:  1 process
Phase 2:  33 processes (1 main + 32 workers)
Phase 3:  1 process (workers terminated)
Phase 4:  1 process
Phase 5:  1 process
```

---

## Troubleshooting with Monitoring

### **Problem: CPU Always Low (~5%)**

**Symptoms:**
- CPU never reaches 3200% during pretokenization
- Process count stays at 1

**Causes:**
- Multiprocessing not enabled in config
- Environment variable `PRETOKEN_PROCS` set to 1

**Fix:**
```yaml
# In aml-job.yml
environment_variables:
  PRETOKEN_PROCS: "32"  # Ensure this is set
```

### **Problem: Out of Memory (OOM)**

**Symptoms:**
- Memory % reaches 100%
- Job fails with "MemoryError" or "Killed"

**Causes:**
- Vocabulary size too large for compute
- Pair count dictionary exceeds available RAM

**Fix 1: Increase compute size**
```bash
# Switch to D64 (256 GiB RAM)
az ml compute update \
  --name cpu-cluster \
  --size Standard_D64_v3 \
  -w bpe-workspace -g bpe-rg
```

**Fix 2: Reduce vocabulary size**
```yaml
environment_variables:
  VOCAB_SIZE: "16000"  # Reduce from 32000
```

### **Problem: Job Stuck (No Progress)**

**Symptoms:**
- CPU near 0% for extended period
- Logs stopped updating
- Memory stable but no activity

**Diagnosis:**
1. Check logs for last message:
   ```bash
   az ml job stream --name <job-name> -g bpe-rg -w bpe-workspace | tail -20
   ```

2. Check if process is still running:
   - Azure ML Studio → Metrics → Process Count (should be > 0)

**Causes:**
- Deadlock in merge loop (rare)
- Waiting for I/O (disk/network)

**Fix:**
```bash
# Cancel and retry
az ml job cancel --name <job-name> -g bpe-rg -w bpe-workspace
az ml job create --file aml-job.yml -g bpe-rg -w bpe-workspace
```

### **Problem: Training Much Slower Than Expected**

**Expected durations:**
- TinyStories (327M tokens, vocab 1000): ~5 minutes
- OpenWebText sample (vocab 32000): ~10 hours

**Symptoms:**
- Training taking 2-3x longer than expected
- CPU utilization lower than expected

**Diagnosis:**
1. Check disk I/O:
   - Metrics → Disk Read MB/s
   - Should be 100-500 MB/s during file loading

2. Check CPU per core:
   - Metrics → CPU per core
   - Should be ~100% for all 32 cores during pretokenization

**Causes:**
- Data not properly mounted (reading from network)
- Too many workers (memory thrashing)
- Slow storage tier

**Fix:**
```yaml
inputs:
  training_data:
    mode: download  # Change from ro_mount to download
```

---

## Advanced: Custom Metrics (Optional)

If you want to add custom training metrics:

### **Option 1: MLflow (Recommended)**

Edit `train_bpe.py`:
```python
import mlflow

# Start run (Azure ML does this automatically, but explicit is fine)
mlflow.start_run()

# Log parameters
mlflow.log_param("vocab_size", config["vocab_size"])
mlflow.log_param("dataset", config["traindata_path"])

# In training loop
for i in range(merge_size):
    # ... BPE merge logic ...

    # Log progress every 1000 steps
    if i % 1000 == 0:
        mlflow.log_metric("merge_step", i, step=i)
        mlflow.log_metric("progress_pct", i / merge_size * 100, step=i)

# Log final metrics
mlflow.log_metric("final_vocab_size", len(vocab))
mlflow.log_metric("training_time_sec", training_duration)
```

**View in Studio:**
- Jobs → Your job → Metrics → Custom metrics

### **Option 2: Print Statements (Simple)**

Already works! Your `print()` statements appear in logs automatically:

```python
print(f"Progress: {i}/{merge_size} ({i/merge_size*100:.1f}%)")
```

Visible in:
- Azure ML Studio → Outputs + logs → std_log.txt
- Terminal via `az ml job stream`

---

## Monitoring Checklist

Before submitting job:
- [ ] Reviewed expected metrics patterns above
- [ ] Determined expected duration for dataset size
- [ ] Confirmed compute size matches memory requirements

During training:
- [ ] CPU reaches ~3200% during pretokenization
- [ ] Process count jumps to 33 during parallel phase
- [ ] Memory grows but stays under 90%
- [ ] Logs show regular progress updates

After training:
- [ ] Review Metrics tab for anomalies
- [ ] Download and inspect training logs
- [ ] Compare metrics across runs

---

## Summary: Monitoring Best Practices

1. **Use Azure ML Studio** for real-time monitoring (easiest)
2. **Monitor CPU during pretokenization** - should spike to 3200%
3. **Monitor memory during pair counting** - watch for steady growth
4. **Check process count** - should show 33 during parallel phase
5. **Stream logs in terminal** for quick debugging
6. **Compare across runs** to identify regressions

**Key insight:** Azure ML monitors everything automatically. No code changes needed!