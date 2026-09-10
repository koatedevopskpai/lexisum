"""
LLM-as-judge rubric for evaluating abstractive legal summaries.

Human evaluation is the gold standard for abstractive summarisation but is
expensive. We approximate it with a structured rubric scored by a strong
judge model at temperature 0. Each dimension is scored 1-5.
"""

from __future__ import annotations

RUBRIC_DIMENSIONS = [
    "obligation_coverage",
    "risk_liability",
    "termination_clarity",
    "plain_language",
    "faithfulness",
]

RUBRIC_SYSTEM = """You are an impartial legal-evaluation judge.
You will score an AI-generated contract summary on five dimensions.
Return ONLY a valid JSON object. No prose, no markdown fences.

Scoring scale (1-5):
  1 = Completely missing / inaccurate
  2 = Major omissions or errors
  3 = Adequate but incomplete
  4 = Strong, minor gaps
  5 = Excellent, comprehensive

Dimensions:
  1. obligation_coverage
  2. risk_liability
  3. termination_clarity
  4. plain_language
  5. faithfulness
"""

RUBRIC_USER_TEMPLATE = """Score the following summary against the source contract.

<source_contract>
{source}
</source_contract>

<summary_to_evaluate>
{summary}
</summary_to_evaluate>

Return JSON with exactly these keys:
{{
  "obligation_coverage": <int 1-5>,
  "risk_liability": <int 1-5>,
  "termination_clarity": <int 1-5>,
  "plain_language": <int 1-5>,
  "faithfulness": <int 1-5>,
  "rationale": "<one sentence explaining the scores>"
}}
"""