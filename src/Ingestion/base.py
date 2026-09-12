from abc import ABC, abstractmethod
from Ingestion.models import SourceFile, IngestedDocument


class DocumentSource(ABC):

    @abstractmethod
    def confirmFileExistance(self) -> SourceFile:
        pass


class DocumentLoader(ABC):

    @abstractmethod
    def load(self, source: SourceFile) -> IngestedDocument:
        pass