import torch
import torch.nn as nn
from collections.abc import Iterable

def GradientClipping(para_list: Iterable[nn.Parameter], max_l2_norm: float, eps: float = 1e-6):
    """
    Gradient clipping
    
    :param para_list: List of parameters
    :type para_list: Iterable[nn.Parameter]
    :param max_l2_norm: Maximum l2-norm
    :type max_l2_norm: float
    :param eps: Added for numeric stability
    :type eps: float = 1e-6
    """
    params = list(para_list)
    l2_norm = torch.sqrt(sum(para.grad.pow(2).sum() for para in params if para.grad is not None))

    if l2_norm < max_l2_norm:
        return l2_norm.item()
    for para in params:
        if para.grad is None:
            continue
        para.grad = (max_l2_norm / (l2_norm + eps)) * para.grad
    
    return l2_norm.item()

