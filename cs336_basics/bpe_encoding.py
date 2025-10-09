from cs336_basics.tokenizer import Tokenizer
import os
import sys
import io
import numpy as np
import logging
from pathlib import Path
from google.cloud import storage

# ---- logging setup ----
log_level = os.getenv("LOG_LEVEL", "INFO").upper
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("tokenizer")

def is_gcs(path: str) -> bool:
    return path.startswith("gs://")

def read_text(corpus_path: str) -> str:
    if is_gcs(corpus_path):
        client = storage.Client()
        bucket_name, blob_name = corpus_path[5:].split("/", 1)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.download_as_text(encoding="utf-8")
    else:
        return Path(corpus_path).read_text(encoding="utf-8")

def write_artifact(path: str, arr: np.ndarray):
    buf = io.BytesIO()
    np.save(buf, arr)
    buf.seek(0)

    if is_gcs(path):
        client = storage.Client()
        bucket_name, blob_name = path[5:].split("/", 1)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(buf.getvalue())
    else:
        Path(path).write_bytes(buf.getvalue())

def normalize_vocab_merge_path(vocab_path: str, merge_path: str) -> tuple[str, str]:
    if is_gcs(vocab_path) and is_gcs(merge_path):
        vocab_json_text = read_text(vocab_path)
        merge_json_text = read_text(merge_path)

        tmp_path = Path("/tmp/tokenizer")
        tmp_path.mkdir(parents=True, exist_ok=True)
        tmp_vocab_path = tmp_path / "vocab.json"
        tmp_merge_path = tmp_path / "merge.json"

        tmp_vocab_path.write_text(vocab_json_text, encoding="utf-8")
        tmp_merge_path.write_text(merge_json_text, encoding="utf-8")

        return str(tmp_vocab_path), str(tmp_merge_path)
    else:
        return vocab_path, merge_path

def main():
    corpus_path = os.getenv("CORPUS_PATH")
    vocab_path = os.getenv("VOCAB_PATH")
    merge_path = os.getenv("MERGE_PATH")
    artifact_path = os.getenv("ARTIFACT_PATH")

    corpus_basename = Path(corpus_path).stem

    artifact_final_path = Path(artifact_path) / f"token_ids_uint16_{corpus_basename}.npy"

    if corpus_path is None:
        print("Error: the env variable CORPUS_PATH is not set")
        sys.exit(1)

    if vocab_path is None:
        print("Error: the env variable VOCAB_PATH is not set")
        sys.exit(1)

    if merge_path is None:
        print("Error: the env variable MERGE_PATH is not set")
        sys.exit(1)

    if artifact_path is None:
        print("Error: the env variable ARTIFACT_PATH is not set")
        sys.exit(1)
    
    logging.info("Job start | vocab_path=%s | merge_path=%s | corpus_path=%s | artifact_path=%s", vocab_path, merge_path, corpus_path, artifact_path)

    vocab_path, merge_path = normalize_vocab_merge_path(vocab_path, merge_path)

    tokenizer = Tokenizer.from_files(vocab_path, merge_path, ["<|endoftext|>"])

    corpus = read_text(corpus_path)

    token_ids = tokenizer.encode(corpus)

    token_ids_np = np.array(token_ids, dtype=np.uint16)

    # np.save(artifact_final_path, token_ids_np)

    write_artifact(artifact_final_path, token_ids_np)

    # print(f"Save {len(token_ids_np)} in {artifact_final_path}")
    logger.info("Encode done | token_count=%d | artifact_path=%s", len(token_ids), artifact_final_path)


if __name__ == "__main__":
    main()

