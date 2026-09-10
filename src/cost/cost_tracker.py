"""
FinOps cost tracker: estimates vs. actuals.

LexiSum records every LLM invocation so teams can reconcile projected spend
against actual usage. The tracker:

  - Produces a pre-flight *estimate* for the UI (before a user commits).
  - Logs the *actual* usage to a JSON-lines file after generation, tagged
    with environment/team metadata for FinOps analytics.

Each record stores input/output tokens, USD cost, the strategy used, the
model, and the caller-supplied tags. Because estimates and actuals use the
same `pricing` module, comparisons are always apples-to-apples.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.config import _load_tags, settings
from src.cost.pricing import compute_cost, get_price

_lock = threading.Lock()


def _resolve_log_path(log_path: Optional[str]) -> str:
    """Resolve the usage log path at call time (env wins over settings)."""
    if log_path:
        return log_path
    return os.getenv("USAGE_LOG_PATH") or settings.usage_log_path


def _resolve_tags(tags: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge default FinOps tags (env or settings) with caller tags."""
    env_raw = os.getenv("FINOP_TAGS")
    defaults = _load_tags() if env_raw is not None else settings.finop_tags
    return {**defaults, **(tags or {})}


class CostTracker:
    """Estimate, log, and query LLM usage for FinOps accounting."""

    # ------------------------------------------------------------------
    # Estimation
    # ------------------------------------------------------------------
    @classmethod
    def estimate_cost(cls, model: str, input_text: str, output_estimate_tokens: int = 500) -> Dict[str, float]:
        """Estimate the cost of summarising `input_text` with `model`."""
        import tiktoken

        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")

        input_tokens = len(enc.encode(input_text))
        p = get_price(model)
        input_cost = (input_tokens / 1_000_000) * p["input"]
        output_cost = (output_estimate_tokens / 1_000_000) * p["output"]
        return {
            "input_tokens": input_tokens,
            "estimated_output_tokens": output_estimate_tokens,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_estimate_usd": round(input_cost + output_cost, 6),
        }

    # ------------------------------------------------------------------
    # Actual logging
    # ------------------------------------------------------------------
    @classmethod
    def log_usage(
        cls,
        doc_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        tags: Optional[Dict[str, Any]] = None,
        log_path: Optional[str] = None,
    ) -> None:
        """
        Append an actual-usage record (JSON line) to the usage log.

        The default tags (environment, team) are merged with the caller
        tags; caller tags win on conflicts.
        """
        total_cost = compute_cost(model, input_tokens, output_tokens)
        merged_tags = _resolve_tags(tags)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "doc_id": doc_id,
            "model": model,
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "input_cost_usd": round((input_tokens / 1_000_000) * get_price(model)["input"], 6),
            "output_cost_usd": round((output_tokens / 1_000_000) * get_price(model)["output"], 6),
            "total_cost_usd": total_cost,
            "tags": merged_tags,
        }

        path = _resolve_log_path(log_path)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with _lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------
    @classmethod
    def read_log(cls, log_path: Optional[str] = None) -> list[Dict[str, Any]]:
        """Read all usage records from the log file."""
        path = _resolve_log_path(log_path)
        if not os.path.exists(path):
            return []
        records: list[Dict[str, Any]] = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return records