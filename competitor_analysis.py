import pandas as pd
from typing import Dict, Any


class CompetitorAnalyzer:
    def __init__(self, competitor_df: pd.DataFrame):
        """
        Competitor DataFrame structure expected fields:
        ['competitor_name', 'product_id', 'product_name', 'competitor_price', 'rating']
        """
        self.df = competitor_df

    def analyze_market_positioning(self, internal_catalog: list[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates product pricing indices compared to regional averages."""
        positioning_report = {}

        for item in internal_catalog:
            pid = item["id"]
            my_price = item["price"]

            # Filter benchmark data for the same product baseline
            comp_matches = self.df[self.df['product_id'] == pid]

            if comp_matches.empty:
                continue

            avg_market_price = comp_matches['competitor_price'].mean()
            min_market_price = comp_matches['competitor_price'].min()

            # Price Index calculation: > 100 means internal price is more expensive
            price_index = (my_price / avg_market_price) * 100

            if price_index > 110:
                strategy = "Premium Positioned (Consider adding value or dropping price)"
            elif price_index < 90:
                strategy = "Underpriced Venture (Opportunity to raise price and grow margin)"
            else:
                strategy = "Market Aligned (Highly competitive pricing status)"

            positioning_report[item["name"]] = {
                "your_price": my_price,
                "market_average": round(float(avg_market_price), 2),
                "market_minimum": round(float(min_market_price), 2),
                "pricing_index": round(price_index, 1),
                "strategic_action": strategy
            }

        return positioning_report
