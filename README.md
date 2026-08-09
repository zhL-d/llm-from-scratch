# GPT-Style Language Model from Scratch

## Highlights

- A GPT-style Transformer language model built from raw PyTorch tensor
operations, no nn.Transformer, no Hugging Face. Full development details are documented in the blog: [Transformer Architecture from Scratch](docs/blog/transformer-from-scratch.md). Key components include:

  - A from-scratch **BPE tokenizer**
  ([`train_bpe.py`](cs336_basics/train_bpe.py),
  [`bpetokenizer_trainer.py`](cs336_basics/bpetokenizer_trainer.py),
  [`tokenizer.py`](cs336_basics/tokenizer.py))
  - The full **Transformer architecture**: Embedding
  ([`embedding.py`](cs336_basics/embedding.py)), RMSNorm
  ([`rmsnorm_einx.py`](cs336_basics/rmsnorm_einx.py)), RoPE-based
  Multi-Head Self-Attention
  ([`multihead_self_attention_rope.py`](cs336_basics/multihead_self_attention_rope.py),
  using [`rope_einx.py`](cs336_basics/rope_einx.py)), SwiGLU-based
  Position-Wise Feed-Forward
  ([`positionwise_feedforward_einx.py`](cs336_basics/positionwise_feedforward_einx.py)),
  Linear ([`linear_module.py`](cs336_basics/linear_module.py)),
  Softmax ([`softmax_einx.py`](cs336_basics/softmax_einx.py))
  - A **Training Pipeline**: Data Loader
  ([`data_loading.py`](cs336_basics/data_loading.py)), Cross-Entropy Loss ([`cross_entropy.py`](cs336_basics/cross_entropy.py)), Gradient Clipping ([`gradient_clipping.py`](cs336_basics/gradient_clipping.py)),
  LR Scheduling
  ([`learning_rate_schedule.py`](cs336_basics/learning_rate_schedule.py)),
  AdamW ([`adamw.py`](cs336_basics/adamw.py)), Checkpointing
  ([`checkpointing.py`](cs336_basics/checkpointing.py)) tied together
  in [`training_together.py`](cs336_basics/training_together.py)
  - A **Inference Pipeline** 
  ([`generate.py`](cs336_basics/generate.py),
  [`decoding.py`](cs336_basics/decoding.py)) with temperature and
  top-p sampling

- Trained on dataset([TinyStories](https://huggingface.co/datasets/roneneldan/TinyStories)) through a learning-rate sweep, reaching a
  validation loss of **1.62**, see **Weights & Biases** experiments report([Training Experiments: The Importance of Parameter Initialization](https://wandb.ai/sft_llm/stf-assignment1-basics-cs336_basics/reports/Tune-the-learning-rate-Report--VmlldzoxNjU1ODcwNg)).
- Architecture Ablations(Ablation 1: **Remove RMSNorm**, Ablation 2: **Pre-norm vs. Post-norm**) to confirm their impact, see **Weights & Biases** experiments report([Ablation 1: Remove RMSNorm](https://wandb.ai/sft_llm/stf-assignment1-basics-cs336_basics/reports/Ablation-1-Remove-RMSNorm--VmlldzoxNzY1NzQzMA), [Ablation 2: Pre-norm vs. Post-norm](https://wandb.ai/sft_llm/stf-assignment1-basics-cs336_basics/reports/Ablation-1-pre_norm_ablation--VmlldzoxNzY1NzQ2OA))
- Profiled and optimized the BPE tokenizer trainer (cProfile, scalene)
  for a **~3x** training-time speedup, see blog
  [BPE Tokenizer: 4 Optimization Rounds](docs/blog/tokenizer-performance.md).
- Automated deployment (GitHub Actions CI/CD) of the tokenizer's
  training/encoding pipeline (Docker) to both **GCP** (Vertex AI, GCS)
  and **Azure** (ACA Jobs, ACR, Bicep IaC). See blog
  [Training the BPE Tokenizer in the Cloud](docs/blog/tokenizer-cloud-training.md).
- FLOPs/memory resource accounting
  ([`transformer_accounting.ipynb`](cs336_basics/notebooks/transformer_accounting.ipynb),
  [`adamwAccounting.ipynb`](cs336_basics/notebooks/adamwAccounting.ipynb))
  across model scales, see blog [Resource Accounting: Parameters, Memory, and FLOPs](docs/blog/resource-accounting.md)

## Write-ups

- [Transformer Architecture from Scratch](docs/blog/transformer-from-scratch.md)
- [BPE Tokenizer: 4 Optimization Rounds](docs/blog/tokenizer-performance.md)
- [Resource Accounting: Parameters, Memory, and FLOPs](docs/blog/resource-accounting.md)
- [Training the BPE Tokenizer in the Cloud](docs/blog/tokenizer-cloud-training.md)
- [Training Experiments: The Importance of Parameter Initialization](https://wandb.ai/sft_llm/stf-assignment1-basics-cs336_basics/reports/Tune-the-learning-rate-Report--VmlldzoxNjU1ODcwNg)
- [Training Experiments: Ablation 1: Remove RMSNorm](https://wandb.ai/sft_llm/stf-assignment1-basics-cs336_basics/reports/Ablation-1-Remove-RMSNorm--VmlldzoxNzY1NzQzMA)
- [Training Experiments: Ablation 2: Pre-norm vs. Post-norm](https://wandb.ai/sft_llm/stf-assignment1-basics-cs336_basics/reports/Ablation-1-pre_norm_ablation--VmlldzoxNzY1NzQ2OA)


