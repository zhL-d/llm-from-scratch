import random
import os

input_path = "cs336_basics/smoke_test_fixture/sample_data/TinyStoriesV2-GPT4-train.txt"
sampel_num = 10

input_path_basename = os.path.basename(input_path)
name_without_ext, _ = os.path.splitext(input_path_basename)
output_path = f"cs336_basics/smoke_test_fixture/sample_data/sample_{name_without_ext}_k{sampel_num}.txt"

with open(input_path, encoding="utf-8") as f:
    corpus = f.read()

docs = corpus.split("<|endoftext|>")
sample_docs = random.sample(docs, k=sampel_num)

with open(output_path, "w", encoding="utf-8") as f_out:
    for doc in sample_docs:
        f_out.write(doc + "<|endoftext|>")

print(f"Save {len(sample_docs)} sampled docs to {output_path}")