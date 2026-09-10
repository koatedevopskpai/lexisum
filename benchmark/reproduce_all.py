"""
Reproduce the full LexiSum benchmark suite:
  1. Extractive: TF-IDF vs Sentence-BERT
  2. Abstractive: GPT-4o-mini vs Claude Haiku vs Gemini Flash
  3. Evaluation: BERTScore + LLM-as-judge rubric

Usage:
    python -m benchmark.reproduce_all
"""

from benchmark.evaluate_abstractive import evaluate
from benchmark.run_abstractive_benchmark import run_abstractive_benchmark
from benchmark.run_benchmark import run_benchmark

if __name__ == "__main__":
    print("=" * 70)
    print("STEP 1/3 - Extractive benchmark")
    print("=" * 70)
    run_benchmark(sample_size=100, top_n=3)

    print("\n" + "=" * 70)
    print("STEP 2/3 - Abstractive generation (3 models x 50 contracts)")
    print("=" * 70)
    run_abstractive_benchmark(sample_size=50)

    print("\n" + "=" * 70)
    print("STEP 3/3 - Abstractive evaluation (BERTScore + rubric)")
    print("=" * 70)
    evaluate(judge_sample_size=15)