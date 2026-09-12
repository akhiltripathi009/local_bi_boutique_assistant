"""
tests/test_chat_actions.py
===========================
Automated test suite verifying Shivi Deep Agent's conversational action execution:
1. Intent detection & parameter extraction for email dispatch and operational routines
2. End-to-end report generation & simulated SMTP dispatch via chat command
3. Fast-path action routing for routines, circuit breakers, VIP lookup, and HITL approvals
4. POST /api/copilot/action endpoint verification
5. GET /api/reports/latest-generated-pdf binary stream verification
6. SSE streaming integration with action metadata cards
"""

import json
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.server.app import app
from src.data.db_manager import DatabaseManager
from src.deep_agent.orchestrator import ShiviDeepAgent


class ShiviChatActionsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = DatabaseManager()
        cls.agent = ShiviDeepAgent(cls.db)

    def test_01_detect_send_audit_report_intent(self):
        """Verify intent extractor correctly parses target email and report type."""
        # User request exact pattern
        query = "Now want to send Todays audit report to on mail ID example@gmail.com"
        intent = self.agent.detect_chat_action(query)
        self.assertIsNotNone(intent)
        self.assertEqual(intent.get("action"), "send_report_email")
        self.assertEqual(intent.get("target_email"), "example@gmail.com")
        self.assertEqual(intent.get("report_type"), "daily_closing")

        # Morning opening variation
        q_opening = "Email the morning briefing to manager@mishika.com please"
        intent_opening = self.agent.detect_chat_action(q_opening)
        self.assertIsNotNone(intent_opening)
        self.assertEqual(intent_opening.get("action"), "send_report_email")
        self.assertEqual(intent_opening.get("target_email"), "manager@mishika.com")
        self.assertEqual(intent_opening.get("report_type"), "morning_opening")

        # Implicit admin recipient
        q_admin = "Send today's closing audit report to admin"
        intent_admin = self.agent.detect_chat_action(q_admin)
        self.assertIsNotNone(intent_admin)
        self.assertEqual(intent_admin.get("action"), "send_report_email")

    def test_02_detect_operational_routines_intent(self):
        """Verify routine triggers are properly identified."""
        self.assertEqual(
            self.agent.detect_chat_action("Run morning opening routine").get("action"),
            "run_routine"
        )
        self.assertEqual(
            self.agent.detect_chat_action("Execute evening closing audit").get("action"),
            "run_routine"
        )
        self.assertEqual(
            self.agent.detect_chat_action("Scan back in stock alerts").get("action"),
            "run_routine"
        )
        self.assertEqual(
            self.agent.detect_chat_action("Dispatch birthday perks for this week").get("action"),
            "run_routine"
        )

    def test_03_detect_circuit_breaker_and_vip_lookup(self):
        """Verify circuit breaker and VIP lookup intents."""
        cb_intent = self.agent.detect_chat_action("Halt sales for Royal Silk Saree")
        self.assertIsNotNone(cb_intent)
        self.assertEqual(cb_intent.get("action"), "circuit_breaker")
        self.assertFalse(cb_intent.get("enable"))

        vip_intent = self.agent.detect_chat_action("Lookup customer Aisha Sharma")
        self.assertIsNotNone(vip_intent)
        self.assertEqual(vip_intent.get("action"), "lookup_vip")

    def test_04_execute_send_audit_report_action(self):
        """Verify end-to-end execution of sending today's audit report via chat."""
        query = "Send Todays audit report to on mail ID example@gmail.com"
        res = self.agent.execute_chat_action(query)
        self.assertIsNotNone(res)
        self.assertTrue(res.success)
        self.assertEqual(res.action, "send_report_email")
        self.assertIsNotNone(res.pdf_bytes)
        self.assertGreater(len(res.pdf_bytes), 1000)
        self.assertTrue(res.pdf_name.endswith(".pdf"))
        self.assertIn("example@gmail.com", res.narrative)
        self.assertIn("card", res.to_dict())
        self.assertEqual(res.card.get("download_url"), "/api/reports/latest-generated-pdf")

    def test_05_api_copilot_action_endpoint(self):
        """Verify POST /api/copilot/action processes conversational commands."""
        # 1. Action query
        payload = {"query": "Send Todays audit report to on mail ID example@gmail.com"}
        resp = self.client.post("/api/copilot/action", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertTrue(data.get("is_action"))
        res_obj = data.get("result")
        self.assertEqual(res_obj.get("action"), "send_report_email")
        self.assertTrue(res_obj.get("pdf_available"))

        # 2. Non-action query
        payload_non_action = {"query": "What is our current sell through rate?"}
        resp_non = self.client.post("/api/copilot/action", json=payload_non_action)
        self.assertEqual(resp_non.status_code, 200)
        data_non = resp_non.json()
        self.assertFalse(data_non.get("is_action"))

    def test_06_latest_generated_pdf_endpoint(self):
        """Verify GET /api/reports/latest-generated-pdf streams binary PDF."""
        resp = self.client.get("/api/reports/latest-generated-pdf")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("content-type"), "application/pdf")
        self.assertGreater(len(resp.content), 1000)
        self.assertTrue(resp.content.startswith(b"%PDF"))

    def test_07_copilot_stream_with_action_sse(self):
        """Verify SSE streaming delivers action card and text tokens when action triggered."""
        req_body = {
            "messages": [
                {"role": "user", "content": "Send Todays audit report to on mail ID example@gmail.com"}
            ],
            "model": "llama3.2:3b",
            "persona_key": "👔 Senior Merchandise Director"
        }
        resp = self.client.post("/api/copilot/stream", json=req_body)
        self.assertEqual(resp.status_code, 200)
        content_str = resp.text
        self.assertIn("data: ", content_str)
        self.assertIn('"action":', content_str)
        self.assertIn('"done": true', content_str)


if __name__ == "__main__":
    unittest.main()
