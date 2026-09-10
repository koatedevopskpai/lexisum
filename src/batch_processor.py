"""
Async batch processor for high-throughput contract processing.

The problem statement requires ~200 contracts/day. Synchronous, one-at-a-time
processing is impractical, so this module provides:

  - a concurrency-bounded async runner (`Semaphore`)
  - progress callbacks for the UI / CLI
  - structured per-document results

Each document still flows through the full dual-engine pipeline; only the
orchestration is parallelised.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, Iterable, List

from src.pipeline import LegalSummarizationPipeline

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int], None]


class BatchProcessor:
    """Process many documents concurrently with a bounded worker pool."""

    def __init__(self, max_concurrent: int = 5) -> None:
        self.max_concurrent = max(max_concurrent, 1)
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

    async def _process_one(
        self,
        pipeline: LegalSummarizationPipeline,
        doc_id: str,
        text: str,
    ) -> Dict[str, Any]:
        async with self.semaphore:
            return await asyncio.to_thread(pipeline.process_contract, text, doc_id)

    async def process_batch(
        self,
        texts: Dict[str, str],
        pipeline: Optional[LegalSummarizationPipeline] = None,
        on_progress: Optional[ProgressCallback] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process a mapping of {doc_id: text} concurrently.

        Returns a list of results aligned with the input order.
        """
        pipeline = pipeline or LegalSummarizationPipeline()
        items = list(texts.items())
        total = len(items)
        results: List[Any] = [None] * total

        async def worker(index: int, doc_id: str, text: str):
            results[index] = await self._process_one(pipeline, doc_id, text)
            if on_progress:
                done = sum(1 for r in results if r is not None)
                on_progress(done, total)

        await asyncio.gather(*(worker(i, d, t) for i, (d, t) in enumerate(items)))
        return results

    def run(
        self,
        texts: Dict[str, str],
        pipeline: Optional[LegalSummarizationPipeline] = None,
        on_progress: Optional[ProgressCallback] = None,
    ) -> List[Dict[str, Any]]:
        """Synchronous wrapper around :meth:`process_batch`."""
        return asyncio.run(self.process_batch(texts, pipeline, on_progress))