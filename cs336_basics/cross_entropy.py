import torch
from jaxtyping import Float, Int
from torch import Tensor

def CrossEntropy(o: Float[Tensor, "batch_size vocab_size"], targets: Int[Tensor, " batch_size"]) -> Float[Tensor, ""]:
    target_expanded = targets.unsqueeze(-1)

    o_norm = o - o.max(dim=-1, keepdim=True).values

    o_target = o_norm.gather(dim=-1, index=target_expanded).squeeze(-1)
    # See cross_entropy_derivation.md for the full derivation.
    cross_entropy = torch.log(o_norm.exp().sum(-1)) - o_target
    return cross_entropy.mean()
