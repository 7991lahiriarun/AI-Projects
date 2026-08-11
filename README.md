# Claude-Lite: Retrieval-augmented, tool-enabled conversational assistant

This repository is a starter implementation of "Claude‑Lite": a Claude‑style assistant with retrieval-augmented generation (RAG), multi-turn memory, safety filtering, and an easy local-first deployment.

What you'll find here
- FastAPI backend with endpoints:
  - POST /ingest — upload documents to the vector store
  - POST /chat — multi-turn chat (RAG + LLM call)
- Simple Gradio web UI to talk to the assistant (web/gradio_app.py)
- Vector store using Chroma and embeddings from sentence-transformers
- LLM client abstraction: supports Anthropic (if ANTHROPIC_API_KEY set) or a local HF text-generation fallback

Quickstart (local)
1. Clone and enter the repo
   git clone https://github.com/7991lahiriarun/AI-Projects
   cd AI-Projects

2. Create a virtual environment and install deps
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

3. Copy .env.example -> .env and set keys as needed
   cp .env.example .env
   # optionally set ANTHROPIC_API_KEY if you want to use Anthropic's API

4. Start the API (development)
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

5. In another shell, run the Gradio UI
   python web/gradio_app.py



