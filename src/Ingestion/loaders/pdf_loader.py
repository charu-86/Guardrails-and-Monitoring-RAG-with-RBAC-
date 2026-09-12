import os
import uuid

from pypdf import PdfReader

from ingestion.base import DocumentLoader
from ingestion.models import SourceFile, IngestedDocument

class PDFLoader(DocumentLoader):

    def load(self, source: SourceFile) -> IngestedDocument:

        if not os.path.isfile(source.path):
            raise FileNotFoundError(
                f"PDF file not found: {source.path}"
            )

        reader = PdfReader(source.path)

        pages = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text)

        content = "\n\n".join(pages)

        if not content.strip():
            raise ValueError(
                f"No extractable text found in PDF: {source.filename}"
            )

        return IngestedDocument(
            id=str(uuid.uuid4()),
            filename=source.filename,
            file_type="pdf",
            content=content,
            metadata={
                **source.metadata,
                "page_count": len(reader.pages)
            }
        )