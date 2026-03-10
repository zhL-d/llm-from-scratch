from pathlib import Path
import numpy as np
from torch import Tensor
from jaxtyping import Int, Float
from dataclasses import asdict, dataclass
import argparse
import wandb
from datetime import datetime
import json
import time

from cs336_basics.tokenizer import Tokenizer
from cs336_basics.data_loading import DataLoading
from cs336_basics.transformer_lm import TransformerLM
from cs336_basics.cross_entropy import CrossEntropy
from cs336_basics.learning_rate_schedule import LearningRateSchedule
from cs336_basics.adamw import AdamW
from cs336_basics.checkpointing import save_checkpoint
from cs336_basics.gradient_clipping import GradientClipping

@dataclass
class TrainConfig:
    vocab_path: str = "cs336_basics/prod/output_TinyStoriesV2-GPT4-train_serialization_vocab_20251010_112414.json"
    merge_path: str = "cs336_basics/prod/output_TinyStoriesV2-GPT4-train_serialization_merge_20251010_112414.json"
    special_tokens: list[str] = ["<|endoftext|>"]
    data_path: Path = Path("cs336_basics/owedataset/owt_valid_sample.txt")
    data_vali_path: Path = Path("cs336_basics/owedataset/owt_valid_sample.txt")
    tokenids_path: Path = Path("cs336_basics/owedataset/token_ids.npy")
    tokenids_vali_path: Path = Path("cs336_basics/owedataset/token_vali_ids.npy")
    # checkpoint_path: Path = Path("cs336_basics/checkpoint/checkpoint.pt")
    checkpoint_path: Path = Path("cs336_basics/checkpoint")
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

def make_run_dir(base_path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = base_path / ts
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir

def save_config(cfg: TrainConfig, path: Path):
    path.write_text(json.dumps(asdict(cfg), indent=2, default=str), encoding="utf-8")

def training_loop():

    args = build_parser().parse_args()
    cfg = load_cfg(args)

    run_dir = make_run_dir(cfg.checkpoint_path)
    save_config(cfg, run_dir / "config.json")

    run = wandb.init(
    entity="sft_llm",
    project="wb-hello-world",
    config=asdict(cfg),
    dir=str(run_dir)
)
    
    lastckpt = run_dir / "last_checkpoint.pt"

    # tokenizer = Tokenizer.from_files(cfg.vocab_path, cfg.merge_path, cfg.special_tokens)
    # training_corpus = cfg.data_path.read_text(encoding="utf-8", errors="surrogatepass")
    # token_ids = tokenizer.encode(training_corpus)

    # token_ids_ndarray = np.array(token_ids)

    if not cfg.tokenids_path.exists():
        tokenize_and_save(cfg)

    token_ids_ndarray = np.load(cfg.tokenids_path, mmap_mode='r')

    transformerlm = TransformerLM(cfg.vocab_size, cfg.context_length, cfg.num_layers,
                                  cfg.d_model, cfg.num_heads, cfg.d_ff,
                                  cfg.rope_theta).to(cfg.device)
    transformerlm.train()

    optimizer = AdamW(transformerlm.parameters(), cfg.alpha_max, cfg.betas, cfg.eps, cfg.weight_decay)


    for t in range(cfg.steps):
        start_time = time.time()           

        data_batch_tuple = DataLoading(token_ids_ndarray, cfg.batch_size, cfg.context_length, cfg.device)
        training_data: Int[Tensor, " batch_size context_length"] = data_batch_tuple[0]
        validation_data: Int[Tensor, " batch_size context_length"] = data_batch_tuple[1]
    
        logit: Float[Tensor, " batch_size context_length vocab_size"] = transformerlm.forward(training_data)

        loss = CrossEntropy(logit, validation_data)
    
        optimizer.zero_grad()
        loss.backward()
        GradientClipping(transformerlm.parameters(), max_l2_norm=1.0)

        lr = LearningRateSchedule(t, cfg.alpha_max, cfg.alpha_min, cfg.t_w, cfg.t_c)
        for group in optimizer.param_groups:
            group["lr"] = lr

        optimizer.step()

        # Log metrics to wandb.
        run.log(
            {
                "loss": loss,
                "learning_rate": lr,
                "step": t,
                "wallclock time": time.time() - start_time,
            }
        )

        if t % 1000 == 0 or t == (cfg.steps - 1):
            save_checkpoint(transformerlm, optimizer, t, lastckpt)

    # Finish the run and upload any remaining data.
    artifact = wandb.Artifact("transformer_checkpoint_config", type="model")
    artifact.add_dir(str(run_dir))
    run.log_artifact(artifact)
    run.finish()

    




    
