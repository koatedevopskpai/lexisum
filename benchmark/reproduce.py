"""
One-command reproduction of the LexiSum extractive benchmark.

Usage:
    python -m benchmark.reproduce
"""

from benchmark.run_benchmark import run_benchmark

if __name__ == "__main__":
    run_benchmark(sample_size=100, top_n=3)