"""
AI Copilot: Local Ollama RAG Assistant, Executive Audits, and FAQ Knowledge Bases.
"""
from src.ai.ollama_client import (
    LocalOllamaBoutiqueAnalyst,
    generate_executive_audit_commentary,
    COPILOT_FAQS,
    PERSONAS,
    PRESET_PROMPT_CHIPS
)

__all__ = [
    "LocalOllamaBoutiqueAnalyst",
    "generate_executive_audit_commentary",
    "COPILOT_FAQS",
    "PERSONAS",
    "PRESET_PROMPT_CHIPS"
]
