# GPT-Style Language Model from Scratch

A GPT-style Transformer language model built from raw PyTorch tensor
operations, no `nn.Transformer`, no Hugging Face. Includes:

- A from-scratch **BPE tokenizer**
- The full Transformer architecture: **Embedding**, **RMSNorm**,
  **RoPE**-based multi-head self-attention, **SwiGLU**-based
  position-wise feed-forward, **Linear**, **Softmax**
- A training pipeline: data loader, cross-entropy loss, gradient
  clipping, LR scheduling, **AdamW**
- Autoregressive inference (temperature and top-p sampling)
- FLOPs/memory resource accounting across model scales

## Highlights

- Trained on TinyStories through a learning-rate sweep; followed up with architecture ablations
  (removing normalization, pre-norm vs. post-norm) to confirm their
  impact, tracked with Weights & Biases.
- Profiled and optimized the BPE tokenizer trainer (cProfile, scalene)
  for a **~3x** training-time speedup.
- Automated deployment (GitHub Actions CI/CD) of the tokenizer's
  training/encoding pipeline (Docker) to both **GCP** (Vertex AI, GCS)
  and **Azure** (ACA Jobs, ACR, Bicep IaC).

## Write-ups

- [Transformer Architecture from Scratch](docs/blog/transformer-from-scratch.md)
- [BPE Tokenizer: 4 Optimization Rounds](docs/blog/tokenizer-performance.md)
- [Training Experiments: LR Search and Two Ablations](docs/blog/training-experiments.md)
- [Resource Accounting: Parameters, Memory, and FLOPs](docs/blog/resource-accounting.md)
- [Training the BPE Tokenizer in the Cloud](docs/blog/tokenizer-cloud-training.md)


## Setup


