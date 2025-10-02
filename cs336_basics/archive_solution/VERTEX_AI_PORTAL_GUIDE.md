# Vertex AI Custom Training Jobs - Portal Only Guide

Complete guide for setting up BPE training on GCP Vertex AI using **only the web console** (no CLI required).

---

## **What You'll Build**

Same as Azure ML: Submit training jobs that auto-shutdown when complete, with automatic CPU/memory monitoring.

**Time to first training:** 90 minutes (all via web browser)

---

## **Prerequisites**

1. GCP account with $300 free credits
2. Web browser
3. Your BPE training code on your local machine

---

## **Step 1: Create GCP Project (5 min)**

### **1.1 Sign up for GCP**

1. Go to: https://console.cloud.google.com/
2. Click **"Get started for free"**
3. Enter credit card (won't be charged, $300 free credits)
4. Verify account

### **1.2 Create new project**

1. Click project dropdown (top left, next to "Google Cloud")
2. Click **"NEW PROJECT"**
3. Fill in:
   - **Project name:** `bpe-training-project`
   - **Organization:** Leave as "No organization"
4. Click **"CREATE"**
5. Wait 30 seconds for project creation
6. **Copy your Project ID** (looks like: `bpe-training-project-123456`)

---

## **Step 2: Enable Required APIs (5 min)**

### **2.1 Enable Vertex AI API**

1. Go to: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
2. Make sure your project is selected (top left)
3. Click **"ENABLE"**
4. Wait 1-2 minutes

### **2.2 Enable Cloud Storage API**

1. Go to: https://console.cloud.google.com/apis/library/storage.googleapis.com
2. Click **"ENABLE"**

### **2.3 Enable Container Registry API**

1. Go to: https://console.cloud.google.com/apis/library/containerregistry.googleapis.com
2. Click **"ENABLE"**

### **2.4 Enable Artifact Registry API**

1. Go to: https://console.cloud.google.com/apis/library/artifactregistry.googleapis.com
2. Click **"ENABLE"**

---

## **Step 3: Create Cloud Storage Bucket (5 min)**

### **3.1 Create bucket for data and outputs**

1. Go to: https://console.cloud.google.com/storage/browser
2. Click **"CREATE BUCKET"**
3. Fill in:
   - **Name:** `bpe-training-YOUR_PROJECT_ID` (must be globally unique)
   - **Location type:** Region
   - **Region:** `us-central1`
   - **Storage class:** Standard
   - **Access control:** Uniform
4. Click **"CREATE"**

### **3.2 Upload training data**

1. Click on your bucket name
2. Click **"CREATE FOLDER"**
   - **Name:** `data`
3. Click on `data` folder
4. Click **"UPLOAD FILES"**
5. Select your training data files:
   - `corpus.en` (for testing)
   - `owt_train.txt` (for production)
6. Wait for upload to complete

### **3.3 Create outputs folder**

1. Go back to bucket root
2. Click **"CREATE FOLDER"**
   - **Name:** `outputs`

---

## **Step 4: Prepare Docker Container (30 min)**

Since you can't use CLI, you have **two options**:

### **Option A: Use Cloud Shell (Recommended - No local Docker needed)**

1. Go to: https://console.cloud.google.com/
2. Click **Cloud Shell icon** (top right, looks like `>_`)
3. Wait for shell to start (30 seconds)

**In Cloud Shell, run these commands:**

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Clone your code (or upload via "Upload" button in Cloud Shell)
# For now, let's create a minimal setup

# Create working directory
mkdir bpe-training
cd bpe-training

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files (you'll upload these)
COPY . /app

# Install dependencies
RUN uv sync --frozen

# Entrypoint
ENTRYPOINT ["uv", "run", "python", "cs336_basics/train_bpe.py"]
EOF

# Now upload your project files using Cloud Shell "Upload" button:
# - pyproject.toml
# - uv.lock
# - cs336_basics/ folder
# - Any other needed files
```

**After uploading files:**

```bash
# Build and push Docker image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/bpe-training:latest

# This will take 5-10 minutes
```

### **Option B: Use Cloud Build Manually**

If Cloud Shell doesn't work, you can use Cloud Build via portal:

1. Go to: https://console.cloud.google.com/cloud-build/builds
2. Click **"CREATE TRIGGER"** (we'll use it manually)
3. Click **"ENABLE CLOUD BUILD API"** if prompted

**But honestly, Option A (Cloud Shell) is much easier.**

---

## **Step 5: Create Training Job (10 min)**

### **5.1 Navigate to Vertex AI**

1. Go to: https://console.cloud.google.com/vertex-ai/training/custom-jobs
2. Make sure your project is selected

### **5.2 Create Custom Training Job**

1. Click **"CREATE"** (top of page)
2. Fill in form:

**Dataset (SKIP THIS)**
- Leave as "No managed dataset"

**Model training method**
- Select **"Custom training (advanced)"**
- Click **"CONTINUE"**

**Model details**
- **Model name:** Leave empty (not creating a model)
- Click **"CONTINUE"**

**Training container**
- **Training method:** Custom container
- **Container image:** `gcr.io/YOUR_PROJECT_ID/bpe-training:latest`
- **Model output directory:** `gs://bpe-training-YOUR_PROJECT_ID/outputs`
- Click **"CONTINUE"**

**Hyperparameters (Environment Variables)**
- Click **"ADD HYPERPARAMETER"**
- Add these one by one:
  - Name: `TRAINDATA_PATH`, Value: `gs://bpe-training-YOUR_PROJECT_ID/data/corpus.en`
  - Name: `OUTPUTS_PATH`, Value: `gs://bpe-training-YOUR_PROJECT_ID/outputs`
  - Name: `VOCAB_SIZE`, Value: `500` (for testing)
  - Name: `PRETOKEN_PROCS`, Value: `4` (for testing)
- Click **"CONTINUE"**

**Compute and pricing**
- **Region:** `us-central1`
- **Machine type:** Click "CHANGE"
  - Select **"n2-highmem-16"** (16 vCPU, 128 GB memory)
  - Or for testing: **"n2-highmem-4"** (4 vCPU, 32 GB memory)
- **Accelerator:** None
- **Boot disk size:** 100 GB
- **Preemptible:** ☑️ Check this box (80% cost savings)
- Click **"CONTINUE"**

**Prediction container (SKIP)**
- Leave as default
- Click **"CONTINUE"**

**Review and submit**
- Review your settings
- Click **"START TRAINING"**

---

## **Step 6: Monitor Training (During training)**

### **6.1 View job status**

1. Go to: https://console.cloud.google.com/vertex-ai/training/custom-jobs
2. You should see your job with status **"Running"**
3. Click on your job name

### **6.2 View logs**

1. In job details, click **"LOGS"** tab
2. You'll see real-time output from your training script
3. Look for:
   - "Loading training data..."
   - "Building BPE vocab..."
   - "Saving tokenizer..."

### **6.3 Monitor CPU and Memory**

1. In job details, click **"MONITORING"** tab
2. You'll see graphs for:
   - **CPU utilization** (should be high during training)
   - **Memory usage** (should gradually increase)
   - **Network traffic**
   - **Disk I/O**

**Expected patterns:**
- First 10%: Low CPU (loading data)
- Middle 80%: High CPU (building vocab with multiprocessing)
- Last 10%: Medium CPU (saving results)

### **6.4 Check for completion**

Job will automatically transition to **"Succeeded"** when done.

**Timeline for small test (corpus.en, vocab_size=500):**
- Total time: ~1-2 minutes
- Auto-shutdown: Immediate

**Timeline for production (owt_train.txt, vocab_size=32000):**
- Total time: ~10 hours
- Auto-shutdown: Immediate after completion

---

## **Step 7: Download Results (5 min)**

### **7.1 Navigate to Cloud Storage**

1. Go to: https://console.cloud.google.com/storage/browser
2. Click on your bucket: `bpe-training-YOUR_PROJECT_ID`
3. Click on `outputs` folder

### **7.2 Download output files**

1. Find your tokenizer files:
   - `tokenizer.pkl`
   - `vocab.txt` (if you enabled serialization)
2. Check the box next to each file
3. Click **"DOWNLOAD"** (three dots menu → Download)

**Alternative: Download entire folder**
1. Check box next to `outputs` folder
2. Click three dots → **"Download"**
3. Will download as ZIP file

---

## **Step 8: Production Training (When ready)**

### **8.1 Update job for production data**

1. Go to: https://console.cloud.google.com/vertex-ai/training/custom-jobs
2. Find your previous test job
3. Click **"CLONE"** button
4. Update these settings:
   - **TRAINDATA_PATH:** Change to `gs://bpe-training-YOUR_PROJECT_ID/data/owt_train.txt`
   - **VOCAB_SIZE:** Change to `32000`
   - **PRETOKEN_PROCS:** Change to `16` (use full cores)
   - **Machine type:** Keep `n2-highmem-16`
   - **Preemptible:** Keep checked
5. Click **"START TRAINING"**

### **8.2 Monitor (same as Step 6)**

Production training will take ~10 hours.

---

## **Cost Breakdown**

### **Test run (corpus.en, 2 minutes):**
- n2-highmem-4: $0.24/hour × (2/60) hours = **$0.008**
- Storage: $0.02/GB × 0.1 GB = **$0.002**
- **Total: $0.01** (essentially free)

### **Production run (owt_train.txt, 10 hours):**
- n2-highmem-16 preemptible: $0.24/hour × 10 hours = **$2.40**
- Storage: $0.02/GB × 100 GB = **$2.00**
- **Total: $4.40**

**Your $300 free credits:**
- After test + production: **$295.59 remaining**
- Can run **60+ more production trainings**

---

## **Monitoring Comparison: Vertex AI vs Azure ML**

| Feature | Vertex AI Custom Job | Azure ML Job |
|---------|---------------------|--------------|
| Auto-shutdown | ✅ Yes | ✅ Yes |
| CPU monitoring | ✅ Per-core graphs | ✅ Per-core graphs |
| Memory monitoring | ✅ Real-time dashboard | ✅ Real-time dashboard |
| Log streaming | ✅ Real-time in portal | ✅ Real-time in portal |
| Historical metrics | ✅ 30 days | ✅ 30 days |
| Cost after completion | ✅ $0 | ✅ $0 |

**They're nearly identical!** Same professional ML platform experience.

---

## **Troubleshooting**

### **Issue: "Permission denied" when creating job**

**Fix:**
1. Go to: https://console.cloud.google.com/iam-admin/iam
2. Find your email
3. Click **"EDIT"** (pencil icon)
4. Click **"ADD ANOTHER ROLE"**
5. Add: `Vertex AI User`
6. Click **"SAVE"**

### **Issue: "Container image not found"**

**Fix:**
1. Go to: https://console.cloud.google.com/gcr/images
2. Check if your image exists: `bpe-training`
3. If not, go back to Step 4 and rebuild

### **Issue: "Quota exceeded"**

GCP has much higher default quotas than Azure for Students.

**Check quota:**
1. Go to: https://console.cloud.google.com/iam-admin/quotas
2. Search for "CPUs us-central1"
3. If too low, click **"ALL QUOTAS"** → Select quota → **"EDIT QUOTAS"**

### **Issue: Job fails with "File not found"**

**Fix:**
1. Check Cloud Storage bucket has data:
   - Go to: https://console.cloud.google.com/storage/browser
   - Verify `data/corpus.en` or `data/owt_train.txt` exists
2. Check environment variable paths match:
   - `TRAINDATA_PATH` should be: `gs://your-bucket/data/corpus.en`

### **Issue: No output files after job completes**

**Fix:**
1. Check job logs for errors:
   - Vertex AI → Training → Your Job → LOGS tab
   - Look for Python errors
2. Check if `OUTPUTS_PATH` environment variable is set correctly
3. Verify your `train_bpe.py` reads `OUTPUTS_PATH` from environment:
   ```python
   outputs_path = os.getenv("OUTPUTS_PATH", "./outputs")
   ```

---

## **Cleanup (To avoid costs)**

### **After training completes:**

**Option 1: Keep everything for future runs**
- Cost: ~$2/month for storage
- Training jobs auto-shutdown, so no compute costs

**Option 2: Delete everything**
1. Go to: https://console.cloud.google.com/storage/browser
2. Check box next to your bucket
3. Click **"DELETE"**
4. Go to: https://console.cloud.google.com/vertex-ai/training/custom-jobs
5. Delete old jobs (optional, minimal cost)

**Option 3: Delete project (cleanest)**
1. Go to: https://console.cloud.google.com/cloud-resource-manager
2. Select your project
3. Click **"DELETE"**
4. Confirm deletion

---

## **Next Steps**

### **Recommended workflow:**

1. ✅ **Test first** (corpus.en, 2 min, $0.01)
   - Validates your setup works
   - Checks data paths are correct
   - Verifies outputs are saved

2. ✅ **Production training** (owt_train.txt, 10 hours, $4.40)
   - Update environment variables
   - Clone test job → Modify → Submit
   - Monitor in portal

3. ✅ **Download results**
   - Get tokenizer.pkl from Cloud Storage
   - Use in your downstream tasks

4. ✅ **Cleanup** (optional)
   - Delete storage bucket if done
   - Or keep for future experiments

---

## **Quick Reference**

### **Important URLs:**

- **Custom Jobs:** https://console.cloud.google.com/vertex-ai/training/custom-jobs
- **Cloud Storage:** https://console.cloud.google.com/storage/browser
- **APIs:** https://console.cloud.google.com/apis/library
- **IAM:** https://console.cloud.google.com/iam-admin/iam
- **Quotas:** https://console.cloud.google.com/iam-admin/quotas

### **Machine types for 100GB+ memory:**

| Machine Type | vCPUs | Memory | Cost/hour (Regular) | Cost/hour (Preemptible) |
|--------------|-------|--------|---------------------|------------------------|
| n2-highmem-8 | 8 | 64 GB | $0.48 | $0.12 |
| n2-highmem-16 | 16 | 128 GB | $0.96 | $0.24 |
| n2-highmem-32 | 32 | 256 GB | $1.92 | $0.48 |

**Recommended:** n2-highmem-16 with preemptible for your 100GB requirement.

---

## **Why Vertex AI Custom Jobs?**

✅ **Auto-shutdown** - No manual intervention needed
✅ **Professional monitoring** - Same as Azure ML
✅ **Cost-effective** - Pay only for training time
✅ **Resume-worthy** - Industry standard platform
✅ **Reproducible** - Can clone and re-run jobs
✅ **Safe for beginners** - Can't forget and waste credits

**vs. Workbench:** Requires manual shutdown, keeps charging if you forget.

---

## **Summary**

You've set up a professional ML training pipeline equivalent to Azure ML:
- ✅ Auto-scaling compute (scales to 0 after training)
- ✅ Automatic CPU/memory monitoring
- ✅ Managed data storage
- ✅ Reproducible job configs
- ✅ Cost-optimized with preemptible VMs

**Total setup time:** 90 minutes (all via portal)
**Test run cost:** $0.01
**Production run cost:** $4.40
**Auto-shutdown:** Yes
**Monitoring:** Professional dashboards

All without CLI! Everything done in web browser.
