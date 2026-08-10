from pydantic import BaseModel
from typing import Optional

class IngestResponse(BaseModel):
    ingested: str

class ChatRequest(BaseModel):
    session_id: Optional[str]
    message: str

class ChatResponse(BaseModel):
    response: str
    sources: list
