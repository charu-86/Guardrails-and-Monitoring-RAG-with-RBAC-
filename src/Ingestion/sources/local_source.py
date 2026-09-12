import os

from ingestion.base import DocumentSource
from ingestion.models import SourceFile


class LocalFileSource(DocumentSource):

    def __init__(self, file_path: str):
        self.file_path = file_path

    def confirmFileExistance(self) -> SourceFile:

        if not os.path.exists(self.file_path):
            raise FileNotFoundError(
                f"File not found: {self.file_path}"
            )

        if not os.path.isfile(self.file_path):
            raise ValueError(
                f"Path is not a file: {self.file_path}"
            )

        return SourceFile(
            filename=os.path.basename(self.file_path),
            path=self.file_path
        )