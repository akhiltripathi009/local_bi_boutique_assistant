"""
tests/test_gemini_client.py
===========================
Automated test suite verifying the Google AI Studio (Gemini) Client and unified factory.
"""

import unittest
from fastapi.testclient import TestClient

from src.server.app import app
from src.ai.gemini_client import (
    GoogleGeminiBoutiqueAnalyst,
    GEMINI_MODELS,
    DEFAULT_GEMINI_MODEL,
)
from src.ai.ollama_client import LocalOllamaBoutiqueAnalyst
from src.ai import get_boutique_analyst


class TestGoogleGeminiClient(unittest.TestCase):
    """Verifies Google AI Studio client integration, factory resolution, and API endpoints."""

    def setUp(self):
        self.client = TestClient(app)

    def test_01_gemini_analyst_initialization(self):
        """Verifies GoogleGeminiBoutiqueAnalyst initializes cleanly without errors."""
        analyst = GoogleGeminiBoutiqueAnalyst(model_name="gemini-1.5-flash")
        self.assertEqual(analyst.model_name, "gemini-1.5-flash")
        models = analyst.get_available_models()
        self.assertIn("gemini-1.5-flash", models)
        self.assertIn("gemini-1.5-pro", models)
        self.assertIn("gemini-2.0-flash", models)

    def test_02_unified_factory_resolution(self):
        """Verifies get_boutique_analyst correctly resolves Gemini vs Ollama based on model."""
        # Explicit Gemini tag
        g_analyst = get_boutique_analyst("gemini-1.5-flash")
        self.assertIsInstance(g_analyst, GoogleGeminiBoutiqueAnalyst)
        self.assertEqual(g_analyst.model_name, "gemini-1.5-flash")

        # Explicit Gemini Pro tag
        g_pro = get_boutique_analyst("gemini-1.5-pro")
        self.assertIsInstance(g_pro, GoogleGeminiBoutiqueAnalyst)

        # Explicit Ollama tag
        o_analyst = get_boutique_analyst("llama3.2:3b")
        self.assertIsInstance(o_analyst, LocalOllamaBoutiqueAnalyst)

    def test_03_unconfigured_api_key_streaming_notice(self):
        """Verifies that an unconfigured Gemini client yields a friendly guidance notice."""
        analyst = GoogleGeminiBoutiqueAnalyst(api_key="")
        # Force is_configured to False for test
        analyst.api_key = None
        chunks = list(analyst.stream_copilot_response(
            messages=[{"role": "user", "content": "Hello"}],
            model="gemini-1.5-flash"
        ))
        full_text = "".join(chunks)
        self.assertIn("Google AI Studio", full_text)
        self.assertIn("aistudio.google.com", full_text)

    def test_04_format_context_for_prompt(self):
        """Verifies retail RAG context formatting produces clean Markdown for Gemini."""
        analyst = GoogleGeminiBoutiqueAnalyst()
        sample_ctx = {
            "financial_overview": {
                "total_revenue_usd": 15450.75,
                "average_gross_margin_pct": 38.5
            },
            "hot_sellers": [
                {"product_name": "Royal Silk Saree", "sell_through_pct": 82.5, "status": "Hot Seller"}
            ],
            "critical_low_stock_items": [
                {"product_name": "Velvet Gown", "category": "Dresses", "stock_balance": 8, "unit_price": 280.0}
            ]
        }
        prompt_txt = analyst.format_context_for_prompt(sample_ctx)
        self.assertIn("Royal Silk Saree", prompt_txt)
        self.assertIn("Velvet Gown", prompt_txt)
        self.assertIn("15,450.75", prompt_txt)

    def test_05_api_models_endpoint_includes_gemini(self):
        """Verifies GET /api/copilot/models returns both Google AI Studio and Ollama models."""
        resp = self.client.get("/api/copilot/models")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        models = data.get("models", [])
        self.assertIn("gemini-1.5-flash", models)
        self.assertIn("gemini-1.5-pro", models)
        self.assertIn("gemini-2.0-flash", models)
        self.assertIn("gemini_models", data)
        self.assertIn("gemini_configured", data)

    def test_06_copilot_stream_endpoint_gemini_routing(self):
        """Verifies POST /api/copilot/stream accepts gemini-1.5-flash model request."""
        payload = {
            "messages": [{"role": "user", "content": "Summarize today revenue."}],
            "model": "gemini-1.5-flash",
            "persona_key": "👔 Senior Merchandise Director"
        }
        resp = self.client.post("/api/copilot/stream", json=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/event-stream", resp.headers.get("content-type", ""))
        content = resp.text
        self.assertIn("data:", content)


if __name__ == "__main__":
    unittest.main()
