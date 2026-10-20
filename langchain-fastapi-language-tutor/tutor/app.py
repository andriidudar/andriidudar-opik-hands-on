"""FastAPI backend for the Spanish-tutor chat widget."""
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from tutor.chain import build_chain, remember

STATIC = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="Luz, the Spanish tutor")


@lru_cache
def get_chain():
    return build_chain()  # built on first request so imports need no API key


class ChatIn(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = Field(min_length=1)


class ChatOut(BaseModel):
    reply: str
    session_id: str


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    reply = get_chain().invoke(body.message, config={"configurable": {"session_id": body.session_id}})
    remember(body.session_id, body.message, reply)
    return ChatOut(reply=reply, session_id=body.session_id)
