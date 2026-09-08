import sqlite3
import pandas as pd
import logging
from typing import Dict, Any, List, Optional
try:
    from src.core.logger import setup_logging
    from src.core.config import DB_PATH
    from src.core.catalog import CATALOG
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

            # Size Matrix Stock: Detailed inventory tracking by size variant
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS size_matrix_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    size_variant TEXT NOT NULL,
                    stock_on_hand INTEGER NOT NULL,
                    UNIQUE(product_id, size_variant)
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

            # Seed initial data if tables were just created
            try:
                # CATALOG imported at top-level
                for pid in CATALOG:
                    for size in ['S', 'M', 'L', 'XL']:
                        initial_stock = 0 if int(pid[1:]) >= 16 else 15
                        cursor.execute("""
                            INSERT OR IGNORE INTO size_matrix_stock (product_id, size_variant, stock_on_hand)
                            VALUES (?, ?, ?)
                        """, (pid, size, initial_stock))

                        cursor.execute("""
                            INSERT OR IGNORE INTO store_circuit_controls (product_id, sales_enabled, purchase_enabled, max_stock)
                            VALUES (?, 1, 1, 100)
                        """, (pid,))
            except ImportError:
                logger.warning("Could not import CATALOG; skipping initial data seeding.")
            except Exception as e:
                logger.error(f"Error seeding initial database values: {e}")

            conn.commit()
            conn.close()
            logger.info("Database schema verification completed successfully.")
        except sqlite3.Error as e:
            logger.error(f"Database schema verification failed: {e}")
            raise

    def save_sale(self, data: Dict[str, Any]) -> None:
        """
        Records a completed customer transaction into the sales ledger.
        
        Args:
            data (Dict): Dictionary containing keys: timestamp, product_id, product_name, 
                        quantity, unit_price, unit_cost, total_revenue, total_cost, 
                        gross_profit, is_promotional, campaign_name.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sales_ledger 
                (timestamp, product_id, product_name, quantity, unit_price, unit_cost, total_revenue, total_cost, gross_profit, is_promotional, campaign_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data['timestamp'], data['product_id'], data['product_name'], data['quantity'], data['unit_price'],
                  data['unit_cost'], data['total_revenue'], data['total_cost'], data['gross_profit'],
                  data['is_promotional'], data['campaign_name']))
            conn.commit()
            conn.close()
            logger.debug(f"Sale recorded for {data['product_name']} ({data['product_id']})")
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


