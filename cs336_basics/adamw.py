from collections.abc import Callable
import torch
import math

class AdamW(torch.optim.Optimizer):
    def __init__(self, params, lr, betas, eps, weight_decay):
        if lr < 0:
            raise ValueError(f"Invalid learning rate: {lr}")
        defaults = {
            "lr": lr,
            "betas": betas,
            "eps": eps,
            "weight_decay": weight_decay
        }
        super().__init__(params, defaults)
    def step(self, closure: Callable | None = None):
        loss = None if closure is None else closure()
        for group in self.param_groups:
            lr = group["lr"]
            beta_1 = group["betas"][0]
            beta_2 = group["betas"][1]
            eps = group["eps"]
            weight_decay = group["weight_decay"]

            for p in group["params"]:
                if p.grad is None:
                    continue

                state = self.state[p]

                if len(state) == 0:
                    state["t"] = 1
                    state["m"] = torch.zeros_like(p.data)
                    state["v"] = torch.zeros_like(p.data)

                m = state["m"]
                v = state["v"]
                t = state["t"]


                grad = p.grad.data

                state["m"] = beta_1 * m + (1 - beta_1) * grad
                state["v"] = beta_2 * v + (1 - beta_2) * (grad ** 2)

                lr_t = lr * (math.sqrt(1 - math.pow(beta_2, t)) / (1 - math.pow(beta_1, t)))
                p.data = p.data - lr_t * (state["m"] / (torch.sqrt(state["v"]) + eps))
                p.data = p.data - lr * weight_decay * p.data

                state["t"] = t + 1
        
        return loss
