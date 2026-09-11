from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.data.db_manager import DatabaseManager
from src.core.catalog import CATEGORIES
from src.deep_agent.guardrails import DiscountSafetyGuardrail

router = APIRouter(prefix="/api/campaigns", tags=["Marketing Campaigns"])

def get_db():
    return DatabaseManager()

class CreateCampaignRequest(BaseModel):
    name: str = Field(min_length=3)
    description: str = Field(min_length=5)
    discount_pct: float = Field(ge=0.0, le=100.0)
    target_category: str = "All Categories"
    banner_tagline: Optional[str] = None
    launched_by: str = "Marketing Lead"

class UpdateCampaignStatusRequest(BaseModel):
    status: str # "Active", "Paused", "Ended"

@router.get("")
def list_campaigns() -> Dict[str, Any]:
    """Retrieves all promotional marketing campaigns."""
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
    """Launches a new promotional campaign with enterprise 50% discount cap guardrail."""
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
    """Updates campaign status ('Active', 'Paused', 'Ended')."""
    db = get_db()
    if req.status not in ["Active", "Paused", "Ended"]:
        raise HTTPException(status_code=400, detail="Status must be 'Active', 'Paused', or 'Ended'.")

    ok = db.update_campaign_status(campaign_id, req.status)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to update campaign status.")

    return {
        "success": True,
        "message": f"Campaign #{campaign_id} status changed to '{req.status}'.",
        "campaign_id": campaign_id,
        "status": req.status
    }
