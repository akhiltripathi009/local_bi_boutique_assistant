"""
Core infrastructure: Configuration, Logging, and Master Catalog.
"""
from src.core.config import (
    BASE_DIR, STORAGE_DIR, DB_DIR, EXPORTS_DIR, LOGS_DIR,
    DB_PATH, LOG_FILE, CRITICAL_STOCK_THRESHOLD, APP_TITLE, APP_VERSION
)
from src.core.logger import setup_logging
from src.core.catalog import CATALOG, generate_initial_inventory

__all__ = [
    "BASE_DIR", "STORAGE_DIR", "DB_DIR", "EXPORTS_DIR", "LOGS_DIR",
    "DB_PATH", "LOG_FILE", "CRITICAL_STOCK_THRESHOLD", "APP_TITLE", "APP_VERSION",
    "setup_logging", "CATALOG", "generate_initial_inventory"
]
