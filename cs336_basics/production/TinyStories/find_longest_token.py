import json

with open("/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/production/TinyStories/serialization_vocab.json", "r", encoding="utf-8") as f:
    vocab = json.load(f)

longest_token = max(vocab.values(), key=len)

print(f"Longest token of vocab is[{longest_token}]")