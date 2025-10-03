#!/bin/bash
set -e

# GCS data download script (runs before training)
# This keeps training code platform-agnostic

echo "=== Data Download Stage ==="

# Check if TRAINDATA_PATH is a GCS path
if [[ "${TRAINDATA_PATH}" == gs://* ]]; then
    echo "Detected GCS path: ${TRAINDATA_PATH}"

    # Download to /tmp (fast local SSD on Vertex AI)
    LOCAL_PATH="/tmp/$(basename ${TRAINDATA_PATH})"
    echo "Downloading to: ${LOCAL_PATH}"

    gsutil -m cp "${TRAINDATA_PATH}" "${LOCAL_PATH}"

    echo "Download complete. Size:"
    ls -lh "${LOCAL_PATH}"

    # Override env var to point to local path
    export TRAINDATA_PATH="${LOCAL_PATH}"
fi

echo "=== Training Stage ==="
echo "Using data path: ${TRAINDATA_PATH}"

# Run training with local path
uv run python cs336_basics/train_bpe.py
