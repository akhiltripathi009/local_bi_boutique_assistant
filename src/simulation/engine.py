"""
src/simulation/engine.py
========================
Discrete event simulation engine for retail boutique store operations.

Why Required:
- Real-world retail analytics requires realistic transactional throughput (sales, restocks,
  markdown elasticities, broken curves) to power executive dashboards and agent triggers.
- In a local or development environment without connected POS hardware, this engine generates
  high-fidelity, deterministic synthetic telemetry persisted into SQLite.
- Simulates realistic competitor pricing volatility across tiered retail benchmarks
  to test dynamic margin optimization strategies.
"""

import random
import time
import sqlite3
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List

try:
    from src.core.logger import setup_logging
    from src.core.catalog import CATALOG
    from src.core.constants import (
        DBTable,
        SimEventType,
        SalesChannel,
        ApparelSize,
        CompetitorBrands,
        BrandDefaults,
        OperationalThresholds,
        LoyaltyTier,
    )
    from src.data.db_manager import DatabaseManager
except ImportError:
    from logger_config import setup_logging
    from src.core.constants import (
        DBTable,
        SimEventType,
        SalesChannel,
        ApparelSize,
        CompetitorBrands,
        BrandDefaults,
        OperationalThresholds,
        LoyaltyTier,
    )


logger = setup_logging("simulation_engine")


class SimulationEngine:
    """
    Simulates retail operations including customer sales and procurement restocks.
    
    Working:
    - Maintains customer pools, checks circuit-breaker thresholds, and resolves promotional markdowns.
    - Routes simulation ticks into two probabilistic channels:
        Channel A: Patron checkout (sales ledger entry, customer attribution, shop floor stock decrement).
        Channel B: Procurement logistics (purchase ledger entry, warehouse/shop replenishment).
    - Periodically injects competitor pricing changes into the competitor_benchmarks table.
    
    Why Required:
    - Connects discrete event simulation with SQLite persistence, feeding the live BI dashboard,
      KPI charts, and autonomous agent watchdog triggers with authentic operational behavior.
    """

    # Competitor brand pricing tier profiles from centralized constants
    COMPETITOR_TIERS = CompetitorBrands.TIER_MULTIPLIERS

    def __init__(self, catalog: Dict[str, Any], db_manager):
        """
        Initializes the SimulationEngine with active catalog and database connectivity.
        
        Args:
            catalog (Dict[str, Any]): Product catalog specification dictionary.
            db_manager (DatabaseManager): Initialized database manager instance.
        """
        self.catalog = catalog
        self.db = db_manager
        self._cached_customers: List[Dict[str, Any]] = []

    def _get_customer_pool(self) -> List[Dict[str, Any]]:
        """
        Retrieves and caches the 20 VIP boutique customers for transaction attribution.
        
        Working:
        - Lazily loads seeded VIP customer profiles from SQLite on first invocation.
        - Keeps an in-memory cache to avoid repeated disk reads during high-frequency simulation ticks.
        
        Why Required:
        - Ensures every simulated sale is attributed to a genuine patron profile (linking lifetime spend,
          sizing preferences, and loyalty tier history).
          
        Returns:
            List[Dict[str, Any]]: List of patron record dictionaries.
        """
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
        
        Working:
        - Executes with ~35% probability per simulation tick.
        - Selects a random catalog product and competitor benchmark tier.
        - Calculates the adjusted benchmark price and inserts a new benchmark row into SQLite.
        
        Why Required:
        - Recreates real-world market price volatility so dynamic pricing models and CPI
          (Competitor Price Index) analytics produce realistic margin opportunities.
        
        Args:
            current_time (str): Formatted timestamp (YYYY-MM-DD HH:MM:SS) for the record.
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

                cursor.execute(f"""
                    INSERT INTO {DBTable.COMPETITOR_BENCHMARKS} 
                    (timestamp, product_id, product_name, your_price, competitor_name, competitor_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (current_time, v_pid, v_prod_name, v_my_price, v_competitor, new_competitor_price))
                conn.commit()
                conn.close()
                logger.debug(f"Tiered competitor price injected for {v_prod_name} [{v_competitor}]: ${new_competitor_price}")
        except Exception as e:
            logger.error(f"Error injecting competitor volatility: {e}")

    def process_tick(self, promo_discount: int, inventory: Dict[str, int]) -> Tuple[str, str, Optional[str]]:
        """
        Executes a single discrete simulation cycle, routing transactions to sales, restocks, or idle states.
        
        Working:
        1. Injects competitor pricing volatility.
        2. Resolves active promotional campaigns and discount percentages.
        3. Evaluates circuit breaker controls (sales enabled, procurement enabled, max capacity).
        4. Channel A (Sale): Randomly picks a patron, decrements shop floor inventory & size matrix,
           calculates margins, and writes to `sales_ledger`.
        5. Channel B (Procurement): Identifies styles needing restock, checks capacity limits,
           increments inventory & size matrix, and writes to `purchase_ledger`.
           
        Why Required:
        - Serves as the operational heart of the Live Operations pipeline, driving the SSE feed,
          updating in-memory state, and keeping the analytical database continuously refreshed.
        
        Args:
            promo_discount (int): Active promotional markdown percentage (0-50%).
            inventory (Dict[str, int]): Mutable in-memory dictionary tracking current stock levels.
            
        Returns:
            Tuple[str, str, Optional[str]]:
                - Human-readable event description message.
                - Event type category string (SimEventType.SALE, SimEventType.PURCHASE, etc.).
                - Product SKU ID involved in the event, or None if idle.
        """
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Inject competitor fluctuations
            self.inject_competitor_volatility(current_time)

            # Query active circuit breaker controls from SQLite on every execution tick
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
                    return (
                        f"⚠️ **BLOCKED SALE:** Customer tried buying {self.catalog[pid]['name']}, but sales are disabled.",
                        SimEventType.BLOCKED,
                        pid
                    )

                if inventory.get(pid, 0) > 0:
                    inventory[pid] -= 1

                    # Select one of the seeded VIP patrons
                    customer_pool = self._get_customer_pool()
                    if customer_pool:
                        customer = random.choice(customer_pool)
                        cust_id = int(customer["id"])
                        cust_name = customer["name"]
                        cust_email = customer["email"]
                        cust_phone = customer["phone"]
                        preferred_size = customer.get("preferred_size", ApparelSize.DEFAULT_SIZE)
                        purchased_size = preferred_size if preferred_size in ApparelSize.ALL_SIZES else random.choice(ApparelSize.ALL_SIZES)
                        tier_badge = customer.get("loyalty_tier", LoyaltyTier.VIP)
                    else:
                        cust_id = None
                        cust_name = BrandDefaults.FALLBACK_CLIENT_NAME
                        cust_email = BrandDefaults.FALLBACK_CLIENT_EMAIL
                        cust_phone = BrandDefaults.FALLBACK_CLIENT_PHONE
                        purchased_size = random.choice(ApparelSize.ALL_SIZES)
                        tier_badge = LoyaltyTier.VIP

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
                        "channel": SalesChannel.IN_STORE
                    }
                    self.db.save_sale(sale_data)

                    # Deduct stock ONLY from Shop Floor stock matrix (Warehouse Stock is isolated)
                    conn = sqlite3.connect(self.db.db_path)
                    cursor = conn.cursor()
                    cursor.execute(f"""
                        UPDATE {DBTable.SIZE_MATRIX_STOCK} 
                        SET stock_on_hand = MAX(0, stock_on_hand - 1) 
                        WHERE product_id = ? AND size_variant = ?
                    """, (pid, purchased_size))
                    conn.commit()
                    conn.close()

                    msg = f"🛍️ **{cust_name}** ({tier_badge}) purchased {self.catalog[pid]['name']} (Size {purchased_size}) for **${final_price:.2f}**"
                    logger.info(f"Sale: {cust_name} purchased {self.catalog[pid]['name']} (Size {purchased_size}) at ${final_price:.2f}")
                    return msg, SimEventType.SALE, pid
                else:
                    return (
                        f"❌ **OUT OF STOCK:** Customer tried to buy {self.catalog[pid]['name']}, but item is empty.",
                        SimEventType.BLOCKED,
                        pid
                    )

            # --- CHANNEL B: PROCUREMENT LOGISTICS RESTOCK ROUTING ---
            else:
                # Find items that actually need replenishment and have procurement enabled
                eligible_pids = [
                    p for p in self.catalog.keys()
                    if db_controls.get(p, {}).get("purchase_enabled", True)
                    and inventory.get(p, 0) < db_controls.get(p, {}).get("max_stock", OperationalThresholds.DEFAULT_MAX_STOCK)
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
                    return (
                        f"🚚 **BLOCKED RESTOCK:** Procurement delivery for {self.catalog[pid]['name']} rejected (Purchases Disabled).",
                        SimEventType.BLOCKED,
                        pid
                    )

                current_stock = inventory.get(pid, 0)
                max_allowed = item_controls["max_stock"]

                if current_stock >= max_allowed:
                    return (
                        f"⚠️ **BLOCKED RESTOCK:** Rejected shipment of {self.catalog[pid]['name']}. Already at capacity limit ({current_stock}/{max_allowed} units).",
                        SimEventType.BLOCKED,
                        pid
                    )

                restock_qty = min(OperationalThresholds.DEFAULT_RESTOCK_BATCH_QTY, max_allowed - current_stock)
                inventory[pid] = current_stock + restock_qty
                total_cost = restock_qty * self.catalog[pid]["cost"]

                purchase_data = {
                    "timestamp": current_time,
                    "product_id": pid,
                    "product_name": self.catalog[pid]["name"],
                    "quantity": restock_qty,
                    "total_cost": total_cost
                }
                self.db.save_purchase(purchase_data)

                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                qty_per_size = restock_qty // len(ApparelSize.ALL_SIZES) if restock_qty >= len(ApparelSize.ALL_SIZES) else 1
                for size in ApparelSize.ALL_SIZES:
                    cursor.execute(f"""
                        UPDATE {DBTable.SIZE_MATRIX_STOCK} 
                        SET stock_on_hand = stock_on_hand + ? 
                        WHERE product_id = ? AND size_variant = ?
                    """, (qty_per_size, pid, size))
                conn.commit()
                conn.close()

                msg = f"🚚 Received {restock_qty}x {self.catalog[pid]['name']} at store warehouse."
                logger.info(f"Purchase: Received {restock_qty}x {self.catalog[pid]['name']}")
                return msg, SimEventType.PURCHASE, pid

            return "⏱️ Background transaction checks running smoothly...", SimEventType.IDLE, None
        except Exception as e:
            logger.error(f"Error in simulation process_tick: {e}")
            return f"❌ **ENGINE ERROR:** {str(e)}", SimEventType.ERROR, None
