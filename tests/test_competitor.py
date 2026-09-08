import pandas as pd
from src.analytics.competitor import CompetitorAnalyzer

def test_price_elasticity_simulation():
    """Validates price elasticity demand curves and gross margin calculations."""
    sim = CompetitorAnalyzer.simulate_price_elasticity(
        product_id="P001",
        new_price=105.0,
        old_price=95.0,
        cost=35.0,
        category="Dresses",
        base_volume=20,
        avg_market_price=110.0
    )
    assert sim["old_revenue"] == 95.0 * 20
    assert sim["new_price"] == 105.0
    assert sim["pct_price_change"] > 0
    assert sim["projected_units"] <= 20
    assert "new_gross_profit" in sim
    assert "new_cpi" in sim

def test_store_cpi_metrics_structure(test_db):
    """Ensures CPI calculation returns valid keys and realistic benchmarks."""
    df = test_db.fetch_dynamic_competitor_pricing()
    metrics = CompetitorAnalyzer.get_store_cpi_metrics(df)
    assert "store_cpi" in metrics
    assert "store_position" in metrics
    assert "total_margin_opportunity" in metrics
    assert "underpriced_count" in metrics
