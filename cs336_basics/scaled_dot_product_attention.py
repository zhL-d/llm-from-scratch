import torch
import torch.nn as nn
from jaxtyping import Float, Bool
from torch import Tensor

class SDPAttention(nn.Module):
    def __init__(self, q: Float[Tensor, "... d_k"], k: Float[Tensor, "... d_k"], v: Float[Tensor, "... d_v"], mask: Bool[Tensor, "seq_len seq_len"] | None = None):
        super().__init__()
    def forward(self) -> Float[Tensor, "... d_v"]:
        pass