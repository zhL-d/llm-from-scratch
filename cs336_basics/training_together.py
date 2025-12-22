from pathlib import Path
import numpy as np
from torch import Tensor
from jaxtyping import Int, Float


from cs336_basics.tokenizer import Tokenizer
from cs336_basics.data_loading import DataLoading
from cs336_basics.transformer_lm import TransformerLM
from cs336_basics.cross_entropy import CrossEntropy
from cs336_basics.learning_rate_schedule import LearningRateSchedule
from cs336_basics.adamw import AdamW

def training_loop():
    vocab_path = "cs336_basics/prod/output_TinyStoriesV2-GPT4-train_serialization_vocab_20251010_112414.json"
    merge_path = "cs336_basics/prod/output_TinyStoriesV2-GPT4-train_serialization_merge_20251010_112414.json"
    data_path = Path("cs336_basics/owedataset/owt_valid_sample.txt")
    batch_size = 4
    context_length = 1024
    device = "cpu"
    vocab_size = 50257
    d_model =  1600
    num_layers = 48
    num_heads = 25
    d_ff = 6400
    rope_theta = 10000.0
    steps = 100
    # lr schedule
    alpha_max = 1
    alpha_min = 1 * 0.1
    t_w = 7
    t_c = 21
    # optimizer
    betas = (0.9, 0.999)
    eps = 1e-8
    weight_decay = 0.01

    tokenizer = Tokenizer.from_files(vocab_path, merge_path, ["<|endoftext|>"])
    training_corpus = data_path.read_text(encoding="utf-8")
    token_ids = tokenizer.encode(training_corpus)

    token_ids_ndarray = np.array(token_ids)

    for t in range(steps):
        data_batch_tuple = DataLoading(token_ids_ndarray, batch_size, context_length, device)
        training_data: Int[Tensor, " batch_size context_length"] = data_batch_tuple[0]
        validation_data: Int[Tensor, " batch_size context_length"] = data_batch_tuple[1]
    
        transformerlm = TransformerLM(vocab_size, context_length, num_layers, d_model, num_heads, d_ff, rope_theta)
        logit: Float[Tensor, " batch_size context_length vocab_size"] = transformerlm.forward(training_data)

        loss = CrossEntropy(logit, validation_data)

        lr = LearningRateSchedule(t, alpha_max, alpha_min, t_w, t_c)
        optimizer = AdamW(transformerlm.parameters(), lr, betas, eps, weight_decay)       
        optimizer.zero_grad()
    
        loss.backward()

        # lr = LearningRateSchedule(t, alpha_max, alpha_min, t_w, t_c)

        # optimizer = AdamW(transformerlm.parameters(), lr, betas, eps, weight_decay)
        optimizer.step()

    




    
