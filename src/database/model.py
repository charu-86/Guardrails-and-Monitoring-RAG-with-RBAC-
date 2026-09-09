from pydantic import BaseModel, Field
from typing import List, Optional

class User(BaseModel):
    id: int
    name: str
    email: str
    password: str
    # roles: List[str] = Field(default_factory=list)

class Roles(BaseModel):
    id: int
    roles: List[str] = Field(default_factory=list)

class Permisson(BaseModel):
    role: str
    permissions: List[str] = Field(default_factory=list)

class Token(BaseModel):
    access_token: str
    token_type: str

class RagQuery(BaseModel):
    query: str

class RagResponse(BaseModel):
    results: str
    query_time: float

class DocumentItem(BaseModel):
    id: str
    text: str
    category: str


 
