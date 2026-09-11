"""
Core infrastructure: Configuration, Logging, Master Catalog, and Constants.
"""
from src.core.config import (
    BASE_DIR, STORAGE_DIR, DB_DIR, EXPORTS_DIR, LOGS_DIR,
    DB_PATH, LOG_FILE, CRITICAL_STOCK_THRESHOLD, APP_TITLE, APP_VERSION
)
from src.core.logger import setup_logging
from src.core.catalog import CATALOG, generate_initial_inventory
from src.core.constants import (
    DBTable, StockLocation, ApparelSize, CampaignStatus,
    ApprovalStatus, LoyaltyTier, SalesChannel, SimEventType,
    AgentActionType, OperationalThresholds, CompetitorBrands,
    Actors, BrandDefaults
)

__all__ = [
    "BASE_DIR", "STORAGE_DIR", "DB_DIR", "EXPORTS_DIR", "LOGS_DIR",
    "DB_PATH", "LOG_FILE", "CRITICAL_STOCK_THRESHOLD", "APP_TITLE", "APP_VERSION",
    "setup_logging", "CATALOG", "generate_initial_inventory",
    "DBTable", "StockLocation", "ApparelSize", "CampaignStatus",
    "ApprovalStatus", "LoyaltyTier", "SalesChannel", "SimEventType",
    "AgentActionType", "OperationalThresholds", "CompetitorBrands",
    "Actors", "BrandDefaults"
]
