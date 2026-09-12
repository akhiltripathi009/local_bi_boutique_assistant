"""
src/ai/__init__.py
==================
Unified AI Copilot Studio provider bridge supporting both:
1. Google AI Studio (Gemini 1.5 Flash, Gemini 1.5 Pro, Gemini 2.0 Flash)
2. Local Ollama (Llama 3.2 3B, Mistral)
"""

import os
from typing import Optional, Union

from src.ai.ollama_client import (
    LocalOllamaBoutiqueAnalyst,
    COPILOT_FAQS,
    PERSONAS,
    PRESET_PROMPT_CHIPS,
)
from src.ai.gemini_client import (
    GoogleGeminiBoutiqueAnalyst,
    GEMINI_MODELS,
    DEFAULT_GEMINI_MODEL,
)


def get_boutique_analyst(model_or_provider: Optional[str] = None) -> Union[GoogleGeminiBoutiqueAnalyst, LocalOllamaBoutiqueAnalyst]:
    """
    Unified factory for resolving the active Boutique Intelligence AI analyst.

    Working:
    - If `model_or_provider` specifies a Gemini model (e.g. 'gemini-1.5-flash'), routes to GoogleGeminiBoutiqueAnalyst.
    - If environment `AI_PROVIDER` is set to 'gemini', routes to GoogleGeminiBoutiqueAnalyst.
    - If `GEMINI_API_KEY` is present in environment/config and no model specified, defaults to GoogleGeminiBoutiqueAnalyst.
    - Otherwise defaults to LocalOllamaBoutiqueAnalyst.
    """
    target = (model_or_provider or "").lower().strip()

    if target.startswith("gemini") or "google" in target:
        clean_model = model_or_provider.split(" ")[0].strip() if model_or_provider else DEFAULT_GEMINI_MODEL
        return GoogleGeminiBoutiqueAnalyst(model_name=clean_model)

    provider_env = os.getenv("AI_PROVIDER", "auto").lower()
    has_gemini_key = bool(GoogleGeminiBoutiqueAnalyst._resolve_api_key())

    if provider_env == "gemini" or (provider_env == "auto" and has_gemini_key and not target.startswith("llama")):
        return GoogleGeminiBoutiqueAnalyst(model_name=model_or_provider or DEFAULT_GEMINI_MODEL)

    return LocalOllamaBoutiqueAnalyst(model_name=model_or_provider or "llama3.2:3b")


def generate_executive_audit_commentary(report_data, timeframe_label: str = "Weekly", model: Optional[str] = None) -> str:
    """Convenience functional wrapper delegating to the active analyst."""
    analyst = get_boutique_analyst(model)
    return analyst.generate_executive_audit_commentary(report_data, timeframe_label, model=model)


__all__ = [
    "GoogleGeminiBoutiqueAnalyst",
    "LocalOllamaBoutiqueAnalyst",
    "get_boutique_analyst",
    "generate_executive_audit_commentary",
    "GEMINI_MODELS",
    "DEFAULT_GEMINI_MODEL",
    "COPILOT_FAQS",
    "PERSONAS",
    "PRESET_PROMPT_CHIPS",
]
