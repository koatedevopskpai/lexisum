"""
Central configuration for LexiSum.

All runtime behaviour is driven by environment variables (via `.env`)
so the same codebase runs on Azure, GCP, AWS, or plain OpenAI with no
code changes - just different credentials and a model id.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict

from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Model context windows (tokens). Used by the context-strategy to decide
# between single-shot and chunked-recursive summarisation.
# ---------------------------------------------------------------------------
MODEL_CONTEXT_LIMITS: Dict[str, int] = {
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-4-turbo": 128_000,
    "claude-3-5-sonnet": 200_000,
    "claude-3-5-haiku": 200_000,
    "claude-3-haiku": 200_000,
    "gemini-1.5-pro": 2_000_000,
    "gemini-1.5-flash": 1_000_000,
    "gemini-2.0-flash": 1_000_000,
}


def _load_tags() -> Dict[str, str]:
    """Parse FINOP_TAGS JSON from env, returning a safe default on error."""
    raw = os.getenv("FINOP_TAGS", "{}")
    try:
        tags = json.loads(raw)
        if not isinstance(tags, dict):
            return {}
        return {str(k): str(v) for k, v in tags.items()}
    except json.JSONDecodeError:
        return {}


@dataclass(frozen=True)
class Settings:
    """Immutable application settings loaded from the environment."""

    # Context strategy
    context_strategy: str = os.getenv("CONTEXT_STRATEGY", "auto")
    chunk_overlap_ratio: float = float(os.getenv("CHUNK_OVERLAP_RATIO", "0.1"))
    max_chunk_tokens: int = int(os.getenv("MAX_CHUNK_TOKENS", "6000"))

    # Abstractive
    abstractive_model: str = os.getenv("ABSTRACTIVE_MODEL", "gpt-4o-mini")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    max_output_tokens: int = int(os.getenv("MAX_OUTPUT_TOKENS", "800"))

    # Extractive
    extractive_engine: str = os.getenv("EXTRACTIVE_ENGINE", "sbert")
    sbert_model: str = os.getenv("SBERT_MODEL", "all-MiniLM-L6-v2")
    extractive_top_n: int = int(os.getenv("EXTRACTIVE_TOP_N", "3"))

    # FinOps
    finop_tags: Dict[str, str] = field(default_factory=_load_tags)
    usage_log_path: str = os.getenv("USAGE_LOG_PATH", "logs/usage.log")


settings = Settings()


def get_model_context_limit(model: str) -> int:
    """Return the context-window (tokens) for a model, with a safe fallback."""
    return MODEL_CONTEXT_LIMITS.get(model, 8_000)


def get_provider_config() -> Dict[str, str]:
    """
    Return the provider-specific environment configuration needed by LiteLLM.
    Only includes keys that are actually set, so LiteLLM can auto-discover
    credentials for the active provider.
    """
    providers = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY", ""),
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        "AZURE_OPENAI_DEPLOYMENT_NAME": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", ""),
        "AZURE_OPENAI_API_VERSION": os.getenv("AZURE_OPENAI_API_VERSION", ""),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID", ""),
        "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        "AWS_REGION": os.getenv("AWS_REGION", "us-east-1"),
    }
    return {k: v for k, v in providers.items() if v}