# import torch
# import torch.nn as nn
# from jaxtyping import Float
# from torch import Tensor
# import cs336_basics.softmax_einx as sm
# import math
# import einx

# class SDPAttention(nn.Module):
#     def __init__(self, q: Float[Tensor, "... queries d_k"], k: Float[Tensor, "... keys d_k"], v: Float[Tensor, "... values d_v"], mask: Float[Tensor, " ... queries keys"] | None = None):
#         super().__init__()

#         self.Q = q
#         self.K = k
#         self.V = v
#         self.mask = mask
#     def forward(self) -> Float[Tensor, "... d_v"]:
#         attention_score_raw = einx.dot("... queries [d_k], ... [d_k] keys -> ... queries keys", self.Q, self.K.transpose(-2, -1))
#         # qk = self.Q @ self.K.transpose(-2, -1)
#         attention_score_raw_norm = einx.divide("... queries keys, -> ... queries keys", attention_score_raw, math.sqrt(self.Q.size(-1)))
#         # qk_norm = qk / math.sqrt(self.Q.size(-1))
#         mask_ninf = einx.where("... queries keys, , -> ... queries keys", self.mask, torch.tensor(0.0), float('-inf'))
#         # mask_ninf = torch.where(self.mask, torch.zeros_like(self.mask), float('-inf'))
#         attention_score_raw_norm_mask = einx.add("... queries keys, ... queries keys -> ... queries keys", attention_score_raw_norm, mask_ninf)
#         # qk_norm_mask = qk_norm + mask_ninf
        
#         attention_score = sm.Softmax(attention_score_raw_norm_mask, -1)
#         result = einx.dot("... queries [keys], ... [values] d_v -> ... queries d_v", attention_score, self.V)
#         # result = attention_score @ self.V

#         return result

