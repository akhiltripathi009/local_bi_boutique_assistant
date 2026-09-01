import sqlite3


def initialize_database():
    conn = sqlite3.connect("boutique_bi.db")
    cursor = conn.cursor()

    # 1. Create Sales Ledger Table
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

    # 2. Create Purchase Ledger Table
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

    conn.commit()
    conn.close()
    print("✅ Local SQLite database 'boutique_bi.db' initialized successfully!")


import sqlite3


def add_size_matrix_table():
    conn = sqlite3.connect("boutique_bi.db")
    cursor = conn.cursor()

    # Create an explicit size tracking catalog table matrix
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS size_matrix_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            size_variant TEXT NOT NULL, -- 'S', 'M', 'L', 'XL'
            stock_on_hand INTEGER NOT NULL,
            UNIQUE(product_id, size_variant)
        )
    """)

    # Pre-populate sizes for your 20 products if empty
    from catalog_config import CATALOG
    for pid in CATALOG:
        for size in ['S', 'M', 'L', 'XL']:
            # Seed standard items with stock, and out-of-stock items with 0
            initial_stock = 0 if int(pid[1:]) >= 16 else 15
            cursor.execute("""
                INSERT OR IGNORE INTO size_matrix_stock (product_id, size_variant, stock_on_hand)
                VALUES (?, ?, ?)
            """, (pid, size, initial_stock))

    conn.commit()
    conn.close()
    print("✅ Dynamic size matrix table initialized inside boutique_bi.db!")

if __name__ == "__main__":
    initialize_database()
    add_size_matrix_table()

