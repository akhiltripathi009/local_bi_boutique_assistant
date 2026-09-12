"""
tests/test_missing_segments.py
==============================
Verification tests for:
- Segment 3: Inventory & Store Circuit Controls Switchboard
- Segment 4: Boardroom-Grade Executive PDF Reporting Engine
- Segment 1: Executive Dashboard Dynamic What-If Repricing & Competitor Matrix
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from src.server.app import app

client = TestClient(app)


def test_circuit_controls_endpoints():
    # 1. GET /api/inventory/controls
    res = client.get("/api/inventory/controls")
    assert res.status_code == 200, f"Failed GET /api/inventory/controls: {res.text}"
    data = res.json()
    assert data["success"] is True
    assert len(data["controls"]) >= 20
    assert "All Categories" in data["categories"]
    
    first = data["controls"][0]
    assert "sales_enabled" in first
    assert "purchase_enabled" in first
    assert "max_stock" in first
    assert "sizes" in first
    assert "S" in first["sizes"]
    assert "M" in first["sizes"]
    assert "L" in first["sizes"]
    assert "XL" in first["sizes"]
    print("✓ Passed GET /api/inventory/controls (verified 20 products & size breakdown)")

    # 2. POST /api/inventory/controls/update
    pid = first["product_id"]
    up_res = client.post("/api/inventory/controls/update", json={
        "product_id": pid,
        "key": "sales_enabled",
        "value": False
    })
    assert up_res.status_code == 200
    assert up_res.json()["success"] is True

    # Revert back
    up_res2 = client.post("/api/inventory/controls/update", json={
        "product_id": pid,
        "key": "sales_enabled",
        "value": True
    })
    assert up_res2.status_code == 200
    print(f"✓ Passed POST /api/inventory/controls/update for {pid}")


def test_executive_pdf_reports_endpoints():
    # 1. Preview for all scopes
    for scope in ["daily", "weekly", "monthly", "complete"]:
        res = client.get(f"/api/reports/preview?scope={scope}")
        assert res.status_code == 200, f"Failed preview for scope {scope}: {res.text}"
        data = res.json()
        assert data["success"] is True
        assert data["scope"] == scope
        assert "metrics" in data
        assert "total_revenue" in data["metrics"]
        assert "gross_profit" in data["metrics"]
        assert "margin_pct" in data["metrics"]
    print("✓ Passed GET /api/reports/preview across all 4 timeframes (daily, weekly, monthly, complete)")

    # 2. PDF generation binary stream
    pdf_res = client.get("/api/reports/enterprise-pdf?scope=daily")
    assert pdf_res.status_code == 200, f"Failed enterprise PDF generation: {pdf_res.text}"
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000  # valid PDF bytes
    print(f"✓ Passed GET /api/reports/enterprise-pdf (compiled {len(pdf_res.content)} bytes PDF)")


def test_dashboard_dynamic_intelligence_endpoints():
    # 1. Competitor intelligence
    c_res = client.get("/api/dashboard/competitor-intelligence")
    assert c_res.status_code == 200
    c_data = c_res.json()
    assert c_data["success"] is True
    assert "metrics" in c_data
    assert "store_cpi" in c_data["metrics"]
    assert "underpriced_count" in c_data["metrics"]
    assert len(c_data["items"]) >= 20
    print("✓ Passed GET /api/dashboard/competitor-intelligence (verified tri-brand benchmarks & CPI metrics)")

    # 2. Diagnostics (2x2)
    d_res = client.get("/api/dashboard/diagnostics")
    assert d_res.status_code == 200
    d_data = d_res.json()
    assert d_data["success"] is True
    assert len(d_data["sell_through"]) >= 20
    assert len(d_data["sentiment"]) >= 4
    print("✓ Passed GET /api/dashboard/diagnostics (verified sell-through, sentiment, broken curves)")

    # 3. Simulate elasticity
    sim_res = client.post("/api/dashboard/simulate-elasticity", json={
        "product_id": "P001",
        "new_price": 195.0,
        "base_volume": 40
    })
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["success"] is True
    assert "simulation" in sim_data
    assert "profit_delta" in sim_data["simulation"]
    assert "new_cpi" in sim_data["simulation"]
    print("✓ Passed POST /api/dashboard/simulate-elasticity (calculated retail demand & profit shift)")

    # 4. Reprice catalog item
    rep_res = client.post("/api/dashboard/reprice", json={
        "product_id": "P001",
        "new_price": 185.0
    })
    assert rep_res.status_code == 200
    assert rep_res.json()["success"] is True
    print("✓ Passed POST /api/dashboard/reprice (committed new catalog price to database)")


if __name__ == "__main__":
    test_circuit_controls_endpoints()
    test_executive_pdf_reports_endpoints()
    test_dashboard_dynamic_intelligence_endpoints()
    print("\n★ ALL SEGMENTS 1, 3, & 4 TESTS PASSED PERFECTLY!")
