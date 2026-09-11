"""
src/core/constants.py
=====================
Centralized enterprise domain constants and enumerations for Local BI Boutique Assistant.

Why Required:
- Eliminates magic strings and hardcoded literals scattered across the codebase.
- Ensures strict consistency across database queries, simulation events, API payloads,
  analytics calculations, and UI presentation layers.
- Provides a single source of truth for business rules, operational thresholds,
  brand guidelines, and lifecycle statuses.
"""

from typing import Tuple, List, Dict


class DBTable:
    """
    Centralized SQLite table identifiers.
    
    Why Required:
    Prevents typos and disjointed table naming across data access, migrations,
    and analytical query layers.
    """
    SALES_LEDGER = "sales_ledger"
    PURCHASE_LEDGER = "purchase_ledger"
    COMPETITOR_BENCHMARKS = "competitor_benchmarks"
    SIZE_MATRIX_STOCK = "size_matrix_stock"
    WAREHOUSE_INVENTORY = "warehouse_inventory"
    WAREHOUSE_TRANSFERS = "warehouse_transfers"
    PROCUREMENT_ORDERS = "procurement_orders"
    PROMOTIONAL_CAMPAIGNS = "promotional_campaigns"
    VIP_CUSTOMERS = "vip_customers"
    COMMUNICATIONS_LOG = "communications_log"
    CIRCUIT_BREAKER_CONTROLS = "circuit_breaker_controls"
    AGENT_MEMORY = "agent_memory"
    HUMAN_APPROVAL_QUEUE = "human_approval_queue"

    ALL_TABLES: Tuple[str, ...] = (
        SALES_LEDGER,
        PURCHASE_LEDGER,
        COMPETITOR_BENCHMARKS,
        SIZE_MATRIX_STOCK,
        WAREHOUSE_INVENTORY,
        WAREHOUSE_TRANSFERS,
        PROCUREMENT_ORDERS,
        PROMOTIONAL_CAMPAIGNS,
        VIP_CUSTOMERS,
        COMMUNICATIONS_LOG,
        CIRCUIT_BREAKER_CONTROLS,
        AGENT_MEMORY,
        HUMAN_APPROVAL_QUEUE,
    )


class StockLocation:
    """
    Physical storage and merchandising locations within the boutique enterprise.
    
    Why Required:
    Enforces the dual-inventory architecture isolating customer-facing Shop Floor
    from backroom Warehouse Reserve to prevent inventory double-counting.
    """
    SHOP_FLOOR = "Shop Floor"
    WAREHOUSE_RESERVE = "Warehouse Reserve"

    # Normalized lowercase codes used in database queries & API dispatch
    CODE_SHOP = "shop"
    CODE_WAREHOUSE = "warehouse"


class ApparelSize:
    """
    Standard apparel sizing curve definitions.
    
    Why Required:
    Boutique luxury apparel operates on size curves (S, M, L, XL). Broken size
    curves (e.g., S and M sold out while L remains) hurt sell-through and require
    automated detection.
    """
    SMALL = "S"
    MEDIUM = "M"
    LARGE = "L"
    EXTRA_LARGE = "XL"

    ALL_SIZES: Tuple[str, ...] = (SMALL, MEDIUM, LARGE, EXTRA_LARGE)
    DEFAULT_SIZE: str = MEDIUM


class CampaignStatus:
    """
    Lifecycle states for promotional marketing campaigns.
    
    Why Required:
    Guarantees deterministic state transitions (Draft -> Active <-> Paused -> Ended)
    so the pricing engine only applies active promotional markdowns.
    """
    ACTIVE = "Active"
    PAUSED = "Paused"
    ENDED = "Ended"
    DRAFT = "Draft"

    ALL_STATUSES: Tuple[str, ...] = (ACTIVE, PAUSED, ENDED, DRAFT)


class ApprovalStatus:
    """
    Human-in-the-loop (HITL) steering approval states for autonomous agent actions.
    
    Why Required:
    High-impact operational actions (large purchase orders, heavy price cuts)
    must be queued for human executive review before autonomous dispatch.
    """
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

    ALL_STATUSES: Tuple[str, ...] = (PENDING, APPROVED, REJECTED)


class LoyaltyTier:
    """
    VIP patron clienteling and loyalty tiers.
    
    Why Required:
    Enables targeted marketing, concierge personalization, and automated birthday
    perks scaled by customer relationship tier.
    """
    VIP = "VIP"
    BLACK_CARD = "Black Card"
    GOLD_PATRON = "Gold Patron"
    PLATINUM_COUTURE = "Platinum Couture"
    DIAMOND_EXECUTIVE = "Diamond Executive"
    VIP_PLATINUM = "VIP Platinum"

    ALL_TIERS: Tuple[str, ...] = (
        VIP,
        BLACK_CARD,
        GOLD_PATRON,
        PLATINUM_COUTURE,
        DIAMOND_EXECUTIVE,
        VIP_PLATINUM,
    )


class SalesChannel:
    """
    Retail transaction points of origin.
    
    Why Required:
    Tracks sales provenance across physical salon, digital boutique, private trunk shows,
    and VIP concierge chats.
    """
    IN_STORE = "In-Store Boutique"
    ONLINE = "Online Atelier"
    TRUNK_SHOW = "Private Trunk Show"
    WHATSAPP = "WhatsApp VIP"

    DEFAULT = IN_STORE


class SimEventType:
    """
    Discrete event simulation event categories.
    
    Why Required:
    Categorizes ticks in the live store simulator for real-time dashboard badges,
    SSE streaming, and audit logging.
    """
    SALE = "Sale"
    PURCHASE = "Purchase"
    BLOCKED = "Blocked"
    IDLE = "Idle"
    ERROR = "Error"


class AgentActionType:
    """
    Named operational routines executable by Shivi Deep Agent.
    
    Why Required:
    Maps incoming REST API execution requests to specific autonomous agent routines.
    """
    MORNING_OPENING = "morning_opening"
    EVENING_CLOSING = "evening_closing"
    FASHION_NEWS = "fashion_news"
    CAMPAIGN_LAUNCH = "campaign_launch"
    STOCK_WATCHDOG = "stock_watchdog"
    BIRTHDAY_CONCIERGE = "birthday_concierge"

    ALL_ACTIONS: Tuple[str, ...] = (
        MORNING_OPENING,
        EVENING_CLOSING,
        FASHION_NEWS,
        CAMPAIGN_LAUNCH,
        STOCK_WATCHDOG,
        BIRTHDAY_CONCIERGE,
    )


class OperationalThresholds:
    """
    Business guardrail limits and inventory safety parameters.
    
    Why Required:
    Centralizes critical enterprise boundary constraints to protect boutique margins
    and prevent stockouts.
    """
    # Minimum shop floor stock before flagging urgent replenishment alert
    CRITICAL_STOCK_THRESHOLD: int = 15

    # Maximum promotional markdown percentage without executive override
    MAX_PERMISSIBLE_DISCOUNT: float = 50.0

    # Default lead time in days for replenishment supplier orders
    DEFAULT_LEAD_TIME_DAYS: float = 3.0

    # Z-score factor for 95% service level stock availability
    SERVICE_FACTOR_95_PCT: float = 1.65

    # Annual inventory holding cost percentage of wholesale cost
    ANNUAL_HOLDING_COST_RATE: float = 0.25

    # Target maximum inventory capacity per product style
    DEFAULT_MAX_STOCK: int = 150

    # Default restock batch size
    DEFAULT_RESTOCK_BATCH_QTY: int = 20


class CompetitorBrands:
    """
    External retail fashion competitor benchmark labels and relative pricing multiplier bands.
    
    Why Required:
    Simulates realistic price elasticity against luxury, contemporary, and fast-fashion rivals.
    """
    VELVET_AND_VINE = "Velvet & Vine Boutique"       # Luxury Designer (+15% to +35%)
    AVENUE_APPAREL = "Avenue Apparel"               # Contemporary Mid-Tier (-5% to +8%)
    MINIMALIST_THREAD = "Minimalist Thread Co."     # Fast Fashion / Budget (-15% to -30%)
    GLOBAL_LUXURY = "Global Luxury House"           # Benchmark reference

    TIER_MULTIPLIERS: Dict[str, Tuple[float, float]] = {
        VELVET_AND_VINE: (1.15, 1.35),
        AVENUE_APPAREL: (0.95, 1.08),
        MINIMALIST_THREAD: (0.70, 0.85),
    }


class Actors:
    """
    Default actor personas and administrative identities for audit logging.
    
    Why Required:
    Maintains traceability for stock transfers, campaign creation, and approval decisions.
    """
    PORTAL_ADMIN = "Portal Admin"
    MARKETING_LEAD = "Marketing Lead"
    EXECUTIVE_ADMIN = "Executive Admin"
    DEEP_AGENT = "Shivi Deep Agent"
    STORE_MANAGER = "Store Manager"


class BrandDefaults:
    """
    Luxury boutique branding, currency, and presentation defaults.
    
    Why Required:
    Ensures cohesive editorial styling across generated PDFs, email newsletters,
    and web views.
    """
    APP_TITLE = "Local BI Boutique Assistant"
    BRAND_NAME = "Mishika Fashion Luxury Boutique"
    CURRENCY_SYMBOL = "$"
    FALLBACK_CLIENT_NAME = "VIP Client"
    FALLBACK_CLIENT_EMAIL = "client@boutique.com"
    FALLBACK_CLIENT_PHONE = "+1-555-0100"
