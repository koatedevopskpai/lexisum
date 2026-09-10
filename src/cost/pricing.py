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

# USD per 1M tokens, keyed by model id (LiteLLM-canonical).
PRICING_PER_MILLION: Dict[str, Dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "context": 128_000},
    "gpt-4o": {"input": 2.50, "output": 10.00, "context": 128_000},
    "gpt-4.1": {"input": 2.00, "output": 8.00, "context": 1_047_576},
    "o3-mini": {"input": 1.10, "output": 4.40, "context": 200_000},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00, "context": 200_000},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00, "context": 200_000},
    "gemini/gemini-2.0-flash": {"input": 0.10, "output": 0.40, "context": 1_048_576},
    "gemini/gemini-2.5-flash": {"input": 0.30, "output": 2.50, "context": 1_048_576},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00, "context": 1_048_576},
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