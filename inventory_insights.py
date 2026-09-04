import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any
from logger_config import setup_logging

logger = setup_logging("inventory_insights")

class AdvancedInventoryManager:
    """
    Provides data-driven inventory optimization insights.
    Calculates safety stock, reorder points, and flags overstocked/understocked items.
    """
    def __init__(self, sales_df: pd.DataFrame):
        """
        Initializes the manager with sales history.
        
        Args:
            sales_df (pd.DataFrame): Dataframe containing 'product_id', 'date', and 'quantity_sold'.
        """
        self.sales = sales_df
        try:
            self.sales['date'] = pd.to_datetime(self.sales['date'])
        except Exception as e:
            logger.error(f"Error converting sales dates to datetime: {e}")

    def calculate_stock_optimization(self, current_inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyzes current inventory and generates prescriptive actions for stock management.
        
        Args:
            current_inventory (List[Dict]): List of inventory status dictionaries.
            
        Returns:
            List[Dict]: List of optimization insights per product.
        """
        try:
            optimized_inventory_insights = []

            for item in current_inventory:
                pid = item.get("product_id")
                if not pid:
                    continue

                # Calculate actual daily sales velocity variance
                item_sales = self.sales[self.sales['product_id'] == pid]
                daily_series = item_sales.groupby(item_sales['date'].dt.date)['quantity_sold'].sum()

                avg_daily_demand = daily_series.mean() if not daily_series.empty else 0.5
                std_daily_demand = daily_series.std() if len(daily_series) > 1 else 0.1

                # Operational Parameters
                avg_lead_time_days = 3.0
                service_factor_95 = 1.65  # Statistical Z-score for 95% service level protection

                # Reorder Point (ROP) Calculation
                demand_during_lead_time = avg_daily_demand * avg_lead_time_days
                safety_stock = service_factor_95 * np.sqrt(avg_lead_time_days * (std_daily_demand ** 2))
                calculated_reorder_point = demand_during_lead_time + safety_stock

                # inventory health evaluation
                stock_level = item.get("current_stock_level", 0)
                unit_cost = item.get("unit_cost", 0.0)
                holding_cost_annual = unit_cost * 0.25

                status = "Optimal Stocking Level"
                action = "Monitor standard depletion updates."
                capital_leak = 0.0

                if stock_level <= calculated_reorder_point:
                    status = "Critical Stockout Hazard Alert"
                    action = f"Generate immediate restock replenishment order of {item.get('reorder_qty', 20)} units."
                elif stock_level > (calculated_reorder_point * 2.5):
                    status = "Dead Capital / Overstocked Surplus"
                    action = "Run a targeted marketing discount promotion campaign to unlock tied up cash flow."
                    excess_units = stock_level - (calculated_reorder_point * 2)
                    capital_leak = excess_units * holding_cost_annual

                optimized_inventory_insights.append({
                    "product_name": item.get("product_name", "Unknown"),
                    "current_stock": stock_level,
                    "recommended_reorder_point": int(np.ceil(calculated_reorder_point)),
                    "status_evaluation": status,
                    "prescriptive_action": action,
                    "estimated_annual_holding_leak": round(float(capital_leak), 2)
                })

            logger.info(f"Inventory optimization analysis completed for {len(optimized_inventory_insights)} products.")
            return optimized_inventory_insights
        except Exception as e:
            logger.error(f"Error calculating stock optimization: {e}")
            return []
