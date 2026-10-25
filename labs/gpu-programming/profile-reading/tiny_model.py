"""A tiny pre-LayerNorm transformer used as a profiling target (CPU, seeded, deterministic shapes)."""
from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F

B, T, D, H, LAYERS = 8, 64, 128, 4, 2  # batch, sequence, model width, heads, layers


class Block(nn.Module):
    def __init__(self, d: int, heads: int, attention: str) -> None:
        super().__init__()
        self.heads, self.attention = heads, attention
        self.ln1, self.ln2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.qkv, self.proj = nn.Linear(d, 3 * d), nn.Linear(d, d)
        self.up, self.down = nn.Linear(d, 4 * d), nn.Linear(4 * d, d)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, t, d = x.shape
        dh = d // self.heads
        q, k, v = self.qkv(self.ln1(x)).view(b, t, 3, self.heads, dh).permute(2, 0, 3, 1, 4)
        if self.attention == "explicit":
            # the (b, heads, t, t) score matrix is materialized, then read back by softmax, then by the product
            scores = (q @ k.transpose(-2, -1)) / math.sqrt(dh)
            causal = torch.triu(torch.ones(t, t, dtype=torch.bool), diagonal=1)
            y = torch.softmax(scores.masked_fill(causal, float("-inf")), dim=-1) @ v
        else:
            y = F.scaled_dot_product_attention(q, k, v, is_causal=True)  # one fused operator
        x = x + self.proj(y.transpose(1, 2).reshape(b, t, d))
        return x + self.down(F.gelu(self.up(self.ln2(x))))


def build(attention: str = "explicit", seed: int = 0) -> tuple[nn.Module, torch.Tensor]:
    torch.manual_seed(seed)
    model = nn.Sequential(*[Block(D, H, attention) for _ in range(LAYERS)])
    return model, torch.randn(B, T, D)


def step(model: nn.Module, x: torch.Tensor) -> None:
    model(x).pow(2).mean().backward()


def forward_matmul_flops() -> int:
    """Dense-matmul FLOPs of one forward pass: per layer 24 B T D^2 (qkv, proj, up, down) + 4 B T^2 D
    (scores and weighted sum). A multiply-add counts as 2 FLOP."""
    return LAYERS * (24 * B * T * D * D + 4 * B * T * T * D)
