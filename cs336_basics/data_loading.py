import torch
import random
from torch import Tensor
import numpy.typing as npt
from jaxtyping import Int

def DataLoading(x: npt.NDArray, batch_size: int, context_length: int, device: str) -> tuple[Int[Tensor, " batch_size context_length"], Int[Tensor, " batch_size context_length"]]:
    input_seqs = torch.empty((batch_size, context_length), device=device, dtype=torch.int)
    targets_next_token = torch.empty((batch_size, context_length), device= device, dtype=torch.int)

    for b in range(batch_size):
        i = random.randrange(0, len(x) - context_length)

        input_seq_sample = torch.from_numpy(x[i : i+context_length]).to(device=input_seqs.device).to(dtype=input_seqs.dtype)
        target_next_token_sample = torch.from_numpy(x[i+1 : i+1+context_length]).to(device=targets_next_token.device).to(dtype=targets_next_token.dtype)

        input_seqs[b] = input_seq_sample
        targets_next_token[b] = target_next_token_sample
    
    return (input_seqs, targets_next_token)

