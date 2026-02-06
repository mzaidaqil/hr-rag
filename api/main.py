from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

from hr_assistant.config import load_settings
from hr_assistant.orchestrator import Orchestrator
from hr_assistant.rag import RagService


app = FastAPI(title="HR RAG Assistant API", version="0.1.0")

load_dotenv()
_settings = load_settings()
_rag = RagService(_settings)
_orch = Orchestrator(_rag)


class ChatRequest(BaseModel):
    user_id: str = Field(..., description="Stable user identifier")
    text: str = Field(..., description="User message")
    region: str | None = Field(None, description="Optional region hint (e.g., US)")


class ChatResponse(BaseModel):
    route: str
    text: str


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    user_context = {}
    if req.region:
        user_context["region"] = req.region
    resp = _orch.handle(user_id=req.user_id, text=req.text, user_context=user_context)
    return ChatResponse(route=resp.route, text=resp.text)

