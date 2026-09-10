"""
Download and prepare the CUAD dataset for benchmarking.

CUAD (Contract Understanding Atticus Dataset) contains 510 commercial legal
contracts with 13,000+ expert annotations across 41 clause types. We build a
gold extractive reference by concatenating each contract's annotated clause
texts, which lets us measure whether an extractor selects the clauses a
human expert flagged as important.

Dataset: https://huggingface.co/datasets/theatticusproject/cuad-qa
Paper:   https://arxiv.org/abs/2103.06268

Note: the original HuggingFace dataset ships a loading *script*, which the
`datasets` library no longer executes (v4+). We therefore download the official
auto-converted Parquet files directly, which is faster and dependency-light.
"""

from __future__ import annotations

import json
import os
import random
import urllib.request
from typing import Dict, List

# Auto-converted Parquet files (SQuAD-style: id, title, context, question, answers).
_PARQUET_BASE = (
    "https://huggingface.co/datasets/theatticusproject/cuad-qa/resolve/"
    "refs%2Fconvert%2Fparquet/default"
)
TRAIN_FILES = [f"{_PARQUET_BASE}/train/{i:04d}.parquet" for i in range(3)]

CACHE_DIR = os.path.join("benchmark", "results", "_cuad_cache")


def _download_parquet(urls: List[str], cache_dir: str = CACHE_DIR) -> List[str]:
    """Download Parquet shards to a local cache and return their paths."""
    os.makedirs(cache_dir, exist_ok=True)
    local_paths: List[str] = []
    for url in urls:
        filename = url.rsplit("/", 1)[-1]
        local_path = os.path.join(cache_dir, filename)
        if not os.path.exists(local_path):
            print(f"  downloading {filename}...")
            urllib.request.urlretrieve(url, local_path)
        local_paths.append(local_path)
    return local_paths


def download_cuad(sample_size: int = 100, seed: int = 42) -> List[Dict]:
    """
    Load CUAD and return a deterministic sample of contracts.

    Each item:
      {
        "contract_id": str,
        "contract_text": str,
        "gold_clauses": [str, ...],
        "gold_summary": str,
      }
    """
    from datasets import load_dataset

    print(f"Loading CUAD Parquet files ({len(TRAIN_FILES)} shards)...")
    local_files = _download_parquet(TRAIN_FILES)
    dataset = load_dataset("parquet", data_files=local_files, split="train")

    contracts: Dict[str, Dict] = {}
    for row in dataset:
        title = (
            row.get("title")
            or row.get("contract_name")
            or str(row.get("id", "unknown"))
        )
        entry = contracts.setdefault(
            title,
            {
                "contract_id": title,
                "contract_text": row.get("context", "") or row.get("text", ""),
                "gold_clauses": [],
            },
        )
        answer = row.get("answers", {})
        if isinstance(answer, dict):
            texts = answer.get("text", [])
            clause_text = texts[0] if len(texts) else ""
        else:
            clause_text = str(answer)
        if clause_text and clause_text.strip():
            entry["gold_clauses"].append(clause_text.strip())

    valid = [
        c
        for c in contracts.values()
        if len(c["contract_text"].split()) > 500 and len(c["gold_clauses"]) >= 3
    ]

    random.seed(seed)
    sample = random.sample(valid, min(sample_size, len(valid)))
    for c in sample:
        c["gold_summary"] = " ".join(c["gold_clauses"])

    print(f"Loaded {len(sample)} contracts (from {len(valid)} valid).")
    return sample


def save_local(data: List[Dict], path: str = "benchmark/results/cuad_sample.json") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Saved sample to {path}")


if __name__ == "__main__":
    save_local(download_cuad(sample_size=100))