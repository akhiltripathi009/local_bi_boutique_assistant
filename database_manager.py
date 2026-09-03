import sqlite3
import pandas as pd
from typing import Dict, Any


class DatabaseManager:
    def __init__(self, db_path: str = "boutique_bi.db"):
        # Initialize the database path
        self.db_path = db_path
        # Automatically runs table checks and creates them if they don't exist on startup
        self._verify_schema()  # Automatically runs table checks on startup

    def _verify_schema(self) -> None:
        """Self-healing guard rails: Creates all necessary tables if missing."""
        # Open a connection to the SQLite database
        conn = sqlite3.connect(self.db_path)
        # Create a cursor object to execute SQL commands
        cursor = conn.cursor()

        # 1. Sales Ledger Table: Stores all transaction records
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

        # 2. Purchase Ledger Table: Stores stock acquisition records
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

        # 3. Competitor Benchmarks Table: Stores external market pricing data
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

        # 4. 🔥 CRASH FIX: Auto-Inject Dynamic Size Matrix Table if missing: Manages size-level stock
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS size_matrix_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                size_variant TEXT NOT NULL,
                stock_on_hand INTEGER NOT NULL,
                UNIQUE(product_id, size_variant)
            )
        """)

        # Store Circuit Controls: Manages operational toggles and limits for products
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS store_circuit_controls (
                product_id TEXT PRIMARY KEY,
                sales_enabled INTEGER NOT NULL DEFAULT 1,
                purchase_enabled INTEGER NOT NULL DEFAULT 1,
                max_stock INTEGER NOT NULL DEFAULT 100
            )
        """)

        # 5. Pre-populate sizes for your 20 products if table was completely pristine
        try:
            # Import the catalog configuration
            from catalog_config import CATALOG
            # Iterate through each product in the catalog
            for pid in CATALOG:
                # Iterate through standard size variants
                for size in ['S', 'M', 'L', 'XL']:
                    # Seed standard items with stock (15 units) and out-of-stock items (P016-P020) with 0
                    initial_stock = 0 if int(pid[1:]) >= 16 else 15
                    # Insert initial stock levels for each size variant
                    cursor.execute("""
                        INSERT OR IGNORE INTO size_matrix_stock (product_id, size_variant, stock_on_hand)
                        VALUES (?, ?, ?)
                    """, (pid, size, initial_stock))

                    # Insert default circuit control settings for the product
                    cursor.execute("""
                                        INSERT OR IGNORE INTO store_circuit_controls (product_id, sales_enabled, purchase_enabled, max_stock)
                                        VALUES (?, 1, 1, 100)
                                    """, (pid,))
        except Exception:
            # Suppress temporary import lookup skips on early initialization phases
            pass

        # Commit all changes to the database
        conn.commit()
        # Close the database connection
        conn.close()

    def save_sale(self, data: Dict[str, Any]) -> None:
        # Establish connection to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Insert a new sale record into the sales_ledger table
        cursor.execute("""
            INSERT INTO sales_ledger 
            (timestamp, product_id, product_name, quantity, unit_price, unit_cost, total_revenue, total_cost, gross_profit, is_promotional, campaign_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data['timestamp'], data['product_id'], data['product_name'], data['quantity'], data['unit_price'],
              data['unit_cost'], data['total_revenue'], data['total_cost'], data['gross_profit'],
              data['is_promotional'], data['campaign_name']))
        # Save changes and close connection
        conn.commit()
        conn.close()

    def save_purchase(self, data: Dict[str, Any]) -> None:
        # Establish connection to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Insert a new purchase record into the purchase_ledger table
        cursor.execute("""
            INSERT INTO purchase_ledger (timestamp, product_id, product_name, quantity, total_cost)
            VALUES (?, ?, ?, ?, ?)
        """, (data['timestamp'], data['product_id'], data['product_name'], data['quantity'], data['total_cost']))
        # Save changes and close connection
        conn.commit()
        conn.close()

    def fetch_logs(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            # Use pandas to read the most recent logs from the specified table
            df = pd.read_sql_query(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT {limit}", conn)
            # Close connection
            conn.close()
            return df
        except Exception:
            # Return an empty dataframe if an error occurs (e.g., table doesn't exist)
            return pd.DataFrame()

    def get_total_historical_revenue(self) -> float:
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Calculate the sum of total_revenue column from sales_ledger
            cursor.execute("SELECT SUM(total_revenue) FROM sales_ledger")
            result = cursor.fetchone()
            conn.close()
            # Return result as float, defaulting to 0.0 if no data
            return float(result[0]) if result and result[0] is not None else 0.0
        except Exception:
            return 0.0

    def get_average_gross_margin(self) -> float:
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Calculate total gross profit and total revenue to find margin
            cursor.execute("SELECT SUM(gross_profit), SUM(total_revenue) FROM sales_ledger")
            result = cursor.fetchone()
            conn.close()
            # Calculate margin percentage if revenue is greater than zero
            if result and result[0] is not None and result[1] is not None and result[1] > 0:
                return (result[0] / result[1]) * 100
            # Default benchmark margin if no data exists
            return 54.2
        except Exception:
            return 54.2

    def fetch_dynamic_competitor_pricing(self) -> pd.DataFrame:
        # Ensures table is built prior to grouping attempts
        self._verify_schema()

        # Connect to database
        conn = sqlite3.connect(self.db_path)
        # SQL query to get average market price per product from benchmarks
        query = """
            SELECT product_name, your_price, AVG(competitor_price) as avg_market_price
            FROM competitor_benchmarks GROUP BY product_id
        """
        # Execute query and load into DataFrame
        df = pd.read_sql_query(query, conn)
        conn.close()

        # Fallback dataset if the competitor engine hasn't generated values yet
        if df.empty:
            return pd.DataFrame([
                {"product_name": "Linen Wrap Dress", "pricing_index": 108.0, "position": "Market Aligned"},
                {"product_name": "Silk Slip Skirt", "pricing_index": 88.2, "position": "Underpriced Hazard"},
                {"product_name": "Ribbed Knit Tank", "pricing_index": 116.6, "position": "Premium Positioned"},
                {"product_name": "Oversized Denim Jacket", "pricing_index": 104.3, "position": "Market Aligned"}
            ])

        # Calculate pricing index relative to market average (100 = market avg)
        df["pricing_index"] = round((df["your_price"] / df["avg_market_price"]) * 100, 1)
        # Categorize market position based on pricing index thresholds
        df["position"] = df["pricing_index"].apply(
            lambda x: "Premium Positioned" if x > 112 else ("Underpriced Hazard" if x < 92 else "Market Aligned"))
        return df

    def calculate_dynamic_broken_curves(self) -> list:
        """
        Queries the size matrix and dynamically flags styles that have
        completely run out of stock on core consumer sizes (S, M, L).
        """
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Pull all size allocations grouped by product to identify gaps
        cursor.execute("""
            SELECT product_id, size_variant, stock_on_hand 
            FROM size_matrix_stock
        """)
        rows = cursor.fetchall()
        conn.close()

        # Organize data rows inside dictionary groupings by product ID
        product_sizes = {}
        for pid, size, stock in rows:
            if pid not in product_sizes:
                product_sizes[pid] = {}
            product_sizes[pid][size] = stock

        dynamic_alerts = []
        # Import catalog to get product names
        from catalog_config import CATALOG

        # Analyze each product for "broken curves" (missing core sizes)
        for pid, sizes in product_sizes.items():
            if pid not in CATALOG:
                continue

            # Core boutique buying loop focus target sizes
            core_sizes = ['S', 'M', 'L']
            # Identify core sizes that are currently out of stock (stock == 0)
            missing_core = [size for size in core_sizes if sizes.get(size, 0) == 0]
            # Calculate total stock remaining across all sizes for this product
            total_stranded = sum(sizes.values())

            # If some core sizes are missing, but we still hold lingering inventory items
            if missing_core and total_stranded > 0:
                # Add alert for products that have stock but are missing key sizes
                dynamic_alerts.append({
                    "product_name": CATALOG[pid]["name"],
                    "missing_core_sizes": missing_core,
                    "stranded_stock_volume": total_stranded,
                    "remedy": f"Core shortage detected. Consolidate remaining fringe units to clearance racks or trigger vendor restock vectors for sizes: {', '.join(missing_core)}."
                })

        return dynamic_alerts

    def update_circuit_control(self, pid: str, key: str, value: Any) -> None:
        """Saves toggle positions natively onto the hard drive database."""
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Convert boolean parameters to integer bits safely for SQLite (True -> 1, False -> 0)
        db_val = int(value) if isinstance(value, bool) else value

        # Update the specific control field for the given product ID
        cursor.execute(f"""
            UPDATE store_circuit_controls 
            SET {key} = ? 
            WHERE product_id = ?
        """, (db_val, pid))

        # Commit and close
        conn.commit()
        conn.close()

    def get_all_circuit_controls(self) -> dict:
        """Fetches the active configuration bounds for all 20 clothing styles with correct type casting."""
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Retrieve all control settings from the table
        cursor.execute("SELECT product_id, sales_enabled, purchase_enabled, max_stock FROM store_circuit_controls")
        rows = cursor.fetchall()
        conn.close()

        # 🔥 CRASH FIX: Parse column indices explicitly so 1 maps to True and 0 maps to False
        # Return a dictionary mapped by product ID containing boolean and integer settings
        return {
            row[0]: {
                "sales_enabled": True if row[1] == 1 else False,
                "purchase_enabled": True if row[2] == 1 else False,
                "max_stock": int(row[3])
            } for row in rows
        }

    def fetch_dynamic_sell_through_metrics(self) -> pd.DataFrame:
        """
        Calculates Sell-Through Rate (STR) across all 20 catalog products dynamically.
        STR % = (Units Sold / (Units Sold + Current Inventory Stock)) * 100
        """
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        # Pull total quantities sold per item from the database ledger
        sales_query = "SELECT product_id, SUM(quantity) as units_sold FROM sales_ledger GROUP BY product_id"
        sales_df = pd.read_sql_query(sales_query, conn)

        # Pull the absolute breakdown of remaining sizes to get current stock levels
        stock_query = "SELECT product_id, SUM(stock_on_hand) as units_in_stock FROM size_matrix_stock GROUP BY product_id"
        stock_df = pd.read_sql_query(stock_query, conn)
        conn.close()

        # Import catalog configuration
        from catalog_config import CATALOG

        # Build out a fresh dataframe framework encompassing all 20 products
        rows = []
        for pid, details in CATALOG.items():
            # Get units sold for this product, defaulting to 0 if no sales recorded
            sold = int(sales_df[sales_df["product_id"] == pid]["units_sold"].iloc[0]) if not sales_df[
                sales_df["product_id"] == pid].empty else 0
            # Get current stock for this product, defaulting to 0 if not found
            stock = int(stock_df[stock_df["product_id"] == pid]["units_in_stock"].iloc[0]) if not stock_df[
                stock_df["product_id"] == pid].empty else 0

            # Calculate total allocated stock (sold + remaining)
            total_allocated = sold + stock
            # Calculate Sell-Through Rate percentage
            str_pct = round((sold / total_allocated * 100), 1) if total_allocated > 0 else 0.0

            # Formulate dynamic fashion inventory threshold status alerts based on STR
            if str_pct >= 70.0:
                status = "Hot Seller"
            elif str_pct <= 25.0 and total_allocated > 0:
                status = "Dead Inventory Risk"
            else:
                status = "Healthy"

            # Append product metrics to the results list
            rows.append({
                "product_name": details["name"],
                "sell_through_pct": str_pct,
                "status": status
            })

        # Create DataFrame from collected rows
        df_result = pd.DataFrame(rows)
        # Sort so top sellers natively surface at the peak positions of your charts
        return df_result.sort_values(by="sell_through_pct", ascending=False).reset_index(drop=True)

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
        """Queries the size matrix to pull the exact cumulative stock balance per product style."""
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Sum all stock on hand for each product ID
        cursor.execute(
            "SELECT product_id, SUM(stock_on_hand) as total_stock FROM size_matrix_stock GROUP BY product_id")
        rows = cursor.fetchall()
        conn.close()

        # Returns a mapped key-value database dictionary format e.g., {'P001': 42, 'P002': 0}
        return {row[0]: int(row[1]) for row in rows}

    def update_single_size_stock(self, pid: str, size: str, new_qty: int) -> None:
        """Natively locks explicit size numbers directly onto the hard drive ledger."""
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Update stock count for a specific product and size variant
        cursor.execute("""
            UPDATE size_matrix_stock 
            SET stock_on_hand = ? 
            WHERE product_id = ? AND size_variant = ?
        """, (new_qty, pid, size))
        # Save changes and close connection
        conn.commit()
        conn.close()


