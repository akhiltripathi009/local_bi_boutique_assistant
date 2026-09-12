import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from src.server.app import app

client = TestClient(app)

def test_timeframe_stats_and_charts():
    results = {}
    for tf in ["hourly", "daily", "monthly", "yearly", "annual", "annually"]:
        res = client.get(f"/api/dashboard/stats?timeframe={tf}")
        assert res.status_code == 200, f"Stats failed for {tf}: {res.text}"
        data = res.json()
        assert data["success"] is True
        expected_tf = "yearly" if tf in ["annual", "annually"] else tf
        assert data["timeframe"] == expected_tf
        assert "total_revenue" in data
        assert "gross_profit" in data
        assert "realized_margin_pct" in data
        assert "sell_through_rate_pct" in data
        assert "units_sold" in data
        results[tf] = data

        res_ch = client.get(f"/api/dashboard/charts?timeframe={tf}")
        assert res_ch.status_code == 200, f"Charts failed for {tf}: {res_ch.text}"
        ch_data = res_ch.json()
        assert ch_data["success"] is True
        assert ch_data["timeframe"] == expected_tf
        assert len(ch_data["hourly_sales"]) > 0
        assert len(ch_data["category_summary"]) > 0
        assert len(ch_data["top_styles"]) > 0

    print("\n--- ALL TIMEFRAMES VERIFIED ---")
    for tf, d in results.items():
        print(f"[{tf.upper()}] Rev: ${d['total_revenue']:,.2f} | Profit: ${d['gross_profit']:,.2f} | Margin: {d['realized_margin_pct']}% | STR: {d['sell_through_rate_pct']}% | Units: {d['units_sold']}")

if __name__ == "__main__":
    test_timeframe_stats_and_charts()
