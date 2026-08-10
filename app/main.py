from fastapi import FastAPI
from .routes import ingest, chat
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Claude-Lite")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

@app.get("/status")
async def status():
    return {"status":"ok"}
