from fastapi import APIRouter, UploadFile, File, Form
from ..vectorstore import ChromaStore
from typing import List
import os

router = APIRouter()

store = ChromaStore()

@router.post("/file")
async def ingest_file(file: UploadFile = File(...), doc_id: str = Form(None)):
    # read file bytes and decode minimally
    content = await file.read()
    text = content.decode(errors='ignore')[:500000]
    did = doc_id or file.filename
    store.add_document(did, text)
    return {"ingested": did}

@router.post("/text")
async def ingest_text(text: str = Form(...), doc_id: str = Form(None)):
    did = doc_id or f"doc-{len(text)}"
    store.add_document(did, text)
    return {"ingested": did}
