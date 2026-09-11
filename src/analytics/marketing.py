import pandas as pd
import logging
from typing import Dict, Any
try:
    from src.core.logger import setup_logging
except ImportError:
    from logger_config import setup_logging

logger = setup_logging("marketing_optimizer")

class MarketingCampaignOptimizer:
    """
    Evaluates financial ROI, margin elasticity, and volume efficiency across promotional campaigns.
    
    Working:
    - Aggregates sales transaction ledgers by `campaign_name`.
    - Computes realized margin percentage:
        Margin % = (Gross Profit Yield / Total Revenue Generated) * 100
    - Rates campaign efficiency:
        'Highly Efficient' if margin > 30% (healthy luxury volume lift offsets discount).
        'Insolvent Margin Loss' if margin <= 30% (excessive markdown eroding operating profit).
        
    Why Required:
    - Prevents "unprofitable volume growth" where flash promotions boost gross sales
      while diluting net profit dollars.
    """
    def __init__(self, sales_df: pd.DataFrame):
        """
        Initializes the optimizer with sales transaction history.
        
        Args:
            sales_df (pd.DataFrame): Dataframe containing transaction records with campaign tags.
        """
        self.sales = sales_df

    def evaluate_campaign_roi(self) -> Dict[str, Any]:
        """
        Analyzes performance metrics across all tracked promotional campaigns.
        
        Working:
        - Filters out non-promotional baseline transactions.
        - Calculates revenue contribution, volume moved, achieved margins, and efficiency ratings.
        
        Why Required:
        - Informs the marketing director and Shivi Deep Agent which campaign structures
          are delivering accretive cash flow.
        
        Returns:
            Dict[str, Any]: Ledger containing campaign revenue, profit, margin %, and efficiency ratings.
        """
        try:
            if 'is_promotional' not in self.sales.columns:
                return {"status": "No campaign field tracks discovered."}

            # Group performance parameters by tracking campaigns
            summary = self.sales.groupby('campaign_name').agg(
                total_revenue_generated=('total_revenue', 'sum'),
                total_cost_basis=('total_cost', 'sum'),
                units_moved_volume=('quantity', 'sum'), # Fixed column name from quantity_sold to quantity based on sales_ledger schema
                net_profit_yield=('gross_profit', 'sum')
            ).reset_index()

            campaign_analysis = []

            for _, row in summary.iterrows():
                name = row['campaign_name']
                if name == "None" or name is None:
                    continue

                revenue = row['total_revenue_generated']
                profit = row['net_profit_yield']
                margin = (profit / revenue) * 100 if revenue > 0 else 0.0

                campaign_analysis.append({
                    "campaign_name": name,
                    "revenue": round(float(revenue), 2),
                    "units_moved": int(row['units_moved_volume']),
                    "achieved_margin_pct": round(float(margin), 1),
                    "absolute_profit_contribution": round(float(profit), 2),
                    "efficiency_rating": "Highly Efficient (Strong volume offset margin compression)" if margin > 30 else "Insolvent Margin Loss (Reassess discount parameters)"
                })

            logger.info(f"Campaign ROI evaluation completed for {len(campaign_analysis)} campaigns.")
            return {"campaigns_performance_ledger": campaign_analysis}
        except Exception as e:
            logger.error(f"Error evaluating campaign ROI: {e}")
            return {"status": f"Error: {str(e)}", "campaigns_performance_ledger": []}
