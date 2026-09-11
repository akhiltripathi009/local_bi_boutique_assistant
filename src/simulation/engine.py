import random
import time
import sqlite3
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
try:
    from src.core.logger import setup_logging
    from src.core.catalog import CATALOG
    from src.data.db_manager import DatabaseManager
except ImportError:
    from logger_config import setup_logging
    # CATALOG imported at top-level
    # DatabaseManager imported at top-level


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
        self._cached_customers = []

    # Competitor brand pricing tier profiles
    COMPETITOR_TIERS = {
        "Velvet & Vine Boutique": (1.15, 1.35),     # Luxury Designer (+15% to +35%)
        "Avenue Apparel": (0.95, 1.08),             # Contemporary Mid-Tier (-5% to +8%)
        "Minimalist Thread Co.": (0.70, 0.85)       # Fast Fashion / Budget (-15% to -30%)
    }

    def _get_customer_pool(self):
        """Retrieves and caches the 20 VIP boutique customers for transaction attribution."""
        if not self._cached_customers:
            cust_df = self.db.get_all_customers()
            if not cust_df.empty:
                self._cached_customers = cust_df.to_dict('records')
        return self._cached_customers

    def inject_competitor_volatility(self, current_time: str) -> None:
        """
        Randomly generates competitor price fluctuations reflecting realistic brand tiers:
        - Velvet & Vine Boutique: Luxury Designer (+15% to +35%)
        - Avenue Apparel: Contemporary Mid-Tier (-5% to +8%)
        - Minimalist Thread Co.: Fast Fashion / Value (-15% to -30%)
        
        Args:
            current_time (str): Timestamp for the record.
        """
        try:
            if random.random() < 0.35:
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()

                v_pid = random.choice(list(self.catalog.keys()))
                v_prod_name = self.catalog[v_pid]["name"]
                v_my_price = self.catalog[v_pid]["price"]
                v_competitor = random.choice(list(self.COMPETITOR_TIERS.keys()))

                low_mult, high_mult = self.COMPETITOR_TIERS[v_competitor]
                variance_factor = random.uniform(low_mult, high_mult)
                new_competitor_price = round(v_my_price * variance_factor, 2)

                cursor.execute("""
                    INSERT INTO competitor_benchmarks (timestamp, product_id, product_name, your_price, competitor_name, competitor_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (current_time, v_pid, v_prod_name, v_my_price, v_competitor, new_competitor_price))
                conn.commit()
                conn.close()
                logger.debug(f"Tiered competitor price injected for {v_prod_name} [{v_competitor}]: ${new_competitor_price}")
        except Exception as e:
            logger.error(f"Error injecting competitor volatility: {e}")

    def process_tick(self, promo_discount: int, inventory: Dict[str, int]) -> Tuple[str, str, Optional[str]]:
        """
        Executes a single simulation cycle, handling sales, restocks, or idle states.
        All new customer transactions are attributed to the 20 seeded customers.
        
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

            # Check if active campaign exists if manual promo slider is 0
            active_camp = self.db.get_active_campaign()
            effective_discount = promo_discount
            campaign_name = "None"
            if effective_discount <= 0 and active_camp:
                effective_discount = int(active_camp.get("discount_pct", 0))
                campaign_name = active_camp.get("name", "Active Campaign")

            is_promo = 1 if effective_discount > 0 else 0
            if is_promo and campaign_name == "None":
                campaign_name = f"Flash Sale {effective_discount}% Off"

            event_roll = random.random()
            sale_threshold = 0.65 if not is_promo else min(0.85, 0.65 + (effective_discount / 100) * 0.30)

            # --- CHANNEL A: CUSTOMER TRANSACTION ROUTING ---
            if event_roll <= sale_threshold:
                pid = random.choice(list(self.catalog.keys()))
                item_controls = db_controls.get(pid, {"sales_enabled": True, "purchase_enabled": True, "max_stock": 100})

                final_price = round(self.catalog[pid]["price"] * (1 - (effective_discount / 100)), 2)
                cost_basis = self.catalog[pid]["cost"]

                if not item_controls["sales_enabled"]:
                    return f"⚠️ **BLOCKED SALE:** Customer tried buying {self.catalog[pid]['name']}, but sales are disabled.", "Blocked", pid

                if inventory.get(pid, 0) > 0:
                    inventory[pid] -= 1

                    # Select one of the 20 dummy customers
                    customer_pool = self._get_customer_pool()
                    if customer_pool:
                        customer = random.choice(customer_pool)
                        cust_id = int(customer["id"])
                        cust_name = customer["name"]
                        cust_email = customer["email"]
                        cust_phone = customer["phone"]
                        preferred_size = customer.get("preferred_size", "M")
                        purchased_size = preferred_size if preferred_size in ['S', 'M', 'L', 'XL'] else random.choice(['S', 'M', 'L', 'XL'])
                        tier_badge = customer.get("loyalty_tier", "VIP")
                    else:
                        cust_id = None
                        cust_name = "VIP Client"
                        cust_email = "client@boutique.com"
                        cust_phone = "+1-555-0100"
                        purchased_size = random.choice(['S', 'M', 'L', 'XL'])
                        tier_badge = "VIP"

                    sale_data = {
                        "timestamp": current_time,
                        "product_id": pid,
                        "product_name": self.catalog[pid]["name"],
                        "quantity": 1,
                        "unit_price": final_price,
                        "unit_cost": cost_basis,
                        "total_revenue": final_price,
                        "total_cost": cost_basis,
                        "gross_profit": round(final_price - cost_basis, 2),
                        "is_promotional": is_promo,
                        "campaign_name": campaign_name,
                        "customer_id": cust_id,
                        "customer_name": cust_name,
                        "customer_email": cust_email,
                        "customer_phone": cust_phone,
                        "size_purchased": purchased_size,
                        "channel": "In-Store Boutique"
                    }
                    self.db.save_sale(sale_data)

                    # Deduct stock ONLY from Shop Floor stock matrix (Warehouse Stock is isolated)
                    conn = sqlite3.connect(self.db.db_path)
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE size_matrix_stock 
                        SET stock_on_hand = MAX(0, stock_on_hand - 1) 
                        WHERE product_id = ? AND size_variant = ?
                    """, (pid, purchased_size))
                    conn.commit()
                    conn.close()

                    msg = f"🛍️ **{cust_name}** ({tier_badge}) purchased {self.catalog[pid]['name']} (Size {purchased_size}) for **${final_price:.2f}**"
                    logger.info(f"Sale: {cust_name} purchased {self.catalog[pid]['name']} (Size {purchased_size}) at ${final_price:.2f}")
                    return msg, "Sale", pid
                else:
                    return f"❌ **OUT OF STOCK:** Customer tried to buy {self.catalog[pid]['name']}, but item is empty.", "Blocked", pid


            # --- CHANNEL B: PROCUREMENT LOGISTICS RESTOCK ROUTING ---
            else:
                # Find items that actually need replenishment and have procurement enabled
                eligible_pids = [
                    p for p in self.catalog.keys()
                    if db_controls.get(p, {}).get("purchase_enabled", True)
                    and inventory.get(p, 0) < db_controls.get(p, {}).get("max_stock", 150)
                ]

                if eligible_pids:
                    # Sort by lowest stock balance to prioritize urgent replenishment
                    eligible_pids.sort(key=lambda p: inventory.get(p, 0))
                    # Pick from the most urgent styles needing replenishment
                    pid = random.choice(eligible_pids[:3])
                else:
                    pid = random.choice(list(self.catalog.keys()))

                item_controls = db_controls.get(pid, {"sales_enabled": True, "purchase_enabled": True, "max_stock": 100})

                if not item_controls["purchase_enabled"]:
                    return f"🚚 **BLOCKED RESTOCK:** Procurement delivery for {self.catalog[pid]['name']} rejected (Purchases Disabled).", "Blocked", pid

                current_stock = inventory.get(pid, 0)
                max_allowed = item_controls["max_stock"]

                if current_stock >= max_allowed:
                    return f"⚠️ **BLOCKED RESTOCK:** Rejected shipment of {self.catalog[pid]['name']}. Already at capacity limit ({current_stock}/{max_allowed} units).", "Blocked", pid

                restock_qty = min(20, max_allowed - current_stock)
                inventory[pid] = current_stock + restock_qty
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
                logger.info(f"Purchase: Received {restock_qty}x {self.catalog[pid]['name']}")
                return msg, "Purchase", pid

            return "⏱️ Background transaction checks running smoothly...", "Idle", None
        except Exception as e:
            logger.error(f"Error in simulation process_tick: {e}")
            return f"❌ **ENGINE ERROR:** {str(e)}", "Error", None
