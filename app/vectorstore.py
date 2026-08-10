from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import os

class ChromaStore:
    def __init__(self, persist_dir: Optional[str]=None, embedding_model: str="all-MiniLM-L6-v2"):
        self.persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR","./chroma_db")
        self.client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=self.persist_dir))
        self.collection = None
        self.model = SentenceTransformer(embedding_model)
        self._get_collection()

    def _get_collection(self):
        try:
            self.collection = self.client.get_collection(name="claude_lite")
        except Exception:
            self.collection = self.client.create_collection(name="claude_lite")

    def add_document(self, doc_id: str, text: str):
        # naive chunking
        chunks = [text[i:i+1000] for i in range(0, len(text), 1000) if text[i:i+1000].strip()]
        embeddings = [e.tolist() for e in self.model.encode(chunks)]
        ids = [f"{doc_id}-{i}" for i in range(len(chunks))]
        metadatas = [{"doc_id": doc_id} for _ in chunks]
        self.collection.add(ids=ids, documents=chunks, metadatas=metadatas, embeddings=embeddings)
        self.client.persist()

    def retrieve(self, query: str, k: int = 3) -> List[Dict]:
        emb = self.model.encode([query])[0].tolist()
        res = self.collection.query(query_embeddings=[emb], n_results=k)
        results = []
        for ids, docs, metas in zip(res["ids"], res["documents"], res["metadatas"]):
            for i in range(len(ids)):
                results.append({"id": ids[i], "text": docs[i], "meta": metas[i]})
        return results
