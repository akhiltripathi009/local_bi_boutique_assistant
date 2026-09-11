"""
tests/test_agent_routes.py
===========================
Automated test suite verifying the extended FastAPI endpoints for Shivi Deep Agent:
1. Status, metrics & skills loaded
2. Fashion news curations & RSS live wire / default fallback
3. Guardrails inspector (PII redaction & discount cap clamping)
4. Email configuration persistence & test endpoint
5. 6 Operational Dispatcher routines (Opening, Closing, News, Campaign, Restock, Birthday)
6. Communication logs ledger
"""

import unittest
from fastapi.testclient import TestClient
from src.server.app import app

class ShiviAgentRoutesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_agent_status_metrics(self):
        """Verify /api/agent/status delivers guardrails, skills, tools, and memory metrics."""
        response = self.client.get("/api/agent/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("agent_name"), "Shivi")
        self.assertEqual(data.get("skills_count"), 4)
        self.assertEqual(data.get("tools_count"), 5)
        self.assertIn("guardrails_status", data)
        self.assertIn("email_configured", data)
        self.assertIn("subagents", data)
        self.assertEqual(len(data["subagents"]), 4)

    def test_02_news_preview_default_and_topic(self):
        """Verify /api/agent/news-preview curates personalized patron newsletters."""
        # 1. Default news preview
        resp = self.client.get("/api/agent/news-preview")
        self.assertEqual(resp.status_code, 200)
        d = resp.json()
        self.assertTrue(d.get("success"))
        self.assertGreater(d.get("count", 0), 0)
        self.assertIn("messages", d)
        first = d["messages"][0]
        self.assertIn("customer_name", first)
        self.assertIn("email_html", first)
        self.assertIn("whatsapp_text", first)
        self.assertIn("masked_email", first)
        self.assertIn("masked_phone", first)

        # 2. Filtered topic query
        resp_topic = self.client.get("/api/agent/news-preview?topic_query=paris+haute+couture")
        self.assertEqual(resp_topic.status_code, 200)
        d_topic = resp_topic.json()
        self.assertTrue(d_topic.get("success"))
        self.assertGreater(d_topic.get("count", 0), 0)

    def test_03_guardrails_pii_redaction(self):
        """Verify /api/agent/guardrails/redact-pii masks emails and phone numbers."""
        sample = "Patron Elena Rostova at elena.rostova@vogue-luxury.com with phone +1-555-0101 reserved a silk gown."
        resp = self.client.post("/api/agent/guardrails/redact-pii", json={"text": sample})
        self.assertEqual(resp.status_code, 200)
        d = resp.json()
        self.assertTrue(d.get("success"))
        sanitized = d.get("sanitized_text")
        self.assertNotIn("elena.rostova@vogue-luxury.com", sanitized)
        self.assertIn("@vogue-luxury.com", sanitized)
        self.assertNotIn("+1-555-0101", sanitized)

    def test_04_guardrails_discount_validation(self):
        """Verify /api/agent/guardrails/validate-discount enforces the 50% max cap."""
        # Safe discount
        resp_safe = self.client.post("/api/agent/guardrails/validate-discount", json={"discount_pct": 30.0})
        self.assertEqual(resp_safe.status_code, 200)
        d_safe = resp_safe.json()
        self.assertTrue(d_safe.get("is_safe"))
        self.assertEqual(d_safe.get("effective_discount"), 30.0)

        # Dangerous discount (>50%) - must clamp to 50.0
        resp_clamp = self.client.post("/api/agent/guardrails/validate-discount", json={"discount_pct": 70.0})
        self.assertEqual(resp_clamp.status_code, 200)
        d_clamp = resp_clamp.json()
        self.assertFalse(d_clamp.get("is_safe"))
        self.assertEqual(d_clamp.get("effective_discount"), 50.0)
        self.assertIn("clamped", d_clamp.get("message", "").lower())

    def test_05_email_config_api(self):
        """Verify /api/agent/email-config allows retrieving configuration."""
        resp = self.client.get("/api/agent/email-config")
        self.assertEqual(resp.status_code, 200)
        d = resp.json()
        self.assertTrue(d.get("success"))
        cfg = d.get("config", {})
        self.assertIn("smtp_host", cfg)
        self.assertIn("smtp_port", cfg)

    def test_06_operational_dispatchers(self):
        """Verify running specialized actions via /api/agent/run-action."""
        # 1. Morning Opening
        resp_open = self.client.post("/api/agent/run-action", json={"action": "morning_opening"})
        self.assertEqual(resp_open.status_code, 200)
        d_open = resp_open.json()
        self.assertTrue(d_open.get("success"))
        self.assertTrue(d_open["result"].get("pdf_available"))

        # 2. Evening Closing
        resp_close = self.client.post("/api/agent/run-action", json={"action": "evening_closing"})
        self.assertEqual(resp_close.status_code, 200)
        d_close = resp_close.json()
        self.assertTrue(d_close.get("success"))
        self.assertTrue(d_close["result"].get("pdf_available"))

        # 3. Fashion News (Dry Run)
        resp_news = self.client.post("/api/agent/run-action", json={"action": "fashion_news", "dry_run": True})
        self.assertEqual(resp_news.status_code, 200)
        self.assertTrue(resp_news.json().get("success"))

        # 4. Campaign Launch (Dry Run)
        resp_camp = self.client.post("/api/agent/run-action", json={"action": "campaign_launch", "dry_run": True})
        self.assertEqual(resp_camp.status_code, 200)
        self.assertTrue(resp_camp.json().get("success"))

        # 5. Restock Alert (Dry Run)
        resp_restock = self.client.post("/api/agent/run-action", json={"action": "restock", "dry_run": True})
        self.assertEqual(resp_restock.status_code, 200)
        self.assertTrue(resp_restock.json().get("success"))

        # 6. Birthday Perks (Dry Run)
        resp_bday = self.client.post("/api/agent/run-action", json={"action": "birthday", "dry_run": True})
        self.assertEqual(resp_bday.status_code, 200)
        self.assertTrue(resp_bday.json().get("success"))

    def test_07_communications_ledger(self):
        """Verify /api/agent/communications returns logged dispatches."""
        resp = self.client.get("/api/agent/communications")
        self.assertEqual(resp.status_code, 200)
        d = resp.json()
        self.assertTrue(d.get("success"))
        self.assertIsInstance(d.get("communications"), list)

if __name__ == "__main__":
    unittest.main()
