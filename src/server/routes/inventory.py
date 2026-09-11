from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import pandas as pd

from src.data.db_manager import DatabaseManager
from src.core.catalog import CATALOG, CATEGORIES

router = APIRouter(prefix="/api/inventory", tags=["Inventory & Warehouse"])

def get_db():
    return DatabaseManager()

class StockTransferRequest(BaseModel):
    product_id: str
    size_variant: str = "M"
    quantity: int = Field(gt=0, description="Quantity to transfer must be greater than 0")
    source_location: str = "Shop Floor" # or "Warehouse Reserve"
    dest_location: str = "Warehouse Reserve" # or "Shop Floor"
    performed_by: str = "Portal Admin"
    notes: Optional[str] = None

class AddProductRequest(BaseModel):
    product_id: str
    product_name: str
    category: str
    wholesale_cost: float = Field(gt=0)
    retail_price: float = Field(gt=0)
    competitor_price: float = Field(gt=0)
    competitor_name: str = "Global Luxury House"
    color: str = "Noir"
    initial_shop_stock: int = 15
    initial_warehouse_stock: int = 25

class ProcurementOrderRequest(BaseModel):
    product_name: str
    quantity: int = Field(gt=0)
    notes: Optional[str] = "Standard Restock Batch"

@router.get("/overview")
def get_inventory_overview() -> Dict[str, Any]:
    """Retrieves full dual-location inventory matrix (Shop Floor vs Warehouse Reserve)."""
    db = get_db()
    shop_matrix = db.get_size_matrix_stock()
    wh_matrix = db.get_warehouse_matrix_stock()
    shop_totals = db.get_current_stock_on_hand()
    wh_totals = db.get_warehouse_stock_on_hand()

    # Merge product styles list
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
            "safety_status": "CRITICAL LOW" if s_qty <= 15 else "HEALTHY"
        })

    # Detailed size matrix breakdowns
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
    """Transfers stock between Shop Floor and Warehouse Reserve with real-time balance validation."""
    db = get_db()
    source = "shop" if "shop" in req.source_location.lower() else "warehouse"
    dest = "warehouse" if "warehouse" in req.dest_location.lower() else "shop"
    
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
    """Adds a new catalog apparel style across Shop Floor and Warehouse Reserve."""
    db = get_db()
    shop_stock_map = {"S": req.initial_shop_stock, "M": req.initial_shop_stock, "L": req.initial_shop_stock, "XL": req.initial_shop_stock}
    wh_stock_map = {"S": req.initial_warehouse_stock, "M": req.initial_warehouse_stock, "L": req.initial_warehouse_stock, "XL": req.initial_warehouse_stock}

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
    """Orders any product from catalog in any quantity delivered to warehouse backroom."""
    db = get_db()
    
    # Locate product ID from product name or fallback
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
        destination="warehouse",
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
    """Returns the immutable audit log of inventory transfers."""
    db = get_db()
    transfers_df = db.get_stock_transfers(limit=limit)
    records = transfers_df.to_dict("records") if not transfers_df.empty else []
    return {
        "success": True,
        "count": len(records),
        "transfers": records
    }
