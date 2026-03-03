import torch
from torch import Tensor
import numpy.typing as npt
from jaxtyping import Float, Int
import einx
from dataclasses import dataclass

from cs336_basics.transformer_lm import TransformerLM

@dataclass
class TrainConfig:
    vocab_size: int = 50257
    context_length: int = 1024
    d_model: int =  1600
    num_layers: int = 48
    num_heads: int = 25
    d_ff: int = 6400
    rope_theta: float = 10000.0

cfg = TrainConfig()
llm = TransformerLM(cfg.vocab_size, cfg.context_length, cfg.num_layers, cfg.d_model, cfg.num_heads, cfg.d_ff, cfg.rope_theta)

def Decoding(model: TransformerLM, prompt_ids: npt.NDArray, max_tokens: int, temperature: float, topp_threshold: float, eos_id: int, context_length: int) -> Int[Tensor, "B Seq"]:
    device = next(model.parameters()).device
    
    prompt_ids_tensor: Int[Tensor, "batch_size seq_length"] = torch.from_numpy(prompt_ids)
    x = prompt_ids_tensor.to(device)   # [B, Seq]

    finished = torch.zeros(x.size(0), dtype=torch.bool, device=device)

    with torch.no_grad():
        for _ in range(max_tokens):
            x_in = x[:, -context_length:]
            
            logits = model(x_in)    # [B, context_len, V]
            logit_last = logits[:, -1, :] # [B, V]

            probs = SoftmaxTemp(logit_last, dim=-1, temp=temperature)   # [B, V]
            probs = TopP(probs, topp_threshold) # [B, V]

            next_id = torch.multinomial(probs, num_samples=1).squeeze(1) # [B]
            next_id = torch.where(finished, torch.full_like(next_id, eos_id), next_id)  # [B]

            x = torch.cat([x, next_id.unsqueeze(1)], dim=1) # [B, Seq]

            finished = finished | (next_id == eos_id)

            if finished.all():
                break
    
    return x


def TopP(probs: float[Tensor, "B V"], p: float) -> float[Tensor, "B V"]:
    B, V = probs.shape

    sorted_probs, sorted_idx = torch.sort(probs, dim=-1, descending=True)

    cum = torch.cumsum(sorted_probs, dim=-1) # [B, V]

    cutoff_pos = (cum >= p).float().argmax(-1) # [B]

    pos = torch.arange(V, device=probs.device).unsqueeze(0) # [1, V]
    keep_sorted = pos <= cutoff_pos.unsqueeze(-1)   # [B V]

    keep_vocab = torch.zeros_like(keep_sorted)
    keep_sorted.scatter_(dim=-1, index=sorted_idx, src=keep_sorted)

    kept = probs * keep_sorted.to(probs.dtype) # [B, V]
    denom = kept.sum(dim=-1, keepdim=True) # [B, 1]
    return kept / denom

def SoftmaxTemp(x: Float[Tensor, " ..."], dim: int, temp: float) -> Float[Tensor, " ..."]:
    logit_stable = einx.subtract("... logits, ... 1 -> ... logits", x, x.max(dim=dim, keepdim=True).values)
    logit_stable_exp = torch.exp(logit_stable / temp)
    result = einx.divide("... logits, ... 1 -> ... logits", logit_stable_exp, logit_stable_exp.sum(dim=dim, keepdim=True))

    return result
