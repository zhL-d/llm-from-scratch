import json
import torch
from pathlib import Path

from cs336_basics.transformer_lm import TransformerLM
from cs336_basics.tokenizer import Tokenizer
from cs336_basics.decoding import Decoding

def Generate():
    config_path = Path("cs336_basics/checkpoint_gold/config.json")
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    model = TransformerLM(
        vocab_size=config["vocab_size"],
        context_length=config["context_length"],
        num_layers=config["num_layers"],
        d_model=config["d_model"],
        num_heads=config["num_heads"],
        d_ff=config["d_ff"],
        rope_theta=config["rope_theta"]
    )

    cpt_path = Path("cs336_basics/checkpoint_gold/last_checkpoint.pt")
    states = torch.load(cpt_path, map_location="cpu")
    model.load_state_dict(states["model"])

    prompt = "one"
    tokenizer = Tokenizer.from_files(
        vocab_filepath=config["vocab_path"],
        merges_filepath=config["merge_path"],
        special_tokens=config["special_tokens"]
    )
    prompt_ids = tokenizer.encode(prompt)
    eos_id = tokenizer.encode(config["special_tokens"][0])[0]

    model.eval()

    generated_ids = Decoding(
        model=model,
        prompt_ids=prompt_ids,
        max_tokens=256,
        temperature=0.7,
        topp_threshold=0.9,
        eos_id=eos_id,
        context_length=config["context_length"]
    )

    for i in range(generated_ids.size(0)):
        generated_text = tokenizer.decode(generated_ids[i].tolist())
        print(f"generated_text[{i}]: {generated_text}")
    

if __name__ == "__main__":
    Generate()
