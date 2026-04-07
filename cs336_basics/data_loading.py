import torch
import numpy as np
from torch import Tensor
import numpy.typing as npt
from jaxtyping import Int

def DataLoading(x: npt.NDArray, batch_size: int, context_length: int, device: str) -> tuple[Int[Tensor, " batch_size context_length"], Int[Tensor, " batch_size context_length"]]:

    starts = np.random.randint(0, len(x) - context_length, size=batch_size)
    offsets = np.arange(context_length)

    input_idx = starts[:, None] + offsets[None, :]
    target_idx = starts[:, None] + offsets[None, :] + 1

    input_seq = torch.from_numpy(np.array(x[input_idx])).to(device, dtype=torch.long)
    target_seq = torch.from_numpy(np.array(x[target_idx])).to(device, dtype=torch.long)

    return input_seq, target_seq

