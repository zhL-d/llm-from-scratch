import torch
import torch.nn as nn
from jaxtyping import Float
from torch import Tensor
import cs336_basics.softmax_einx as sm
import math

class SDPAttention(nn.Module):
    def __init__(self):
        super().__init__()

        # self.Q = q
        # self.K = k
        # self.V = v
        # self.mask = mask
    def forward(self, q: Float[Tensor, "... seq_len d_k"], k: Float[Tensor, "... seq_len d_k"], v: Float[Tensor, "... seq_len d_v"], mask: Float[Tensor, " ... queries keys"] | None = None) -> Float[Tensor, "... d_v"]:
        qk = q @ k.transpose(-2, -1)
        qk_norm = qk / math.sqrt(q.size(-1))

        mask_ninf = torch.where(mask, torch.zeros_like(qk_norm), float('-inf'))

        qk_norm_mask = qk_norm + mask_ninf
        
        attention_score = sm.Softmax(qk_norm_mask, -1)
        result = attention_score @ v

        return result

