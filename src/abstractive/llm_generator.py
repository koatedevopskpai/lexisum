"""
LLM-based abstractive summariser with dynamic context management.

This is the core of the "bulletproof" requirement: it never crashes on
long documents. It uses a context strategy (`auto` | `single_shot` |
`chunked_recursive`) that adapts to the selected model's context window:

  - `single_shot`  : one API call with the full document (best coherence).
  - `chunked_recursive`: sentence-aware overlapping chunks are summarised
    in parallel, then merged into a final summary (handles any length).
  - `auto`         : picks single-shot when the doc fits, else chunks.

It also tracks aggregate token usage across every call (needed for FinOps
cost reconciliation) and supports streaming the final summary.

Provider-agnostic via LiteLLM: the same code talks to OpenAI, Azure OpenAI,
GCP Vertex, AWS Bedrock, or any of ~100 other providers by swapping the
model id and credentials.
"""

from __future__ import annotations

import asyncio
from typing import Dict, Generator, List, Optional

import tiktoken
from litellm import completion

from src.config import get_model_context_limit, settings

DEFAULT_PRICE_PER_MILLION = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "o3-mini": {"input": 1.10, "output": 4.40},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "gemini/gemini-3.6-flash": {"input": 0.75, "output": 3.75},
}

# A leaner default for models without a known mapping (USD per 1M tokens).
_FALLBACK_PRICE = {"input": 0.15, "output": 0.60}


class AbstractiveGenerator:
    """Generate plain-language two-paragraph summaries from contract text."""

    def __init__(
        self,
        model_name: str,
        strategy: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: int = 800,
    ) -> None:
        self.model_name = model_name
        self.strategy = strategy or settings.context_strategy
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.limit = get_model_context_limit(model_name)

        try:
            self.encoder = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoder = tiktoken.get_encoding("cl100k_base")

        # Aggregate usage across all calls within one generation.
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0
        self.strategy_used = "single_shot"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_plain_language_summary(self, document_text: str) -> str:
        """Non-streaming entry point (used by CLI, batch, and tests)."""
        return "".join(self.generate_plain_language_summary_stream(document_text))

    def generate_plain_language_summary_stream(
        self, document_text: str
    ) -> Generator[str, None, None]:
        """
        Streaming entry point. Yields text deltas as they arrive.
        For chunked_recursive, intermediate chunks are summarised in
        parallel (non-streamed), then the final merge is streamed.
        """
        token_count = self._count_tokens(document_text)
        use_single_shot = (
            self.strategy == "single_shot"
            or (self.strategy == "auto" and token_count <= int(0.7 * self.limit))
        )

        if use_single_shot:
            self.strategy_used = "single_shot"
            yield from self._stream_final(document_text)
            return

        self.strategy_used = "chunked_recursive"
        chunks = self._chunk_document(document_text)
        if len(chunks) == 1:
            self.strategy_used = "single_shot"
            yield from self._stream_final(chunks[0])
            return

        chunk_summaries = self._summarise_chunks_parallel(chunks)
        combined = "\n\n".join(chunk_summaries)
        yield from self._stream_raw(self._build_merge_prompt(combined))

    def get_usage(self) -> Dict[str, object]:
        """Return aggregate token usage + strategy metadata for FinOps."""
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "calls": self.call_count,
            "strategy": self.strategy_used,
        }

    def estimate_cost(self, document_text: str, output_estimate_tokens: int = 500) -> Dict[str, float]:
        """Return a pre-flight cost estimate for a document + this model."""
        price = DEFAULT_PRICE_PER_MILLION.get(self.model_name, _FALLBACK_PRICE)
        input_tokens = self._count_tokens(document_text)
        input_cost = (input_tokens / 1_000_000) * price["input"]
        output_cost = (output_estimate_tokens / 1_000_000) * price["output"]
        return {
            "input_tokens": input_tokens,
            "estimated_output_tokens": output_estimate_tokens,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_estimate_usd": round(input_cost + output_cost, 6),
        }

    # ------------------------------------------------------------------
    # Streaming internals
    # ------------------------------------------------------------------
    def _stream_final(self, text: str) -> Generator[str, None, None]:
        yield from self._stream_raw(self._build_final_prompt(text))

    def _stream_raw(self, prompt: str) -> Generator[str, None, None]:
        """Low-level streaming call with token accounting."""
        try:
            response = completion(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
                stream=True,
                stream_options={"include_usage": True},
            )
        except Exception as exc:  # pragma: no cover - network/provider errors
            raise RuntimeError(f"LLM call failed for {self.model_name}: {exc}") from exc

        full_output: List[str] = []
        for chunk in response:
            usage = getattr(chunk, "usage", None)
            if usage:
                self.total_input_tokens += int(getattr(usage, "prompt_tokens", 0) or 0)
                self.total_output_tokens += int(getattr(usage, "completion_tokens", 0) or 0)
                continue
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                full_output.append(content)
                yield content

        self.call_count += 1

        # Fallback accounting if the provider didn't return usage chunks.
        if self.total_input_tokens == 0 and self.total_output_tokens == 0:
            self.total_input_tokens += self._count_tokens(prompt)
            self.total_output_tokens += self._count_tokens("".join(full_output))

    # ------------------------------------------------------------------
    # Chunking internals
    # ------------------------------------------------------------------
    def _summarise_chunks_parallel(self, chunks: List[str]) -> List[str]:
        """Summarise chunks concurrently using asyncio.to_thread."""

        async def run():
            tasks = [
                asyncio.to_thread(self._call_llm_sync, self._build_chunk_prompt(c))
                for c in chunks
            ]
            return await asyncio.gather(*tasks)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(run())
        else:
            return loop.run_until_complete(run())

    def _call_llm_sync(self, prompt: str) -> str:
        """Synchronous LLM call with token accounting."""
        try:
            response = completion(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_output_tokens,
            )
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"LLM call failed for {self.model_name}: {exc}") from exc

        usage = getattr(response, "usage", None)
        content = response.choices[0].message.content.strip()
        if usage:
            self.total_input_tokens += int(getattr(usage, "prompt_tokens", 0) or 0)
            self.total_output_tokens += int(getattr(usage, "completion_tokens", 0) or 0)
        else:
            self.total_input_tokens += self._count_tokens(prompt)
            self.total_output_tokens += self._count_tokens(content)
        self.call_count += 1
        return content

    # ------------------------------------------------------------------
    # Chunking helpers
    # ------------------------------------------------------------------
    def _count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))

    def _chunk_document(self, text: str) -> List[str]:
        """
        Sentence-aware, overlapping chunking.
        Falls back to token-window chunking if sentence parsing fails.
        """
        try:
            from src.ingestion.document_parser import DocumentParser

            parser = DocumentParser()
            sentences = parser.parse_document(text)["sentences"]
        except Exception:
            return self._token_window_chunks(text)

        if not sentences:
            return [text]

        chunk_size = min(settings.max_chunk_tokens, int(self.limit * 0.4))
        overlap_budget = int(chunk_size * settings.chunk_overlap_ratio)

        chunks: List[str] = []
        current: List[str] = []
        current_tokens = 0

        for sent in sentences:
            sent_tokens = self._count_tokens(sent)
            if current and current_tokens + sent_tokens > chunk_size:
                chunks.append(" ".join(current))
                overlap: List[str] = []
                overlap_tokens = 0
                for s in reversed(current):
                    st = self._count_tokens(s)
                    if overlap_tokens + st > overlap_budget:
                        break
                    overlap.insert(0, s)
                    overlap_tokens += st
                current = overlap
                current_tokens = overlap_tokens
            current.append(sent)
            current_tokens += sent_tokens

        if current:
            chunks.append(" ".join(current))

        return chunks or [text]

    def _token_window_chunks(self, text: str) -> List[str]:
        tokens = self.encoder.encode(text)
        chunk_size = min(settings.max_chunk_tokens, int(self.limit * 0.4))
        overlap = int(chunk_size * settings.chunk_overlap_ratio)
        step = chunk_size - overlap
        chunks = []
        for i in range(0, len(tokens), step):
            chunk_tokens = tokens[i : i + chunk_size]
            chunks.append(self.encoder.decode(chunk_tokens))
            if i + chunk_size >= len(tokens):
                break
        return chunks or [text]

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------
    def _build_final_prompt(self, text: str) -> str:
        return f"""You are an expert legal counsel assisting non-legal stakeholders.
Read the following legal contract and produce a clear, plain-language business summary.

CONSTRAINTS:
1. Output EXACTLY TWO PARAGRAPHS, separated by a blank line.
2. Paragraph 1: Key commercial obligations, operational duties, and service commitments.
3. Paragraph 2: Core liabilities, indemnification risks, and termination conditions.
4. Tone: Professional, direct, plain English. No dense legalese or Latin phrases.

CONTRACT TEXT:
{text}
"""

    def _build_chunk_prompt(self, text: str) -> str:
        return f"""You are a legal summariser. Summarise the following section of a contract.
Focus strictly on: obligations, liabilities, indemnification, and termination conditions.
Be factual, neutral, and concise. Use bullet points.

SECTION TEXT:
{text}
"""

    def _build_merge_prompt(self, combined: str) -> str:
        return f"""You are an expert legal synthesizer. You previously summarised sections of a large contract.
Combine the section summaries below into ONE cohesive, 2-paragraph business summary.

CONSTRAINTS:
1. Output EXACTLY TWO PARAGRAPHS, separated by a blank line.
2. Paragraph 1: Consolidated commercial obligations and service commitments.
3. Paragraph 2: Consolidated liabilities, indemnification risks, and termination conditions.
4. Resolve any contradictions. Do not omit any material obligation or risk.
5. Tone: Professional, direct, plain English.

SECTION SUMMARIES:
{combined}
"""