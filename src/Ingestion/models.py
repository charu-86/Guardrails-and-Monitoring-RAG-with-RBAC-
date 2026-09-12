from dataclasses import dataclass, field
from typing import Any
from pydantic import BaseModel


@dataclass
class SourceFile:
    filename: str
    path: str
    content_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class IngestedDocument:
    id: str
    filename: str
    file_type: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

class LocalPDFRequest(BaseModel):
    file_path: str