"""
Central pricing table (USD per 1M tokens).

This is the single source of truth for cost estimation and reconciliation.
It mirrors provider public pricing and is deliberately separate from the
generator so that estimates and actuals always use the same numbers.

Note: pricing is a snapshot for estimation and logging; always consult the
provider for current rates.
"""

from __future__ import annotations

from typing import Dict

# USD per 1M tokens, keyed by model id.
PRICING_PER_MILLION: Dict[str, Dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "context": 128_000},
    "gpt-4o": {"input": 2.50, "output": 10.00, "context": 128_000},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.00, "context": 200_000},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00, "context": 200_000},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30, "context": 1_000_000},
    "gemini-1.5-pro": {"input": 2.50, "output": 7.50, "context": 2_000_000},
}

# Fallback for unknown models (keeps estimation non-fatal).
_FALLBACK = {"input": 0.15, "output": 0.60, "context": 128_000}


def get_price(model: str) -> Dict[str, float]:
    """Return {input, output, context} pricing for a model."""
    return PRICING_PER_MILLION.get(model, _FALLBACK)


def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Compute USD cost for a given token usage."""
    p = get_price(model)
    return round(
        (input_tokens / 1_000_000) * p["input"]
        + (output_tokens / 1_000_000) * p["output"],
        6,
    )