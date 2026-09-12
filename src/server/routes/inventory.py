"""
src/server/routes/inventory.py
==============================
FastAPI route controller for Boutique Inventory, Dual-Location Logistics, and Procurement.

Why Required:
- Implements the boutique's dual-location inventory model (Shop Floor vs. Warehouse Reserve).
- Manages inter-location stock transfers, dynamic style registration, and purchase orders.
- Prevents stockouts and inventory imbalances across the four standard size variants ('S', 'M', 'L', 'XL').
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import pandas as pd

from src.data.db_manager import DatabaseManager
from src.core.catalog import CATALOG, CATEGORIES
from src.core.constants import (
    StockLocation,
    ApparelSize,
    OperationalThresholds,
    CompetitorBrands,
    Actors,
)

router = APIRouter(prefix="/api/inventory", tags=["Inventory & Warehouse"])


def get_db() -> DatabaseManager:
    """
    Dependency provider for DatabaseManager.
    
    Returns:
        DatabaseManager: Initialized SQLite database manager.
    """
    return DatabaseManager()


class StockTransferRequest(BaseModel):
    """
    Request model for transferring units between Shop Floor and Warehouse Reserve.
    
    Why Required:
    Validates transfer quantities, size curve variants, and origin/destination locations
    before executing atomic database balance transfers.
    """
    product_id: str = Field(..., description="Target SKU identifier (e.g. 'P001').")
    size_variant: str = Field(ApparelSize.DEFAULT_SIZE, description="Specific apparel size ('S', 'M', 'L', 'XL') or 'ALL'.")
    quantity: int = Field(..., gt=0, description="Number of units to relocate (must be > 0).")
    source_location: str = Field(StockLocation.SHOP_FLOOR, description="Origin location ('Shop Floor' or 'Warehouse Reserve').")
    dest_location: str = Field(StockLocation.WAREHOUSE_RESERVE, description="Destination location ('Shop Floor' or 'Warehouse Reserve').")
    performed_by: str = Field(Actors.PORTAL_ADMIN, description="User or agent identity executing the transfer.")
    notes: Optional[str] = Field(None, description="Optional operational notes or restocking reason.")


class AddProductRequest(BaseModel):
    """
    Request model for provisioning a new merchandise style into the boutique catalog.
    
    Why Required:
    Validates wholesale cost, retail price, color aesthetics, and initial size distribution
    to keep catalog and stock matrices synchronized.
    """
    product_id: str = Field(..., description="Unique product code (e.g. 'P021').")
    product_name: str = Field(..., description="Editorial style title.")
    category: str = Field(..., description="Merchandise category (e.g. 'Outerwear', 'Dresses').")
    wholesale_cost: float = Field(..., gt=0, description="Procurement acquisition cost.")
    retail_price: float = Field(..., gt=0, description="Recommended retail price.")
    competitor_price: float = Field(..., gt=0, description="Benchmark competitor price.")
    competitor_name: str = Field(CompetitorBrands.GLOBAL_LUXURY, description="External competitor label.")
    color: str = Field("#2c3e50", description="Hex color code for UI visualization.")
    initial_shop_stock: int = Field(OperationalThresholds.CRITICAL_STOCK_THRESHOLD, ge=0, description="Units seeded per size on shop floor.")
    initial_warehouse_stock: int = Field(25, ge=0, description="Units seeded per size in warehouse reserve.")


class ProcurementOrderRequest(BaseModel):
    """
    Request model for submitting an external supplier restock order.
    
    Why Required:
    Enables reordering depleted inventory directly into warehouse reserve backrooms.
    """
    product_name: str = Field(..., description="Catalog style name or SKU to reorder.")
    quantity: int = Field(..., gt=0, description="Number of units to order from supplier.")
    notes: Optional[str] = Field("Standard Restock Batch", description="Purchase order justification or vendor PO notes.")


@router.get("/overview")
def get_inventory_overview() -> Dict[str, Any]:
    """
    Retrieves the complete dual-location inventory matrix across all boutique styles.
    
    Working:
    - Queries shop floor size matrix, warehouse stock matrix, and cumulative totals.
    - Evaluates critical safety stock status (flagged when shop units <= 15).
    - Calculates enterprise inventory valuation using wholesale cost bases.
    
    Why Required:
    - Provides real-time visibility into stock runways, backroom reserve depth,
      and broken size curves for store managers and Shivi Deep Agent.
      
    Returns:
        Dict[str, Any]: Catalog style summaries, dual matrices, and total unit aggregates.
    """
    db = get_db()
    shop_matrix = db.get_size_matrix_stock()
    wh_matrix = db.get_warehouse_matrix_stock()
    shop_totals = db.get_current_stock_on_hand()
    wh_totals = db.get_warehouse_stock_on_hand()

    all_products = []
    seen_pids = set()

    for pid, info in CATALOG.items():
        seen_pids.add(pid)
        p_name = info["name"]
        cat = info.get("category", "Luxury Apparel")
        cost = info.get("wholesale_cost", info.get("cost", 0.0))
        price = info.get("retail_price", info.get("price", 0.0))
        s_qty = shop_totals.get(pid, shop_totals.get(p_name, 0))
        w_qty = wh_totals.get(pid, wh_totals.get(p_name, 0))
        all_products.append({
            "product_id": pid,
            "product_name": p_name,
            "category": cat,
            "wholesale_cost": cost,
            "retail_price": price,
            "shop_stock": s_qty,
            "warehouse_stock": w_qty,
            "total_enterprise_units": s_qty + w_qty,
            "inventory_valuation": round((s_qty + w_qty) * cost, 2),
            "safety_status": "CRITICAL LOW" if s_qty <= OperationalThresholds.CRITICAL_STOCK_THRESHOLD else "HEALTHY"
        })

    shop_variants = shop_matrix.to_dict("records") if not shop_matrix.empty else []
    wh_variants = wh_matrix.to_dict("records") if not wh_matrix.empty else []

    return {
        "success": True,
        "products": all_products,
        "categories": CATEGORIES,
        "shop_matrix": shop_variants,
        "warehouse_matrix": wh_variants,
        "total_shop_units": sum(shop_totals.values()),
        "total_warehouse_units": sum(wh_totals.values()),
        "total_enterprise_units": sum(shop_totals.values()) + sum(wh_totals.values())
    }


@router.post("/transfer")
def transfer_stock(req: StockTransferRequest) -> Dict[str, Any]:
    """
    Transfers inventory between Shop Floor and Warehouse Reserve with atomic balance validation.
    
    Working:
    - Converts textual locations to standardized internal codes.
    - Validates source availability and executes atomic decrements/increments.
    - Logs an immutable record into `stock_transfers` ledger.
    
    Why Required:
    - Maintains strict separation between backroom reserve and retail merchandising floor,
      preventing stock phantom availability.
      
    Args:
        req (StockTransferRequest): Relocation request parameters.
        
    Returns:
        Dict[str, Any]: Transfer confirmation with affected locations and quantity.
    """
    db = get_db()
    source = StockLocation.CODE_SHOP if "shop" in req.source_location.lower() else StockLocation.CODE_WAREHOUSE
    dest = StockLocation.CODE_WAREHOUSE if "warehouse" in req.dest_location.lower() else StockLocation.CODE_SHOP
    
    success, message = db.transfer_stock(
        product_id=req.product_id,
        size_variant=req.size_variant,
        source=source,
        destination=dest,
        quantity=req.quantity,
        notes=req.notes or "",
        performed_by=req.performed_by
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "product_id": req.product_id,
        "size_variant": req.size_variant,
        "quantity": req.quantity,
        "source": req.source_location,
        "destination": req.dest_location
    }


@router.post("/add-product")
def add_new_product(req: AddProductRequest) -> Dict[str, Any]:
    """
    Creates and provisions a new luxury apparel style into active catalogs and inventory matrices.
    
    Working:
    - Distributes initial stock counts across all four size variants (S, M, L, XL).
    - Seeds SQLite tables (`custom_products`, `size_matrix_stock`, `warehouse_stock`, `competitor_benchmarks`).
    - Updates runtime memory CATALOG.
    
    Why Required:
    - Allows rapid catalog expansion for seasonal capsule drops without code modifications.
    
    Args:
        req (AddProductRequest): Full product specification.
        
    Returns:
        Dict[str, Any]: Registration confirmation payload.
    """
    db = get_db()
    shop_stock_map = {sz: req.initial_shop_stock for sz in ApparelSize.ALL_SIZES}
    wh_stock_map = {sz: req.initial_warehouse_stock for sz in ApparelSize.ALL_SIZES}

    success, message = db.add_new_product(
        product_id=req.product_id,
        name=req.product_name,
        cost=req.wholesale_cost,
        price=req.retail_price,
        color=req.color,
        category=req.category,
        initial_shop_stock=shop_stock_map,
        initial_warehouse_stock=wh_stock_map
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "product_id": req.product_id,
        "product_name": req.product_name
    }


@router.post("/procurement-order")
def place_procurement_order(req: ProcurementOrderRequest) -> Dict[str, Any]:
    """
    Submits a procurement replenishment order delivered directly to the warehouse backroom.
    
    Working:
    - Resolves SKU from name query.
    - Appends purchase record to `purchase_ledger` and increments warehouse reserve size matrix.
    
    Why Required:
    - Powers manual restock requests from store staff as well as automated watchdog replenishment.
    
    Args:
        req (ProcurementOrderRequest): Reorder quantity and style identifier.
        
    Returns:
        Dict[str, Any]: Purchase order confirmation with delivery destination.
    """
    db = get_db()
    
    target_pid = None
    for pid, item in CATALOG.items():
        if item.get("name", "").lower() == req.product_name.lower() or pid.lower() == req.product_name.lower():
            target_pid = pid
            break
    if not target_pid:
        target_pid = "P001"

    success, message = db.order_product(
        product_id=target_pid,
        quantity=req.quantity,
        destination=StockLocation.CODE_WAREHOUSE,
        notes=req.notes or ""
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "product_name": req.product_name,
        "product_id": target_pid,
        "quantity": req.quantity
    }


@router.get("/transfers")
def get_transfer_history(limit: int = 50) -> Dict[str, Any]:
    """
    Retrieves the immutable audit log of dual-location inventory movements.
    
    Working:
    - Queries `stock_transfers` table ordered by most recent transfer.
    
    Why Required:
    - Ensures total accountability and discrepancy tracking between shop floor and warehouse.
    
    Args:
        limit (int): Maximum number of log rows to return.
        
    Returns:
        Dict[str, Any]: List of audit transfer entries.
    """
    db = get_db()
    transfers_df = db.get_stock_transfers(limit=limit)
    records = transfers_df.to_dict("records") if not transfers_df.empty else []
    return {
        "success": True,
        "count": len(records),
        "transfers": records
    }


class CircuitControlUpdateRequest(BaseModel):
    product_id: str
    key: str
    value: Any


@router.get("/controls")
def get_circuit_controls() -> Dict[str, Any]:
    """
    Returns full Master Circuit Switchboard datasets:
    - Products with current shop & warehouse inventory balances
    - Circuit breakers (sales_enabled, purchase_enabled, max_stock)
    - Granular Size Matrix distribution across S, M, L, XL
    - Broken curve flags
    """
    db = get_db()
    controls_map = db.get_all_circuit_controls()
    shop_totals = db.get_current_stock_on_hand()
    wh_totals = db.get_warehouse_stock_on_hand()
    shop_matrix = db.get_size_matrix_stock()
    
    size_map = {}
    if not shop_matrix.empty and "product_id" in shop_matrix.columns:
        for _, row in shop_matrix.iterrows():
            pid = row["product_id"]
            if pid not in size_map:
                size_map[pid] = {}
            size_map[pid][str(row["size_variant"])] = int(row["stock_on_hand"])
            
    items = []
    categories = set()
    for pid, details in CATALOG.items():
        cat = details.get("category", "Luxury Apparel")
        categories.add(cat)
        ctrl = controls_map.get(pid, {"sales_enabled": True, "purchase_enabled": True, "max_stock": 100})
        s_qty = shop_totals.get(pid, shop_totals.get(details.get("name", ""), 0))
        w_qty = wh_totals.get(pid, wh_totals.get(details.get("name", ""), 0))
        p_sizes = size_map.get(pid, {"S": 0, "M": 0, "L": 0, "XL": 0})
        
        core_depleted = [sz for sz in ["S", "M", "L"] if p_sizes.get(sz, 0) <= 2]
        is_broken = len(core_depleted) >= 1
        
        items.append({
            "product_id": pid,
            "product_name": details.get("name", pid),
            "category": cat,
            "wholesale_cost": details.get("wholesale_cost", details.get("cost", 0.0)),
            "retail_price": details.get("retail_price", details.get("price", 0.0)),
            "shop_stock": s_qty,
            "warehouse_stock": w_qty,
            "total_stock": s_qty + w_qty,
            "is_low_stock": s_qty <= OperationalThresholds.CRITICAL_STOCK_THRESHOLD,
            "sales_enabled": bool(ctrl.get("sales_enabled", True)),
            "purchase_enabled": bool(ctrl.get("purchase_enabled", True)),
            "max_stock": int(ctrl.get("max_stock", 100)),
            "sizes": p_sizes,
            "is_broken_curve": is_broken,
            "missing_sizes": core_depleted
        })
        
    return {
        "success": True,
        "controls": items,
        "categories": ["All Categories"] + sorted(list(categories)),
        "total_low_stock": sum(1 for x in items if x["is_low_stock"]),
        "total_broken_curves": sum(1 for x in items if x["is_broken_curve"])
    }


@router.post("/controls/update")
def update_circuit_control_setting(req: CircuitControlUpdateRequest) -> Dict[str, Any]:
    """
    Updates operational guardrail circuit settings (sales_enabled, purchase_enabled, max_stock)
    in the SQLite store_circuit_controls table.
    """
    db = get_db()
    if req.product_id not in CATALOG:
        raise HTTPException(status_code=404, detail=f"Product '{req.product_id}' not found.")
        
    if req.key not in ["sales_enabled", "purchase_enabled", "max_stock"]:
        raise HTTPException(status_code=400, detail=f"Invalid circuit control key '{req.key}'.")
        
    val = req.value
    if req.key in ["sales_enabled", "purchase_enabled"]:
        val = bool(val)
    elif req.key == "max_stock":
        try:
            val = int(val)
            if val < 10:
                raise ValueError("max_stock must be at least 10.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid max_stock value: {e}")
            
    db.update_circuit_control(req.product_id, req.key, val)
    return {
        "success": True,
        "product_id": req.product_id,
        "key": req.key,
        "value": val,
        "message": f"Circuit breaker '{req.key}' updated to {val} for {req.product_id}."
    }

