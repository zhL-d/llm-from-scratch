import torch
import torch.nn as nn
from jaxtyping import Float
from torch import Tensor
from cs336_basics.rmsnorm_einx import RMSNorm
from cs336_basics.multihead_self_attention_rope import MultiHeadSelfAttentionRope
from cs336_basics.positionwise_feedforward_einx import PWFFN

class TransformerBlock(nn.Module):
    def __init__(self, d_model: int, num_heads: int, d_ff: int, max_seq_len: int, theta: float):
        """Implement the pre-norm Transformer block
        
            Args:
                d_model (int): Dimensionality of the Transformer block inputs
                num_heads (int): Number of heads to use in multi-head self-attention
                d_ff (int): Dimensionality of the position-wise feed-forward inner layer
                max_seq_len (int): Maximum sequence length to pre-cache if your implementation does that.
                theta (float): RoPE parameter
        """
        super().__init__()

        self.rmsnorm_first_layer = RMSNorm(d_model)
        self.rmsnorm_second_layer = RMSNorm(d_model)
        self.multiheadselfattentionrops_layer = MultiHeadSelfAttentionRope(d_model, num_heads, max_seq_len, theta)
        self.positionwiseffn_layer = PWFFN(d_model, d_ff)
    def forward(self, x: Float[Tensor, " batch sequence_length d_model"]) -> Float[Tensor, " batch sequence_length d_model"]:
        x_norm = self.rmsnorm_first_layer.forward(x)
        embedding_attention = self.multiheadselfattentionrops_layer.forward(x_norm)
        result_firstsublayer = x + embedding_attention

        result_firstsublayer_norm = self.rmsnorm_second_layer.forward(result_firstsublayer)
        embedding_pwffn = self.positionwiseffn_layer.forward(result_firstsublayer_norm)
        result_secondsublayer = result_firstsublayer + embedding_pwffn

        return result_secondsublayer