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
import time
import logging

from src.data.db_manager import DatabaseManager
from src.server.routes.agent import get_agent
from src.ai import (
    get_boutique_analyst,
    GoogleGeminiBoutiqueAnalyst,
    LocalOllamaBoutiqueAnalyst,
    GEMINI_MODELS,
    PERSONAS,
    COPILOT_FAQS,
    PRESET_PROMPT_CHIPS,
)

logger = logging.getLogger("copilot_routes")

router = APIRouter(prefix="/api/copilot", tags=["AI Copilot Studio"])


def get_analyst(model_or_provider: Optional[str] = None):
    """
    Dependency provider for Boutique BI Analyst (dynamically selects Google Gemini or Local Ollama).
    """
    return get_boutique_analyst(model_or_provider)


def get_db() -> DatabaseManager:
    """
    Dependency provider for DatabaseManager.
    
    Returns:
        DatabaseManager: Initialized SQLite database manager.
    """
    return DatabaseManager()


class StreamChatRequest(BaseModel):
    """
    Request model for conversational token streaming with Ollama or Google AI Studio (Gemini).
    
    Why Required:
    Validates conversational message history, target model tag, and executive persona style.
    """
    messages: List[Dict[str, Any]] = Field(..., description="Message history: [{'role': 'user', 'content': '...'}]")
    model: Optional[str] = Field("gemini-1.5-flash", description="AI Model tag (e.g. gemini-1.5-flash, llama3.2:3b).")
    persona_key: str = Field("👔 Senior Merchandise Director", description="Persona prompt template key.")


class ChatActionRequest(BaseModel):
    """
    Request model for triggering autonomous Shivi Deep Agent actions via natural language.
    """
    query: str = Field(..., description="Natural language operational instruction (e.g. 'Send today's audit report to example@gmail.com').")
    to_email: Optional[str] = Field(None, description="Optional override destination email address.")


@router.get("/models")
def get_available_models() -> Dict[str, Any]:
    """
    Lists available neural models from both Google AI Studio (Gemini) and Local Ollama.
    
    Working:
    - Queries Google AI Studio models (gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash).
    - Queries local Ollama daemon for installed offline models (llama3.2:3b, mistral).
    - Identifies if GEMINI_API_KEY is configured in the environment.
    """
    gemini_analyst = GoogleGeminiBoutiqueAnalyst()
    ollama_analyst = LocalOllamaBoutiqueAnalyst()

    gemini_models = gemini_analyst.get_available_models()
    ollama_models = ollama_analyst.get_available_models()
    is_gemini_active = gemini_analyst.is_configured()

    # Prioritize Gemini models first if configured, else prioritize local Ollama
    if is_gemini_active:
        all_models = gemini_models + [m for m in ollama_models if m not in gemini_models]
        active_default = gemini_models[0] if gemini_models else "gemini-1.5-flash"
    else:
        all_models = gemini_models + [m for m in ollama_models if m not in gemini_models]
        active_default = ollama_models[0] if ollama_models else "gemini-1.5-flash"

    return {
        "success": True,
        "models": all_models,
        "gemini_models": gemini_models,
        "ollama_models": ollama_models,
        "gemini_configured": is_gemini_active,
        "active_default": active_default
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


@router.post("/action")
def execute_copilot_action(req: ChatActionRequest) -> Dict[str, Any]:
    """
    Direct endpoint for evaluating and executing conversational operational actions.
    """
    agent = get_agent()
    intent = agent.detect_chat_action(req.query)
    if not intent:
        return {
            "success": False,
            "is_action": False,
            "message": "No actionable operational command recognized. Process as an advisory conversational query."
        }

    res = agent.execute_chat_action(req.query, to_email=req.to_email)
    if not res:
        return {
            "success": False,
            "is_action": False,
            "message": "Action execution could not be completed."
        }

    return {
        "success": True,
        "is_action": True,
        "result": res.to_dict()
    }


@router.post("/stream")
def stream_copilot_chat(req: StreamChatRequest):
    """
    Streams AI responses token-by-token using Server-Sent Events (SSE).
    Autonomously executes operational actions if detected in the user message.
    """
    db = get_db()
    agent = get_agent()

    # 1. Inspect latest user message for actionable operational intent
    latest_user_query = ""
    for m in reversed(req.messages):
        if m.get("role") == "user":
            latest_user_query = m.get("content", "").strip()
            break

    detected_intent = agent.detect_chat_action(latest_user_query) if latest_user_query else None

    if detected_intent:
        logger.info(f"Chat action detected in query: '{latest_user_query}' -> {detected_intent.get('action')}")

        def action_event_stream():
            try:
                # Immediate acknowledgment token so UI responds instantly while PDF compiles and SMTP connects
                yield f"data: {json.dumps({'token': '⚡ *Engaging Shivi Deep Agent & validating operational parameters...*\n\n'})}\n\n"
                time.sleep(0.05)

                action_res = agent.execute_chat_action(latest_user_query)
                if action_res:
                    # Send structured action card first
                    yield f"data: {json.dumps({'action': action_res.card})}\n\n"

                    # Yield narrative text in readable chunks
                    words = action_res.narrative.split(" ")
                    for i in range(0, len(words), 3):
                        chunk = " ".join(words[i:i+3]) + (" " if i+3 < len(words) else "")
                        yield f"data: {json.dumps({'token': chunk})}\n\n"
                        time.sleep(0.01)

                    yield f"data: {json.dumps({'done': True})}\n\n"
                else:
                    yield f"data: {json.dumps({'token': 'Action recognized, but could not be completed.', 'done': True})}\n\n"
            except Exception as e:
                logger.error(f"Chat action execution error: {e}")
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

        return StreamingResponse(
            action_event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    # 2. Dynamic AI RAG streaming (Google AI Studio Gemini or Local Ollama)
    analyst = get_analyst(req.model)
    live_ctx = analyst.build_live_boutique_context(db)
    # Sanitize message payload to role and string content
    clean_messages = [{"role": str(m.get("role", "user")), "content": str(m.get("content", ""))} for m in req.messages]

    def sse_event_stream():
        try:
            token_generator = analyst.stream_copilot_response(
                messages=clean_messages,
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
