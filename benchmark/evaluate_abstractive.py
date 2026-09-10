"""
Evaluate abstractive summaries with BERTScore + LLM-as-judge rubric.

Inputs:
  benchmark/results/abstractive_results.json  (generated summaries + usage)
  benchmark/results/cuad_sample.json          (contracts + gold references)

Outputs:
  benchmark/results/abstractive_scores.json
  benchmark/results/ABSTRACTIVE_BENCHMARK.md
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
from typing import Any, Dict, List

import pandas as pd
from tabulate import tabulate

from benchmark.rubric_prompts import RUBRIC_DIMENSIONS, RUBRIC_SYSTEM, RUBRIC_USER_TEMPLATE

JUDGE_MODEL = "gpt-4o"


def compute_bertscore(predictions: List[str], references: List[str]) -> Dict[str, float]:
    """Mean BERTScore P/R/F1 using a lightweight English encoder."""
    from bert_score import score as bert_score

    P, R, F1 = bert_score(
        predictions,
        references,
        lang="en",
        model_type="distilbert-base-uncased",
        verbose=False,
        batch_size=8,
    )
    return {
        "bertscore_precision": round(P.mean().item(), 4),
        "bertscore_recall": round(R.mean().item(), 4),
        "bertscore_f1": round(F1.mean().item(), 4),
    }


def judge_single(summary: str, source: str, model: str = JUDGE_MODEL) -> Dict[str, Any]:
    """Call the judge LLM and return parsed JSON scores."""
    from litellm import completion

    user_prompt = RUBRIC_USER_TEMPLATE.format(source=source[:8000], summary=summary)
    try:
        resp = completion(
            model=model,
            messages=[
                {"role": "system", "content": RUBRIC_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(resp.choices[0].message.content.strip())
        return {k: parsed.get(k, 0) for k in RUBRIC_DIMENSIONS}
    except Exception:
        return {k: 0 for k in RUBRIC_DIMENSIONS}


def run_rubric_evaluation(
    records: List[Dict],
    contracts: List[Dict],
    judge_sample_size: int = 15,
    seed: int = 42,
) -> Dict[str, Dict[str, float]]:
    random.seed(seed)
    contract_map = {c["contract_id"]: c for c in contracts}

    by_model: Dict[str, List[Dict]] = {}
    for r in records:
        if r["error"]:
            continue
        by_model.setdefault(r["model"], []).append(r)

    results: Dict[str, Dict[str, float]] = {}
    for model, recs in by_model.items():
        print(f"\nJudging {model} on {min(judge_sample_size, len(recs))} samples...")
        sample = random.sample(recs, min(judge_sample_size, len(recs)))
        per_dim: Dict[str, List[int]] = {d: [] for d in RUBRIC_DIMENSIONS}
        for r in sample:
            contract = contract_map.get(r["contract_id"])
            if not contract:
                continue
            scores = judge_single(r["summary"], contract["contract_text"])
            for d in RUBRIC_DIMENSIONS:
                per_dim[d].append(scores[d])

        results[model] = {
            d: round(statistics.mean(vals), 2) if vals else 0.0
            for d, vals in per_dim.items()
        }
        all_vals = [v for vals in per_dim.values() for v in vals]
        results[model]["overall"] = round(statistics.mean(all_vals), 2) if all_vals else 0.0

    return results


def evaluate(output_dir: str = "benchmark/results", judge_sample_size: int = 15) -> pd.DataFrame:
    with open(os.path.join(output_dir, "abstractive_results.json"), encoding="utf-8") as f:
        records = json.load(f)
    with open(os.path.join(output_dir, "cuad_sample.json"), encoding="utf-8") as f:
        contracts = json.load(f)
    contract_map = {c["contract_id"]: c for c in contracts}

    valid = [r for r in records if not r["error"] and r["summary"]]

    print("\nComputing BERTScore per model...")
    bert_results: Dict[str, Dict[str, float]] = {}
    for model in sorted({r["model"] for r in valid}):
        m = [r for r in valid if r["model"] == model]
        preds = [r["summary"] for r in m]
        refs = [contract_map[r["contract_id"]]["gold_summary"] for r in m]
        bert_results[model] = compute_bertscore(preds, refs)
        print(f"  {model}: F1 = {bert_results[model]['bertscore_f1']}")

    rubric_results = run_rubric_evaluation(valid, contracts, judge_sample_size=judge_sample_size)

    cost_results = {}
    for model in sorted({r["model"] for r in valid}):
        m = [r for r in valid if r["model"] == model]
        cost_results[model] = {
            "avg_cost_usd": round(statistics.mean(r["cost_usd"] for r in m), 5),
            "avg_input_tokens": round(statistics.mean(r["input_tokens"] for r in m), 0),
            "avg_output_tokens": round(statistics.mean(r["output_tokens"] for r in m), 0),
        }

    rows = []
    for model in sorted(bert_results.keys()):
        rows.append(
            {
                "Model": model,
                "BERTScore F1": bert_results[model]["bertscore_f1"],
                "Rubric Overall": rubric_results.get(model, {}).get("overall", 0),
                "Obligations": rubric_results.get(model, {}).get("obligation_coverage", 0),
                "Risk/Liability": rubric_results.get(model, {}).get("risk_liability", 0),
                "Termination": rubric_results.get(model, {}).get("termination_clarity", 0),
                "Plain Lang.": rubric_results.get(model, {}).get("plain_language", 0),
                "Faithful": rubric_results.get(model, {}).get("faithfulness", 0),
                "Avg Cost ($)": cost_results[model]["avg_cost_usd"],
            }
        )

    df = pd.DataFrame(rows).sort_values("BERTScore F1", ascending=False)

    combined = {"bertscore": bert_results, "rubric": rubric_results, "cost": cost_results}
    with open(os.path.join(output_dir, "abstractive_scores.json"), "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)

    md_lines = [
        "## Abstractive Benchmark: Multi-Model Comparison",
        "",
        f"**Corpus:** CUAD - {len(contracts)} contracts (sampled).  ",
        "**Reference:** Expert-annotated clause text.  ",
        "**Metrics:** BERTScore F1 (semantic), Rubric (1-5 LLM-as-judge), Avg Cost/contract.  ",
        f"**Judge model:** `{JUDGE_MODEL}` on {judge_sample_size} samples per model.",
        "",
        tabulate(df, headers="keys", tablefmt="github", showindex=False),
        "",
        "**Rubric dimensions:** Obligations, Risk/Liability, Termination clarity, "
        "Plain Language, Faithfulness.",
        "",
        "> **Takeaway:** See README for narrative interpretation of these results.",
    ]
    md_path = os.path.join(output_dir, "ABSTRACTIVE_BENCHMARK.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print("\n" + "=" * 90)
    print(tabulate(df, headers="keys", tablefmt="github", showindex=False))
    print("=" * 90)
    print(f"\nMarkdown saved to {md_path}")
    return df


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=str, default="benchmark/results")
    p.add_argument("--judge-sample-size", type=int, default=15)
    args = p.parse_args()
    evaluate(args.output_dir, args.judge_sample_size)