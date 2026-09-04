import random
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from logger_config import setup_logging

logger = setup_logging("simulation_engine")

class SimulationEngine:
    """
    Simulates retail operations including customer sales and procurement restocks.
    Interacts with DatabaseManager to persist transaction logs and market benchmarks.
    """
    def __init__(self, catalog: Dict[str, Any], db_manager):
        """
        Initializes the SimulationEngine.
        
        Args:
            catalog (Dict): Product catalog configuration.
            db_manager (DatabaseManager): Initialized database manager instance.
        """
        self.catalog = catalog
        self.db = db_manager

    def inject_competitor_volatility(self, current_time: str) -> None:
        """
        Randomly generates competitor price fluctuations to simulate market dynamics.
        
        Args:
            current_time (str): Timestamp for the record.
        """
        try:
            if random.random() < 0.30:
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()

                v_pid = random.choice(list(self.catalog.keys()))
                v_prod_name = self.catalog[v_pid]["name"]
                v_my_price = self.catalog[v_pid]["price"]
                v_competitor = random.choice(["Velvet & Vine Boutique", "Avenue Apparel", "Minimalist Thread Co."])

                variance_factor = 1 + (random.choice([-1, 1]) * random.uniform(0.10, 0.25))
                new_competitor_price = round(v_my_price * variance_factor, 2)

                cursor.execute("""
                    INSERT INTO competitor_benchmarks (timestamp, product_id, product_name, your_price, competitor_name, competitor_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (current_time, v_pid, v_prod_name, v_my_price, v_competitor, new_competitor_price))
                conn.commit()
                conn.close()
                logger.debug(f"Competitor price injected for {v_prod_name}: {new_competitor_price}")
        except Exception as e:
            logger.error(f"Error injecting competitor volatility: {e}")

    def process_tick(self, promo_discount: int, inventory: Dict[str, int]) -> Tuple[str, str, Optional[str]]:
        """
        Executes a single simulation cycle, handling sales, restocks, or idle states.
        
        Args:
            promo_discount (int): Active promotional discount percentage.
            inventory (Dict): Mutable dictionary tracking current stock levels.
            
        Returns:
            Tuple[str, str, Optional[str]]: (Event description message, Event type tag, Product ID involved).
        """
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Inject competitor fluctuations
            self.inject_competitor_volatility(current_time)

            # Query active control settings from SQLite on every execution tick
            db_controls = self.db.get_all_circuit_controls()

            event_roll = random.random()
            is_promo = 1 if promo_discount > 0 else 0
            campaign_name = f"Flash Sale {promo_discount}% Off" if is_promo else "None"
            sale_threshold = 0.50 if not is_promo else (0.50 + (promo_discount / 100) * 0.50)

            # --- CHANNEL A: CUSTOMER TRANSACTION ROUTING ---
            if event_roll <= sale_threshold:
                pid = random.choice(list(self.catalog.keys()))
                item_controls = db_controls.get(pid, {"sales_enabled": True, "purchase_enabled": True, "max_stock": 100})

                final_price = round(self.catalog[pid]["price"] * (1 - (promo_discount / 100)), 2)
                cost_basis = self.catalog[pid]["cost"]

                if not item_controls["sales_enabled"]:
                    return f"⚠️ **BLOCKED SALE:** Customer tried buying {self.catalog[pid]['name']}, but sales are disabled.", "Blocked", pid

                if inventory[pid] > 0:
                    inventory[pid] -= 1

                    sale_data = {
                        "timestamp": current_time, "product_id": pid, "product_name": self.catalog[pid]["name"],
                        "quantity": 1, "unit_price": final_price, "unit_cost": cost_basis, "total_revenue": final_price,
                        "total_cost": cost_basis, "gross_profit": round(final_price - cost_basis, 2),
                        "is_promotional": is_promo, "campaign_name": campaign_name
                    }
                    self.db.save_sale(sale_data)

                    purchased_size = random.choice(['S', 'M', 'L', 'XL'])
                    conn = sqlite3.connect(self.db.db_path)
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE size_matrix_stock 
                        SET stock_on_hand = MAX(0, stock_on_hand - 1) 
                        WHERE product_id = ? AND size_variant = ?
                    """, (pid, purchased_size))
                    conn.commit()
                    conn.close()

                    msg = f"🛍️ Sold {self.catalog[pid]['name']} (Size {purchased_size}) at ${final_price:.2f} (Profit: ${sale_data['gross_profit']:.2f})"
                    logger.info(msg)
                    return msg, "Sale", pid
                else:
                    return f"❌ **OUT OF STOCK:** Customer tried to buy {self.catalog[pid]['name']}, but item is empty.", "Blocked", pid

            # --- CHANNEL B: PROCUREMENT LOGISTICS RESTOCK ROUTING ---
            elif event_roll > 0.85:
                pid = random.choice(list(self.catalog.keys()))
                item_controls = db_controls.get(pid, {"sales_enabled": True, "purchase_enabled": True, "max_stock": 100})

                if not item_controls["purchase_enabled"]:
                    return f"🚚 **BLOCKED RESTOCK:** Procurement delivery for {self.catalog[pid]['name']} rejected (Purchases Disabled).", "Blocked", pid

                current_stock = inventory[pid]
                max_allowed = item_controls["max_stock"]

                if current_stock >= max_allowed:
                    return f"⚠️ **BLOCKED RESTOCK:** Rejected shipment of {self.catalog[pid]['name']}. Already at capacity limit ({current_stock}/{max_allowed} units).", "Blocked", pid

                restock_qty = min(20, max_allowed - current_stock)
                inventory[pid] += restock_qty
                total_cost = restock_qty * self.catalog[pid]["cost"]

                purchase_data = {
                    "timestamp": current_time, "product_id": pid, "product_name": self.catalog[pid]["name"],
                    "quantity": restock_qty, "total_cost": total_cost
                }
                self.db.save_purchase(purchase_data)

                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                qty_per_size = restock_qty // 4 if restock_qty >= 4 else 1
                for size in ['S', 'M', 'L', 'XL']:
                    cursor.execute("""
                        UPDATE size_matrix_stock 
                        SET stock_on_hand = stock_on_hand + ? 
                        WHERE product_id = ? AND size_variant = ?
                    """, (qty_per_size, pid, size))
                conn.commit()
                conn.close()

                msg = f"🚚 Received {restock_qty}x {self.catalog[pid]['name']} at store warehouse."
                logger.info(msg)
                return msg, "Purchase", pid

            return "⏱️ Background transaction checks running smoothly...", "Idle", None
        except Exception as e:
            logger.error(f"Error in simulation process_tick: {e}")
            return f"❌ **ENGINE ERROR:** {str(e)}", "Error", None
