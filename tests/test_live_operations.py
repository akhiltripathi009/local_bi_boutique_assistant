"""
tests/test_live_operations.py
=============================
Automated test suite for Segment 2: Live Store & Shop Operations Pipeline.
Verifies FastAPI endpoints, discrete simulation tick execution, simulation controls,
stock chart color taxonomy, and ledger streaming.
"""

import unittest
from fastapi.testclient import TestClient
from src.server.app import app

class LiveOperationsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_get_status(self):
        """Verify /api/live-ops/status returns valid pipeline state."""
        response = self.client.get("/api/live-ops/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("running", data)
        self.assertIn("tick_speed", data)
        self.assertIn("promo_discount", data)
        self.assertIn("total_revenue", data)
        self.assertIn("low_stock_count", data)
        self.assertIn("active_product_context", data)

    def test_02_step_tick(self):
        """Verify /api/live-ops/tick triggers simulation and advances frame counter."""
        initial_status = self.client.get("/api/live-ops/status").json()
        initial_frame = initial_status.get("frame_counter", 0)

        response = self.client.post("/api/live-ops/tick")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertGreater(data.get("frame_counter", 0), initial_frame)
        self.assertIn("event", data)
        self.assertIn("event_type", data["event"])
        self.assertIn("inventory_snapshot", data)

    def test_03_update_settings(self):
        """Verify /api/live-ops/settings modifies promo markdown and tick speed."""
        payload = {"promo_discount": 25, "tick_speed": 0.55}
        response = self.client.post("/api/live-ops/settings", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("promo_discount"), 25)
        self.assertAlmostEqual(data.get("tick_speed"), 0.55, places=2)

        # Confirm via status
        status = self.client.get("/api/live-ops/status").json()
        self.assertEqual(status.get("promo_discount"), 25)

        # Reset back
        self.client.post("/api/live-ops/settings", json={"promo_discount": 0, "tick_speed": 0.35})

    def test_04_start_and_pause_loop(self):
        """Verify start and pause endpoints toggle running state."""
        res_start = self.client.post("/api/live-ops/start")
        self.assertEqual(res_start.status_code, 200)
        self.assertTrue(res_start.json().get("running"))

        status = self.client.get("/api/live-ops/status").json()
        self.assertTrue(status.get("running"))

        res_pause = self.client.post("/api/live-ops/pause")
        self.assertEqual(res_pause.status_code, 200)
        self.assertFalse(res_pause.json().get("running"))

        status = self.client.get("/api/live-ops/status").json()
        self.assertFalse(status.get("running"))

    def test_05_stock_chart_data(self):
        """Verify /api/live-ops/stock-chart delivers 20 categorized catalog styles."""
        response = self.client.get("/api/live-ops/stock-chart")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        items = data.get("items", [])
        self.assertGreaterEqual(len(items), 20)
        for item in items:
            self.assertIn("product_id", item)
            self.assertIn("stock", item)
            self.assertIn("color", item)
            self.assertIn("tag", item)
            self.assertTrue(item["color"].startswith("#"))

    def test_06_logs_and_ledgers(self):
        """Verify /api/live-ops/logs returns sales and restock ledgers."""
        response = self.client.get("/api/live-ops/logs?limit=5")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("sales_log", data)
        self.assertIn("restocks_log", data)

    def test_07_reset_inventory(self):
        """Verify /api/live-ops/reset synchronizes in-memory stock from SQLite."""
        response = self.client.post("/api/live-ops/reset")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))

if __name__ == "__main__":
    unittest.main()
