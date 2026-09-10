"""
GCP Document AI adapter for OCR/PDF text extraction.

This is an optional integration. The heavy Google Cloud SDK is imported
lazily so that users who only need the local pipeline are not forced to
install cloud dependencies.
"""

from __future__ import annotations

from typing import Optional


class GCPDocumentAI:
    """Extract text from PDFs using Google Cloud Document AI."""

    def __init__(
        self,
        project_id: str,
        processor_id: str,
        location: str = "us",
        credentials_path: Optional[str] = None,
    ) -> None:
        self.project_id = project_id
        self.processor_id = processor_id
        self.location = location
        self.credentials_path = credentials_path

    def extract_text(self, pdf_bytes: bytes) -> str:
        """
        Send raw PDF bytes to Document AI and return extracted text.

        Requires the `google-cloud-documentai` and `google-auth` packages.
        """
        try:
            from google.api_core.client_options import ClientOptions
            from google.cloud import documentai_v1 as documentai
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "GCP Document AI support requires 'google-cloud-documentai'. "
                "Install it to use GCP ingestion."
            ) from exc

        client = documentai.DocumentProcessorServiceClient(
            client_options=ClientOptions(api_endpoint=f"{self.location}-documentai.googleapis.com"),
            credentials=self._credentials(),
        )
        name = client.processor_path(self.project_id, self.location, self.processor_id)

        request = documentai.ProcessRequest(
            name=name,
            raw_document=documentai.RawDocument(content=pdf_bytes, mime_type="application/pdf"),
        )
        result = client.process_document(request=request)
        return result.document.text

    def _credentials(self):
        if self.credentials_path:
            from google.oauth2 import service_account

            return service_account.Credentials.from_service_account_file(self.credentials_path)
        return None