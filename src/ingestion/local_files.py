"""
Local file / stream ingestion helpers.

Supports plain text, PDF (via pypdf), and DOCX (via python-docx).
Each loader accepts either a filesystem path or a binary file-like object
(e.g. a Streamlit UploadedFile), so the same helpers serve the CLI and UI.
Cloud OCR (GCP Document AI / AWS Textract) is available through the
dedicated adapters in this package.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Union

PathLike = Union[str, Path]
Source = Union[PathLike, "io.BytesIO", object]


def load_text_file(source: Source) -> str:
    """Read a UTF-8 (or UTF-16 fallback) text file from a path or stream."""
    if hasattr(source, "read"):
        raw = source.read()
        if isinstance(raw, bytes):
            return _decode(raw)
        return raw
    p = Path(source)
    return _decode(p.read_bytes())


def _decode(raw: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="ignore")


def load_pdf(source: Source) -> str:
    """Extract text from a PDF using pypdf (path or stream)."""
    from pypdf import PdfReader

    reader = PdfReader(source)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def load_docx(source: Source) -> str:
    """Extract text from a .docx using python-docx (path or stream)."""
    from docx import Document

    doc = Document(source)
    return "\n".join(p.text for p in doc.paragraphs)


def load_document(path: PathLike) -> str:
    """Dispatch to the right loader based on file extension (path only)."""
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return load_pdf(path)
    if suffix == ".docx":
        return load_docx(path)
    if suffix in {".txt", ".md", ".text"}:
        return load_text_file(path)
    raise ValueError(f"Unsupported file type: {suffix}")