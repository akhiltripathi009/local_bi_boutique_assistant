from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.data.db_manager import DatabaseManager
from src.deep_agent.orchestrator import ShiviDeepAgent
from src.deep_agent.delivery import EmailDeliveryService, WhatsAppDeliveryService
from src.deep_agent.guardrails import PIIGuardrail, DiscountSafetyGuardrail

router = APIRouter(prefix="/api/agent", tags=["Shivi Deep Agent"])

# Singleton agent instance for server session
_agent_instance: Optional[ShiviDeepAgent] = None

def get_agent() -> ShiviDeepAgent:
    global _agent_instance
    if _agent_instance is None:
        db = DatabaseManager()
        _agent_instance = ShiviDeepAgent(db_manager=db)
    return _agent_instance

class AgentActionRequest(BaseModel):
    action: str # "morning_opening", "evening_closing", "fashion_news", "campaign_launch", "stock_watchdog", "birthday_concierge"
    dry_run: bool = False
    topic_query: Optional[str] = None
    customer_id: Optional[int] = None

class ApprovalActionRequest(BaseModel):
    decision: str # "Approve" or "Reject"
    reviewed_by: str = "Executive Admin"

class SendEmailRequest(BaseModel):
    to_email: Optional[str] = None
    subject: Optional[str] = None
    html_body: Optional[str] = None
    plain_body: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    batch: bool = False
    messages: Optional[List[Dict[str, Any]]] = None

class EmailConfigRequest(BaseModel):
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: Optional[str] = None
    from_name: str = "Mishika Fashion Boutique Concierge"
    admin_email: str = ""
    auto_send_admin_audits: bool = True
    auto_send_customer_emails: bool = True

class TestEmailRequest(BaseModel):
    to_email: str
    config: Optional[Dict[str, Any]] = None

class PIIRedactRequest(BaseModel):
    text: str

class ValidateDiscountRequest(BaseModel):
    discount_pct: float
    is_superadmin: bool = False

@router.get("/status")
def get_agent_status() -> Dict[str, Any]:
    """Retrieves current autonomous agent status, active goal, subagents, and memory."""
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
        "brand": "Mishika Fashion Luxury Boutique",
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
    """Executes a specialized autonomous Deep Agent routine."""
    agent = get_agent()
    act = req.action.lower().replace("-", "_")

    if act in ["opening_briefing", "opening", "morning_opening"]:
        res = agent.run_opening_routine()
    elif act in ["closing_audit", "closing", "evening_closing"]:
        res = agent.run_closing_routine()
    elif act in ["eod_consolidation", "eod", "full_audit"]:
        res = agent.run_closing_routine()
    elif act in ["fashion_news", "trend_news", "news"]:
        res = agent.dispatch_trending_fashion_news(customer_id=req.customer_id, dry_run=req.dry_run)
    elif act in ["campaign_launch", "campaign"]:
        res = agent.broadcast_campaign_launch(dry_run=req.dry_run)
    elif act in ["stock_watchdog", "restock", "back_in_stock", "restock_alert"]:
        res = agent.check_and_notify_back_in_stock(dry_run=req.dry_run)
    elif act in ["birthday_concierge", "birthday", "birthday_perks"]:
        res = agent.dispatch_birthday_perks(days_ahead=14, dry_run=req.dry_run)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown agent action: '{req.action}'.")

    # Serialize PDF bytes if present for clean JSON response
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
def get_news_preview(topic_query: Optional[str] = None, randomize: bool = False, customer_id: Optional[int] = None) -> Dict[str, Any]:
    """Curates fashion trends and generates draft newsletters/WhatsApp messages."""
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
    """Sends single or batch emails via configured SMTP gateway and logs in SQLite."""
    agent = get_agent()
    conf = EmailDeliveryService.load_email_config()
    if not conf.get("is_configured"):
        raise HTTPException(status_code=400, detail="Gmail SMTP not configured. Please enter your Gmail address and 16-character App Password in Settings.")

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
                    "customer_name": m.get("customer_name", "VIP Patron"),
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

        sub = req.subject or "Mishika Fashion Boutique Alert"
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
            "customer_name": req.customer_name or "VIP Patron",
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
    """Retrieves current SMTP email configuration."""
    conf = EmailDeliveryService.load_email_config()
    # Mask password for secure UI display
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
    """Persists SMTP email configuration to storage and .env."""
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
    """Tests SMTP connection and sends live verification email."""
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
    """Applies real-time PII redaction to text."""
    redacted = PIIGuardrail.redact_pii(req.text)
    return {
        "success": True,
        "original_text": req.text,
        "sanitized_text": redacted
    }

@router.post("/guardrails/validate-discount")
def validate_discount_preview(req: ValidateDiscountRequest) -> Dict[str, Any]:
    """Validates promotional discount cap safety."""
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
    """Retrieves pending Human-in-the-Loop approval requests."""
    agent = get_agent()
    queue = agent.steering.get_pending_queue()
    return {
        "success": True,
        "count": len(queue),
        "approvals": queue
    }

@router.post("/approvals/{approval_id}/action")
def process_approval(approval_id: int, req: ApprovalActionRequest) -> Dict[str, Any]:
    """Authorizes or rejects a pending high-impact action."""
    agent = get_agent()
    if req.decision.lower() == "approve":
        ok, msg = agent.steering.approve_action(approval_id, reviewed_by=req.reviewed_by)
    elif req.decision.lower() == "reject":
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
    """Returns outbound email and WhatsApp communication logs."""
    agent = get_agent()
    df = agent.db.get_agent_communications(limit=limit)
    records = df.to_dict("records") if not df.empty else []
    return {
        "success": True,
        "count": len(records),
        "communications": records
    }
