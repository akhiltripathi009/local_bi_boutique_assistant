import sqlite3
import pandas as pd
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
try:
    from src.core.logger import setup_logging
    from src.core.config import DB_PATH
    from src.core.catalog import CATALOG, register_product
except ImportError:
    from logger_config import setup_logging
    # CATALOG imported at top-level
    DB_PATH = "boutique_bi.db"


logger = setup_logging("database_manager")

class DatabaseManager:
    """
    Core engine for managing all SQLite database interactions.
    Handles schema verification, transaction logging (sales/purchases), 
    competitor benchmarking, and stock level tracking.
    """
    def __init__(self, db_path: str = DB_PATH):
        """
        Initializes the DatabaseManager with a specific database path.
        
        Args:
            db_path (str): The file path to the SQLite database. Defaults to "boutique_bi.db".
        """
        self.db_path = db_path
        try:
            self._verify_schema()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Critical error during database initialization: {e}")
            raise

    def _verify_schema(self) -> None:
        """
        Verifies and enforces the database schema. 
        Creates all required tables and seeds initial data if the database is new.
        Provides self-healing guard rails for missing structural components.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Sales Ledger: Core transaction history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    unit_cost REAL NOT NULL,
                    total_revenue REAL NOT NULL,
                    total_cost REAL NOT NULL,
                    gross_profit REAL NOT NULL,
                    is_promotional INTEGER NOT NULL,
                    campaign_name TEXT NOT NULL
                )
            """)

            # Non-destructively add customer attribution columns to sales_ledger if missing
            cursor.execute("PRAGMA table_info(sales_ledger)")
            sales_cols = {col[1] for col in cursor.fetchall()}
            if "customer_id" not in sales_cols:
                cursor.execute("ALTER TABLE sales_ledger ADD COLUMN customer_id INTEGER")
            if "customer_name" not in sales_cols:
                cursor.execute("ALTER TABLE sales_ledger ADD COLUMN customer_name TEXT")
            if "customer_email" not in sales_cols:
                cursor.execute("ALTER TABLE sales_ledger ADD COLUMN customer_email TEXT")
            if "customer_phone" not in sales_cols:
                cursor.execute("ALTER TABLE sales_ledger ADD COLUMN customer_phone TEXT")
            if "size_purchased" not in sales_cols:
                cursor.execute("ALTER TABLE sales_ledger ADD COLUMN size_purchased TEXT")
            if "channel" not in sales_cols:
                cursor.execute("ALTER TABLE sales_ledger ADD COLUMN channel TEXT DEFAULT 'In-Store'")

            # Purchase Ledger: Supply chain restock history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchase_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    total_cost REAL NOT NULL
                )
            """)

            # Competitor Benchmarks: Market pricing index storage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS competitor_benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    your_price REAL NOT NULL,
                    competitor_name TEXT NOT NULL,
                    competitor_price REAL NOT NULL
                )
            """)

            # Size Matrix Stock: Active Shop Floor inventory tracking by size variant
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS size_matrix_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    size_variant TEXT NOT NULL,
                    stock_on_hand INTEGER NOT NULL,
                    UNIQUE(product_id, size_variant)
                )
            """)

            # Warehouse Stock: Isolated warehouse backroom inventory
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS warehouse_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    size_variant TEXT NOT NULL,
                    stock_on_hand INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(product_id, size_variant)
                )
            """)

            # Stock Transfers: Audit ledger of movements between Shop and Warehouse
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    size_variant TEXT NOT NULL,
                    source_location TEXT NOT NULL,
                    dest_location TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    performed_by TEXT NOT NULL DEFAULT 'Portal Admin',
                    notes TEXT
                )
            """)

            # Customers: VIP Customer CRM Registry (20 Dummy Customers)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    email TEXT NOT NULL,
                    dob TEXT NOT NULL,
                    preferred_size TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    style_preference TEXT NOT NULL,
                    loyalty_tier TEXT NOT NULL DEFAULT 'Silver',
                    total_spend REAL NOT NULL DEFAULT 0.0,
                    purchase_count INTEGER NOT NULL DEFAULT 0,
                    joined_date TEXT NOT NULL,
                    opt_in_whatsapp INTEGER NOT NULL DEFAULT 1,
                    opt_in_email INTEGER NOT NULL DEFAULT 1
                )
            """)

            # Campaigns: Custom Promotional Campaigns Hub
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    discount_pct REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Active',
                    target_category TEXT DEFAULT 'All Categories',
                    banner_tagline TEXT,
                    launched_by TEXT DEFAULT 'Marketing Admin'
                )
            """)

            # Agent Communications: Log of Email & WhatsApp dispatches by Shivi Deep Agent
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_communications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    customer_id INTEGER,
                    customer_name TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    subject TEXT,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Delivered',
                    campaign_id INTEGER
                )
            """)

            # Agent Memory: Semantic & Episodic Memory store for Shivi
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    memory_key TEXT NOT NULL,
                    memory_value TEXT NOT NULL
                )
            """)

            # Agent Approval Queue: Human-in-the-Loop (HITL) Steering Queue
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_approval_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    requested_by TEXT DEFAULT 'Shivi Deep Agent',
                    reviewed_at TEXT,
                    review_notes TEXT
                )
            """)

            # Custom Products: Dynamic registry for user-added catalog items
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS custom_products (
                    product_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    cost REAL NOT NULL,
                    price REAL NOT NULL,
                    color TEXT NOT NULL,
                    category TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # Store Circuit Controls: Operational toggles and safety limits
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS store_circuit_controls (
                    product_id TEXT PRIMARY KEY,
                    sales_enabled INTEGER NOT NULL DEFAULT 1,
                    purchase_enabled INTEGER NOT NULL DEFAULT 1,
                    max_stock INTEGER NOT NULL DEFAULT 100
                )
            """)

            # Seed initial shop size matrix & circuit controls
            try:
                for pid in CATALOG:
                    for size in ['S', 'M', 'L', 'XL']:
                        initial_stock = 0 if pid.startswith("P") and pid[1:].isdigit() and int(pid[1:]) >= 16 else 15
                        cursor.execute("""
                            INSERT OR IGNORE INTO size_matrix_stock (product_id, size_variant, stock_on_hand)
                            VALUES (?, ?, ?)
                        """, (pid, size, initial_stock))

                        cursor.execute("""
                            INSERT OR IGNORE INTO store_circuit_controls (product_id, sales_enabled, purchase_enabled, max_stock)
                            VALUES (?, 1, 1, 100)
                        """, (pid,))
            except Exception as e:
                logger.error(f"Error seeding initial database values: {e}")

            conn.commit()

            # Seed 20 dummy customers, initial warehouse inventory, campaigns, and custom products
            self._seed_20_dummy_customers_internal(conn)
            self._seed_warehouse_stock_internal(conn)
            self._seed_default_campaigns_internal(conn)
            self._load_custom_products_internal(conn)

            conn.close()
            logger.info("Database schema verification completed successfully.")
        except sqlite3.Error as e:
            logger.error(f"Database schema verification failed: {e}")
            raise

    def save_sale(self, data: Dict[str, Any]) -> None:
        """
        Records a completed customer transaction into the sales ledger.
        Maintains backward compatibility while attaching customer attribution if provided.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            c_id = data.get('customer_id')
            c_name = data.get('customer_name')
            c_email = data.get('customer_email')
            c_phone = data.get('customer_phone')
            c_size = data.get('size_purchased')
            c_channel = data.get('channel', 'In-Store')

            cursor.execute("""
                INSERT INTO sales_ledger 
                (timestamp, product_id, product_name, quantity, unit_price, unit_cost, total_revenue, total_cost, gross_profit, is_promotional, campaign_name, customer_id, customer_name, customer_email, customer_phone, size_purchased, channel)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data['timestamp'], data['product_id'], data['product_name'], data['quantity'], data['unit_price'],
                  data['unit_cost'], data['total_revenue'], data['total_cost'], data['gross_profit'],
                  data['is_promotional'], data['campaign_name'], c_id, c_name, c_email, c_phone, c_size, c_channel))

            # If customer attribution exists, update customer total spend & purchase count
            if c_id:
                cursor.execute("""
                    UPDATE customers 
                    SET total_spend = total_spend + ?,
                        purchase_count = purchase_count + 1
                    WHERE id = ? OR customer_code = ?
                """, (data['total_revenue'], c_id, str(c_id)))

            conn.commit()
            conn.close()
            logger.debug(f"Sale recorded for {data['product_name']} ({data['product_id']}) attributed to {c_name or 'Walk-in'}")
        except sqlite3.Error as e:
            logger.error(f"Failed to save sale data for {data.get('product_id')}: {e}")


    def save_purchase(self, data: Dict[str, Any]) -> None:
        """
        Records a stock procurement delivery into the purchase ledger.
        
        Args:
            data (Dict): Dictionary containing keys: timestamp, product_id, product_name, 
                        quantity, total_cost.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO purchase_ledger (timestamp, product_id, product_name, quantity, total_cost)
                VALUES (?, ?, ?, ?, ?)
            """, (data['timestamp'], data['product_id'], data['product_name'], data['quantity'], data['total_cost']))
            conn.commit()
            conn.close()
            logger.debug(f"Purchase recorded for {data['product_name']} ({data['product_id']})")
        except sqlite3.Error as e:
            logger.error(f"Failed to save purchase data for {data.get('product_id')}: {e}")

    def fetch_logs(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """
        Retrieves recent activity logs from a specific table.
        
        Args:
            table_name (str): Name of the table to query (e.g., 'sales_ledger').
            limit (int): Number of most recent records to return. Defaults to 5.
            
        Returns:
            pd.DataFrame: A pandas DataFrame containing the requested log records.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT {limit}", conn)
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Error fetching logs from {table_name}: {e}")
            return pd.DataFrame()

    def get_total_historical_revenue(self) -> float:
        """
        Calculates the cumulative gross revenue across all recorded sales.
        
        Returns:
            float: Total revenue value.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(total_revenue) FROM sales_ledger")
            result = cursor.fetchone()
            conn.close()
            return float(result[0]) if result and result[0] is not None else 0.0
        except Exception as e:
            logger.error(f"Error calculating total historical revenue: {e}")
            return 0.0

    def get_average_gross_margin(self) -> float:
        """
        Calculates the overall gross margin percentage based on profit vs revenue.
        
        Returns:
            float: Average gross margin percentage.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(gross_profit), SUM(total_revenue) FROM sales_ledger")
            result = cursor.fetchone()
            conn.close()
            if result and result[0] is not None and result[1] is not None and result[1] > 0:
                return (result[0] / result[1]) * 100
            return 54.2 # Default industry benchmark
        except Exception as e:
            logger.error(f"Error calculating average gross margin: {e}")
            return 54.2

    def seed_competitor_benchmarks_if_needed(self, force_refresh: bool = False) -> None:
        """
        Populates or re-synchronizes the competitor_benchmarks table with realistic brand tiers:
        - Velvet & Vine Boutique (Luxury Tier: +15% to +35%)
        - Avenue Apparel (Contemporary Mid-Tier: -5% to +8%)
        - Minimalist Thread Co. (Fast Fashion / Budget: -15% to -30%)
        
        Guarantees realistic market spread with authentic Underpriced Hazards and Premium opportunities.
        """
        try:
            # CATALOG imported at top-level
            from datetime import datetime
            import random

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check existing count and distinct competitors
            cursor.execute("SELECT COUNT(DISTINCT product_id), COUNT(DISTINCT competitor_name) FROM competitor_benchmarks")
            p_count, c_count = cursor.fetchone()

            if not force_refresh and p_count >= len(CATALOG) and c_count >= 3:
                conn.close()
                return

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Strategic market divergence rules for realistic luxury retail benchmarks
            market_biases = {
                "P002": {"Velvet & Vine Boutique": 1.38, "Avenue Apparel": 1.15, "Minimalist Thread Co.": 0.95}, # Silk Slip Skirt: strongly underpriced
                "P008": {"Velvet & Vine Boutique": 1.35, "Avenue Apparel": 1.12, "Minimalist Thread Co.": 0.88}, # Trench Coat: underpriced
                "P009": {"Velvet & Vine Boutique": 1.30, "Avenue Apparel": 1.14, "Minimalist Thread Co.": 0.90}, # Boho Maxi: underpriced
                "P003": {"Velvet & Vine Boutique": 1.12, "Avenue Apparel": 0.85, "Minimalist Thread Co.": 0.65}, # Knit Tank: premium positioned
                "P011": {"Velvet & Vine Boutique": 1.15, "Avenue Apparel": 0.88, "Minimalist Thread Co.": 0.68}, # Cable Vest: premium positioned
            }

            competitor_defaults = {
                "Velvet & Vine Boutique": (1.18, 1.32),
                "Avenue Apparel": (0.96, 1.06),
                "Minimalist Thread Co.": (0.72, 0.84)
            }

            for pid, info in CATALOG.items():
                p_name = info["name"]
                my_price = info["price"]
                for comp_name, (min_v, max_v) in competitor_defaults.items():
                    if pid in market_biases and comp_name in market_biases[pid]:
                        comp_price = round(my_price * market_biases[pid][comp_name], 2)
                    else:
                        comp_price = round(my_price * random.uniform(min_v, max_v), 2)

                    cursor.execute("""
                        INSERT INTO competitor_benchmarks (timestamp, product_id, product_name, your_price, competitor_name, competitor_price)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (now_str, pid, p_name, my_price, comp_name, comp_price))

            conn.commit()
            conn.close()
            logger.info("Competitor benchmarks seeded successfully with realistic brand tiers!")
        except Exception as e:
            logger.error(f"Error seeding competitor benchmarks: {e}")

    def fetch_dynamic_competitor_pricing(self) -> pd.DataFrame:
        """
        Aggregates the latest market pricing benchmarks per competitor and product.
        Computes store-wide and style-level Price Indices, position flags, recommended prices,
        and potential margin gaps.
        
        Returns:
            pd.DataFrame: High-density dataframe with product attributes, competitor prices,
                          market average, price index, position, and recommended pricing.
        """
        try:
            self._verify_schema()
            self.seed_competitor_benchmarks_if_needed()
            # CATALOG imported at top-level

            conn = sqlite3.connect(self.db_path)
            # Fetch latest price record for each (product_id, competitor_name)
            query = """
                SELECT c.product_id, c.product_name, c.your_price, c.competitor_name, c.competitor_price, c.timestamp
                FROM competitor_benchmarks c
                INNER JOIN (
                    SELECT product_id, competitor_name, MAX(id) as max_id
                    FROM competitor_benchmarks
                    GROUP BY product_id, competitor_name
                ) latest ON c.id = latest.max_id
            """
            raw_df = pd.read_sql_query(query, conn)
            conn.close()

            if raw_df.empty:
                logger.warning("No competitor benchmarks found after seeding attempt.")
                return pd.DataFrame()

            # Pivot to wide format: 1 entry per product
            products = {}
            for _, row in raw_df.iterrows():
                pid = str(row["product_id"])
                pname = row["product_name"]
                y_price = float(row["your_price"])
                cname = row["competitor_name"]
                cprice = float(row["competitor_price"])

                if pid not in products:
                    cat_info = CATALOG.get(pid, {})
                    cost = cat_info.get("cost", round(y_price * 0.45, 2))
                    category = cat_info.get("category", "Apparel")
                    # Prioritize active catalog price if present
                    active_price = cat_info.get("price", y_price)
                    products[pid] = {
                        "product_id": pid,
                        "product_name": pname,
                        "category": category,
                        "cost": cost,
                        "your_price": active_price,
                        "velvet_vine_price": None,
                        "avenue_price": None,
                        "minimalist_price": None,
                        "competitor_prices": []
                    }

                if "Velvet" in cname:
                    products[pid]["velvet_vine_price"] = cprice
                elif "Avenue" in cname:
                    products[pid]["avenue_price"] = cprice
                elif "Minimalist" in cname:
                    products[pid]["minimalist_price"] = cprice
                products[pid]["competitor_prices"].append(cprice)

            # Build enriched dataframe rows
            rows = []
            for pid, d in products.items():
                c_prices = d["competitor_prices"]
                avg_market = round(sum(c_prices) / len(c_prices), 2) if c_prices else d["your_price"]
                min_market = round(min(c_prices), 2) if c_prices else d["your_price"]
                max_market = round(max(c_prices), 2) if c_prices else d["your_price"]
                price_idx = round((d["your_price"] / avg_market) * 100, 1) if avg_market > 0 else 100.0

                # Determine Market Position
                if price_idx < 92.0:
                    pos = "Underpriced Hazard"
                    rec_price = round(avg_market * 0.97, 2)
                    strat_action = f"Raise to ${rec_price:.2f} (Capture +${rec_price - d['your_price']:.2f} margin)"
                elif price_idx > 112.0:
                    pos = "Premium Positioned"
                    rec_price = round(avg_market * 1.05, 2)
                    strat_action = "Premium Positioned (Monitor sell-through & fabric value)"
                else:
                    pos = "Market Aligned"
                    rec_price = d["your_price"]
                    strat_action = "Market Aligned (Competitive parity)"

                margin_pct = round(((d["your_price"] - d["cost"]) / d["your_price"]) * 100, 1) if d["your_price"] > 0 else 0.0
                potential_gain = round(max(0.0, rec_price - d["your_price"]), 2)

                rows.append({
                    "product_id": pid,
                    "product_name": d["product_name"],
                    "category": d["category"],
                    "cost": d["cost"],
                    "your_price": d["your_price"],
                    "margin_pct": margin_pct,
                    "velvet_vine_price": d["velvet_vine_price"] or round(d["your_price"] * 1.25, 2),
                    "avenue_price": d["avenue_price"] or round(d["your_price"] * 1.02, 2),
                    "minimalist_price": d["minimalist_price"] or round(d["your_price"] * 0.78, 2),
                    "avg_market_price": avg_market,
                    "min_market_price": min_market,
                    "max_market_price": max_market,
                    "pricing_index": price_idx,
                    "position": pos,
                    "recommended_price": rec_price,
                    "margin_gap": potential_gain,
                    "strategic_action": strat_action
                })

            df = pd.DataFrame(rows)
            # Sort by pricing_index ascending so underpriced hazards appear first
            df = df.sort_values(by="pricing_index", ascending=True).reset_index(drop=True)
            return df
        except Exception as e:
            logger.error(f"Error fetching competitor pricing: {e}")
            return pd.DataFrame()

    def update_catalog_price(self, product_id: str, new_price: float) -> bool:
        """
        Updates the active retail price for a product in CATALOG and persists the change
        into competitor_benchmarks for the latest snapshot.
        
        Args:
            product_id: Product ID string (e.g. 'P002')
            new_price: New retail price
            
        Returns:
            bool: True if updated successfully
        """
        try:
            # CATALOG imported at top-level
            from datetime import datetime

            new_price = round(float(new_price), 2)
            if product_id in CATALOG:
                CATALOG[product_id]["price"] = new_price

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                UPDATE competitor_benchmarks 
                SET your_price = ? 
                WHERE product_id = ?
            """, (new_price, product_id))

            conn.commit()
            conn.close()
            logger.info(f"Updated retail price for {product_id} to ${new_price:.2f}")
            return True
        except Exception as e:
            logger.error(f"Error updating catalog price: {e}")
            return False

    def calculate_dynamic_broken_curves(self) -> list:
        """
        Identifies inventory fragmentation where core sizes (S, M, L) are missing.
        
        Returns:
            list: List of dictionaries containing product alerts and recommended remedies.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT product_id, size_variant, stock_on_hand 
                FROM size_matrix_stock
            """)
            rows = cursor.fetchall()
            conn.close()

            product_sizes = {}
            for pid, size, stock in rows:
                if pid not in product_sizes:
                    product_sizes[pid] = {}
                product_sizes[pid][size] = stock

            dynamic_alerts = []
            # CATALOG imported at top-level

            for pid, sizes in product_sizes.items():
                if pid not in CATALOG:
                    continue

                core_sizes = ['S', 'M', 'L']
                missing_core = [size for size in core_sizes if sizes.get(size, 0) == 0]
                total_stranded = sum(sizes.values())

                if missing_core and total_stranded > 0:
                    dynamic_alerts.append({
                        "product_name": CATALOG[pid]["name"],
                        "missing_core_sizes": missing_core,
                        "stranded_stock_volume": total_stranded,
                        "remedy": f"Core shortage detected. Consolidate remaining fringe units to clearance racks or trigger vendor restock vectors for sizes: {', '.join(missing_core)}."
                    })

            return dynamic_alerts
        except Exception as e:
            logger.error(f"Error calculating broken size curves: {e}")
            return []

    def update_circuit_control(self, pid: str, key: str, value: Any) -> None:
        """
        Updates the operational circuit settings (e.g., enable/disable sales) for a product.
        
        Args:
            pid (str): The product ID to update.
            key (str): The control field name to modify.
            value (Any): The new value (boolean toggles or integer limits).
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            db_val = int(value) if isinstance(value, bool) else value
            
            # Using f-string for column name is safe here as it comes from internal toggle keys
            cursor.execute(f"""
                UPDATE store_circuit_controls 
                SET {key} = ? 
                WHERE product_id = ?
            """, (db_val, pid))
            conn.commit()
            conn.close()
            logger.info(f"Circuit control '{key}' updated for {pid} to {value}")
        except sqlite3.Error as e:
            logger.error(f"Failed to update circuit control for {pid}: {e}")

    def get_all_circuit_controls(self) -> dict:
        """
        Fetches active configuration bounds for all catalog items.
        
        Returns:
            dict: Dictionary mapped by product ID containing sales_enabled, 
                  purchase_enabled, and max_stock settings.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT product_id, sales_enabled, purchase_enabled, max_stock FROM store_circuit_controls")
            rows = cursor.fetchall()
            conn.close()

            return {
                row[0]: {
                    "sales_enabled": True if row[1] == 1 else False,
                    "purchase_enabled": True if row[2] == 1 else False,
                    "max_stock": int(row[3])
                } for row in rows
            }
        except Exception as e:
            logger.error(f"Error fetching circuit controls: {e}")
            return {}

    def fetch_dynamic_sell_through_metrics(self) -> pd.DataFrame:
        """
        Calculates Sell-Through Rate (STR) across all catalog products.
        Formula: (Units Sold / (Units Sold + Current Inventory)) * 100
        
        Returns:
            pd.DataFrame: Sorted dataframe with sell-through percentages and status alerts.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            sales_query = "SELECT product_id, SUM(quantity) as units_sold FROM sales_ledger GROUP BY product_id"
            sales_df = pd.read_sql_query(sales_query, conn)

            stock_query = "SELECT product_id, SUM(stock_on_hand) as units_in_stock FROM size_matrix_stock GROUP BY product_id"
            stock_df = pd.read_sql_query(stock_query, conn)
            conn.close()

            # CATALOG imported at top-level

            rows = []
            for pid, details in CATALOG.items():
                sold = int(sales_df[sales_df["product_id"] == pid]["units_sold"].iloc[0]) if not sales_df[
                    sales_df["product_id"] == pid].empty else 0
                stock = int(stock_df[stock_df["product_id"] == pid]["units_in_stock"].iloc[0]) if not stock_df[
                    stock_df["product_id"] == pid].empty else 0

                total_allocated = sold + stock
                str_pct = round((sold / total_allocated * 100), 1) if total_allocated > 0 else 0.0

                if str_pct >= 70.0:
                    status = "Hot Seller"
                elif str_pct <= 25.0 and total_allocated > 0:
                    status = "Dead Inventory Risk"
                else:
                    status = "Healthy"

                rows.append({
                    "product_name": details["name"],
                    "sell_through_pct": str_pct,
                    "status": status
                })

            df_result = pd.DataFrame(rows)
            return df_result.sort_values(by="sell_through_pct", ascending=False).reset_index(drop=True)
        except Exception as e:
            logger.error(f"Error calculating sell-through metrics: {e}")
            return pd.DataFrame()

    def fetch_dynamic_sentiment_metrics(self) -> pd.DataFrame:
        """
        Aggregates mock operational reviews and parses emotional polarity scores.
        In a production pipeline, this tracks moving review index averages.
        """
        # Formulate a dynamic matrix pulling safely from calculated sentiment metrics
        # If your feedback dataset expands over time, query AVG(computed_sentiment_score) grouped by category
        # Currently returns hardcoded mock data for demonstration
        return pd.DataFrame([
            {"Operational Category": "Product Quality", "Average Sentiment Score": -0.35,
             "Status": "Negative Volatility Alert"},
            {"Operational Category": "Store Environment", "Average Sentiment Score": 0.65,
             "Status": "Optimal Positive Index"},
            {"Operational Category": "Service & Staff", "Average Sentiment Score": 0.42,
             "Status": "Optimal Positive Index"},
            {"Operational Category": "Pricing & Value", "Average Sentiment Score": 0.12,
             "Status": "Optimal Positive Index"}
        ])

    def get_current_stock_on_hand(self) -> dict:
        """
        Calculates exact cumulative stock balance across all size variants for every product.
        
        Returns:
            dict: Mapped product_id to total stock quantity.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT product_id, SUM(stock_on_hand) as total_stock FROM size_matrix_stock GROUP BY product_id")
            rows = cursor.fetchall()
            conn.close()

            return {row[0]: int(row[1]) for row in rows}
        except Exception as e:
            logger.error(f"Error fetching cumulative stock on hand: {e}")
            return {}

    def update_single_size_stock(self, pid: str, size: str, new_qty: int) -> None:
        """
        Updates the stock level for a specific product size variant.
        
        Args:
            pid (str): Product ID.
            size (str): Size variant (e.g., 'M').
            new_qty (int): The new stock quantity.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE size_matrix_stock 
                SET stock_on_hand = ? 
                WHERE product_id = ? AND size_variant = ?
            """, (new_qty, pid, size))
            conn.commit()
            conn.close()
            logger.debug(f"Stock updated for {pid} size {size} to {new_qty}")
        except sqlite3.Error as e:
            logger.error(f"Failed to update size stock for {pid} size {size}: {e}")

    # ==========================================
    # INTERNAL SEEDING HELPERS
    # ==========================================
    def _seed_20_dummy_customers_internal(self, conn: sqlite3.Connection) -> None:
        """Seeds 20 realistic luxury boutique customers if table is empty."""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM customers")
            count = cursor.fetchone()[0]
            if count >= 20:
                return

            dummy_customers = [
                ("CUST-001", "Elena Rostova", "+1-555-0101", "elena.rostova@vogue-elegance.com", "1994-03-15", "S", "Female", "Luxury Silk & Tailoring", "VIP Platinum", 1250.0, 8, "2024-01-15", 1, 1),
                ("CUST-002", "Sophia Chen", "+1-555-0102", "sophia.chen@atelier-chic.com", "1996-07-22", "M", "Female", "Minimalist Knitwear", "VIP Platinum", 980.0, 6, "2024-02-10", 1, 1),
                ("CUST-003", "Marcus Sterling", "+1-555-0103", "m.sterling@savilerow.com", "1988-11-04", "L", "Male", "Tailored Outerwear & Blazers", "Gold", 1450.0, 7, "2023-11-20", 1, 1),
                ("CUST-004", "Isabella Rossi", "+1-555-0104", "isabella.rossi@milano-mode.it", "1992-09-18", "S", "Female", "Bohemian Maxi & Dresses", "VIP Platinum", 2100.0, 12, "2023-08-14", 1, 1),
                ("CUST-005", "Liam Hemsworth", "+1-555-0105", "liam.h@coastal-threads.com", "1990-05-30", "XL", "Male", "Denim & Heavyweight Basics", "Silver", 420.0, 3, "2024-04-02", 1, 1),
                ("CUST-006", "Priya Sharma", "+1-555-0106", "priya.sharma@couture-india.com", "1995-10-12", "M", "Female", "Silk Skirts & Cashmere", "VIP Platinum", 1890.0, 10, "2023-09-05", 1, 1),
                ("CUST-007", "Lucas Vance", "+1-555-0107", "lucas.vance@urbanline.com", "1993-01-25", "M", "Male", "Streetwear & Jackets", "Gold", 760.0, 5, "2024-03-12", 1, 1),
                ("CUST-008", "Camille Laurent", "+1-555-0108", "camille.l@parisiennelook.fr", "1991-04-08", "S", "Female", "French Chic & Linen", "VIP Platinum", 1650.0, 9, "2023-10-18", 1, 1),
                ("CUST-009", "Alexander Wright", "+1-555-0109", "a.wright@bespoke-london.co.uk", "1985-12-03", "L", "Male", "Classic Poplin & Blazers", "Gold", 890.0, 5, "2023-12-01", 1, 1),
                ("CUST-010", "Maya Lin", "+1-555-0110", "maya.lin@zenith-apparel.com", "1998-02-14", "S", "Female", "Cropped Knits & Skirts", "Silver", 540.0, 4, "2024-05-10", 1, 1),
                ("CUST-011", "Oliver Davies", "+1-555-0111", "oliver.davies@heritage-tweed.com", "1989-08-19", "XL", "Male", "Trench Coats & Sweaters", "Gold", 1120.0, 6, "2023-07-28", 1, 1),
                ("CUST-012", "Zara Al-Mansoor", "+1-555-0112", "zara.almansoor@gulf-mishika.ae", "1997-06-05", "M", "Female", "Evening Gowns & Velvet", "VIP Platinum", 2400.0, 14, "2023-06-12", 1, 1),
                ("CUST-013", "Mateo Hernandez", "+1-555-0113", "mateo.h@valencia-style.es", "1992-03-29", "M", "Male", "Linen Shirts & Trousers", "Silver", 480.0, 3, "2024-01-20", 1, 1),
                ("CUST-014", "Chloe DuPont", "+1-555-0114", "chloe.dupont@geneve-lux.ch", "1996-10-31", "S", "Female", "Cashmere Crewnecks & Midi", "Gold", 1320.0, 8, "2023-11-15", 1, 1),
                ("CUST-015", "Tariq Jackson", "+1-555-0115", "tariq.j@metro-attire.com", "1991-07-09", "L", "Male", "Moto Jackets & Denim", "Gold", 950.0, 6, "2024-02-18", 1, 1),
                ("CUST-016", "Ananya Patel", "+1-555-0116", "ananya.patel@mumbai-vogue.in", "1999-04-18", "S", "Female", "Contemporary Bohemian", "Silver", 380.0, 2, "2024-06-01", 1, 1),
                ("CUST-017", "Henrik Lindqvist", "+1-555-0117", "henrik.l@nordic-wool.se", "1987-11-28", "L", "Male", "Merino Cardigans & Tailored", "Gold", 1050.0, 7, "2023-09-22", 1, 1),
                ("CUST-018", "Valentina Gomez", "+1-555-0118", "valentina.g@buenosaires-chic.ar", "1995-08-14", "M", "Female", "Satin Pleated Skirts", "Silver", 620.0, 4, "2024-03-05", 1, 1),
                ("CUST-019", "David Kim", "+1-555-0119", "david.kim@seoul-minimal.kr", "1994-09-02", "M", "Male", "Clean Tailoring & Utility", "Gold", 880.0, 5, "2024-01-10", 1, 1),
                ("CUST-020", "Natasha Romanoff", "+1-555-0120", "natasha.r@blacktie-vip.com", "1990-12-19", "S", "Female", "Vegan Leather & Power Blazers", "VIP Platinum", 2850.0, 16, "2023-05-18", 1, 1)
            ]

            cursor.executemany("""
                INSERT OR IGNORE INTO customers
                (customer_code, name, phone, email, dob, preferred_size, gender, style_preference, loyalty_tier, total_spend, purchase_count, joined_date, opt_in_whatsapp, opt_in_email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, dummy_customers)
            conn.commit()
            logger.info("Seeded 20 VIP boutique customers successfully.")
        except Exception as e:
            logger.error(f"Error seeding 20 dummy customers: {e}")

    def _seed_warehouse_stock_internal(self, conn: sqlite3.Connection) -> None:
        """Seeds initial warehouse backroom inventory if table is empty."""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM warehouse_stock")
            count = cursor.fetchone()[0]
            if count >= len(CATALOG) * 4:
                return

            for pid in CATALOG:
                for size in ['S', 'M', 'L', 'XL']:
                    # Warehouse starts with healthy backroom reserve (15-25 units)
                    stock_qty = 20
                    cursor.execute("""
                        INSERT OR IGNORE INTO warehouse_stock (product_id, size_variant, stock_on_hand)
                        VALUES (?, ?, ?)
                    """, (pid, size, stock_qty))
            conn.commit()
            logger.info("Seeded initial warehouse backroom inventory.")
        except Exception as e:
            logger.error(f"Error seeding warehouse stock: {e}")

    def _seed_default_campaigns_internal(self, conn: sqlite3.Connection) -> None:
        """Seeds default promotional campaigns if empty."""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM campaigns")
            if cursor.fetchone()[0] > 0:
                return

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            campaigns = [
                (now_str, "Summer Riviera Elegance", "20% off all resort dresses, silk skirts, and linen tailoring", 20.0, "Active", "Dresses", "Sun-Drenched Coastal Luxury", "Shivi Deep Agent"),
                (now_str, "Autumn Cashmere Preview", "15% off fine cashmere crewnecks, cardigans, and knitwear", 15.0, "Active", "Knitwear", "Quiet Luxury Knits & Warmth", "Shivi Deep Agent"),
                (now_str, "VIP Private Flash Access", "25% celebratory boutique markdown for elite patrons", 25.0, "Active", "All Categories", "Exclusive Insider Privilege", "Shivi Deep Agent")
            ]
            cursor.executemany("""
                INSERT INTO campaigns (created_at, name, description, discount_pct, status, target_category, banner_tagline, launched_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, campaigns)
            conn.commit()
            logger.info("Seeded default promotional campaigns.")
        except Exception as e:
            logger.error(f"Error seeding campaigns: {e}")

    def _load_custom_products_internal(self, conn: sqlite3.Connection) -> None:
        """Loads user-added custom products from SQLite into memory CATALOG."""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT product_id, name, cost, price, color, category FROM custom_products")
            rows = cursor.fetchall()
            for row in rows:
                register_product(row[0], row[1], float(row[2]), float(row[3]), row[4], row[5])
        except Exception as e:
            logger.error(f"Error loading custom products: {e}")

    # ==========================================
    # PORTAL FEATURE 1: SHOP ⇄ WAREHOUSE STOCK TRANSFER
    # ==========================================
    def transfer_stock(self, product_id: str, size_variant: str, source: str, destination: str, quantity: int, notes: str = "", performed_by: str = "Portal Admin") -> Tuple[bool, str]:
        """
        Moves product stock between Shop Floor and Warehouse Reserve.
        Items inside warehouse are isolated from shop stock.
        """
        source = source.lower().strip()
        destination = destination.lower().strip()

        if source not in ("shop", "warehouse") or destination not in ("shop", "warehouse"):
            return False, "Source and destination must be either 'shop' or 'warehouse'."

        if source == destination:
            return False, "Source and destination locations cannot be the same."

        if quantity <= 0:
            return False, "Transfer quantity must be greater than zero."

        product_name = CATALOG.get(product_id, {}).get("name", product_id)
        valid_sizes = ['S', 'M', 'L', 'XL'] if size_variant == "ALL" else [size_variant]

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            qty_per_size = quantity // len(valid_sizes)
            if qty_per_size <= 0:
                qty_per_size = 1

            # Check availability across all target sizes first
            for sz in valid_sizes:
                if source == "shop":
                    cursor.execute("SELECT stock_on_hand FROM size_matrix_stock WHERE product_id = ? AND size_variant = ?", (product_id, sz))
                else:
                    cursor.execute("SELECT stock_on_hand FROM warehouse_stock WHERE product_id = ? AND size_variant = ?", (product_id, sz))

                row = cursor.fetchone()
                avail = row[0] if row else 0
                if avail < qty_per_size:
                    conn.close()
                    src_label = "Shop Floor" if source == "shop" else "Warehouse Reserve"
                    return False, f"Insufficient stock for size {sz} in {src_label}. Requested: {qty_per_size}, Available: {avail}."

            # Perform atomic movement
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            total_transferred = 0

            for sz in valid_sizes:
                # Deduct from source
                if source == "shop":
                    cursor.execute("""
                        UPDATE size_matrix_stock 
                        SET stock_on_hand = stock_on_hand - ? 
                        WHERE product_id = ? AND size_variant = ?
                    """, (qty_per_size, product_id, sz))
                else:
                    cursor.execute("""
                        UPDATE warehouse_stock 
                        SET stock_on_hand = stock_on_hand - ? 
                        WHERE product_id = ? AND size_variant = ?
                    """, (qty_per_size, product_id, sz))

                # Add to destination
                if destination == "shop":
                    cursor.execute("""
                        INSERT INTO size_matrix_stock (product_id, size_variant, stock_on_hand)
                        VALUES (?, ?, ?)
                        ON CONFLICT(product_id, size_variant) DO UPDATE SET stock_on_hand = stock_on_hand + ?
                    """, (product_id, sz, qty_per_size, qty_per_size))
                else:
                    cursor.execute("""
                        INSERT INTO warehouse_stock (product_id, size_variant, stock_on_hand)
                        VALUES (?, ?, ?)
                        ON CONFLICT(product_id, size_variant) DO UPDATE SET stock_on_hand = stock_on_hand + ?
                    """, (product_id, sz, qty_per_size, qty_per_size))

                # Record in transfer ledger
                cursor.execute("""
                    INSERT INTO stock_transfers (timestamp, product_id, product_name, size_variant, source_location, dest_location, quantity, performed_by, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (now_str, product_id, product_name, sz, source.title(), destination.title(), qty_per_size, performed_by, notes))

                total_transferred += qty_per_size

            conn.commit()
            conn.close()

            src_display = "Shop Floor" if source == "shop" else "Warehouse Reserve"
            dst_display = "Warehouse Reserve" if destination == "warehouse" else "Shop Floor"
            msg = f"✅ Successfully transferred {total_transferred} unit(s) of '{product_name}' from {src_display} to {dst_display}."
            logger.info(msg)
            return True, msg
        except Exception as e:
            logger.error(f"Error executing stock transfer: {e}")
            return False, f"Transfer failed due to database error: {str(e)}"

    def get_warehouse_stock_on_hand(self) -> Dict[str, int]:
        """Calculates cumulative isolated warehouse stock balance across sizes."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT product_id, SUM(stock_on_hand) FROM warehouse_stock GROUP BY product_id")
            rows = cursor.fetchall()
            conn.close()
            return {row[0]: int(row[1]) for row in rows}
        except Exception as e:
            logger.error(f"Error fetching warehouse stock: {e}")
            return {}

    def get_warehouse_matrix_stock(self) -> pd.DataFrame:
        """Fetches detailed warehouse stock breakdown by size variant."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT product_id, size_variant, stock_on_hand FROM warehouse_stock ORDER BY product_id, size_variant", conn)
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Error fetching warehouse matrix: {e}")
            return pd.DataFrame()

    def get_stock_transfers(self, limit: int = 50) -> pd.DataFrame:
        """Fetches recent transfer audit logs."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(f"SELECT * FROM stock_transfers ORDER BY id DESC LIMIT {limit}", conn)
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Error fetching stock transfers: {e}")
            return pd.DataFrame()

    # ==========================================
    # PORTAL FEATURE 2 & 3: ADD NEW PRODUCT & RE-ORDER
    # ==========================================
    def add_new_product(
        self,
        product_id: str,
        name: str,
        cost: float,
        price: float,
        color: str,
        category: str,
        initial_shop_stock: Dict[str, int],
        initial_warehouse_stock: Dict[str, int]
    ) -> Tuple[bool, str]:
        """
        Dynamically registers a new merchandise style into catalog, shop stock, and warehouse stock.
        """
        product_id = product_id.strip().upper()
        name = name.strip()
        if not product_id or not name:
            return False, "Product ID and Product Name cannot be empty."

        if product_id in CATALOG:
            return False, f"Product ID '{product_id}' already exists in the catalog."

        if cost <= 0 or price <= 0:
            return False, "Cost and Retail Price must be positive values."

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 1. Register in custom_products table
            cursor.execute("""
                INSERT INTO custom_products (product_id, name, cost, price, color, category, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (product_id, name, cost, price, color, category, now_str))

            # 2. Update in-memory CATALOG
            register_product(product_id, name, cost, price, color, category)

            # 3. Seed Shop Floor Size Matrix Stock
            for size in ['S', 'M', 'L', 'XL']:
                s_qty = initial_shop_stock.get(size, 10)
                cursor.execute("""
                    INSERT INTO size_matrix_stock (product_id, size_variant, stock_on_hand)
                    VALUES (?, ?, ?)
                """, (product_id, size, s_qty))

            # 4. Seed Warehouse Stock
            for size in ['S', 'M', 'L', 'XL']:
                w_qty = initial_warehouse_stock.get(size, 15)
                cursor.execute("""
                    INSERT INTO warehouse_stock (product_id, size_variant, stock_on_hand)
                    VALUES (?, ?, ?)
                """, (product_id, size, w_qty))

            # 5. Seed Store Circuit Controls
            cursor.execute("""
                INSERT INTO store_circuit_controls (product_id, sales_enabled, purchase_enabled, max_stock)
                VALUES (?, 1, 1, 150)
            """, (product_id,))

            # 6. Seed Competitor Benchmarks for market price indexing
            cursor.execute("""
                INSERT INTO competitor_benchmarks (timestamp, product_id, product_name, your_price, competitor_name, competitor_price)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (now_str, product_id, name, price, "Velvet & Vine Boutique", round(price * 1.25, 2)))
            cursor.execute("""
                INSERT INTO competitor_benchmarks (timestamp, product_id, product_name, your_price, competitor_name, competitor_price)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (now_str, product_id, name, price, "Avenue Apparel", round(price * 1.02, 2)))
            cursor.execute("""
                INSERT INTO competitor_benchmarks (timestamp, product_id, product_name, your_price, competitor_name, competitor_price)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (now_str, product_id, name, price, "Minimalist Thread Co.", round(price * 0.78, 2)))

            conn.commit()
            conn.close()
            msg = f"✨ Product '{name}' ({product_id}) successfully created and registered into store catalog!"
            logger.info(msg)
            return True, msg
        except Exception as e:
            logger.error(f"Error creating product {product_id}: {e}")
            return False, f"Failed to create product: {str(e)}"

    def order_product(
        self,
        product_id: str,
        quantity: int,
        destination: str = "warehouse",
        unit_cost: Optional[float] = None,
        notes: str = ""
    ) -> Tuple[bool, str]:
        """
        Orders any product from the catalog in any quantity, with destination routing.
        """
        if quantity <= 0:
            return False, "Order quantity must be greater than zero."

        if product_id not in CATALOG:
            return False, f"Product ID '{product_id}' not found in catalog."

        destination = destination.lower().strip()
        if destination not in ("shop", "warehouse"):
            destination = "warehouse"

        p_info = CATALOG[product_id]
        p_name = p_info["name"]
        cost = unit_cost if unit_cost is not None and unit_cost > 0 else p_info["cost"]
        total_cost = round(cost * quantity, 2)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Record in purchase ledger
            cursor.execute("""
                INSERT INTO purchase_ledger (timestamp, product_id, product_name, quantity, total_cost)
                VALUES (?, ?, ?, ?, ?)
            """, (now_str, product_id, p_name, quantity, total_cost))

            # Distribute incoming stock across S, M, L, XL
            qty_per_size = quantity // 4
            remainder = quantity % 4
            sizes = ['S', 'M', 'L', 'XL']

            for i, sz in enumerate(sizes):
                add_qty = qty_per_size + (1 if i < remainder else 0)
                if destination == "warehouse":
                    cursor.execute("""
                        INSERT INTO warehouse_stock (product_id, size_variant, stock_on_hand)
                        VALUES (?, ?, ?)
                        ON CONFLICT(product_id, size_variant) DO UPDATE SET stock_on_hand = stock_on_hand + ?
                    """, (product_id, sz, add_qty, add_qty))
                else:
                    cursor.execute("""
                        INSERT INTO size_matrix_stock (product_id, size_variant, stock_on_hand)
                        VALUES (?, ?, ?)
                        ON CONFLICT(product_id, size_variant) DO UPDATE SET stock_on_hand = stock_on_hand + ?
                    """, (product_id, sz, add_qty, add_qty))

            conn.commit()
            conn.close()

            dst_name = "Warehouse Storage" if destination == "warehouse" else "Shop Floor"
            msg = f"🚚 Order placed: Received {quantity}x '{p_name}' delivered to {dst_name} (Total Cost: ${total_cost:,.2f})."
            logger.info(msg)
            return True, msg
        except Exception as e:
            logger.error(f"Error placing product order: {e}")
            return False, f"Order failed: {str(e)}"

    # ==========================================
    # PORTAL FEATURE 4: CAMPAIGNS MANAGEMENT
    # ==========================================
    def create_campaign(
        self,
        name: str,
        description: str,
        discount_pct: float,
        target_category: str = "All Categories",
        banner_tagline: str = "",
        launched_by: str = "Marketing Admin"
    ) -> Tuple[bool, str]:
        """Creates and launches a new custom promotional campaign."""
        name = name.strip()
        description = description.strip()
        if not name or not description:
            return False, "Campaign name and description are required."

        discount_pct = float(discount_pct)
        if discount_pct < 0 or discount_pct > 70:
            return False, "Discount must be between 0% and 70%."

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT INTO campaigns (created_at, name, description, discount_pct, status, target_category, banner_tagline, launched_by)
                VALUES (?, ?, ?, ?, 'Active', ?, ?, ?)
            """, (now_str, name, description, discount_pct, target_category, banner_tagline, launched_by))

            conn.commit()
            conn.close()
            msg = f"🚀 Campaign '{name}' ({discount_pct:.0f}% Off) launched successfully!"
            logger.info(msg)
            return True, msg
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            return False, f"Failed to launch campaign: {str(e)}"

    def get_all_campaigns(self) -> pd.DataFrame:
        """Fetches all campaigns recorded in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM campaigns ORDER BY id DESC", conn)
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Error fetching campaigns: {e}")
            return pd.DataFrame()

    def update_campaign_status(self, campaign_id: int, status: str) -> bool:
        """Updates the status of a promotional campaign ('Active', 'Paused', 'Ended')."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE campaigns SET status = ? WHERE id = ?", (status, campaign_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating campaign {campaign_id}: {e}")
            return False

    def get_active_campaign(self) -> Optional[Dict[str, Any]]:
        """Returns the most recent active promotional campaign if any."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description, discount_pct, target_category, banner_tagline FROM campaigns WHERE status = 'Active' ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "discount_pct": float(row[3]),
                    "target_category": row[4],
                    "banner_tagline": row[5]
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching active campaign: {e}")
            return None

    # ==========================================
    # STEP 2: CUSTOMERS CRM & PURCHASE HISTORY
    # ==========================================
    def get_all_customers(self) -> pd.DataFrame:
        """Fetches all 20 VIP customer profiles."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM customers ORDER BY total_spend DESC", conn)
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Error fetching customers: {e}")
            return pd.DataFrame()

    def get_customer_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a specific customer's profile by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                cols = ["id", "customer_code", "name", "phone", "email", "dob", "preferred_size", "gender", "style_preference", "loyalty_tier", "total_spend", "purchase_count", "joined_date", "opt_in_whatsapp", "opt_in_email"]
                return dict(zip(cols, row))
            return None
        except Exception as e:
            logger.error(f"Error fetching customer {customer_id}: {e}")
            return None

    def get_customer_purchase_history(self, customer_id: int) -> pd.DataFrame:
        """Retrieves complete purchase history for a specific customer."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT timestamp, product_name, quantity, unit_price, total_revenue, campaign_name, size_purchased, channel FROM sales_ledger WHERE customer_id = ? ORDER BY id DESC"
            df = pd.read_sql_query(query, conn, params=(customer_id,))
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Error fetching customer purchase history: {e}")
            return pd.DataFrame()

    def get_upcoming_birthday_customers(self, days_ahead: int = 14) -> List[Dict[str, Any]]:
        """Identifies customers whose birthday occurs within the next N days."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, customer_code, name, email, phone, dob, preferred_size, loyalty_tier, style_preference FROM customers")
            rows = cursor.fetchall()
            conn.close()

            today = datetime.now()
            matches = []
            for r in rows:
                dob_str = r[5]
                try:
                    dob = datetime.strptime(dob_str, "%Y-%m-%d")
                    bday_this_year = dob.replace(year=today.year)
                    delta = (bday_this_year - today).days
                    if 0 <= delta <= days_ahead:
                        matches.append({
                            "id": r[0],
                            "code": r[1],
                            "name": r[2],
                            "email": r[3],
                            "phone": r[4],
                            "dob": dob_str,
                            "days_until": delta,
                            "preferred_size": r[6],
                            "loyalty_tier": r[7],
                            "style_preference": r[8]
                        })
                except Exception:
                    continue
            return sorted(matches, key=lambda x: x["days_until"])
        except Exception as e:
            logger.error(f"Error fetching birthday customers: {e}")
            return []

    def update_customer_contact(
        self,
        customer_id: int,
        phone: str,
        email: str,
        name: Optional[str] = None,
        preferred_size: Optional[str] = None,
        style_preference: Optional[str] = None,
        loyalty_tier: Optional[str] = None,
        opt_in_whatsapp: Optional[int] = None,
        opt_in_email: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Updates contact details, preferences, and notification consents for a customer."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name, phone, email, preferred_size, style_preference, loyalty_tier, opt_in_whatsapp, opt_in_email FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False, f"Customer with ID {customer_id} not found."

            final_name = name if name is not None else row[0]
            final_phone = phone if phone is not None else row[1]
            final_email = email if email is not None else row[2]
            final_size = preferred_size if preferred_size is not None else row[3]
            final_style = style_preference if style_preference is not None else row[4]
            final_tier = loyalty_tier if loyalty_tier is not None else row[5]
            final_opt_wa = opt_in_whatsapp if opt_in_whatsapp is not None else row[6]
            final_opt_em = opt_in_email if opt_in_email is not None else row[7]

            cursor.execute("""
                UPDATE customers
                SET name = ?, phone = ?, email = ?, preferred_size = ?, style_preference = ?, loyalty_tier = ?, opt_in_whatsapp = ?, opt_in_email = ?
                WHERE id = ?
            """, (final_name, final_phone, final_email, final_size, final_style, final_tier, final_opt_wa, final_opt_em, customer_id))
            conn.commit()
            conn.close()
            return True, f"Contact details for {final_name} updated successfully."
        except Exception as e:
            logger.error(f"Error updating customer {customer_id}: {e}")
            return False, f"Database error updating customer: {str(e)}"

    # ==========================================
    # STEP 3: DEEP AGENT "SHIVI" PERSISTENCE
    # ==========================================
    def save_agent_communication(self, data: Dict[str, Any]) -> int:
        """Records an outgoing Email or WhatsApp dispatch from Shivi Deep Agent."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO agent_communications (timestamp, customer_id, customer_name, channel, message_type, subject, content, status, campaign_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("timestamp", now_str),
                data.get("customer_id"),
                data.get("customer_name", "Valued Client"),
                data.get("channel", "Email"),
                data.get("message_type", "General"),
                data.get("subject", ""),
                data.get("content", ""),
                data.get("status", "Delivered"),
                data.get("campaign_id")
            ))
            comm_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return comm_id or 0
        except Exception as e:
            logger.error(f"Error saving agent communication: {e}")
            return 0

    def get_agent_communications(self, limit: int = 50) -> pd.DataFrame:
        """Fetches recent communications dispatched by Shivi Deep Agent."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(f"SELECT * FROM agent_communications ORDER BY id DESC LIMIT {limit}", conn)
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Error fetching agent communications: {e}")
            return pd.DataFrame()

    def save_agent_memory(self, session_id: str, memory_type: str, key: str, value: str) -> None:
        """Stores a memory snippet into Shivi's episodic/semantic memory."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO agent_memory (timestamp, session_id, memory_type, memory_key, memory_value)
                VALUES (?, ?, ?, ?, ?)
            """, (now_str, session_id, memory_type, key, value))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving agent memory: {e}")

    def get_agent_memories(self, session_id: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        """Retrieves memories stored by Shivi."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if session_id:
                cursor.execute("SELECT timestamp, session_id, memory_type, memory_key, memory_value FROM agent_memory WHERE session_id = ? ORDER BY id DESC LIMIT ?", (session_id, limit))
            else:
                cursor.execute("SELECT timestamp, session_id, memory_type, memory_key, memory_value FROM agent_memory ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            return [{"timestamp": r[0], "session_id": r[1], "type": r[2], "key": r[3], "value": r[4]} for r in rows]
        except Exception as e:
            logger.error(f"Error fetching agent memories: {e}")
            return []

    def add_to_approval_queue(self, action_type: str, title: str, description: str, payload: Dict[str, Any], requested_by: str = "Shivi Deep Agent") -> int:
        """Adds a high-impact action to the Human-in-the-Loop approval queue."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            payload_str = json.dumps(payload)
            cursor.execute("""
                INSERT INTO agent_approval_queue (timestamp, action_type, title, description, payload_json, status, requested_by)
                VALUES (?, ?, ?, ?, ?, 'Pending', ?)
            """, (now_str, action_type, title, description, payload_str, requested_by))
            q_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return q_id or 0
        except Exception as e:
            logger.error(f"Error adding to approval queue: {e}")
            return 0

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Fetches pending steering approvals for human review."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, timestamp, action_type, title, description, payload_json, status, requested_by FROM agent_approval_queue WHERE status = 'Pending' ORDER BY id ASC")
            rows = cursor.fetchall()
            conn.close()
            items = []
            for r in rows:
                try:
                    payload = json.loads(r[5])
                except Exception:
                    payload = {}
                items.append({
                    "id": r[0],
                    "timestamp": r[1],
                    "action_type": r[2],
                    "title": r[3],
                    "description": r[4],
                    "payload": payload,
                    "status": r[6],
                    "requested_by": r[7]
                })
            return items
        except Exception as e:
            logger.error(f"Error fetching pending approvals: {e}")
            return []

    def update_approval_status(self, approval_id: int, status: str, review_notes: str = "") -> bool:
        """Approves or rejects a pending human-in-the-loop steering request."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                UPDATE agent_approval_queue 
                SET status = ?, reviewed_at = ?, review_notes = ? 
                WHERE id = ?
            """, (status, now_str, review_notes, approval_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating approval status: {e}")
            return False



