"""
LexiSum CLI - batch process contracts from a directory.

Usage examples:
    python main.py --input-dir ./contracts --output-dir ./summaries
    python main.py --input-dir ./contracts --output-dir ./summaries --concurrency 5
    python main.py --single path/to/contract.pdf --output-dir ./out
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict

from src.batch_processor import BatchProcessor
from src.export.document_generator import DocumentExportEngine
from src.ingestion.local_files import load_document
from src.pipeline import LegalSummarizationPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("lexisum")


def collect_texts(input_dir: Path) -> Dict[str, str]:
    """Load all supported documents in a directory into {name: text}."""
    texts: Dict[str, str] = {}
    supported = {".pdf", ".txt", ".md", ".text", ".docx"}
    for path in sorted(input_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in supported:
            try:
                texts[path.name] = load_document(path)
                logger.info("Loaded %s (%d chars)", path.name, len(texts[path.name]))
            except Exception as e:
                logger.error("Failed to load %s: %s", path.name, e)
    return texts


def save_result(output_dir: Path, doc_id: str, result: dict, doc_title: str) -> None:
    """Persist a result as JSON + DOCX + PDF."""
    stem = Path(doc_id).stem
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"{stem}.json"
    json_path.write_text(json.dumps(result["result"], indent=2), encoding="utf-8")

    docx = DocumentExportEngine.create_docx(result["result"], doc_title=doc_title)
    (output_dir / f"{stem}_{doc_title}.docx").write_bytes(docx)

    pdf = DocumentExportEngine.create_pdf(result["result"], doc_title=doc_title)
    (output_dir / f"{stem}_{doc_title}.pdf").write_bytes(pdf)

    logger.info("Saved %s results", stem)


def main() -> int:
    parser = argparse.ArgumentParser(description="LexiSum batch contract summarizer")
    parser.add_argument("--input-dir", type=Path, help="Directory of contracts to process")
    parser.add_argument("--single", type=Path, help="Process a single document")
    parser.add_argument("--output-dir", type=Path, default=Path("./summaries"))
    parser.add_argument("--concurrency", type=int, default=5, help="Max concurrent documents")
    parser.add_argument("--doc-title", type=str, default="Contract_Executive_Briefing")
    args = parser.parse_args()

    if args.single:
        if not args.single.exists():
            logger.error("File not found: %s", args.single)
            return 1
        texts = {args.single.name: load_document(args.single)}
    elif args.input_dir:
        if not args.input_dir.exists():
            logger.error("Directory not found: %s", args.input_dir)
            return 1
        texts = collect_texts(args.input_dir)
        if not texts:
            logger.error("No supported documents found in %s", args.input_dir)
            return 1
    else:
        parser.error("Provide --input-dir or --single")

    logger.info("Processing %d document(s) with concurrency %d", len(texts), args.concurrency)
    pipeline = LegalSummarizationPipeline()
    processor = BatchProcessor(max_concurrent=args.concurrency)

    def on_progress(done: int, total: int) -> None:
        logger.info("Progress: %d/%d", done, total)

    results = processor.run(texts, pipeline=pipeline, on_progress=on_progress)

    for doc_id, result in zip(texts.keys(), results):
        save_result(args.output_dir, doc_id, result, args.doc_title)

    logger.info("All done. Results written to %s", args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())