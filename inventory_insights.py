import numpy as np
import pandas as pd
from typing import Dict, List, Any


class AdvancedInventoryManager:
    def __init__(self, sales_df: pd.DataFrame):
        self.sales = sales_df
        self.sales['date'] = pd.to_datetime(self.sales['date'])

    def calculate_stock_optimization(self, current_inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculates safety stock thresholds using standard demand variations."""
        optimized_inventory_insights = []

        for item in current_inventory:
            pid = item["product_id"]

            # Calculate actual daily sales velocity variance
            item_sales = self.sales[self.sales['product_id'] == pid]
            daily_series = item_sales.groupby(item_sales['date'].dt.date)['quantity_sold'].sum()

            avg_daily_demand = daily_series.mean() if not daily_series.empty else 0.5
            std_daily_demand = daily_series.std() if len(daily_series) > 1 else 0.1

            # Constants
            avg_lead_time_days = 3.0
            service_factor_95 = 1.65  # Statistical Z-score for 95% protection against running out of stock

            # Demand during lead time calculation
            demand_during_lead_time = avg_daily_demand * avg_lead_time_days

            # Safety Stock calculation formula
            safety_stock = service_factor_95 * np.sqrt(avg_lead_time_days * (std_daily_demand ** 2))
            calculated_reorder_point = demand_during_lead_time + safety_stock

            # Check current inventory health
            stock_level = item["current_stock_level"]
            holding_cost_annual = item["unit_cost"] * 0.25  # Assuming 25% annual holding cost rate

            status = "Optimal Stocking Level"
            action = "Monitor standard depletion updates."
            capital_leak = 0.0

            if stock_level <= calculated_reorder_point:
                status = "Critical Stockout Hazard Alert"
                action = f"Generate immediate restock replenishment order of {item['reorder_qty']} units."
            elif stock_level > (calculated_reorder_point * 2.5):
                status = "Dead Capital / Overstocked Surplus"
                action = "Run a targeted marketing discount promotion campaign to unlock tied up cash flow."
                excess_units = stock_level - (calculated_reorder_point * 2)
                capital_leak = excess_units * holding_cost_annual

            optimized_inventory_insights.append({
                "product_name": item["product_name"],
                "current_stock": stock_level,
                "recommended_reorder_point": int(np.ceil(calculated_reorder_point)),
                "status_evaluation": status,
                "prescriptive_action": action,
                "estimated_annual_holding_leak": round(capital_leak, 2)
            })

        return optimized_inventory_insights
