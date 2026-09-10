"""
Abstractive multi-model benchmark on CUAD contracts.

Generates a 2-paragraph summary for each contract with each model in
parallel (via LiteLLM `batch_completion`), records token usage, and
computes cost from the shared pricing table.

Models compared by default:
  - gpt-4o-mini
  - claude-3-5-haiku
  - gemini-1.5-flash
"""

from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any, Dict, List

from litellm import batch_completion

from benchmark.download_data import download_cuad, save_local
from src.cost.pricing import PRICING_PER_MILLION, compute_cost

MODELS = ["gpt-4o-mini", "claude-3-5-haiku", "gemini-1.5-flash"]

PROMPT_TEMPLATE = """You are an expert legal counsel assisting non-legal stakeholders.
Read the following contract and produce a clear, plain-language business summary.

CONSTRAINTS:
1. Output EXACTLY TWO PARAGRAPHS, separated by a blank line.
2. Paragraph 1: Key commercial obligations and service commitments.
3. Paragraph 2: Core liabilities, indemnification risks, and termination conditions.
4. Tone: Professional, direct, plain English. No dense legalese or Latin phrases.

CONTRACT:
{contract}
"""


def truncate_for_model(text: str, model: str) -> str:
    """Keep input within 60% of the model's context window (~4 chars/token)."""
    ctx = PRICING_PER_MILLION.get(model, {}).get("context", 128_000)
    return text[: int(ctx * 0.6 * 4)]


def build_messages(contract_text: str, model: str) -> List[Dict]:
    truncated = truncate_for_model(contract_text, model)
    return [{"role": "user", "content": PROMPT_TEMPLATE.format(contract=truncated)}]


def run_single_model_on_contracts(model: str, contracts: List[Dict]) -> List[Dict]:
    print(f"\nGenerating with: {model}")
    message_batches = [build_messages(c["contract_text"], model) for c in contracts]

    t0 = time.perf_counter()
    responses = batch_completion(
        model=model, messages=message_batches, temperature=0.2, max_tokens=800
    )
    elapsed = time.perf_counter() - t0

    records = []
    for contract, resp in zip(contracts, responses):
        if isinstance(resp, Exception):
            records.append(
                {
                    "contract_id": contract["contract_id"],
                    "model": model,
                    "summary": "",
                    "error": str(resp),
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0.0,
                }
            )
            continue

        usage = getattr(resp, "usage", None)
        in_tok = int(getattr(usage, "prompt_tokens", 0) or 0) if usage else 0
        out_tok = int(getattr(usage, "completion_tokens", 0) or 0) if usage else 0
        records.append(
            {
                "contract_id": contract["contract_id"],
                "model": model,
                "summary": resp.choices[0].message.content.strip(),
                "error": None,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "cost_usd": compute_cost(model, in_tok, out_tok),
            }
        )

    print(f"  {model}: {len(records)} generations in {elapsed:.1f}s")
    return records


def run_abstractive_benchmark(
    sample_size: int = 50,
    output_dir: str = "benchmark/results",
    models: List[str] | None = None,
) -> List[Dict[str, Any]]:
    os.makedirs(output_dir, exist_ok=True)
    models = models or MODELS

    data_path = os.path.join(output_dir, "cuad_sample.json")
    if os.path.exists(data_path):
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
        print(f"Loaded cached sample: {len(data)} contracts")
    else:
        data = download_cuad(sample_size=sample_size)
        save_local(data, data_path)

    all_records: List[Dict[str, Any]] = []
    for model in models:
        all_records.extend(run_single_model_on_contracts(model, data))

    out_path = os.path.join(output_dir, "abstractive_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2)
    print(f"\nSaved {len(all_records)} records to {out_path}")

    print("\n" + "=" * 60)
    print("COST SUMMARY")
    print("=" * 60)
    for model in models:
        m = [r for r in all_records if r["model"] == model and not r["error"]]
        if not m:
            continue
        total = sum(r["cost_usd"] for r in m)
        print(
            f"{model:24s} | {len(m):3d} summaries | avg ${total / len(m):.5f} | "
            f"total ${total:.3f} | "
            f"{sum(r['input_tokens'] for r in m):,} in / "
            f"{sum(r['output_tokens'] for r in m):,} out"
        )

    return all_records


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--sample-size", type=int, default=50)
    p.add_argument("--output-dir", type=str, default="benchmark/results")
    p.add_argument("--models", nargs="+", default=MODELS)
    args = p.parse_args()
    run_abstractive_benchmark(args.sample_size, args.output_dir, args.models)