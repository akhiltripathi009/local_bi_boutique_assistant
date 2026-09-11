"""
src/analytics/inventory.py
==========================
Data-driven inventory optimization, safety stock modeling, and reorder point (ROP) calculation engine.

Why Required:
- High-end fashion boutiques face severe financial risks from both understocking (lost sales and client dissatisfaction)
  and overstocking (tied-up working capital and post-season liquidation write-downs).
- Calculates statistical safety stocks and prescriptive replenishment recommendations based on actual sales velocities.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any

try:
    from src.core.logger import setup_logging
    from src.core.constants import OperationalThresholds
except ImportError:
    from logger_config import setup_logging
    from src.core.constants import OperationalThresholds

logger = setup_logging("inventory_insights")


class AdvancedInventoryManager:
    """
    Provides data-driven inventory optimization insights.
    
    Working:
    - Calculates daily demand variance and standard deviation from historical sales.
    - Computes statistical Safety Stock and Reorder Point (ROP) at a 95% service level:
        Safety Stock = Z * sqrt(Lead Time * StdDev^2)
        ROP = (Avg Daily Demand * Lead Time) + Safety Stock
    - Evaluates holding capital leakage on overstocked items:
        Capital Leak = Excess Units * (Unit Cost * Annual Holding Rate)
        
    Why Required:
    - Generates actionable replenishment and markdown alerts for store managers
      and autonomous Deep Agent watchdogs.
    """

    STATUS_OPTIMAL = "Optimal Stocking Level"
    STATUS_STOCKOUT_HAZARD = "Critical Stockout Hazard Alert"
    STATUS_OVERSTOCKED = "Dead Capital / Overstocked Surplus"

    def __init__(self, sales_df: pd.DataFrame):
        """
        Initializes the manager with sales transaction history.
        
        Args:
            sales_df (pd.DataFrame): Dataframe containing 'product_id', 'date' (or 'timestamp'), and quantity.
        """
        self.sales = sales_df.copy()
        if not self.sales.empty:
            date_col = 'date' if 'date' in self.sales.columns else ('timestamp' if 'timestamp' in self.sales.columns else None)
            if date_col:
                try:
                    self.sales['date'] = pd.to_datetime(self.sales[date_col])
                except Exception as e:
                    logger.error(f"Error converting sales dates to datetime: {e}")

    def calculate_stock_optimization(self, current_inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyzes current inventory and generates prescriptive actions for stock management.
        
        Working:
        - Iterates over current merchandise styles, computes daily demand velocity,
          evaluates ROP boundaries, and flags overstocked surplus or critical hazards.
          
        Why Required:
        - Informs the store team whether to order restocks, hold, or launch promotional markdowns.
        
        Args:
            current_inventory (List[Dict[str, Any]]): List of inventory status dictionaries.
            
        Returns:
            List[Dict[str, Any]]: Prescriptive optimization insights per product style.
        """
        try:
            optimized_inventory_insights = []

            for item in current_inventory:
                pid = item.get("product_id")
                if not pid:
                    continue

                # Calculate actual daily sales velocity variance
                qty_col = 'quantity_sold' if 'quantity_sold' in self.sales.columns else ('quantity' if 'quantity' in self.sales.columns else None)
                if qty_col and not self.sales.empty and 'product_id' in self.sales.columns and 'date' in self.sales.columns:
                    item_sales = self.sales[self.sales['product_id'] == pid]
                    daily_series = item_sales.groupby(item_sales['date'].dt.date)[qty_col].sum()
                    avg_daily_demand = daily_series.mean() if not daily_series.empty else 0.5
                    std_daily_demand = daily_series.std() if len(daily_series) > 1 else 0.1
                else:
                    avg_daily_demand = 0.5
                    std_daily_demand = 0.1

                # Operational Parameters from centralized constants
                avg_lead_time_days = OperationalThresholds.DEFAULT_LEAD_TIME_DAYS
                service_factor_95 = OperationalThresholds.SERVICE_FACTOR_95_PCT

                # Reorder Point (ROP) Calculation
                demand_during_lead_time = avg_daily_demand * avg_lead_time_days
                safety_stock = service_factor_95 * np.sqrt(avg_lead_time_days * (std_daily_demand ** 2))
                calculated_reorder_point = demand_during_lead_time + safety_stock

                # Inventory health evaluation
                stock_level = item.get("current_stock_level", 0)
                unit_cost = item.get("unit_cost", 0.0)
                holding_cost_annual = unit_cost * OperationalThresholds.ANNUAL_HOLDING_COST_RATE

                status = self.STATUS_OPTIMAL
                action = "Monitor standard depletion updates."
                capital_leak = 0.0

                reorder_qty = item.get('reorder_qty', OperationalThresholds.DEFAULT_RESTOCK_BATCH_QTY)
                if stock_level <= calculated_reorder_point:
                    status = self.STATUS_STOCKOUT_HAZARD
                    action = f"Generate immediate restock replenishment order of {reorder_qty} units."
                elif stock_level > (calculated_reorder_point * 2.5):
                    status = self.STATUS_OVERSTOCKED
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
