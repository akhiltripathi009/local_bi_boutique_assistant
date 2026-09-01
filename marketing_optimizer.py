import pandas as pd
from typing import Dict, Any


class MarketingCampaignOptimizer:
    def __init__(self, sales_df: pd.DataFrame):
        self.sales = sales_df

    def evaluate_campaign_roi(self) -> Dict[str, Any]:
        """Calculates Return on Investment (ROI) and changes in gross profit margin."""
        if 'is_promotional' not in self.sales.columns:
            return {"status": "No campaign field tracks discovered."}

        # Group performance parameters by tracking campaigns
        summary = self.sales.groupby('campaign_name').agg(
            total_revenue_generated=('total_revenue', 'sum'),
            total_cost_basis=('total_cost', 'sum'),
            units_sold_volume=('quantity_sold', 'sum'),
            net_profit_yield=('gross_profit', 'sum')
        ).reset_index()

        campaign_analysis = []

        for _, row in summary.iterrows():
            name = row['campaign_name']
            if name == "None" or name is None:
                continue

            margin = (row['net_profit_yield'] / row['total_revenue_generated']) * 100

            # Simple baseline comparison mechanism
            baseline = self.sales[self.sales['campaign_name'] == "None"]
            avg_baseline_price = baseline['unit_price'].mean() if not baseline.empty else 1.0

            campaign_analysis.append({
                "campaign_name": name,
                "revenue": round(row['total_revenue_generated'], 2),
                "units_moved": int(row['units_moved_volume']),
                "achieved_margin_pct": round(margin, 1),
                "absolute_profit_contribution": round(row['net_profit_yield'], 2),
                "efficiency_rating": "Highly Efficient (Strong volume offset margin compression)" if margin > 30 else "Insolvent Margin Loss (Reassess discount parameters)"
            })

        return {"campaigns_performance_ledger": campaign_analysis}
