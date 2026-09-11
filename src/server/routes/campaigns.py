"""
src/server/routes/campaigns.py
==============================
FastAPI route controller for Promotional Marketing Campaigns.

Why Required:
- Luxury boutiques depend on disciplined promotional events (private seasonal flash sales,
  category discounts, VIP appreciation weeks) to stimulate revenue without eroding brand equity.
- Enforces enterprise margin safety guardrails (capping discounts at <= 50.0%) to prevent
  catastrophic pricing dilution.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.data.db_manager import DatabaseManager
from src.core.catalog import CATEGORIES
from src.core.constants import CampaignStatus, Actors, OperationalThresholds
from src.deep_agent.guardrails import DiscountSafetyGuardrail

router = APIRouter(prefix="/api/campaigns", tags=["Marketing Campaigns"])


def get_db() -> DatabaseManager:
    """
    Dependency provider for DatabaseManager.
    
    Returns:
        DatabaseManager: Initialized SQLite database manager.
    """
    return DatabaseManager()


class CreateCampaignRequest(BaseModel):
    """
    Request model for provisioning a new promotional campaign.
    
    Why Required:
    Validates campaign naming, editorial description, discount percentage boundaries,
    and merchandise category targeting before inserting into the database.
    """
    name: str = Field(..., min_length=3, description="Campaign title (e.g., 'Autumn Cashmere Preview').")
    description: str = Field(..., min_length=5, description="Editorial description of the promotion.")
    discount_pct: float = Field(..., ge=0.0, le=100.0, description="Requested markdown percentage.")
    target_category: str = Field("All Categories", description="Targeted apparel category or 'All Categories'.")
    banner_tagline: Optional[str] = Field(None, description="Catchy promotional banner tagline for UI display.")
    launched_by: str = Field(Actors.MARKETING_LEAD, description="Identity of the initiator or agent.")


class UpdateCampaignStatusRequest(BaseModel):
    """
    Request model for mutating campaign lifecycle status.
    
    Why Required:
    Enforces deterministic state transitions ('Active', 'Paused', 'Ended') to control
    when the simulation engine and checkout systems apply promotional markdowns.
    """
    status: str = Field(..., description="Target lifecycle state ('Active', 'Paused', 'Ended').")


@router.get("")
def list_campaigns() -> Dict[str, Any]:
    """
    Retrieves all promotional campaigns and highlights the currently active campaign.
    
    Working:
    - Queries the database for all registered marketing promotions.
    - Resolves the single currently active promotion (if any) used by the POS engine.
    
    Why Required:
    - Feeds the Marketing & Campaigns management portal view with complete history and current status.
    
    Returns:
        Dict[str, Any]: List of campaign records, active campaign object, and category filters.
    """
    db = get_db()
    camps_df = db.get_all_campaigns()
    records = camps_df.to_dict("records") if not camps_df.empty else []
    active = db.get_active_campaign()
    return {
        "success": True,
        "count": len(records),
        "active_campaign": active,
        "campaigns": records,
        "categories": ["All Categories"] + CATEGORIES
    }


@router.post("/create")
def create_campaign(req: CreateCampaignRequest) -> Dict[str, Any]:
    """
    Launches a new promotional campaign with enterprise margin guardrail validation.
    
    Working:
    1. Intercepts requested discount and executes `DiscountSafetyGuardrail.validate_discount`.
    2. Clamps discount to enterprise maximum (50.0%) if exceeded, logging a warning.
    3. Persists campaign into SQLite and broadcasts status confirmation.
    
    Why Required:
    - Protects boutique margins by preventing unauthorized or erroneous markdown values (>50%)
      from being activated across the point-of-sale or simulation engine.
      
    Args:
        req (CreateCampaignRequest): Campaign payload with requested discount and targeting.
        
    Returns:
        Dict[str, Any]: Creation status, effective clamped discount, and guardrail warnings.
    """
    db = get_db()
    
    # 1. Enforce Guardrail
    is_safe, valid_discount, guardrail_msg = DiscountSafetyGuardrail.validate_discount(req.discount_pct)
    warning = guardrail_msg if not is_safe else None
    
    success, message = db.create_campaign(
        name=req.name,
        description=req.description,
        discount_pct=valid_discount,
        target_category=req.target_category,
        banner_tagline=req.banner_tagline,
        launched_by=req.launched_by
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "guardrail_warning": warning,
        "effective_discount": valid_discount,
        "discount_pct": valid_discount,
        "campaign_name": req.name
    }


@router.post("/{campaign_id}/status")
def update_campaign_status(campaign_id: int, req: UpdateCampaignStatusRequest) -> Dict[str, Any]:
    """
    Updates the operational lifecycle state of an existing promotional campaign.
    
    Working:
    - Validates target status against allowed lifecycle states (Active, Paused, Ended).
    - Updates SQLite record and triggers audit logging.
    
    Why Required:
    - Enables boutique staff to pause flash sales during inventory shortages or end completed promotions.
    
    Args:
        campaign_id (int): Primary key ID of the target campaign.
        req (UpdateCampaignStatusRequest): Container with desired status string.
        
    Returns:
        Dict[str, Any]: Confirmation payload with new status.
    """
    db = get_db()
    if req.status not in (CampaignStatus.ACTIVE, CampaignStatus.PAUSED, CampaignStatus.ENDED):
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of: '{CampaignStatus.ACTIVE}', '{CampaignStatus.PAUSED}', or '{CampaignStatus.ENDED}'."
        )

    ok = db.update_campaign_status(campaign_id, req.status)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to update campaign status.")

    return {
        "success": True,
        "message": f"Campaign #{campaign_id} status changed to '{req.status}'.",
        "campaign_id": campaign_id,
        "status": req.status
    }
