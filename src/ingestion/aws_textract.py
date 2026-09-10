"""
AWS Textract adapter for OCR/PDF text extraction.

This is an optional integration. The `boto3` SDK is imported lazily.
"""

from __future__ import annotations

from typing import Optional


class AWSTextract:
    """Extract text from PDFs using Amazon Textract."""

    def __init__(self, region: str = "us-east-1", **boto_kwargs) -> None:
        self.region = region
        self.boto_kwargs = boto_kwargs

    def _client(self):
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "AWS Textract support requires 'boto3'. Install it to use AWS ingestion."
            ) from exc
        return boto3.client("textract", region_name=self.region, **self.boto_kwargs)

    def extract_text(self, pdf_bytes: bytes) -> str:
        """
        Send raw PDF bytes to Textract and return extracted text.
        Falls back to `detect_document_text` if `analyze_document` is unavailable.
        """
        client = self._client()
        blocks = client.detect_document_text(Document={"Bytes": pdf_bytes})["Blocks"]
        # Order blocks by Y then X for rough reading order.
        blocks = sorted(
            (b for b in blocks if b["BlockType"] == "LINE"),
            key=lambda b: (b["Geometry"]["BoundingBox"]["Top"], b["Geometry"]["BoundingBox"]["Left"]),
        )
        return "\n".join(b["Text"] for b in blocks)