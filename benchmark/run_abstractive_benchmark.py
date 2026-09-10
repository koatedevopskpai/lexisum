"""
Abstractive multi-model benchmark on CUAD contracts.

Generates a 2-paragraph summary for each contract with each model, records
token usage, and computes cost from the shared pricing table.

Rate-limit safety
-----------------
Providers enforce request-per-minute limits, so firing hundreds of requests
at once (LiteLLM's `batch_completion` defaults to 100 workers) triggers 429s.
This runner therefore:
  - splits contracts into small batches (`--batch-size`),
  - bounds in-flight requests with `--max-concurrency` (batch_completion
    `max_workers`),
  - lets LiteLLM retry transient failures with exponential backoff
    (`--max-retries`),
  - retries a whole failed batch (`--batch-retries`) before marking its
    contracts as errors,
  - pauses between batches (`--batch-delay`) to smooth RPM.

Models compared by default (current, comparable fast/cheap tier):
  - gpt-4o-mini             (OpenAI)
  - claude-haiku-4-5        (Anthropic)
  - gemini/gemini-3.6-flash (Google)
"""

from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any, Dict, Iterable, List

from litellm import batch_completion

from benchmark.download_data import download_cuad, save_local
from src.cost.pricing import PRICING_PER_MILLION, compute_cost

MODELS = ["gpt-4o-mini", "claude-haiku-4-5", "gemini/gemini-3.6-flash"]

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


def _chunks(items: List[Any], size: int) -> Iterable[List[Any]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _record_from_response(model: str, contract: Dict, resp: Any) -> Dict[str, Any]:
    """Convert a LiteLLM response (or exception) into a result record."""
    if isinstance(resp, Exception):
        return {
            "contract_id": contract["contract_id"],
            "model": model,
            "summary": "",
            "error": str(resp),
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
        }

    usage = getattr(resp, "usage", None)
    in_tok = int(getattr(usage, "prompt_tokens", 0) or 0) if usage else 0
    out_tok = int(getattr(usage, "completion_tokens", 0) or 0) if usage else 0
    return {
        "contract_id": contract["contract_id"],
        "model": model,
        "summary": resp.choices[0].message.content.strip(),
        "error": None,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cost_usd": compute_cost(model, in_tok, out_tok),
    }


def _process_batch(
    model: str,
    batch: List[Dict],
    max_concurrency: int,
    max_retries: int,
    request_timeout: int,
    max_tokens: int,
) -> List[Any]:
    """Call the provider for one batch, retrying whole-batch failures."""
    message_batches = [build_messages(c["contract_text"], model) for c in batch]
    return batch_completion(
        model=model,
        messages=message_batches,
        temperature=0.2,
        max_tokens=max_tokens,
        max_workers=max_concurrency,
        timeout=request_timeout,
        num_retries=max_retries,
    )


def run_single_model_on_contracts(
    model: str,
    contracts: List[Dict],
    batch_size: int = 10,
    max_concurrency: int = 4,
    max_retries: int = 5,
    batch_retries: int = 2,
    request_timeout: int = 120,
    batch_delay: float = 1.0,
    max_tokens: int = 800,
) -> List[Dict]:
    print(
        f"\nGenerating with: {model} "
        f"({len(contracts)} contracts, batch_size={batch_size}, "
        f"concurrency={max_concurrency})"
    )
    batches = list(_chunks(contracts, batch_size))
    records: List[Dict] = []
    t0 = time.perf_counter()

    for bi, batch in enumerate(batches, start=1):
        responses: List[Any] | None = None
        for attempt in range(1, batch_retries + 1):
            try:
                responses = _process_batch(
                    model, batch, max_concurrency, max_retries, request_timeout, max_tokens
                )
                break
            except Exception as exc:  # whole-batch failure (e.g. sustained 429)
                wait = min(2.0 * attempt, 30.0)
                print(
                    f"  [{model}] batch {bi} failed "
                    f"(attempt {attempt}/{batch_retries}): {type(exc).__name__}: "
                    f"{str(exc)[:100]} - retrying in {wait:.0f}s"
                )
                if attempt == batch_retries:
                    responses = [exc] * len(batch)
                else:
                    time.sleep(wait)

        for contract, resp in zip(batch, responses or []):
            records.append(_record_from_response(model, contract, resp))

        print(f"  [{model}] batch {bi}/{len(batches)} done ({len(records)}/{len(contracts)})")
        if bi < len(batches) and batch_delay > 0:
            time.sleep(batch_delay)

    elapsed = time.perf_counter() - t0
    ok = sum(1 for r in records if not r["error"])
    print(f"  {model}: {ok}/{len(records)} generations in {elapsed:.1f}s")
    return records


def run_abstractive_benchmark(
    sample_size: int = 50,
    output_dir: str = "benchmark/results",
    models: List[str] | None = None,
    batch_size: int = 10,
    max_concurrency: int = 4,
    max_retries: int = 5,
    batch_retries: int = 2,
    request_timeout: int = 120,
    batch_delay: float = 1.0,
    max_tokens: int = 800,
) -> List[Dict[str, Any]]:
    os.makedirs(output_dir, exist_ok=True)
    models = models or MODELS

    data_path = os.path.join(output_dir, "cuad_sample.json")
    if os.path.exists(data_path):
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
        data = data[:sample_size]
        print(f"Loaded cached sample: {len(data)} contracts")
    else:
        data = download_cuad(sample_size=sample_size)
        save_local(data, data_path)

    # Resumable: load any existing results so a partial/failed run can be
    # continued without re-paying for contracts that already succeeded.
    out_path = os.path.join(output_dir, "abstractive_results.json")
    existing: List[Dict[str, Any]] = []
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            existing = json.load(f)
        print(f"Resume mode: {len(existing)} existing records loaded")

    # Preserve records for models that are NOT part of this run, then replace
    # (or add) the records for the models being run.
    all_records: List[Dict[str, Any]] = [r for r in existing if r["model"] not in models]
    for model in models:
        old_recs = [r for r in existing if r["model"] == model]
        done_ids = {r["contract_id"] for r in old_recs if not r["error"]}
        todo = [c for c in data if c["contract_id"] not in done_ids]
        if not todo:
            print(f"  {model}: all contracts already complete - skipping")
            merged = old_recs
        else:
            print(f"  {model}: {len(todo)} contracts to (re)run ({len(done_ids)} already done)")
            new_recs = run_single_model_on_contracts(
                model,
                todo,
                batch_size=batch_size,
                max_concurrency=max_concurrency,
                max_retries=max_retries,
                batch_retries=batch_retries,
                request_timeout=request_timeout,
                batch_delay=batch_delay,
                max_tokens=max_tokens,
            )
            merged = [r for r in old_recs if not r["error"]] + new_recs
        all_records.extend(merged)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2)
    print(f"\nSaved {len(all_records)} records to {out_path}")

    print("\n" + "=" * 60)
    print("COST SUMMARY")
    print("=" * 60)
    for model in models:
        m = [r for r in all_records if r["model"] == model and not r["error"]]
        errors = sum(1 for r in all_records if r["model"] == model and r["error"])
        if not m:
            print(f"{model:24s} | 0 summaries | {errors} errors")
            continue
        total = sum(r["cost_usd"] for r in m)
        print(
            f"{model:24s} | {len(m):3d} summaries | avg ${total / len(m):.5f} | "
            f"total ${total:.3f} | "
            f"{sum(r['input_tokens'] for r in m):,} in / "
            f"{sum(r['output_tokens'] for r in m):,} out"
            + (f" | {errors} errors" if errors else "")
        )

    return all_records


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Abstractive multi-model CUAD benchmark")
    p.add_argument("--sample-size", type=int, default=50)
    p.add_argument("--output-dir", type=str, default="benchmark/results")
    p.add_argument("--models", nargs="+", default=MODELS)
    p.add_argument("--batch-size", type=int, default=10, help="Contracts per batch")
    p.add_argument("--max-concurrency", type=int, default=4, help="Max in-flight requests per batch")
    p.add_argument("--max-retries", type=int, default=5, help="LiteLLM per-request retries")
    p.add_argument("--batch-retries", type=int, default=2, help="Whole-batch retries")
    p.add_argument("--request-timeout", type=int, default=120, help="Seconds per request")
    p.add_argument("--batch-delay", type=float, default=1.0, help="Seconds between batches")
    p.add_argument("--max-tokens", type=int, default=800)
    args = p.parse_args()
    run_abstractive_benchmark(
        sample_size=args.sample_size,
        output_dir=args.output_dir,
        models=args.models,
        batch_size=args.batch_size,
        max_concurrency=args.max_concurrency,
        max_retries=args.max_retries,
        batch_retries=args.batch_retries,
        request_timeout=args.request_timeout,
        batch_delay=args.batch_delay,
        max_tokens=args.max_tokens,
    )