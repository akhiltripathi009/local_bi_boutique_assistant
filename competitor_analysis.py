import pandas as pd
import logging
from typing import Dict, Any, List
from logger_config import setup_logging

logger = setup_logging("competitor_analysis")

class CompetitorAnalyzer:
    """
    Analyzes internal pricing strategies against external market benchmarks.
    """
    def __init__(self, competitor_df: pd.DataFrame):
        """
        Initializes the analyzer with competitor data.
        
        Args:
            competitor_df (pd.DataFrame): Dataframe containing 'competitor_name', 
                                         'product_id', 'product_name', 'competitor_price', 'rating'.
        """
        self.df = competitor_df

    def analyze_market_positioning(self, internal_catalog: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates pricing indices and recommends strategic actions.
        
        Args:
            internal_catalog (List[Dict]): List of product dictionaries from the internal catalog.
            
        Returns:
            Dict: Report mapping product names to pricing metrics and strategies.
        """
        try:
            positioning_report = {}

            for item in internal_catalog:
                pid = item.get("id")
                my_price = item.get("price")

                if not pid or my_price is None:
                    continue

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

            logger.info(f"Market positioning analysis completed for {len(positioning_report)} products.")
            return positioning_report
        except Exception as e:
            logger.error(f"Error analyzing market positioning: {e}")
            return {}
