"""
Minimal Gradio UI that calls local pipeline functions. This file runs a Gradio interface that imports the same LLM and vectorstore used by the API for convenience during development.
Run: python web/gradio_app.py
"""
import gradio as gr
import os
import sys

# ensure app package is importable
sys.path.append(os.path.abspath(os.path.join(__file__, "..", "..")))
from app.llm_client import LLMClient
from app.vectorstore import ChromaStore

llm = LLMClient()
store = ChromaStore()

state = []

def chat_fn(message, history):
    # naive history handling
    docs = store.retrieve(message, k=3)
    context = "\n\n".join([f"[DOC {d['id']}]: {d['text'][:500]}" for d in docs])
    prompt = f"You are a helpful assistant. Use the following documents to answer the user.\n\n{context}\n\nUser: {message}\n\nAnswer concisely and include a SOURCES section." 
    resp = llm.generate(prompt)
    history = history or []
    history.append((message, resp))
    return history, history

with gr.Blocks() as demo:
    gr.Markdown("# Claude‑Lite (local dev) — Gradio UI")
    chat = gr.Chatbot()
    txt = gr.Textbox(placeholder="Type your message and press Enter")
    txt.submit(chat_fn, [txt, chat], [chat, chat])

if __name__ == '__main__':
    demo.launch(server_name='0.0.0.0', server_port=7861)
