from fastapi import APIRouter, HTTPException
from starlette.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json

from src.data.db_manager import DatabaseManager
from src.ai.ollama_client import (
    LocalOllamaBoutiqueAnalyst,
    PERSONAS,
    COPILOT_FAQS,
    PRESET_PROMPT_CHIPS
)

router = APIRouter(prefix="/api/copilot", tags=["AI Copilot Studio"])

def get_analyst() -> LocalOllamaBoutiqueAnalyst:
    return LocalOllamaBoutiqueAnalyst()

def get_db():
    return DatabaseManager()

class StreamChatRequest(BaseModel):
    messages: List[Dict[str, str]] # [{"role": "user", "content": "..."}]
    model: Optional[str] = "llama3.2:3b"
    persona_key: str = "👔 Senior Merchandise Director"

@router.get("/models")
def get_available_models() -> Dict[str, Any]:
    """Inspects local Ollama server and lists installed models."""
    analyst = get_analyst()
    models = analyst.get_available_models()
    return {
        "success": True,
        "models": models,
        "active_default": models[0] if models else "llama3.2:3b"
    }

@router.get("/personas")
def get_personas() -> Dict[str, Any]:
    """Returns the 3 specialized luxury boutique executive personas."""
    return {
        "success": True,
        "personas": [
            {
                "key": k,
                "title": v["title"],
                "badge": v["badge"],
                "description": v["description"]
            }
            for k, v in PERSONAS.items()
        ],
        "prompt_chips": PRESET_PROMPT_CHIPS
    }

@router.get("/faqs")
def get_strategic_faqs() -> Dict[str, Any]:
    """Returns tabbed strategic retail FAQs across Financials, Inventory, Pricing, and Sentiment."""
    return {
        "success": True,
        "pillars": COPILOT_FAQS
    }

@router.get("/knowledge")
def get_live_knowledge_context() -> Dict[str, Any]:
    """Returns the real-time SQLite data payload that is injected into Ollama LLM prompts."""
    db = get_db()
    analyst = get_analyst()
    context = analyst.build_live_boutique_context(db)
    return {
        "success": True,
        "context": context
    }

@router.post("/stream")
def stream_copilot_chat(req: StreamChatRequest):
    """
    Streams AI response token-by-token using Server-Sent Events (SSE).
    Directly connected to local Ollama (llama3.2:3b).
    """
    db = get_db()
    analyst = get_analyst()
    live_ctx = analyst.build_live_boutique_context(db)

    def sse_event_stream():
        try:
            token_generator = analyst.stream_copilot_response(
                messages=req.messages,
                model=req.model,
                persona_key=req.persona_key,
                live_context=live_ctx
            )
            for token in token_generator:
                payload = json.dumps({"token": token})
                yield f"data: {payload}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            err_payload = json.dumps({"error": str(e), "done": True})
            yield f"data: {err_payload}\n\n"

    return StreamingResponse(
        sse_event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
