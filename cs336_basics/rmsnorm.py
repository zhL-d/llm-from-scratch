import torch
import torch.nn as nn

class RMSNorm(nn.Module):
    def __init__(self, d_model: int, eps: float = 1e-5, device: torch.device | None = None, dtype: torch.dtype | None = None):
        """ Construct the RMSNorm module.
        
        Args:
            d_model(int): Hidden dimension of the model
            eps(float): Epsilon value for numerical stability
            device(torch.device | None = None): Device to store the parameters on
            dtype(torch.dtype | None = None): Data type of the parameters
        """
        super().__init__()
        self.g = nn.Parameter(torch.randn(10, dtype=dtype, device=device))
        self.eps = eps
    def forword(self, x: torch.Tensor) -> torch.Tensor:
        """Process an input tensor of shape

        Args:
            x (torch.Tensor): shape (batch_size, sequence_length, d_model)
        Returns:
            torch.Tensor: shape (batch_size, sequence_length, d_model)
        """
        in_dtype = x.dtype
        x = x.to(torch.float32)

        x_flat = x.reshape(-1, x.shape[2])
        rms_divisor_flat = torch.vmap(self.rms)(x_flat)
        rms_divisor = rms_divisor_flat.reshape(x.shape[0], x.shape[1], x.shape[2])

        result_after_rms = x / rms_divisor
        result =  result_after_rms * self.g

        return result.to(in_dtype)

    def rms(self, v: torch.Tensor) -> torch.Tensor:
        tmp = (v ** 2).mean() + self.eps
        return torch.sqrt(tmp)
