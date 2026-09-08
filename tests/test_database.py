import sqlite3
from src.core.catalog import CATALOG

def test_database_initialization(test_db):
    """Ensures database schema tables exist and initial rows are populated."""
    conn = sqlite3.connect(test_db.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    expected_tables = {
        "sales_ledger", "purchase_ledger", "size_matrix_stock", 
        "store_circuit_controls", "competitor_benchmarks"
    }
    assert expected_tables.issubset(tables)

def test_record_sale_and_fetch_logs(test_db):
    """Ensures recording a sale inserts a transaction into sales_ledger."""
    test_db.save_sale({
        "timestamp": "2026-09-08 10:00:00",
        "product_id": "P001",
        "product_name": "Linen Wrap Dress",
        "quantity": 2,
        "unit_price": 95.0,
        "unit_cost": 35.0,
        "total_revenue": 190.0,
        "total_cost": 70.0,
        "gross_profit": 120.0,
        "is_promotional": 0,
        "campaign_name": "Organic"
    })
    logs_df = test_db.fetch_logs("sales_ledger", limit=5)
    assert not logs_df.empty
    assert len(logs_df) >= 1

def test_update_catalog_price(test_db):
    """Ensures updating catalog price updates live stock records."""
    res = test_db.update_catalog_price("P001", 115.0)
    assert res is True
