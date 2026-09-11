from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, List, Optional
import pandas as pd

from src.data.db_manager import DatabaseManager

router = APIRouter(prefix="/api/crm", tags=["Customer CRM & VIP Patrons"])

def get_db():
    return DatabaseManager()

class UpdateCustomerContactRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    preferred_size: Optional[str] = None
    style_preference: Optional[str] = None
    loyalty_tier: Optional[str] = None
    opt_in_whatsapp: Optional[int] = None
    opt_in_email: Optional[int] = None

@router.get("/customers")
def list_customers(
    tier: Optional[str] = None,
    search: Optional[str] = None
) -> Dict[str, Any]:
    """Lists all boutique VIP customers with tier filtering and search."""
    db = get_db()
    df = db.get_all_customers()
    if df.empty:
        return {"success": True, "count": 0, "customers": []}

    if tier and tier != "All":
        df = df[df["loyalty_tier"] == tier]

    if search:
        s_lower = search.lower()
        mask = (
            df["name"].str.lower().str.contains(s_lower, na=False) |
            df["email"].str.lower().str.contains(s_lower, na=False) |
            df["phone"].str.contains(s_lower, na=False) |
            df["style_preference"].str.lower().str.contains(s_lower, na=False)
        )
        df = df[mask]

    records = df.to_dict("records")
    return {
        "success": True,
        "count": len(records),
        "customers": records
    }

@router.get("/customer/{customer_id}")
def get_customer_profile(customer_id: int) -> Dict[str, Any]:
    """Retrieves 360-degree VIP client dossier including purchase history."""
    db = get_db()
    profile = db.get_customer_by_id(customer_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Customer #{customer_id} not found.")

    history_df = db.get_customer_purchase_history(customer_id)
    history = history_df.to_dict("records") if not history_df.empty else []

    return {
        "success": True,
        "profile": profile,
        "purchases_count": len(history),
        "purchase_history": history
    }

@router.post("/customer/{customer_id}/update")
def update_customer_contact(
    customer_id: int,
    req: UpdateCustomerContactRequest
) -> Dict[str, Any]:
    """Updates client contact info, sizing, and multi-channel opt-in preferences."""
    db = get_db()
    success, message = db.update_customer_contact(
        customer_id=customer_id,
        phone=req.phone,
        email=req.email,
        name=req.name,
        preferred_size=req.preferred_size,
        style_preference=req.style_preference,
        loyalty_tier=req.loyalty_tier,
        opt_in_whatsapp=req.opt_in_whatsapp,
        opt_in_email=req.opt_in_email
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    updated = db.get_customer_by_id(customer_id)
    return {
        "success": True,
        "message": message,
        "customer": updated
    }

@router.get("/birthdays")
def get_upcoming_birthdays(days_ahead: int = Query(default=14, ge=1, le=60)) -> Dict[str, Any]:
    """Retrieves VIP patrons celebrating birthdays in the upcoming window."""
    db = get_db()
    birthdays = db.get_upcoming_birthday_customers(days_ahead=days_ahead)
    return {
        "success": True,
        "count": len(birthdays),
        "days_ahead": days_ahead,
        "birthdays": birthdays
    }
