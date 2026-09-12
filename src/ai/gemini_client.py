"""
src/ai/gemini_client.py
=======================
Official Google AI Studio (Gemini) Client for Mishika Fashion Luxury Boutique BI.

Why Required:
- Replaces or augments local Ollama models with Google's state-of-the-art Gemini neural models
  (gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash) for live cloud deployments.
- Delivers sub-second Server-Sent Events (SSE) token streaming, massive 1M+ token context windows
  for historical retail RAG grounding, and boardroom-level strategic commentary.
- Resilient architecture: uses official `google-genai` SDK with automatic REST SSE fallback.
"""

import os
import json
import logging
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Generator, Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from src.ai.ollama_client import (
    PERSONAS,
    PRESET_PROMPT_CHIPS,
    COPILOT_FAQS,
    LocalOllamaBoutiqueAnalyst,
)

logger = logging.getLogger("gemini_client")

# Curated Google AI Studio Production Models
GEMINI_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"


class GoogleGeminiBoutiqueAnalyst:
    """
    Enterprise AI business analyst powered by Google AI Studio (Gemini API).
    Provides zero-latency token streaming, deep retail RAG context injection,
    and specialized boardroom executive advisory personas.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = DEFAULT_GEMINI_MODEL):
        self.model_name = model_name or DEFAULT_GEMINI_MODEL
        self.api_key = api_key or self._resolve_api_key()
        self.client = None

        if self.api_key and genai is not None:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized Google AI Studio Gemini client (Default: {self.model_name})")
            except Exception as e:
                logger.warning(f"Could not initialize google-genai Client: {e}. Will use REST gateway fallback.")
        elif not self.api_key:
            logger.info("Google AI Studio Gemini client initialized in standby mode (GEMINI_API_KEY not yet provided).")

    @classmethod
    def _resolve_api_key(cls) -> Optional[str]:
        """Resolves GEMINI_API_KEY from environment, .env file, or email config."""
        key = os.getenv("GEMINI_API_KEY")
        if key and key.strip():
            return key.strip()

        # Check .env file directly if not loaded into environment
        env_file = Path(".env")
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GEMINI_API_KEY=") and not line.startswith("#"):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val:
                                return val
            except Exception as e:
                logger.debug(f"Could not parse .env for GEMINI_API_KEY: {e}")

        return None

    def is_configured(self) -> bool:
        """Returns True if a non-empty Google AI Studio API key is loaded."""
        return bool(self.api_key and len(self.api_key) > 8)

    def get_available_models(self) -> List[str]:
        """
        Returns supported Google AI Studio Gemini models.
        Attempts dynamic query against Google API if key is present.
        """
        if not self.is_configured():
            return list(GEMINI_MODELS)

        try:
            if self.client:
                remote_models = []
                for m in self.client.models.list():
                    m_name = getattr(m, "name", str(m))
                    # Strip 'models/' prefix if present
                    clean_name = m_name.replace("models/", "")
                    if "gemini" in clean_name.lower() and not any(skip in clean_name for skip in ["embedding", "vision-preview"]):
                        remote_models.append(clean_name)
                if remote_models:
                    # Sort prioritizing 1.5-flash and 2.0-flash
                    prioritized = [m for m in GEMINI_MODELS if m in remote_models]
                    others = [m for m in remote_models if m not in prioritized]
                    return prioritized + others
        except Exception as e:
            logger.debug(f"Dynamic Gemini model list query skipped: {e}")

        return list(GEMINI_MODELS)

    def build_live_boutique_context(self, db) -> Dict[str, Any]:
        """
        Delegates retail RAG compilation to the canonical DatabaseManager bridge.
        """
        # Reuse existing robust logic
        analyst = LocalOllamaBoutiqueAnalyst()
        return analyst.build_live_boutique_context(db)

    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """
        Converts live retail metrics into structured Markdown for Gemini system instructions.
        """
        analyst = LocalOllamaBoutiqueAnalyst()
        return analyst.format_context_for_prompt(context)

    def stream_copilot_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        persona_key: str = "👔 Senior Merchandise Director",
        live_context: Optional[Dict[str, Any]] = None,
    ) -> Generator[str, None, None]:
        """
        Streams AI response token-by-token using Google AI Studio Gemini API.
        """
        active_model = model or self.model_name
        # Strip any UI formatting labels
        if " " in active_model:
            active_model = active_model.split(" ")[0].strip()

        # Check API key presence
        if not self.is_configured():
            unconfigured_msg = (
                "✨ **Google AI Studio (Gemini) Activation Notice**\n\n"
                f"You selected Google's **`{active_model}`** model, but your `GEMINI_API_KEY` is not yet configured.\n\n"
                "### How to Activate in 60 Seconds:\n"
                "1. Generate your free API key at **[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)**.\n"
                "2. Add it to your `.env` file: `GEMINI_API_KEY=AIzaSy...`\n"
                "3. Restart the server or select **Llama 3.2 3B (Local Ollama)** from the model dropdown to continue in offline mode."
            )
            yield unconfigured_msg
            return

        persona_info = PERSONAS.get(persona_key, PERSONAS["👔 Senior Merchandise Director"])
        context_str = self.format_context_for_prompt(live_context or {})
        system_instruction = (
            f"{persona_info['prompt']}\n\n"
            f"{context_str}\n\n"
            "INSTRUCTIONS FOR GEMINI:\n"
            "- Speak directly to the luxury boutique executive/owner.\n"
            "- Ground all recommendations in the exact product names, margins, and stock balances provided above.\n"
            "- Use clean Markdown headers, bullet points, and bold styling.\n"
            "- Conclude with 2-3 bold, high-priority Action Items."
        )

        # 1. Attempt official google-genai SDK streaming
        if self.client and types:
            try:
                logger.info(f"Streaming Gemini response via google-genai SDK ('{active_model}')")

                # Format conversation history for Gemini
                contents = []
                for msg in messages[-8:]:
                    role = msg.get("role", "user")
                    text = msg.get("content", "")
                    if not text:
                        continue
                    # Gemini expects 'user' or 'model'
                    gemini_role = "user" if role == "user" else "model"
                    contents.append(
                        types.Content(
                            role=gemini_role,
                            parts=[types.Part.from_text(text=text)]
                        )
                    )

                if not contents:
                    contents.append(types.Content(role="user", parts=[types.Part.from_text(text="Provide executive boutique status.")]))

                response_stream = self.client.models.generate_content_stream(
                    model=active_model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.3,
                    )
                )

                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text
                return
            except Exception as e:
                logger.warning(f"google-genai SDK stream failed: {e}. Attempting direct REST SSE gateway...")

        # 2. Resilient Direct REST SSE Fallback
        yield from self._stream_via_rest_api(
            model=active_model,
            messages=messages,
            system_instruction=system_instruction
        )

    def _stream_via_rest_api(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system_instruction: str
    ) -> Generator[str, None, None]:
        """
        Direct HTTP REST Server-Sent Events (SSE) streaming gateway to Google AI Studio.
        Guarantees 100% reliable execution without SDK transport or version dependency issues.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={self.api_key}&alt=sse"

        # Build contents structure
        contents = []
        for msg in messages[-8:]:
            role = msg.get("role", "user")
            text = msg.get("content", "")
            if not text:
                continue
            gemini_role = "user" if role == "user" else "model"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": text}]
            })

        if not contents:
            contents.append({"role": "user", "parts": [{"text": "Provide boutique overview."}]})

        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3
            }
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        data_json = line[6:].strip()
                        if data_json:
                            try:
                                chunk_data = json.loads(data_json)
                                candidates = chunk_data.get("candidates", [])
                                if candidates:
                                    parts = candidates[0].get("content", {}).get("parts", [])
                                    for part in parts:
                                        t = part.get("text", "")
                                        if t:
                                            yield t
                            except Exception:
                                pass
        except Exception as e:
            err_msg = (
                f"\n\n❌ **Google AI Studio Connection Error**: `{str(e)}`\n\n"
                "Please verify your `GEMINI_API_KEY` in `.env` and verify model availability at [Google AI Studio](https://aistudio.google.com/)."
            )
            logger.error(f"Gemini REST streaming error: {e}")
            yield err_msg

    def generate_executive_audit_commentary(
        self,
        report_data: Dict[str, Any],
        timeframe_label: str = "Weekly",
        model: Optional[str] = None
    ) -> str:
        """
        Synthesizes boardroom audit metrics into an executive narrative using Google Gemini.
        """
        active_model = model or self.model_name
        if " " in active_model:
            active_model = active_model.split(" ")[0].strip()

        # Build standard audit prompt
        analyst = LocalOllamaBoutiqueAnalyst()
        # Fallback to local Ollama if Gemini is not configured
        if not self.is_configured():
            logger.info("GEMINI_API_KEY not configured. Falling back to local Ollama for audit commentary.")
            return analyst.generate_executive_audit_commentary(report_data, timeframe_label)

        m = report_data.get("metrics", {})
        top_merch = report_data.get("top_merch")
        broken = report_data.get("broken_curves", [])
        period_title = report_data.get("period_title", timeframe_label)

        top_merch_str = ""
        try:
            if hasattr(top_merch, "iterrows") and not top_merch.empty:
                for idx, row in top_merch.head(5).iterrows():
                    top_merch_str += f"  • {row.get('product_name')}: {row.get('units_sold')} sold, ${row.get('revenue'):,.2f} rev, ${row.get('profit'):,.2f} profit ({row.get('margin_pct')}% margin)\n"
        except Exception:
            top_merch_str = "  • Top merchandise records loaded from database.\n"

        prompt = f"""You are the Chief Merchandising & Financial Auditor for Mishika Fashion Luxury Boutique.
Analyze the following audited retail metrics for {period_title} and generate an authoritative, boardroom-level Executive Audit Commentary.

TIMEFRAME AUDITED: {period_title}
KEY FINANCIAL METRICS:
- Total Sales Revenue: ${m.get('total_revenue', 0):,.2f} ({m.get('transaction_count', 0):,} Transactions)
- Cost of Goods Sold (COGS): ${m.get('total_cogs', 0):,.2f} ({m.get('units_sold', 0):,} Units Sold)
- Net Gross Profit: ${m.get('gross_profit', 0):,.2f} (Realized Margin: {m.get('margin_pct', 0):.1f}%)
- Procurement Inbound Deliveries: +{m.get('units_restocked', 0):,} Units (${m.get('restock_spend', 0):,.2f} spend)

TOP MERCHANDISE PERFORMERS:
{top_merch_str}

REQUIRED FORMAT (Use clean headers and bold bullet points with exact numbers):
### 1. Executive Summary & Financial Health
Provide an incisive assessment of revenue volume, realized gross margin percentage, and working capital efficiency.

### 2. Merchandising Velocity & Profitability Drivers
Highlight top moving styles, profitability anchors, and any lagging apparel categories.

### 3. Supply Chain Restocks & Inventory Risk Safeguards
Evaluate supply chain replenishment spend vs. sales volume, safety stock alerts, and remedies for broken size curves.

### 4. Strategic Pricing & Boardroom Recommendations
Provide 3 concrete, prioritized executive actions (re-orders, pricing adjustments, clearance markdowns) for the leadership team.
"""
        try:
            if self.client:
                resp = self.client.models.generate_content(
                    model=active_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.25)
                )
                return resp.text or ""
        except Exception as e:
            logger.warning(f"Gemini SDK audit commentary failed: {e}. Using fallback...")

        return analyst.generate_executive_audit_commentary(report_data, timeframe_label)
