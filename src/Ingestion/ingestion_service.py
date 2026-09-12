from Ingestion.sources.local_source import LocalFileSource
from Ingestion.loaders.pdf_loader import PDFLoader
from Ingestion.models import IngestedDocument

class IngestionService:
    def ingest_local_pdf(self, file_path: str) -> IngestedDocument:
        source = LocalFileSource(file_path)
        source_file = source.confirmFileExistance()
        if source_file.filename.lower().endswith(".pdf"):
            loader = PDFLoader()
        else:
            raise ValueError(
                f"Unsupported file type: {source_file.filename}"
            )

        document = loader.load(source_file)

        return document