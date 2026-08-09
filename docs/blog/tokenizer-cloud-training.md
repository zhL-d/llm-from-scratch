# Training the BPE Tokenizer in the Cloud(Azure, GCP)

Repo: [`zhL-d/llm-from-scratch`](https://github.com/zhL-d/stf-assignment1-basics)

## Goal

To build a real, on-demand training
pipeline the way it'd actually be done in production: a container
image built from a commit, run as a managed batch job (no VM to
babysit or forget to shut down), authenticating without any long-lived
secret sitting in GitHub or baked into the image, with results landing
in cloud storage instead of a local folder.

## Training Dataset

[TinyStories](https://huggingface.co/datasets/roneneldan/TinyStories) 2.12M

vocabulary size (10,000)

## Attempt 1: Azure

- [`61317ff`](https://github.com/zhL-d/stf-assignment1-basics/commit/61317ff) "init azure trial vm"
- [`aba1c6e`](https://github.com/zhL-d/stf-assignment1-basics/commit/aba1c6e) "Add Docker support..."
- [`eccb08d`](https://github.com/zhL-d/stf-assignment1-basics/commit/eccb08d) "Add build and push workflow, training workflow, and Docker configurations for BPE project and iac for azure container app job"

The goal: a infra-as-code, fully containerized, CI/CD-automated batch
training job, serverless and on-demand, built and deployed via
GitHub Actions, with no long-lived credentials anywhere (no service
principal secret sitting in GitHub, no storage key baked into the
container), and results landing in cloud storage:

- **Bicep** ([`infra/main.bicep`](https://github.com/zhL-d/stf-assignment1-basics/blob/7c4345a/infra/main.bicep)), 
  Azure's native IaC language, declares the resource group, ACR, and the
  Container Apps Job as code, with separate dev/prod parameter files, so
  the whole environment is reproducible instead of hand-clicked in the
  portal.
- **Azure Container Registry (ACR)**, stores the Docker image the job
  runs.
- **Azure Container Apps Jobs (ACA Jobs)**, the actual compute: a
  serverless container that runs to completion and exits, billed only for
  the run itself, no VM to provision or leave running.
- **GitHub Actions OIDC → Azure AD federated credential**, 
  GitHub issues a short-lived token per run that Azure AD trusts directly,
  so the CI pipeline authenticates to Azure without a stored secret.
- **Azure Blob Storage**, holds the corpus going in and the vocab/merges
  coming out.
- **Managed Identity**, the identity the running container itself uses
  to reach Blob Storage; same no-stored-secret idea as OIDC.
- **azcopy**, the actual data mover, authenticating via that Managed
  Identity to move the corpus in and the results back out of Blob Storage.

**What actually happened**: two separate pipelines, each doing one job:

- [`build-and-push.yml`](../../cs336_basics/archive_solution/build-and-push.yml)
  logs in to Azure via OIDC, then builds the **Docker** image and pushes it
  to **ACR**, tagged with both the resolved tag (defaults to the current
  commit SHA) and `latest`.
- [`train.yml`](../../cs336_basics/archive_solution/train.yml) takes
  that image tag plus training params (vocab size, CPU, memory,
  workload profile) as inputs, logs in via OIDC, and runs
  `az containerapp job update` to point the ACA Job at the new image
  with the new config, then kicking off a run.

Together they ran successfully on a Container Apps **consumption
profile**.

**The wall that ended this attempt**: training with a larger corpus
needed 100GB+ memory, and Azure doesn't support switching an existing
Container Apps environment from consumption to a dedicated profile, 
it need a new environment. Dedicated profiles also bill 24/7 even
when idle, not per-run, which undercuts the whole "serverless, pay
only for the run" premise this was built around.

## Attempt 2: GCP Vertex AI

Unlike Attempt 1's GitHub-Actions-driven pipeline, this path is
simpler and manual: `gcloud` CLI commands, run by hand, build the
image, push it, and launch the job. Cloud
Build compiles straight from the repo, Vertex AI Custom Jobs
runs the container, and
[`download_and_train.sh`](../../download_and_train.sh) (the image's
`ENTRYPOINT`) downloads the corpus from GCS before training and
uploads results back after, so the same container image works whether
it's fed a local path or a `gs://` path.

GCP Vertex AI Custom Jobs don't have Azure Container Apps' consumption/dedicated
split, I just need to pick a machine type per job and pay for that job's
duration, which sidesteps the exact scaling wall Attempt 1 hit.


- [`ba52c61`](https://github.com/zhL-d/stf-assignment1-basics/commit/ba52c61) "add vertex ai script"
- [`7496655`](https://github.com/zhL-d/stf-assignment1-basics/commit/7496655) "add vertex job configuration for BPE encoding"
- [`804b5a6`](https://github.com/zhL-d/stf-assignment1-basics/commit/804b5a6) merged as PR #1

Four distinct GCP services do the actual work here:

- **Cloud Build** compiles the Docker image from source, tagged with the
  git SHA so every image is traceable back to the exact commit that
  produced it:
  ```bash
  export GIT_SHA=$(git rev-parse --short HEAD)
  gcloud builds submit --tag eu.gcr.io/digital-proton-473814-m9/bpe-training:trainer-${GIT_SHA} .
  ```
- **Container Registry** (`eu.gcr.io/...`) stores that image.
- **Cloud Storage (GCS)** (`gs://bpe-training-mfp/...`) holds the corpus
  going in and the vocab/merges/token-IDs coming out.
- **Vertex AI Custom Jobs** is the actual compute that runs the container:
  ```bash
  gcloud ai custom-jobs create --region=europe-west3 --display-name=bpe-training-job --config=vertex-job.json
  ```

This is two separate custom jobs, each with its own image built from
its own Dockerfile:

- **Train the tokenizer** (build the vocab/merges):
  [`Dockerfile`](../../Dockerfile) is `python:3.12-slim` plus the
  Google Cloud SDK (for `gsutil`), with
  [`download_and_train.sh`](../../download_and_train.sh) as
  `ENTRYPOINT`, it detects a `gs://` path in `TRAINDATA_PATH`,
  downloads to local disk with `gsutil`, runs training, then uploads
  `OUTPUTS_PATH` back to GCS if that was a `gs://` path too.
- **Encode a corpus into token IDs** using the trained tokenizer:
  [`Dockerfile.encode`](../../Dockerfile.encode) is a separate image.

`deploy/gcp/` holds the two Vertex AI job configs, each a declarative
`workerPoolSpecs` block: which machine type to provision, which image
to pull, and which env vars to inject:

- [`vertex-job.json`](../../deploy/gcp/vertex-job.json), training job.
  `n2-highmem-4`, the `trainer` image, `TRAINDATA_PATH`/`OUTPUTS_PATH`
  pointing at `gs://bpe-training-mfp/...`.
- [`vertex-job_encode.json`](../../deploy/gcp/vertex-job_encode.json)
  , encoding job. `n2-highmem-8` (double the memory of the training
  job's machine, because encoding holds the full corpus and
  its output token IDs in memory at once.

## Bugs worth noting:

### Bug 1: byte-level tokens don't survive a naive JSON round-trip

The tokenizer's vocabulary is a `dict[int, bytes]`, every token is raw
bytes, not text. Most tokens happen to also be readable text, but not all of
them: a merge can glue together bytes that form an incomplete multi-byte
UTF-8 sequence, e.g. `b'\xe2\x80'` (`0xE2` signals "a 3-byte character
starts here," but only 2 bytes showed up).

`json.dump` can only write text, so every `bytes` value has to become a
`str` first:

```python
bad_token = b'\xe2\x80'

bad_token.decode("utf-8")
# UnicodeDecodeError: 'utf-8' codec can't decode bytes in position 0-1:
# unexpected end of data

s = bad_token.decode("utf-8", "surrogateescape")   # -> '\udce2\udc80', OK
json.dumps({"tok": s})                             # -> succeeds, text still
                                                    #    contains the raw
                                                    #    surrogate chars

open("vocab.json", "w", encoding="utf-8").write(json.dumps({"tok": s}))
# UnicodeEncodeError: 'utf-8' codec can't encode characters in position
# surrogates not allowed
```

Two things had to go right:

- [`b902ba9`](https://github.com/zhL-d/stf-assignment1-basics/commit/b902ba9)
- [`a3738d1`](https://github.com/zhL-d/stf-assignment1-basics/commit/a3738d1)
- [`3bc902d`](https://github.com/zhL-d/stf-assignment1-basics/commit/3bc902d)

1. **Converting `bytes` to `str`** needs `errors="surrogateescape"`, it maps each byte it can't interpret as text to a reserved placeholder
   character that silently remembers the original byte value, instead of
   raising.
2. **Writing that resulting string to a file** is a separate operation
   that doesn't know surrogateescape happened upstream, `open(..., "w",
   encoding="utf-8")` still refuses those placeholder characters by
   default. That needs its own `errors="surrogatepass"` on the `open()`
   call itself, both when writing and later when reading the file back.

## What shipped

The final artifacts ended up published as a [Hugging Face dataset](https://huggingface.co/datasets/zehl/tinystories-tokenized-10k/tree/main):
`vocab.json`, `merges.json`, `token_ids.npy`.
