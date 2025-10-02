# Vertex AI Training Jobs Guide (GCP's Azure ML Equivalent)

Complete guide to using Vertex AI for BPE training with the same workflow as Azure ML.

---

## **Architecture Comparison**

| Azure ML | Vertex AI (GCP) |
|----------|-----------------|
| Resource Group | GCP Project |
| Azure ML Workspace | Vertex AI Workbench |
| Compute Cluster | Training Cluster |
| ML Job | Custom Training Job |
| Datastore | Cloud Storage Bucket |
| LowPriority (Spot) | Preemptible VMs |

---

## **Prerequisites**

1. GCP account with $300 free credits
2. gcloud CLI installed
3. Your BPE training code

---

## **Quick Start (30 minutes)**

### **Step 1: Enable Vertex AI API (2 min)**

```bash
# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### **Step 2: Create Cloud Storage Bucket (1 min)**

```bash
# Create bucket for data and outputs
gsutil mb -l us-central1 gs://bpe-training-bucket

# Upload your data
gsutil -m cp -r ./data gs://bpe-training-bucket/data
```

### **Step 3: Create Training Script (Already Done!)**

Your existing `train_bpe.py` works as-is! Just needs to read from Cloud Storage.

### **Step 4: Option A - Simple Docker Approach (Recommended)**

**Create Dockerfile:**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY . /app

# Install dependencies
RUN uv sync --frozen

# Entrypoint
ENTRYPOINT ["uv", "run", "python", "cs336_basics/train_bpe.py"]
```

**Build and push:**

```bash
# Build Docker image
docker build -t gcr.io/YOUR_PROJECT_ID/bpe-training:latest .

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/bpe-training:latest
```

### **Step 5: Submit Training Job (1 min)**

```bash
# Submit custom training job
gcloud ai custom-jobs create \
  --region=us-central1 \
  --display-name=bpe-training-vocab32k \
  --worker-pool-spec=machine-type=n2-highmem-16,replica-count=1,container-image-uri=gcr.io/YOUR_PROJECT_ID/bpe-training:latest \
  --args="--vocab-size=32000" \
  --service-account=YOUR_SERVICE_ACCOUNT
```

### **Step 6: Monitor Job**

**Via Console (Web UI):**
1. Go to: https://console.cloud.google.com/vertex-ai/training/custom-jobs
2. Click your job
3. View logs and monitoring

**Via CLI:**

```bash
# List jobs
gcloud ai custom-jobs list --region=us-central1

# Stream logs
gcloud ai custom-jobs stream-logs JOB_ID --region=us-central1
```

---

## **Step 4: Option B - Python Package Approach (Alternative)**

**If you don't want to use Docker:**

```bash
# Package your code
python setup.py sdist

# Upload to Cloud Storage
gsutil cp dist/cs336-basics-0.1.tar.gz gs://bpe-training-bucket/packages/

# Submit job with Python package
gcloud ai custom-jobs create \
  --region=us-central1 \
  --display-name=bpe-training \
  --python-package-uris=gs://bpe-training-bucket/packages/cs336-basics-0.1.tar.gz \
  --python-module=cs336_basics.train_bpe \
  --worker-pool-spec=machine-type=n2-highmem-16,replica-count=1
```

---

## **Environment Variables in Vertex AI**

**Pass environment variables to your job:**

```bash
gcloud ai custom-jobs create \
  --region=us-central1 \
  --display-name=bpe-training \
  --worker-pool-spec=machine-type=n2-highmem-16,replica-count=1,container-image-uri=gcr.io/YOUR_PROJECT_ID/bpe-training:latest \
  --environment-variables="VOCAB_SIZE=32000,TRAINDATA_PATH=gs://bpe-training-bucket/data/owt_train.txt,OUTPUTS_PATH=gs://bpe-training-bucket/outputs"
```

---

## **Cost Optimization: Preemptible VMs**

**Use preemptible VMs (like Azure spot instances) for 80% savings:**

```bash
gcloud ai custom-jobs create \
  --region=us-central1 \
  --display-name=bpe-training \
  --worker-pool-spec=machine-type=n2-highmem-16,replica-count=1,container-image-uri=gcr.io/YOUR_PROJECT_ID/bpe-training:latest,reduction-server-replica-count=0,reduction-server-machine-type=n1-highcpu-16 \
  --enable-web-access \
  --enable-dashboard-access \
  --config=custom-job-config.yaml
```

**In YAML config:**

```yaml
workerPoolSpecs:
  - machineSpec:
      machineType: n2-highmem-16
    replicaCount: 1
    # Enable preemptible
    diskSpec:
      bootDiskType: pd-standard
      bootDiskSizeGb: 100
    # This enables preemptible
    reduction_server_replica_count: 0
```

---

## **Monitoring & Logging**

**Automatic monitoring includes:**

- ✅ CPU utilization (per-core)
- ✅ Memory usage (real-time)
- ✅ Disk I/O
- ✅ Network traffic
- ✅ Custom metrics (if you log with Cloud Logging)

**View in console:**
https://console.cloud.google.com/vertex-ai/training/custom-jobs

---

## **Download Results**

**After job completes:**

```bash
# Download outputs from Cloud Storage
gsutil -m cp -r gs://bpe-training-bucket/outputs ./vertex-ai-results
```

---

## **Cost Estimate**

| Resource | Type | Duration | Cost/hour | Total |
|----------|------|----------|-----------|-------|
| n2-highmem-16 | Regular | 10 hours | $0.96 | $9.60 |
| n2-highmem-16 | Preemptible | 10 hours | $0.24 | $2.40 |
| Cloud Storage | 100 GB | 1 month | $0.020/GB | $2.00 |
| **Total (preemptible)** | | | | **$4.40** |

**Using $300 free credit:** $295.60 remaining

---

## **Comparison: Simple VM vs Vertex AI Jobs**

| Feature | Simple VM | Vertex AI Jobs |
|---------|-----------|----------------|
| Setup time | 15 min | 60 min |
| Monitoring | Manual (SSH) | Automatic dashboards |
| Scalability | Manual | Auto-scaling |
| Reproducibility | Medium | High (YAML config) |
| Learning value | Low | High (production-ready) |
| Cost | Same | Same |
| **Recommended for** | One-time training | Multiple experiments |

---

## **My Recommendation**

### **For Your Current Situation (One Training Run):**

Use **simple VM approach** (from GCP_QUICKSTART.md):
- ✅ Faster setup (30 min vs 60 min)
- ✅ Same result
- ✅ Less complexity

### **For Learning / Multiple Runs:**

Use **Vertex AI Custom Jobs**:
- ✅ Learn industry-standard platform
- ✅ Better monitoring
- ✅ Reproducible (YAML configs)
- ✅ Resume-worthy experience

---

## **Troubleshooting**

### **Error: "Permission denied"**

```bash
# Give yourself required roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member=user:YOUR_EMAIL \
  --role=roles/aiplatform.user
```

### **Error: "Quota exceeded"**

GCP also has quotas, but much higher than Azure for Students.

**Check quota:**
```bash
gcloud compute project-info describe --project=YOUR_PROJECT_ID
```

**Request increase:**
https://console.cloud.google.com/iam-admin/quotas

### **Error: "Container image not found"**

```bash
# Verify image pushed correctly
gcloud container images list --repository=gcr.io/YOUR_PROJECT_ID

# Re-push if needed
docker push gcr.io/YOUR_PROJECT_ID/bpe-training:latest
```

---

## **Next Steps**

1. Choose approach (simple VM or Vertex AI)
2. Follow setup steps
3. Submit training job
4. Monitor in console
5. Download results
6. Clean up resources

**Simple VM:** See GCP_QUICKSTART.md
**Vertex AI:** Follow this guide

Both work! Choose based on your time and learning goals.
