from pathlib import Path
import numpy as np
from torch import Tensor
from jaxtyping import Int, Float
from dataclasses import dataclass
import argparse 


from cs336_basics.tokenizer import Tokenizer
from cs336_basics.data_loading import DataLoading
from cs336_basics.transformer_lm import TransformerLM
from cs336_basics.cross_entropy import CrossEntropy
from cs336_basics.learning_rate_schedule import LearningRateSchedule
from cs336_basics.adamw import AdamW
from cs336_basics.checkpointing import save_checkpoint

@dataclass
class TrainConfig:
    vocab_path: str = "cs336_basics/prod/output_TinyStoriesV2-GPT4-train_serialization_vocab_20251010_112414.json"
    merge_path: str = "cs336_basics/prod/output_TinyStoriesV2-GPT4-train_serialization_merge_20251010_112414.json"
    special_tokens: list[str] = ["<|endoftext|>"]
    data_path: Path = Path("cs336_basics/owedataset/owt_valid_sample.txt")
    tokenids_path: Path = Path("cs336_basics/owedataset/token_ids.npy")
    checkpoint_path: Path = Path("cs336_basics/checkpoint/checkpoint.pt")
    batch_size: int = 4
    context_length: int = 1024
    device: str = "cpu"
    vocab_size: int = 50257
    d_model: int =  1600
    num_layers: int = 48
    num_heads: int = 25
    d_ff: int = 6400
    rope_theta: float = 10000.0
    steps: int = 100
    # lr schedule
    alpha_max: float = 1
    alpha_min: float = 1 * 0.1
    t_w: int = 7
    t_c: int = 21
    # optimizer
    betas: tuple[float, float] = (0.9, 0.999)
    eps: float = 1e-8
    weight_decay: float = 0.01

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--vocab_path", type=str, default=TrainConfig.vocab_path)
    p.add_argument("--merge_path", type=str, default=TrainConfig.merge_path)
    p.add_argument("--special_tokens", type=list[str], default=TrainConfig.special_tokens)
    p.add_argument("--data_path", type=Path, default=TrainConfig.data_path)
    p.add_argument("--tokenids_path", type=Path, default=TrainConfig.tokenids_path)
    p.add_argument("--checkpoint_path", type=Path, default=TrainConfig.checkpoint_path)
    p.add_argument("--batch_size", type=int, default=TrainConfig.batch_size)
    p.add_argument("--context_length", type=int, default=TrainConfig.context_length)
    p.add_argument("--device", type=str, default=TrainConfig.device)
    p.add_argument("--vocab_size", type=int, default=TrainConfig.vocab_size)
    p.add_argument("--d_model", type=int, default=TrainConfig.d_model)
    p.add_argument("--num_layers", type=int, default=TrainConfig.num_layers)
    p.add_argument("--num_heads", type=int, default=TrainConfig.num_heads)
    p.add_argument("--d_ff", type=int, default=TrainConfig.d_ff)
    p.add_argument("--rope_theta", type=float, default=TrainConfig.rope_theta)
    p.add_argument("--steps", type=int, default=TrainConfig.steps)
    p.add_argument("--alpha_max", type=float, default=TrainConfig.alpha_max)
    p.add_argument("--alpha_min", type=float, default=TrainConfig.alpha_min)
    p.add_argument("--t_w", type=int, default=TrainConfig.t_w)
    p.add_argument("--t_c", type=int, default=TrainConfig.t_c)
    p.add_argument("--betas", type=tuple[float, float], default=TrainConfig.betas)
    p.add_argument("--eps", type=float, default=TrainConfig.eps)
    p.add_argument("--weight_decay", type=float, default=TrainConfig.weight_decay)

def load_cfg(args) -> TrainConfig:
    cfg = TrainConfig(
        vocab_path = args.vocab_path,
        merge_path = args.merge_path,
        special_tokens = args.special_tokens,
        data_path = args.data_path,
        tokenids_path = args.tokenids_path,
        checkpoint_path = args.checkpoint_path,
        batch_size = args.batch_size,
        context_length = args.context_length,
        device = args.device,
        vocab_size = args.vocab_size,
        d_model =  args.d_model,
        num_layers = args.num_layers,
        num_heads = args.num_heads,
        d_ff = args.d_ff,
        rope_theta = args.rope_theta,
        steps = args.steps,
        # lr schedule
        alpha_max = args.alpha_max,
        alpha_min = args.alpha_min,
        t_w = args.t_w,
        t_c = args.t_c,
        # optimizer
        betas = args.betas,
        eps = args.eps,
        weight_decay = args.weight_decay
    )

    return cfg

def tokenize_and_save(cfg: TrainConfig):
    tokenizer = Tokenizer.from_files(cfg.vocab_path, cfg.merge_path, cfg.special_tokens)
    training_corpus = cfg.data_path.read_text(encoding="utf-8", errors="surrogatepass")
    token_ids = tokenizer.encode(training_corpus)

    token_ids_ndarray = np.array(token_ids)
    
    np.save(cfg.tokenids_path, token_ids_ndarray)


def training_loop():
    # vocab_path = "cs336_basics/prod/output_TinyStoriesV2-GPT4-train_serialization_vocab_20251010_112414.json"
    # merge_path = "cs336_basics/prod/output_TinyStoriesV2-GPT4-train_serialization_merge_20251010_112414.json"
    # special_tokens = ["<|endoftext|>"]
    # data_path = Path("cs336_basics/owedataset/owt_valid_sample.txt")
    # batch_size = 4
    # context_length = 1024
    # device = "cpu"
    # vocab_size = 50257
    # d_model =  1600
    # num_layers = 48
    # num_heads = 25
    # d_ff = 6400
    # rope_theta = 10000.0
    # steps = 100
    # # lr schedule
    # alpha_max = 1
    # alpha_min = 1 * 0.1
    # t_w = 7
    # t_c = 21
    # # optimizer
    # betas = (0.9, 0.999)
    # eps = 1e-8
    # weight_decay = 0.01

    # args = build_parser().parse_args()
 
    # cfg = TrainConfig(
    #     vocab_path = args.vocab_path,
    #     merge_path = args.merge_path,
    #     special_tokens = args.special_tokens,
    #     data_path = args.data_path,
    #     batch_size = args.batch_size,
    #     context_length = args.context_length,
    #     device = args.device,
    #     vocab_size = args.vocab_size,
    #     d_model =  args.d_model,
    #     num_layers = args.num_layers,
    #     num_heads = args.num_heads,
    #     d_ff = args.d_ff,
    #     rope_theta = args.rope_theta,
    #     steps = args.steps,
    #     # lr schedule
    #     alpha_max = args.alpha_max,
    #     alpha_min = args.alpha_min,
    #     t_w = args.t_w,
    #     t_c = args.t_c,
    #     # optimizer
    #     betas = args.betas,
    #     eps = args.eps,
    #     weight_decay = args.weight_decay
    # )

    args = build_parser().parse_args()
    cfg = load_cfg(args)

    # tokenizer = Tokenizer.from_files(cfg.vocab_path, cfg.merge_path, cfg.special_tokens)
    # training_corpus = cfg.data_path.read_text(encoding="utf-8", errors="surrogatepass")
    # token_ids = tokenizer.encode(training_corpus)

    # token_ids_ndarray = np.array(token_ids)

    tokenize_and_save(cfg)
    token_ids_ndarray = np.load(cfg.tokenids_path, mmap_mode='r')

    transformerlm = TransformerLM(cfg.vocab_size, cfg.context_length, cfg.num_layers, cfg.d_model, cfg.num_heads, cfg.d_ff, cfg.rope_theta)


    for t in range(cfg.steps):
        data_batch_tuple = DataLoading(token_ids_ndarray, cfg.batch_size, cfg.context_length, cfg.device)
        training_data: Int[Tensor, " batch_size context_length"] = data_batch_tuple[0]
        validation_data: Int[Tensor, " batch_size context_length"] = data_batch_tuple[1]
    
        logit: Float[Tensor, " batch_size context_length vocab_size"] = transformerlm.forward(training_data)

        loss = CrossEntropy(logit, validation_data)
    
        loss.backward()

        lr = LearningRateSchedule(t, cfg.alpha_max, cfg.alpha_min, cfg.t_w, cfg.t_c)
        optimizer = AdamW(transformerlm.parameters(), lr, cfg.betas, cfg.eps, cfg.weight_decay)
        optimizer.step()

        optimizer.zero_grad()

        save_checkpoint(transformerlm, AdamW, t, cfg.checkpoint_path)

    




    
