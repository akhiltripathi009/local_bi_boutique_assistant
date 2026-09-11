"""
src/server/routes/agent.py
==========================
FastAPI route controller for Shivi Autonomous AI Deep Boutique Agent.

Why Required:
- Orchestrates multi-step autonomous boutique operations: morning briefings, evening closing audits,
  curated fashion trend newsletters, promotional broadcasts, stockout watchdog alerts, and VIP birthday concierge.
- Enforces Human-in-the-Loop (HITL) steering approval queues for high-impact actions.
- Governs enterprise guardrails (PII redaction and promotional discount clamping) and live SMTP email delivery.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.data.db_manager import DatabaseManager
from src.deep_agent.orchestrator import ShiviDeepAgent
from src.deep_agent.delivery import EmailDeliveryService, WhatsAppDeliveryService
from src.deep_agent.guardrails import PIIGuardrail, DiscountSafetyGuardrail
from src.core.constants import (
    AgentActionType,
    ApprovalStatus,
    Actors,
    BrandDefaults,
    OperationalThresholds,
)

router = APIRouter(prefix="/api/agent", tags=["Shivi Deep Agent"])

# Singleton agent instance for server session
_agent_instance: Optional[ShiviDeepAgent] = None


def get_agent() -> ShiviDeepAgent:
    """
    Retrieves or initializes the server session's singleton Shivi Deep Agent.
    
    Why Required:
    Preserves in-memory conversational context, active hierarchical plans, and subagent state
    across sequential API invocations.
    
    Returns:
        ShiviDeepAgent: Initialized orchestrator instance.
    """
    global _agent_instance
    if _agent_instance is None:
        db = DatabaseManager()
        _agent_instance = ShiviDeepAgent(db_manager=db)
    return _agent_instance


class AgentActionRequest(BaseModel):
    """
    Request model for triggering specialized autonomous agent routines.
    
    Why Required:
    Validates the routine identifier, optional topic search query, patron ID, and dry-run flag.
    """
    action: str = Field(
        ...,
        description="Routine key: morning_opening, evening_closing, fashion_news, campaign_launch, stock_watchdog, birthday_concierge."
    )
    dry_run: bool = Field(False, description="When true, compiles messages/audits without dispatching real emails.")
    topic_query: Optional[str] = Field(None, description="Optional fashion trend topic filter for news routines.")
    customer_id: Optional[int] = Field(None, description="Optional target customer ID for personalized dispatches.")


class ApprovalActionRequest(BaseModel):
    """
    Request model for human executive review of queued high-impact actions.
    
    Why Required:
    Enforces explicit executive decision ('Approve' or 'Reject') and records reviewer identity.
    """
    decision: str = Field(..., description="Executive decision: 'Approve' or 'Reject'.")
    reviewed_by: str = Field(Actors.EXECUTIVE_ADMIN, description="Reviewer name or administrative role.")


class SendEmailRequest(BaseModel):
    """
    Request model for outbound email delivery via SMTP.
    
    Why Required:
    Supports single concierge dispatch or bulk batch delivery of personalized newsletters.
    """
    to_email: Optional[str] = Field(None, description="Recipient email address for single dispatch.")
    subject: Optional[str] = Field(None, description="Email subject line.")
    html_body: Optional[str] = Field(None, description="Rich HTML email content.")
    plain_body: Optional[str] = Field(None, description="Optional plaintext fallback.")
    customer_id: Optional[int] = Field(None, description="Target customer ID for audit ledger tracking.")
    customer_name: Optional[str] = Field(None, description="Patron name.")
    batch: bool = Field(False, description="True if dispatching a batch list of messages.")
    messages: Optional[List[Dict[str, Any]]] = Field(None, description="List of pre-curated message objects for batch dispatch.")


class EmailConfigRequest(BaseModel):
    """
    Request model for configuring SMTP server credentials and auto-send policies.
    
    Why Required:
    Ensures safe loading and persistence of SMTP host, port, credentials, and notification settings.
    """
    smtp_host: str = Field("smtp.gmail.com", description="SMTP server hostname.")
    smtp_port: int = Field(587, description="SMTP port (typically 587 for TLS).")
    smtp_user: str = Field("", description="SMTP account username or Gmail address.")
    smtp_pass: str = Field("", description="SMTP password or 16-character Google App Password.")
    smtp_from: Optional[str] = Field(None, description="Sender email address.")
    from_name: str = Field("Mishika Fashion Boutique Concierge", description="Display name for outgoing emails.")
    admin_email: str = Field("", description="Store manager email for receiving boardroom audit PDFs.")
    auto_send_admin_audits: bool = Field(True, description="Automatically email morning/evening PDF audits to admin.")
    auto_send_customer_emails: bool = Field(True, description="Automatically dispatch customer newsletters and perks.")


class TestEmailRequest(BaseModel):
    """
    Request model for validating SMTP connectivity via handshake test.
    
    Why Required:
    Provides immediate feedback on credentials before saving or triggering batch campaigns.
    """
    to_email: str = Field(..., description="Test recipient email address.")
    config: Optional[Dict[str, Any]] = Field(None, description="Optional unsaved config dictionary to test.")


class PIIRedactRequest(BaseModel):
    """
    Request model for PII redaction preview.
    
    Why Required:
    Tests sanitization of customer emails and phone numbers before logging or prompt transmission.
    """
    text: str = Field(..., description="Raw text containing potential sensitive PII.")


class ValidateDiscountRequest(BaseModel):
    """
    Request model for testing promotional markdown safety guardrails.
    
    Why Required:
    Tests the 50.0% discount clamping logic without modifying database records.
    """
    discount_pct: float = Field(..., description="Requested discount percentage.")
    is_superadmin: bool = Field(False, description="Whether super-admin override applies.")


@router.get("/status")
def get_agent_status() -> Dict[str, Any]:
    """
    Retrieves the current operational status of Shivi Deep Agent.
    
    Working:
    - Resolves active hierarchical goal plan.
    - Counts pending human approval items, memory entries, skills, and tools.
    - Inspects SMTP email configuration status.
    
    Why Required:
    - Feeds the AI Agent command center view with live telemetry and system health.
    
    Returns:
        Dict[str, Any]: Agent status payload with subagents, plan, and guardrail metrics.
    """
    agent = get_agent()
    plan = agent.get_or_create_default_plan()
    plan_dict = plan.to_dict() if plan else None
    pending_approvals = agent.steering.get_pending_queue()
    memories = agent.db.get_agent_memories(limit=50)
    email_conf = EmailDeliveryService.load_email_config()

    return {
        "success": True,
        "agent_name": "Shivi",
        "title": "Autonomous AI Deep Boutique Agent",
        "brand": BrandDefaults.BRAND_NAME,
        "current_plan": plan_dict,
        "subagents": [
            {"name": "ReportingSubagent", "role": "Opening/Closing Boardroom Audits & PDFs"},
            {"name": "TrendHunterSubagent", "role": "Live Fashion Runway News & Personalized Newsletters"},
            {"name": "CampaignDispatchSubagent", "role": "VIP Flash Broadcasts & Promotional Blasts"},
            {"name": "StockSafetyWatchdog", "role": "Back-in-Stock & Broken Size Curve Alerts"}
        ],
        "pending_approvals_count": len(pending_approvals),
        "recent_memories_count": len(memories),
        "skills_count": 4,
        "tools_count": 5,
        "guardrails_status": "Active & Enforced (PII Redaction & ≤50% Discount Cap)",
        "email_configured": email_conf.get("is_configured", False),
        "email_user": email_conf.get("smtp_user", "")
    }


@router.post("/run-action")
def run_agent_action(req: AgentActionRequest) -> Dict[str, Any]:
    """
    Executes a specialized autonomous Deep Agent routine with planning and memory retention.
    
    Working:
    - Normalizes action key and routes to corresponding subagent routine:
        - `morning_opening`: Generates opening briefing PDF and stock alerts.
        - `evening_closing`: Generates closing financial audit PDF and drawer reconciliation.
        - `fashion_news`: Curates live runway trends and drafts personalized client newsletters.
        - `campaign_launch`: Prepares promotional broadcasts for active campaigns.
        - `stock_watchdog`: Identifies replenishment needs and back-in-stock notifications.
        - `birthday_concierge`: Prepares bespoke anniversary and birthday perks.
    - Serializes PDF bytes safely and records step execution in active hierarchical plan.
    
    Why Required:
    - Core entry point for triggering Shivi Deep Agent's autonomous executive capabilities.
    
    Args:
        req (AgentActionRequest): Target routine and execution parameters.
        
    Returns:
        Dict[str, Any]: Result payload, updated plan state, and execution summary.
    """
    agent = get_agent()
    act = req.action.lower().replace("-", "_")

    if act in ["opening_briefing", "opening", AgentActionType.MORNING_OPENING]:
        res = agent.run_opening_routine()
    elif act in ["closing_audit", "closing", AgentActionType.EVENING_CLOSING, "eod_consolidation", "eod", "full_audit"]:
        res = agent.run_closing_routine()
    elif act in [AgentActionType.FASHION_NEWS, "trend_news", "news"]:
        res = agent.dispatch_trending_fashion_news(customer_id=req.customer_id, dry_run=req.dry_run)
    elif act in [AgentActionType.CAMPAIGN_LAUNCH, "campaign"]:
        res = agent.broadcast_campaign_launch(dry_run=req.dry_run)
    elif act in [AgentActionType.STOCK_WATCHDOG, "restock", "back_in_stock", "restock_alert"]:
        res = agent.check_and_notify_back_in_stock(dry_run=req.dry_run)
    elif act in [AgentActionType.BIRTHDAY_CONCIERGE, "birthday", "birthday_perks"]:
        res = agent.dispatch_birthday_perks(days_ahead=14, dry_run=req.dry_run)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown agent action: '{req.action}'.")

    response_payload = dict(res)
    if "pdf_bytes" in response_payload:
        response_payload["pdf_available"] = bool(response_payload["pdf_bytes"])
        del response_payload["pdf_bytes"]

    plan_dict = agent.current_plan.to_dict() if agent.current_plan else None

    return {
        "success": True,
        "action": req.action,
        "plan": plan_dict,
        "result": response_payload
    }


@router.get("/news-preview")
def get_news_preview(
    topic_query: Optional[str] = None,
    randomize: bool = False,
    customer_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Curates trending fashion news from live internet feeds with guaranteed fallback.
    
    Working:
    - Queries internet RSS feeds for runway and luxury couture topics.
    - If offline or unreachable, seamlessly falls back to curated luxury default news.
    - Generates personalized email HTML and WhatsApp 1-click text templates for patrons.
    
    Why Required:
    - Allows boutique staff to review and edit client news broadcasts prior to sending.
    
    Returns:
        Dict[str, Any]: Curated messages, live internet indicator flag, and source citation.
    """
    agent = get_agent()
    messages = agent.trend_subagent.curate_and_draft_fashion_news(
        query=topic_query,
        customer_id=customer_id,
        randomize=randomize
    )
    is_live = messages[0].get("is_live_internet", False) if messages else False
    news_source = messages[0].get("news_source", "Curated News") if messages else "Curated News"

    return {
        "success": True,
        "count": len(messages),
        "is_live_internet": is_live,
        "news_source": news_source,
        "messages": messages
    }


@router.post("/send-email")
def send_agent_email(req: SendEmailRequest) -> Dict[str, Any]:
    """
    Dispatches single or batch emails via SMTP and logs delivery into SQLite.
    
    Working:
    - Verifies SMTP credentials.
    - Executes TLS handshake and delivers messages.
    - Logs dispatches in `agent_communications` ledger.
    
    Why Required:
    - Enables automated multi-client marketing broadcasts and concierge communications.
    """
    agent = get_agent()
    conf = EmailDeliveryService.load_email_config()
    if not conf.get("is_configured"):
        raise HTTPException(
            status_code=400,
            detail="Gmail SMTP not configured. Please enter your Gmail address and 16-character App Password in Settings."
        )

    if req.batch:
        items = req.messages or []
        if not items:
            raise HTTPException(status_code=400, detail="No messages provided for batch email dispatch.")

        success_count = 0
        errors = []
        for m in items:
            to_addr = m.get("customer_email")
            sub = m.get("email_subject", req.subject or "Boutique Alert")
            html = m.get("email_html", req.html_body or "")
            if not to_addr or not html:
                continue

            ok, err_msg = EmailDeliveryService.send_smtp_email(to_email=to_addr, subject=sub, html_body=html)
            if ok:
                success_count += 1
                agent.db.save_agent_communication({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "customer_id": m.get("customer_id"),
                    "customer_name": m.get("customer_name", BrandDefaults.FALLBACK_CLIENT_NAME),
                    "channel": "Email",
                    "message_type": "Marketing",
                    "subject": sub,
                    "content": html,
                    "status": f"Sent (Gmail SMTP to {to_addr})"
                })
            else:
                errors.append(f"{to_addr}: {err_msg}")

        return {
            "success": True,
            "dispatched_count": success_count,
            "failed_count": len(errors),
            "errors": errors[:5]
        }
    else:
        if not req.to_email or not req.html_body:
            raise HTTPException(status_code=400, detail="to_email and html_body are required for single email dispatch.")

        sub = req.subject or f"{BrandDefaults.BRAND_NAME} Alert"
        ok, err_msg = EmailDeliveryService.send_smtp_email(
            to_email=req.to_email,
            subject=sub,
            html_body=req.html_body,
            plain_body=req.plain_body
        )
        if not ok:
            raise HTTPException(status_code=500, detail=f"Failed to send email: {err_msg}")

        agent.db.save_agent_communication({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "customer_id": req.customer_id,
            "customer_name": req.customer_name or BrandDefaults.FALLBACK_CLIENT_NAME,
            "channel": "Email",
            "message_type": "Direct Dispatch",
            "subject": sub,
            "content": req.html_body,
            "status": f"Sent (Gmail SMTP to {req.to_email})"
        })

        return {
            "success": True,
            "message": f"Email successfully delivered to {req.to_email} via Gmail SMTP!"
        }


@router.get("/email-config")
def get_email_config() -> Dict[str, Any]:
    """
    Retrieves current SMTP email configuration with masked passwords for safe UI display.
    """
    conf = EmailDeliveryService.load_email_config()
    masked_conf = dict(conf)
    if masked_conf.get("smtp_pass"):
        pwd = masked_conf["smtp_pass"]
        masked_conf["smtp_pass_masked"] = "•" * len(pwd) if len(pwd) <= 16 else "••••••••••••••••"
    return {
        "success": True,
        "config": masked_conf
    }


@router.post("/email-config")
def save_email_config(req: EmailConfigRequest) -> Dict[str, Any]:
    """
    Persists SMTP email configuration to disk storage and environment.
    """
    new_conf = {
        "smtp_host": req.smtp_host.strip(),
        "smtp_port": int(req.smtp_port),
        "smtp_user": req.smtp_user.strip(),
        "smtp_pass": req.smtp_pass.strip(),
        "smtp_from": (req.smtp_from or req.smtp_user).strip(),
        "from_name": req.from_name.strip(),
        "admin_email": req.admin_email.strip(),
        "auto_send_admin_audits": req.auto_send_admin_audits,
        "auto_send_customer_emails": req.auto_send_customer_emails
    }
    ok, msg = EmailDeliveryService.save_email_config(new_conf)
    if not ok:
        raise HTTPException(status_code=500, detail=msg)
    return {
        "success": True,
        "message": msg
    }


@router.post("/test-email")
def test_email_connection(req: TestEmailRequest) -> Dict[str, Any]:
    """
    Executes an active SMTP handshake test and sends a verification email.
    """
    conf = req.config or EmailDeliveryService.load_email_config()
    if not conf.get("smtp_user") or not conf.get("smtp_pass"):
        raise HTTPException(status_code=400, detail="Gmail address and App Password must be provided.")
    if not req.to_email:
        raise HTTPException(status_code=400, detail="Recipient email address is required.")

    ok, msg = EmailDeliveryService.test_smtp_connection(conf, to_email=req.to_email)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "success": True,
        "message": msg
    }


@router.post("/guardrails/redact-pii")
def redact_pii_preview(req: PIIRedactRequest) -> Dict[str, Any]:
    """
    Scans arbitrary text and redacts sensitive Personally Identifiable Information (emails and phones).
    """
    redacted = PIIGuardrail.redact_pii(req.text)
    return {
        "success": True,
        "original_text": req.text,
        "sanitized_text": redacted
    }


@router.post("/guardrails/validate-discount")
def validate_discount_preview(req: ValidateDiscountRequest) -> Dict[str, Any]:
    """
    Evaluates promotional markdown percentage against enterprise 50.0% safety boundary.
    """
    is_safe, eff_d, msg = DiscountSafetyGuardrail.validate_discount(req.discount_pct, is_superadmin=req.is_superadmin)
    return {
        "success": True,
        "requested_discount": req.discount_pct,
        "is_safe": is_safe,
        "effective_discount": eff_d,
        "message": msg
    }


@router.get("/approvals")
def get_pending_approvals() -> Dict[str, Any]:
    """
    Retrieves all pending Human-in-the-Loop steering actions awaiting review.
    """
    agent = get_agent()
    queue = agent.steering.get_pending_queue()
    return {
        "success": True,
        "count": len(queue),
        "approvals": queue
    }


@router.post("/approvals/{approval_id}/action")
def process_approval(approval_id: int, req: ApprovalActionRequest) -> Dict[str, Any]:
    """
    Approves or rejects a pending human-in-the-loop steering request.
    """
    agent = get_agent()
    dec = req.decision.lower().strip()
    if dec == "approve":
        ok, msg = agent.steering.approve_action(approval_id, reviewed_by=req.reviewed_by)
    elif dec == "reject":
        ok, msg = agent.steering.reject_action(approval_id, reviewed_by=req.reviewed_by)
    else:
        raise HTTPException(status_code=400, detail="Decision must be 'Approve' or 'Reject'.")

    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    return {
        "success": True,
        "message": msg,
        "approval_id": approval_id,
        "decision": req.decision
    }


@router.get("/communications")
def list_communications(limit: int = 50) -> Dict[str, Any]:
    """
    Returns audit logs of outbound emails and WhatsApp dispatches executed by Shivi Deep Agent.
    """
    agent = get_agent()
    df = agent.db.get_agent_communications(limit=limit)
    records = df.to_dict("records") if not df.empty else []
    return {
        "success": True,
        "count": len(records),
        "communications": records
    }
