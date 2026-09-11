"""
Unit & Integration tests for Mishika Fashion Luxury Boutique Commercial SaaS API.
Tests all FastAPI endpoints using TestClient.
"""

import os
import sys
import unittest
from pathlib import Path

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from src.server.app import app

class SaasApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_endpoint(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("database_connected", data)

        # Verify static CSS and JS assets load cleanly with 200 OK
        res_css = self.client.get("/css/style.css")
        self.assertEqual(res_css.status_code, 200)
        self.assertIn("text/css", res_css.headers.get("content-type", ""))

        res_js = self.client.get("/js/app.js")
        self.assertEqual(res_js.status_code, 200)

        res_html = self.client.get("/")
        self.assertEqual(res_html.status_code, 200)
        self.assertIn("Mishika Fashion", res_html.text)

    def test_02_dashboard_stats(self):
        res = self.client.get("/api/dashboard/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_revenue", data)
        self.assertIn("gross_profit", data)
        self.assertIn("realized_margin_pct", data)
        self.assertIn("sell_through_rate_pct", data)
        self.assertIn("shop_floor_units", data)
        self.assertIn("warehouse_reserve_units", data)

    def test_03_dashboard_charts(self):
        res = self.client.get("/api/dashboard/charts")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("hourly_sales", data)
        self.assertIn("category_summary", data)
        self.assertIn("top_styles", data)

    def test_04_inventory_overview_and_transfer(self):
        # 1. Overview
        res = self.client.get("/api/inventory/overview")
        self.assertEqual(res.status_code, 200)
        inv = res.json()
        self.assertIn("products", inv)
        self.assertGreater(len(inv["products"]), 0)
        sample_pid = inv["products"][0]["product_id"]

        # 2. Transfer stock (Shop to WH)
        payload = {
            "product_id": sample_pid,
            "size_variant": "M",
            "quantity": 2,
            "source_location": "Shop Floor",
            "dest_location": "Warehouse Reserve"
        }
        res_t = self.client.post("/api/inventory/transfer", json=payload)
        self.assertEqual(res_t.status_code, 200)
        self.assertTrue(res_t.json()["success"])

    def test_05_crm_customers_and_update(self):
        # 1. List
        res = self.client.get("/api/crm/customers?tier=All")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("customers", data)
        self.assertGreater(len(data["customers"]), 0)
        cust_id = data["customers"][0]["id"]

        # 2. Update contact
        update_payload = {
            "name": "Lady Vivienne Test",
            "phone": "+1 (555) 019-9999",
            "email": "vivienne.test@couture.com",
            "preferred_size": "S",
            "style_preference": "Haute Couture",
            "loyalty_tier": "Platinum VIP",
            "opt_in_whatsapp": 1,
            "opt_in_email": 1
        }
        res_u = self.client.post(f"/api/crm/customer/{cust_id}/update", json=update_payload)
        self.assertEqual(res_u.status_code, 200)
        self.assertTrue(res_u.json()["success"])

        # 3. Check profile
        res_p = self.client.get(f"/api/crm/customer/{cust_id}")
        self.assertEqual(res_p.status_code, 200)
        prof = res_p.json()["profile"]
        self.assertEqual(prof["name"], "Lady Vivienne Test")

    def test_06_campaigns_create_and_guardrails(self):
        # 1. Normal campaign creation
        valid_camp = {
            "name": "Winter Gala Privé",
            "description": "Exclusive invitation preview for VIP clients",
            "discount_pct": 20.0,
            "target_category": "Dresses"
        }
        res = self.client.post("/api/campaigns/create", json=valid_camp)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

        # 2. Guardrail test: excessive discount capped at 50%
        excess_camp = {
            "name": "Aggressive Clearance",
            "description": "Attempting 70% markdown",
            "discount_pct": 70.0,
            "target_category": "Outerwear"
        }
        res_ex = self.client.post("/api/campaigns/create", json=excess_camp)
        self.assertEqual(res_ex.status_code, 200)
        data_ex = res_ex.json()
        self.assertEqual(data_ex["discount_pct"], 50.0)
        self.assertIsNotNone(data_ex["guardrail_warning"])

    def test_07_agent_status_and_actions(self):
        res = self.client.get("/api/agent/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["agent_name"], "Shivi")
        self.assertIn("subagents", data)

        # Trigger Morning Opening action
        res_act = self.client.post("/api/agent/run-action", json={"action": "morning_opening"})
        self.assertEqual(res_act.status_code, 200)
        act_data = res_act.json()
        self.assertTrue(act_data["success"])
        self.assertIn("items", act_data["plan"])

    def test_08_copilot_metadata(self):
        res_m = self.client.get("/api/copilot/models")
        self.assertEqual(res_m.status_code, 200)
        self.assertIn("models", res_m.json())

        res_p = self.client.get("/api/copilot/personas")
        self.assertEqual(res_p.status_code, 200)
        self.assertIn("personas", res_p.json())

    def test_09_sandbox_execution(self):
        presets_res = self.client.get("/api/sandbox/presets")
        self.assertEqual(presets_res.status_code, 200)
        self.assertIn("presets", presets_res.json())

        # Execute safe Python code
        code = "total = sum([100, 200, 300])\nprint(f'Calculated Total: ${total}')"
        exec_res = self.client.post("/api/sandbox/execute", json={"code": code})
        self.assertEqual(exec_res.status_code, 200)
        result = exec_res.json()
        self.assertTrue(result["success"])
        self.assertIn("Calculated Total: $600", result["output"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
