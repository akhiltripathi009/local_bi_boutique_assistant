"""
src/server/routes/crm.py
========================
FastAPI route controller for Boutique Customer Relationship Management (CRM) and VIP Patrons.

Why Required:
- High-end luxury boutiques thrive on personalized clienteling: tracking high-net-worth patron
  profiles, lifetime spend, sizing requirements, style preferences, and upcoming birthdays.
- Enables multi-channel concierge communications (WhatsApp VIP and Email) while strictly respecting
  patron opt-in preferences.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import pandas as pd

from src.data.db_manager import DatabaseManager
from src.core.constants import LoyaltyTier

router = APIRouter(prefix="/api/crm", tags=["Customer CRM & VIP Patrons"])


def get_db() -> DatabaseManager:
    """
    Dependency provider for DatabaseManager.
    
    Returns:
        DatabaseManager: Initialized SQLite database manager.
    """
    return DatabaseManager()


class UpdateCustomerContactRequest(BaseModel):
    """
    Request model for updating VIP patron contact dossier and clienteling preferences.
    
    Why Required:
    Validates optional field mutations (phone, email, preferred sizing, loyalty tier, and opt-ins)
    before updating SQLite customer profile records.
    """
    name: Optional[str] = Field(None, description="Updated patron full name.")
    phone: Optional[str] = Field(None, description="International phone format (e.g. '+1-555-0101').")
    email: Optional[str] = Field(None, description="Email address.")
    preferred_size: Optional[str] = Field(None, description="Sizing preference ('S', 'M', 'L', 'XL').")
    style_preference: Optional[str] = Field(None, description="Aesthetic style taste (e.g. 'Minimalist Knitwear').")
    loyalty_tier: Optional[str] = Field(None, description="Client loyalty status tier.")
    opt_in_whatsapp: Optional[int] = Field(None, ge=0, le=1, description="1 if opted into WhatsApp concierge, 0 otherwise.")
    opt_in_email: Optional[int] = Field(None, ge=0, le=1, description="1 if opted into email dispatches, 0 otherwise.")


@router.get("/customers")
def list_customers(
    tier: Optional[str] = None,
    search: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves all boutique VIP customer profiles with tier filtering and full-text search.
    
    Working:
    - Queries `customers` table for all registered profiles.
    - Filters by loyalty tier if specified.
    - Applies multi-column search across name, email, phone, and style preference.
    
    Why Required:
    - Powers the VIP Patron directory in the Atelier CRM portal, allowing stylists
      to quickly access client information before salon consultations.
      
    Args:
        tier (Optional[str]): Loyalty tier filter (e.g., 'VIP Platinum') or None for all.
        search (Optional[str]): Keyword search string.
        
    Returns:
        Dict[str, Any]: List of matching customer records and count.
    """
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
    """
    Retrieves a 360-degree VIP client dossier including complete historical purchase ledger.
    
    Working:
    - Fetches customer base attributes (lifetime spend, tier, sizing, opt-ins) from SQLite.
    - Queries `sales_ledger` for all past transactions attributed to this customer ID.
    
    Why Required:
    - Gives boutique concierges and Shivi Deep Agent full transactional context to tailor
      bespoke styling recommendations and birthday perks.
      
    Args:
        customer_id (int): Primary key ID of the customer.
        
    Returns:
        Dict[str, Any]: Profile dictionary and chronological purchase history list.
    """
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
    """
    Updates client contact details, preferred apparel sizing, and communication opt-ins.
    
    Working:
    - Updates only specified fields in SQLite `customers` table.
    - Re-fetches and returns the fresh record.
    
    Why Required:
    - Allows clienteling stylists to record size changes or opt-in preferences during store visits.
    
    Args:
        customer_id (int): Target customer ID.
        req (UpdateCustomerContactRequest): Fields to update.
        
    Returns:
        Dict[str, Any]: Updated profile record and confirmation message.
    """
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
    """
    Identifies VIP patrons celebrating birthdays within an upcoming time window.
    
    Working:
    - Evaluates calendar month and day differences between today and patron date-of-birth (DOB).
    - Sorts patrons by closest upcoming birthday.
    
    Why Required:
    - Powers Shivi Deep Agent's automated birthday perk concierge routine and stylist reminders.
    
    Args:
        days_ahead (int): Forecast horizon window in days (default 14, max 60).
        
    Returns:
        Dict[str, Any]: List of patron birthday objects with days_until countdown.
    """
    db = get_db()
    birthdays = db.get_upcoming_birthday_customers(days_ahead=days_ahead)
    return {
        "success": True,
        "count": len(birthdays),
        "days_ahead": days_ahead,
        "birthdays": birthdays
    }
