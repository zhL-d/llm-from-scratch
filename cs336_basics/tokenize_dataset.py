import time
import numpy as np
from pathlib import Path
from tqdm import tqdm
from cs336_basics.tokenizer import Tokenizer

VOCAB_PATH = "cs336_basics/prod/output_TinyStoriesV2-GPT4-train_serialization_vocab_20251010_112414.json"
MERGE_PATH = "cs336_basics/prod/output_TinyStoriesV2-GPT4-train_serialization_merge_20251010_112414.json"
TRAIN_TXT = "cs336_basics/mydataset/TinyStoriesV2-GPT4-train.txt"
VALID_TXT = "cs336_basics/mydataset/TinyStoriesV2-GPT4-valid.txt"
TRAIN_NPY = "cs336_basics/mydataset/token_ids.npy"
VALID_NPY = "cs336_basics/mydataset/token_vali_ids.npy"

tokenizer = Tokenizer.from_files(VOCAB_PATH, MERGE_PATH, ["<|endoftext|>"])

for txt_path, npy_path in [(TRAIN_TXT, TRAIN_NPY), (VALID_TXT, VALID_NPY)]:
    if Path(npy_path).exists():
        print(f"Already exists, skipping: {npy_path}")
        continue
    print(f"Tokenizing {txt_path} ...")
    t0 = time.time()
    with open(txt_path, encoding="utf-8") as f:
        arr = np.fromiter(
            tqdm(tokenizer.encode_iterable(f), unit=" tok", desc=Path(txt_path).name,
                 miniters=100_000),
            dtype=np.int32,
        )
    elapsed = time.time() - t0
    np.save(npy_path, arr)
    print(f"Saved {npy_path} — shape: {arr.shape}, time: {elapsed:.0f}s")
