from fastapi import APIRouter
from pydantic import BaseModel
from ..llm_client import LLMClient
from ..vectorstore import ChromaStore
from typing import Optional

router = APIRouter()

llm = LLMClient()
store = ChromaStore()

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

@router.post("/")
async def chat(req: ChatRequest):
    # Safety phase (very simple)
    if "ssn" in req.message.lower():
        return {"error":"Refused: contains sensitive token"}

    # Retrieve
    docs = store.retrieve(req.message, k=3)
    context = "\n\n".join([f"[DOC {d['id']}]: {d['text'][:500]}" for d in docs])

    prompt = f"You are a helpful assistant. Use the following documents to answer the user.\n\n{context}\n\nUser: {req.message}\n\nAnswer concisely and include a SOURCES section." 

    resp = llm.generate(prompt)
    # store memory or session if needed (TODO)
    return {"response": resp, "sources": [d['id'] for d in docs]}
