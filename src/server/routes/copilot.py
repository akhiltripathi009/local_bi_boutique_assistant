"""
src/server/routes/copilot.py
============================
FastAPI route controller for the Local Ollama AI Copilot Studio.

Why Required:
- Provides a conversational AI interface powered by private, locally hosted LLMs (via Ollama).
- Grounds LLM responses in real-time boutique transactional context (live revenue, gross margins,
  inventory runways, and customer dossiers) through zero-latency Server-Sent Events (SSE) token streaming.
"""

from fastapi import APIRouter, HTTPException
from starlette.responses import StreamingResponse
from pydantic import BaseModel, Field
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
    """
    Dependency provider for LocalOllamaBoutiqueAnalyst.
    
    Returns:
        LocalOllamaBoutiqueAnalyst: Configured Ollama bridge instance.
    """
    return LocalOllamaBoutiqueAnalyst()


def get_db() -> DatabaseManager:
    """
    Dependency provider for DatabaseManager.
    
    Returns:
        DatabaseManager: Initialized SQLite database manager.
    """
    return DatabaseManager()


class StreamChatRequest(BaseModel):
    """
    Request model for conversational token streaming with Ollama.
    
    Why Required:
    Validates conversational message history, target Ollama model tag, and executive persona style.
    """
    messages: List[Dict[str, str]] = Field(..., description="Message history: [{'role': 'user', 'content': '...'}]")
    model: Optional[str] = Field("llama3.2:3b", description="Installed Ollama model tag.")
    persona_key: str = Field("👔 Senior Merchandise Director", description="Persona prompt template key.")


@router.get("/models")
def get_available_models() -> Dict[str, Any]:
    """
    Inspects local Ollama server and lists installed neural language models.
    
    Working:
    - Queries the Ollama daemon `/api/tags` endpoint.
    
    Why Required:
    - Allows users to switch between installed models (e.g. llama3.2:3b, mistral, qwen) in the UI.
    
    Returns:
        Dict[str, Any]: List of installed model tags and active default.
    """
    analyst = get_analyst()
    models = analyst.get_available_models()
    return {
        "success": True,
        "models": models,
        "active_default": models[0] if models else "llama3.2:3b"
    }


@router.get("/personas")
def get_personas() -> Dict[str, Any]:
    """
    Returns the specialized luxury boutique executive personas and prompt chips.
    
    Working:
    - Delivers persona descriptors: Senior Merchandise Director, Boutique Financial Controller,
      and Luxury Brand Concierge.
      
    Why Required:
    - Shapes the tone, analytical depth, and domain focus of LLM answers.
    """
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
    """
    Returns tabbed strategic retail FAQs across Financials, Inventory, Pricing, and Sentiment.
    
    Why Required:
    - Provides instant 1-click strategic retail questions for store owners.
    """
    return {
        "success": True,
        "pillars": COPILOT_FAQS
    }


@router.get("/knowledge")
def get_live_knowledge_context() -> Dict[str, Any]:
    """
    Extracts the real-time SQLite data payload that is injected into Ollama LLM prompts.
    
    Working:
    - Compiles current revenue, gross margins, stock levels, and active promotions into text.
    
    Why Required:
    - Provides complete transparency into Retrieval-Augmented Generation (RAG) context.
    """
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
    Streams AI responses token-by-token using Server-Sent Events (SSE).
    
    Working:
    - Retrieves live SQLite context.
    - Yields JSON formatted SSE chunks (`data: {"token": "..."}`) as tokens generate.
    
    Why Required:
    - Eliminates waiting for complete responses on local hardware, creating a responsive chat experience.
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
