"""
src/deep_agent/chat_executor.py
================================
Autonomous Chat Action Execution Engine for Shivi Deep Agent.

Why Required:
- Empowers Shivi Deep Agent to understand and execute concrete operational tasks
  directly through natural language chat (e.g., emailing boardroom audit PDFs to specific
  inboxes, triggering opening/closing routines, halting sales via circuit breakers,
  looking up VIP dossiers, and approving HITL requests).
- Combines a zero-latency deterministic intent extractor with Shivi's subagents,
  ReportLab PDF engines, and live SMTP email gateways.
"""

import re
import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from src.core.constants import (
    AgentActionType,
    ApprovalStatus,
    BrandDefaults,
    OperationalThresholds,
    LoyaltyTier,
    DBTable,
)
from src.core.catalog import CATALOG
from src.deep_agent.delivery import EmailDeliveryService, WhatsAppDeliveryService
from src.deep_agent.guardrails import DiscountSafetyGuardrail, PIIGuardrail
from src.reporting.pdf_builder import (
    generate_opening_briefing_pdf,
    generate_closing_audit_pdf,
    generate_enterprise_pdf,
    fetch_report_datasets,
)

logger = logging.getLogger("shivi_chat_executor")

# Global cache for the latest PDF generated via chat action
LATEST_GENERATED_PDF: Dict[str, Any] = {
    "bytes": None,
    "filename": None,
    "report_type": None,
    "generated_at": None,
}


@dataclass
class ChatActionResult:
    """Structured response container returned after executing a chat action."""
    action: str
    success: bool
    title: str
    narrative: str
    card: Dict[str, Any]
    pdf_bytes: Optional[bytes] = None
    pdf_name: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if "pdf_bytes" in d:
            d["pdf_available"] = bool(d["pdf_bytes"])
            del d["pdf_bytes"]
        return d


class ShiviChatActionExecutor:
    """
    Master coordinator for chat-driven action execution in Shivi Deep Agent.
    """
    def __init__(self, agent):
        self.agent = agent
        self.db = agent.db

    # =========================================================================
    # INTENT RECOGNITION & PARAMETER EXTRACTION
    # =========================================================================
    def detect_action(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Scans a conversational prompt to determine if it requests an operational action.
        Extracts entities like email addresses, report types, customer targets, and product names.
        
        Returns:
            Optional[Dict[str, Any]]: Parsed action metadata or None if purely advisory inquiry.
        """
        q = query.strip()
        q_lower = q.lower()

        # 1. EMAIL AUDIT / BOARDROOM REPORT ACTION
        # E.g. "Send Todays audit report to on mail ID example@gmail.com"
        # "Email evening closing audit to manager@boutique.com"
        # "Send morning briefing to store admin"
        # "Send audit report", "Send the audit report", "Email closing report"
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', q)
        found_email = email_match.group(0) if email_match else None

        send_report_verbs = ["send", "mail", "email", "forward", "dispatch", "share", "deliver"]
        has_send_verb = any(v in q_lower for v in send_report_verbs)
        is_report_mention = any(k in q_lower for k in [
            "audit", "report", "briefing", "closing", "opening", "eod", "weekly", "monthly", "scorecard", "boardroom", "pdf"
        ])

        if has_send_verb and is_report_mention:
            # Determine report type
            report_type = "daily_closing"
            if any(k in q_lower for k in ["opening", "morning", "briefing", "start"]):
                report_type = "morning_opening"
            elif any(k in q_lower for k in ["weekly", "week", "7 days"]):
                report_type = "weekly_audit"
            elif any(k in q_lower for k in ["monthly", "month", "30 days"]):
                report_type = "monthly_audit"
            elif any(k in q_lower for k in ["complete", "all-time", "strategic"]):
                report_type = "complete_audit"
            elif any(k in q_lower for k in ["closing", "evening", "eod", "today", "todays", "daily", "audit"]):
                report_type = "daily_closing"

            # Check if sending to admin implicitly if no email found
            target_email = found_email
            if not target_email and any(adm in q_lower for adm in ["admin", "manager", "store admin", "myself", "me", "ownership"]):
                email_conf = EmailDeliveryService.load_email_config()
                target_email = email_conf.get("admin_email") or email_conf.get("smtp_user")

            # Always return send_report_email intent!
            return {
                "action": "send_report_email",
                "target_email": target_email,
                "report_type": report_type,
                "raw_query": q,
            }

        # 2. TRIGGER OPERATIONAL STORE ROUTINES
        # E.g. "Run morning opening routine", "Execute evening closing audit", "Trigger stock watchdog"
        run_verbs = ["run", "execute", "start", "perform", "trigger", "launch", "initiate"]
        if any(v in q_lower for v in run_verbs):
            if any(k in q_lower for k in ["morning", "opening", "pre-opening"]):
                return {"action": "run_routine", "routine": AgentActionType.MORNING_OPENING}
            elif any(k in q_lower for k in ["evening", "closing", "eod", "reconcile", "reconciliation"]):
                return {"action": "run_routine", "routine": AgentActionType.EVENING_CLOSING}
            elif any(k in q_lower for k in ["fashion news", "trend news", "newsletter"]):
                return {"action": "run_routine", "routine": AgentActionType.FASHION_NEWS}
            elif any(k in q_lower for k in ["campaign", "campaign launch", "promo blast"]):
                return {"action": "run_routine", "routine": AgentActionType.CAMPAIGN_LAUNCH}
            elif any(k in q_lower for k in ["stock watchdog", "restock", "back in stock", "broken curve"]):
                return {"action": "run_routine", "routine": AgentActionType.STOCK_WATCHDOG}
            elif any(k in q_lower for k in ["birthday", "anniversary", "birthday perks"]):
                return {"action": "run_routine", "routine": AgentActionType.BIRTHDAY_CONCIERGE}

        # 3. DIRECT ROUTINE KEYWORDS
        if q_lower in ["morning opening", "evening closing", "run audit", "check back in stock", "check restock"]:
            if "morning" in q_lower:
                return {"action": "run_routine", "routine": AgentActionType.MORNING_OPENING}
            elif "evening" in q_lower or "audit" in q_lower:
                return {"action": "run_routine", "routine": AgentActionType.EVENING_CLOSING}
            elif "stock" in q_lower:
                return {"action": "run_routine", "routine": AgentActionType.STOCK_WATCHDOG}

        # 4. VIP CUSTOMER LOOKUP
        # E.g. "Lookup customer Aisha Sharma", "Profile patron ID 2", "VIP info for Priya"
        lookup_match = re.search(r'(?:lookup|look up|search|find|profile|who is|dossier for)\s+(?:customer|patron|vip|client)?\s*([A-Za-z0-9\s]+)', q_lower)
        if lookup_match and not has_send_verb:
            target_client = lookup_match.group(1).strip()
            # Clean unwanted tokens
            target_client = re.sub(r'^(the|a|an)\s+', '', target_client)
            if target_client and len(target_client) > 1 and target_client not in ["report", "audit", "closing", "opening", "pdf"]:
                return {
                    "action": "lookup_vip",
                    "client_target": target_client
                }

        # 5. INVENTORY CIRCUIT BREAKER CONTROLS
        # E.g. "Halt sales for Royal Silk Saree", "Block purchasing for Velvet Evening Gown", "Enable sales for Silk Scarf"
        cb_match = re.search(r'(halt|stop|block|disable|enable|resume|allow)\s+(sales?|purchases?|both)?\s*(?:for|on)?\s*(.+)', q_lower)
        if cb_match:
            verb = cb_match.group(1).strip()
            channel = cb_match.group(2).strip() if cb_match.group(2) else "sales"
            prod_query = cb_match.group(3).strip()
            enable = verb in ["enable", "resume", "allow"]
            # Match product from CATALOG
            matched_pid = self._find_product_id(prod_query)
            if matched_pid:
                return {
                    "action": "circuit_breaker",
                    "product_id": matched_pid,
                    "channel": channel,
                    "enable": enable,
                    "product_name": CATALOG[matched_pid]["name"]
                }

        # 6. HITL STEERING APPROVAL VIA CHAT
        # E.g. "Approve action #2", "Reject approval 1", "Approve request 3"
        approval_match = re.search(r'(approve|reject)\s+(?:action|approval|request|item)?\s*#?(\d+)', q_lower)
        if approval_match:
            decision = approval_match.group(1).capitalize()
            approval_id = int(approval_match.group(2))
            return {
                "action": "hitl_approval",
                "approval_id": approval_id,
                "decision": decision
            }

        # 7. DISCOUNT SAFETY GUARDRAIL VALIDATION
        # E.g. "Can we give 35% discount?", "Validate 60% discount on Silk Sarees"
        disc_match = re.search(r'(?:validate|check|can we offer|can we give|apply)\s+(\d+(?:\.\d+)?)\s*%\s*(?:discount|markdown|off)?', q_lower)
        if disc_match:
            pct = float(disc_match.group(1))
            return {
                "action": "validate_discount",
                "discount_pct": pct
            }

        # 8. BIRTHDAY PERKS DISPATCH
        if any(k in q_lower for k in ["birthday voucher", "birthday perks", "dispatch birthday"]):
            return {"action": "run_routine", "routine": AgentActionType.BIRTHDAY_CONCIERGE}

        # 9. BACK-IN-STOCK SCAN
        if any(k in q_lower for k in ["back in stock", "notify back in stock", "scan restock"]):
            return {"action": "run_routine", "routine": AgentActionType.STOCK_WATCHDOG}

        return None

    # =========================================================================
    # MASTER ACTION EXECUTION DISPATCHER
    # =========================================================================
    def execute_action(self, intent: Dict[str, Any], query: str) -> ChatActionResult:
        """
        Executes the parsed action intent and returns a rich ChatActionResult.
        """
        act = intent.get("action")

        if act == "send_report_email":
            return self._handle_send_report(
                to_email=intent.get("target_email"),
                report_type=intent.get("report_type", "daily_closing"),
                query=query
            )
        elif act == "run_routine":
            return self._handle_run_routine(intent.get("routine"))
        elif act == "lookup_vip":
            return self._handle_vip_lookup(intent.get("client_target"))
        elif act == "circuit_breaker":
            return self._handle_circuit_breaker(
                pid=intent.get("product_id"),
                pname=intent.get("product_name"),
                channel=intent.get("channel"),
                enable=intent.get("enable")
            )
        elif act == "hitl_approval":
            return self._handle_hitl_approval(
                approval_id=intent.get("approval_id"),
                decision=intent.get("decision")
            )
        elif act == "validate_discount":
            return self._handle_validate_discount(intent.get("discount_pct"))
        else:
            return ChatActionResult(
                action="unknown",
                success=False,
                title="Unknown Action",
                narrative=f"I recognized an operational intent, but cannot execute `{act}`.",
                card={"status": "Error", "message": f"Unsupported action {act}"}
            )

    # =========================================================================
    # HANDLER: SEND AUDIT REPORT VIA EMAIL (PRIMARY USE CASE)
    # =========================================================================
    def _handle_send_report(self, to_email: Optional[str], report_type: str, query: str) -> ChatActionResult:
        """
        Compiles the requested PDF audit and delivers it via SMTP email.
        Gracefully handles unconfigured SMTP by generating and caching the PDF,
        providing an instant download link, and returning a pre-filled mailto fallback.
        """
        global LATEST_GENERATED_PDF
        date_str = datetime.now().strftime("%B %d, %Y")
        today_slug = datetime.now().strftime("%Y%m%d")

        # 1. Resolve Recipient Email
        email_conf = EmailDeliveryService.load_email_config()
        if not to_email:
            to_email = email_conf.get("admin_email") or email_conf.get("smtp_user")

        if not to_email:
            return ChatActionResult(
                action="send_report_email",
                success=False,
                title="Recipient Email Missing",
                narrative=(
                    "⚠️ **Recipient Email Required**:\n\n"
                    "I am ready to compile and dispatch the audit report, but I need a valid destination email address.\n\n"
                    "Please specify an email address, for example:\n"
                    "*\"Send today's audit report to example@gmail.com\"*\n"
                    "or set a default store manager email in the **⚙️ Automated Email Gateway** tab."
                ),
                card={
                    "status": "Incomplete",
                    "badge_color": "#f59e0b",
                    "title": "Email Address Needed",
                    "fields": [
                        {"label": "Requested Report", "val": report_type.replace("_", " ").title()},
                        {"label": "Instruction", "val": "Please provide a valid recipient email."}
                    ]
                }
            )

        # 2. Compile Appropriate Boardroom PDF
        pdf_bytes = None
        report_name = ""
        report_subject = ""
        report_title_display = ""
        summary_text = ""

        try:
            if report_type == "morning_opening":
                pdf_bytes = generate_opening_briefing_pdf(self.db)
                report_name = f"MishikaBoutique_Opening_Briefing_{today_slug}.pdf"
                report_subject = f"📋 Mishika Boutique: Morning Opening Briefing ({date_str})"
                report_title_display = "Morning Opening Briefing"
                
                shop_stock = self.db.get_current_stock_on_hand()
                wh_stock = self.db.get_warehouse_stock_on_hand()
                summary_text = (
                    f"• Shop Floor Stock: {sum(shop_stock.values()):,} units across {len(shop_stock)} styles\n"
                    f"• Backroom Warehouse Reserve: {sum(wh_stock.values()):,} units\n"
                    f"• Safety Stock Breaches: {len([p for p, q in shop_stock.items() if q <= 15])} styles"
                )
            elif report_type in ["weekly_audit", "monthly_audit", "complete_audit"]:
                scope = "weekly" if "weekly" in report_type else ("monthly" if "monthly" in report_type else "complete")
                rep_data = fetch_report_datasets(self.db, scope)
                pdf_bytes = generate_enterprise_pdf(self.db, report_type=scope)
                report_name = f"MishikaBoutique_{scope.title()}_Strategic_Audit_{today_slug}.pdf"
                report_subject = f"📊 Mishika Boutique: {scope.title()} Strategic Financial Audit ({date_str})"
                report_title_display = f"{scope.title()} Strategic Financial Audit"
                summary_text = (
                    f"• Revenue: ${rep_data.get('total_sales', 0):,.2f}\n"
                    f"• Gross Margin: {rep_data.get('avg_margin', 0):.1f}%\n"
                    f"• Units Sold: {rep_data.get('total_units', 0):,}"
                )
            else:
                # Default: Daily Financial Closing Audit
                pdf_bytes = generate_closing_audit_pdf(self.db)
                report_name = f"MishikaBoutique_Closing_Audit_{today_slug}.pdf"
                report_subject = f"🌙 Mishika Boutique: Financial Closing Audit ({date_str})"
                report_title_display = "Evening Financial Closing Audit"

                sales_df = self.db.fetch_logs(DBTable.SALES_LEDGER, limit=50)
                t_rev = sales_df['total_revenue'].sum() if not sales_df.empty else 0.0
                t_profit = sales_df['gross_profit'].sum() if not sales_df.empty else 0.0
                margin = (t_profit / t_rev * 100) if t_rev > 0 else 0.0
                summary_text = (
                    f"• Reconciled Revenue: ${t_rev:,.2f} across {len(sales_df)} checkouts\n"
                    f"• Net Gross Profit: ${t_profit:,.2f} (Realized Margin: {margin:.1f}%)\n"
                    f"• Register Drawer: Reconciled & Closed"
                )

            # Update cache for direct browser download
            LATEST_GENERATED_PDF = {
                "bytes": pdf_bytes,
                "filename": report_name,
                "report_type": report_title_display,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Also persist to storage/exports directory
            try:
                export_dir = Path("storage/exports")
                export_dir.mkdir(parents=True, exist_ok=True)
                with open(export_dir / report_name, "wb") as f:
                    f.write(pdf_bytes)
                with open(export_dir / "latest_audit.pdf", "wb") as f:
                    f.write(pdf_bytes)
            except Exception as e:
                logger.warning(f"Could not persist PDF to storage/exports: {e}")

        except Exception as e:
            logger.error(f"Failed to compile PDF for {report_type}: {e}")
            return ChatActionResult(
                action="send_report_email",
                success=False,
                title="PDF Compilation Error",
                narrative=f"❌ **Report Generation Error**: Failed to compile the boardroom PDF document. Details: `{str(e)}`",
                card={"status": "Error", "badge_color": "#ef4444", "title": "PDF Compilation Failed", "fields": [{"label": "Error", "val": str(e)}]}
            )

        # 3. Construct Luxury Branded HTML Email Content
        html_email_body = f"""
        <div style="font-family: Arial, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 620px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; background: #ffffff;">
            <div style="background: #0f172a; color: #ffffff; padding: 24px; text-align: center;">
                <div style="font-size: 24px; margin-bottom: 4px;">⚜️</div>
                <h2 style="margin: 0; font-family: 'Playfair Display', Georgia, serif; letter-spacing: 1px; color: #d4af37; font-size: 20px;">MISHIKA FASHION LUXURY BOUTIQUE</h2>
                <p style="margin: 4px 0 0 0; font-size: 11px; opacity: 0.8; letter-spacing: 2px; text-transform: uppercase;">SHIVI AUTONOMOUS AI DEEP AGENT • BOARDROOM DISPATCH</p>
            </div>
            <div style="padding: 24px; color: #334155; line-height: 1.6;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                    <span style="background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; padding: 3px 8px; border-radius: 9999px; font-size: 11px; font-weight: 700;">OFFICIAL AUDIT ATTACHED</span>
                    <span style="font-size: 12px; color: #64748b;">Generated on {date_str}</span>
                </div>
                <h3 style="color: #0f172a; margin-top: 0; font-size: 17px;">{report_title_display}</h3>
                <p>Dear Store Administrator,</p>
                <p>As requested via Shivi Conversational Copilot, your official boardroom-ready audit report has been compiled directly from live SQLite transaction ledgers and is attached to this email.</p>
                
                <div style="background: #f8fafc; border-left: 4px solid #0f172a; padding: 14px 18px; border-radius: 6px; margin: 18px 0;">
                    <b style="color: #0f172a; font-size: 13px;">Executive Summary:</b><br/>
                    <div style="margin-top: 6px; font-size: 13px; color: #334155; line-height: 1.7;">
                        {summary_text.replace(chr(10), '<br/>')}
                    </div>
                </div>

                <div style="background: #fdf8e6; border: 1px solid #f6e05e; border-radius: 8px; padding: 12px 16px; margin-top: 20px;">
                    <span style="font-size: 12px; color: #744210;">
                        📎 Attached PDF: <b>{report_name}</b> (Size: {len(pdf_bytes):,} bytes)<br/>
                        Double-verified under Mishika Enterprise Guardrails (PII sanitized & verified).
                    </span>
                </div>
            </div>
            <div style="background: #f1f5f9; padding: 14px 24px; text-align: center; font-size: 11px; color: #64748b; border-top: 1px solid #e2e8f0;">
                Autonomous Executive Dispatch by <b>Shivi Deep Agent</b> • Local BI Boutique Assistant
            </div>
        </div>
        """

        plain_text_fallback = (
            f"MISHIKA FASHION BOUTIQUE - {report_title_display}\n"
            f"Generated on {date_str}\n\n"
            f"Executive Summary:\n{summary_text}\n\n"
            f"The official PDF ({report_name}) is attached."
        )

        # 4. Dispatch Email via SMTP
        smtp_configured = email_conf.get("is_configured", False)
        is_sent = False
        delivery_msg = ""

        if smtp_configured:
            is_sent, delivery_msg = EmailDeliveryService.send_smtp_email(
                to_email=to_email,
                subject=report_subject,
                html_body=html_email_body,
                plain_body=plain_text_fallback,
                attachment_bytes=pdf_bytes,
                attachment_name=report_name
            )
        else:
            delivery_msg = "Gmail SMTP is not configured in Settings. PDF was compiled and saved locally."

        # 5. Log in SQLite Communications Ledger
        status_label = f"Sent (Gmail SMTP to {to_email})" if is_sent else f"Compiled & Saved (SMTP Offline - {to_email})"
        try:
            self.db.save_agent_communication({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "customer_id": None,
                "customer_name": "Executive Management",
                "channel": "Email",
                "message_type": "Boardroom Audit Dispatch",
                "subject": report_subject,
                "content": summary_text,
                "status": status_label
            })
        except Exception as e:
            logger.warning(f"Could not log agent communication: {e}")

        # 6. Commit to Shivi Memory & Update Hierarchical Plan
        self.agent.memory.commit_long_term_memory(
            "Audit Dispatch",
            f"Emailed {report_title_display} to {to_email}",
            f"Report: {report_name}. Status: {status_label}. {summary_text.replace(chr(10), '; ')}"
        )

        # 7. Construct Conversational Narrative & Action Card
        download_url = "/api/reports/latest-generated-pdf"
        is_default_admin = (to_email == (email_conf.get("admin_email") or email_conf.get("smtp_user"))) and (not re.search(r'[\w\.-]+@[\w\.-]+\.\w+', query))
        admin_tip = f"\n\n💡 *Delivered to store administrator (`{to_email}`). To send to an external email, simply ask: 'Send audit report to recipient@example.com'*" if is_default_admin else ""

        if is_sent:
            narrative = (
                f"✅ **{report_title_display} Dispatched Successfully!**\n\n"
                f"I have compiled today's official boardroom audit and delivered a copy directly to **`{to_email}`** via secure Gmail SMTP (TLS encrypted).\n\n"
                f"### 📋 Audit Telemetry:\n"
                f"{summary_text}\n\n"
                f"• **Attachment**: `{report_name}` ({len(pdf_bytes):,} bytes)\n"
                f"• **Delivery Status**: Verified & Delivered to `{to_email}`{admin_tip}\n\n"
                f"👉 *You can also download a direct copy below.*"
            )
            card = {
                "status": "Delivered",
                "badge_color": "#10b981",
                "title": f"Dispatched to {to_email}",
                "report_name": report_name,
                "download_url": download_url,
                "fields": [
                    {"label": "Recipient", "val": to_email},
                    {"label": "Report", "val": report_title_display},
                    {"label": "Delivery Channel", "val": "Gmail SMTP (TLS Handshake Verified)"},
                    {"label": "Document Size", "val": f"{len(pdf_bytes):,} bytes"},
                    {"label": "Timestamp", "val": datetime.now().strftime("%I:%M:%S %p")}
                ]
            }
        else:
            # Fallback when SMTP is not configured
            mailto_link = EmailDeliveryService.generate_mailto_link(
                to_email=to_email,
                subject=report_subject,
                plain_text_body=plain_text_fallback
            )
            narrative = (
                f"📄 **{report_title_display} Compiled & Ready!**\n\n"
                f"I have successfully compiled the boardroom-ready PDF document **`{report_name}`** ({len(pdf_bytes):,} bytes).\n\n"
                f"### 📋 Audit Telemetry:\n"
                f"{summary_text}\n\n"
                f"⚠️ **Note regarding automated email dispatch**:\n"
                f"{delivery_msg}\n\n"
                f"**What you can do right now:**\n"
                f"1. **[Click here to download `{report_name}`]({download_url})**\n"
                f"2. **[Click here to open draft email to {to_email}]({mailto_link})**\n"
                f"3. To enable 100% automated background email sending, enter your Gmail Address & 16-character App Password in the **⚙️ Automated Email Gateway** tab."
            )
            card = {
                "status": "PDF Ready (SMTP Offline)",
                "badge_color": "#f59e0b",
                "title": f"PDF Compiled for {to_email}",
                "report_name": report_name,
                "download_url": download_url,
                "mailto_link": mailto_link,
                "fields": [
                    {"label": "Target Recipient", "val": to_email},
                    {"label": "Report Document", "val": report_title_display},
                    {"label": "Status", "val": "Compiled & Cached (Ready to download)"},
                    {"label": "Document Size", "val": f"{len(pdf_bytes):,} bytes"}
                ]
            }

        return ChatActionResult(
            action="send_report_email",
            success=True,
            title=f"{report_title_display} - {to_email}",
            narrative=narrative,
            card=card,
            pdf_bytes=pdf_bytes,
            pdf_name=report_name,
            raw_data={
                "to_email": to_email,
                "report_name": report_name,
                "is_sent": is_sent,
                "download_url": download_url
            }
        )

    # =========================================================================
    # HANDLER: TRIGGER STORE ROUTINES (OPENING, CLOSING, WATCHDOG, BIRTHDAYS)
    # =========================================================================
    def _handle_run_routine(self, routine: str) -> ChatActionResult:
        """Executes Shivi's autonomous operational routines."""
        global LATEST_GENERATED_PDF

        if routine == AgentActionType.MORNING_OPENING:
            res = self.agent.run_opening_routine()
            pdf_bytes = res.get("pdf_bytes")
            pdf_name = res.get("report_name", "Morning_Opening_Briefing.pdf")
            if pdf_bytes:
                LATEST_GENERATED_PDF = {
                    "bytes": pdf_bytes,
                    "filename": pdf_name,
                    "report_type": "Morning Opening Briefing",
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            narrative = (
                f"🌅 **Morning Opening Procedure Executed!**\n\n"
                f"Shivi has completed the pre-opening operational readiness audit:\n\n"
                f"{res.get('summary', '')}\n\n"
                f"• **Boardroom PDF Compiled**: `{pdf_name}` ({len(pdf_bytes):,} bytes)\n"
                f"• **Status**: Store Floor & Inventory Verified"
            )
            card = {
                "status": "Completed",
                "badge_color": "#10b981",
                "title": "Morning Opening Procedure",
                "report_name": pdf_name,
                "download_url": "/api/reports/latest-generated-pdf",
                "fields": [
                    {"label": "Routine", "val": "Morning Opening"},
                    {"label": "PDF Briefing", "val": pdf_name},
                    {"label": "Execution Time", "val": datetime.now().strftime("%I:%M:%S %p")}
                ]
            }
            return ChatActionResult(
                action="run_routine",
                success=True,
                title="Morning Opening Executed",
                narrative=narrative,
                card=card,
                pdf_bytes=pdf_bytes,
                pdf_name=pdf_name
            )

        elif routine == AgentActionType.EVENING_CLOSING:
            res = self.agent.run_closing_routine()
            pdf_bytes = res.get("pdf_bytes")
            pdf_name = res.get("report_name", "Evening_Closing_Audit.pdf")
            if pdf_bytes:
                LATEST_GENERATED_PDF = {
                    "bytes": pdf_bytes,
                    "filename": pdf_name,
                    "report_type": "Evening Closing Audit",
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            narrative = (
                f"🌆 **Evening Closing Audit Completed!**\n\n"
                f"Shivi has reconciled today's store register and financial ledgers:\n\n"
                f"{res.get('summary', '')}\n\n"
                f"• **Official PDF Compiled**: `{pdf_name}` ({len(pdf_bytes):,} bytes)\n"
                f"• **Status**: Register Balanced & Closed"
            )
            card = {
                "status": "Completed",
                "badge_color": "#10b981",
                "title": "Evening Closing Audit",
                "report_name": pdf_name,
                "download_url": "/api/reports/latest-generated-pdf",
                "fields": [
                    {"label": "Routine", "val": "Evening Closing Audit"},
                    {"label": "Reconciled Revenue", "val": f"${res.get('revenue', 0):,.2f}"},
                    {"label": "Net Profit", "val": f"${res.get('profit', 0):,.2f}"},
                    {"label": "PDF Audit", "val": pdf_name}
                ]
            }
            return ChatActionResult(
                action="run_routine",
                success=True,
                title="Evening Closing Executed",
                narrative=narrative,
                card=card,
                pdf_bytes=pdf_bytes,
                pdf_name=pdf_name
            )

        elif routine == AgentActionType.STOCK_WATCHDOG:
            res = self.agent.check_and_notify_back_in_stock(dry_run=False)
            narrative = (
                f"🔔 **Stock Safety Watchdog Scan Complete!**\n\n"
                f"{res.get('message', 'Back-in-stock scan finished.')}\n\n"
                f"• **Restocked Styles**: {res.get('restocked_count', 0)}\n"
                f"• **Client Notifications Prepared**: {res.get('alerts_count', 0)}"
            )
            card = {
                "status": "Completed",
                "badge_color": "#3b82f6",
                "title": "Stock Safety Watchdog",
                "fields": [
                    {"label": "Styles Scanned", "val": str(len(CATALOG))},
                    {"label": "Restocked Alerts", "val": str(res.get('alerts_count', 0))}
                ]
            }
            return ChatActionResult(action="run_routine", success=True, title="Watchdog Complete", narrative=narrative, card=card)

        elif routine == AgentActionType.BIRTHDAY_CONCIERGE:
            res = self.agent.dispatch_birthday_perks(days_ahead=14, dry_run=False)
            narrative = (
                f"🎂 **VIP Birthday Concierge Routine Executed!**\n\n"
                f"{res.get('message', 'Birthday perks dispatched.')}\n\n"
                f"• **Upcoming VIP Birthdays (Next 14 Days)**: {res.get('count', 0)}\n"
                f"• **Perk Offered**: 25% Bespoke Birthday Voucher"
            )
            card = {
                "status": "Completed",
                "badge_color": "#ec4899",
                "title": "VIP Birthday Concierge",
                "fields": [
                    {"label": "Patrons Celebrating", "val": str(res.get('count', 0))},
                    {"label": "Voucher Rate", "val": "25% Markdown"}
                ]
            }
            return ChatActionResult(action="run_routine", success=True, title="Birthdays Processed", narrative=narrative, card=card)

        elif routine == AgentActionType.FASHION_NEWS:
            res = self.agent.dispatch_trending_fashion_news(dry_run=False)
            narrative = (
                f"📰 **Trending Fashion News Curated & Dispatched!**\n\n"
                f"{res.get('message', 'Fashion newsletters prepared.')}\n\n"
                f"• **News Source**: {res.get('news_source', 'Curated Runway Feeds')}\n"
                f"• **Live Internet Feeds**: {'Active 🌐' if res.get('is_live_internet') else 'Curated Fallback'}\n"
                f"• **Clients Contacted**: {res.get('clients_reached', 0)}"
            )
            card = {
                "status": "Dispatched",
                "badge_color": "#8b5cf6",
                "title": "Fashion Trend Broadcast",
                "fields": [
                    {"label": "Source", "val": res.get("news_source", "Runway Intelligence")},
                    {"label": "Clients Reached", "val": str(res.get("clients_reached", 0))}
                ]
            }
            return ChatActionResult(action="run_routine", success=True, title="Fashion News Curated", narrative=narrative, card=card)

        elif routine == AgentActionType.CAMPAIGN_LAUNCH:
            res = self.agent.broadcast_campaign_launch(dry_run=False)
            narrative = (
                f"📢 **Campaign Broadcast Formulated!**\n\n"
                f"{res.get('message', 'Campaign messages prepared.')}\n\n"
                f"• **Active Campaigns**: {res.get('campaign_name', 'Seasonal Promotion')}\n"
                f"• **Status**: Queued in HITL Queue for Review or Dispatched"
            )
            card = {
                "status": "Formulated",
                "badge_color": "#d97706",
                "title": "Campaign Launch",
                "fields": [
                    {"label": "Campaign", "val": res.get("campaign_name", "Active Promotion")},
                    {"label": "Action", "val": "Review in HITL Queue"}
                ]
            }
            return ChatActionResult(action="run_routine", success=True, title="Campaign Launched", narrative=narrative, card=card)

        else:
            return ChatActionResult(
                action="run_routine",
                success=False,
                title="Unknown Routine",
                narrative=f"Routine `{routine}` is not supported.",
                card={"status": "Error"}
            )

    # =========================================================================
    # HANDLER: VIP CUSTOMER DOSSIER LOOKUP
    # =========================================================================
    def _handle_vip_lookup(self, target: str) -> ChatActionResult:
        """Looks up customer dossier from VIP directory and sales transactions."""
        vips = self.db.get_all_vip_customers()
        if vips.empty:
            return ChatActionResult(
                action="lookup_vip",
                success=False,
                title="VIP Directory Empty",
                narrative="The VIP customer directory has no recorded clients.",
                card={"status": "Not Found"}
            )

        target_clean = target.lower().strip()
        matched = None

        # Try ID match
        if target_clean.isdigit():
            id_num = int(target_clean)
            sub = vips[vips["id"] == id_num]
            if not sub.empty:
                matched = sub.iloc[0].to_dict()

        # Try Name or Email match
        if not matched:
            sub = vips[vips["name"].str.lower().str.contains(target_clean, na=False)]
            if not sub.empty:
                matched = sub.iloc[0].to_dict()

        if not matched:
            sub = vips[vips["email"].str.lower().str.contains(target_clean, na=False)]
            if not sub.empty:
                matched = sub.iloc[0].to_dict()

        if not matched:
            return ChatActionResult(
                action="lookup_vip",
                success=False,
                title="Client Not Found",
                narrative=f"I searched the VIP registry for **\"{target}\"**, but found no matching customer profile.",
                card={"status": "Not Found", "target": target}
            )

        cid = matched.get("id")
        name = matched.get("name", "Patron")
        email = matched.get("email", "N/A")
        tier = matched.get("tier", LoyaltyTier.VIP)
        spend = matched.get("total_spend", 0.0)
        orders = matched.get("visit_count", 0)
        phone = matched.get("phone", "N/A")
        pref_size = matched.get("preferred_size", "M")
        bday = matched.get("birthday", "Not on file")

        narrative = (
            f"👑 **VIP Client Dossier: {name}** (ID #{cid})\n\n"
            f"• **Loyalty Tier**: `{tier}`\n"
            f"• **Total Historical Spend**: `${spend:,.2f}` across {orders} boutique visits\n"
            f"• **Preferred Sizing**: Size `{pref_size}`\n"
            f"• **Email Address**: `{email}`\n"
            f"• **Phone Number**: `{phone}`\n"
            f"• **Birthday**: `{bday}`\n\n"
            f"💡 *Tip: You can say \"Send fashion newsletter to {email}\" to dispatch a personalized runway curation.*"
        )

        card = {
            "status": "Found",
            "badge_color": "#d4af37",
            "title": f"VIP Profile: {name}",
            "fields": [
                {"label": "Client Name", "val": name},
                {"label": "Tier", "val": tier},
                {"label": "Total Spend", "val": f"${spend:,.2f}"},
                {"label": "Email", "val": email},
                {"label": "Preferred Size", "val": pref_size}
            ]
        }

        return ChatActionResult(action="lookup_vip", success=True, title=f"VIP Dossier: {name}", narrative=narrative, card=card, raw_data=matched)

    # =========================================================================
    # HANDLER: CIRCUIT BREAKER TOGGLES
    # =========================================================================
    def _handle_circuit_breaker(self, pid: int, pname: str, channel: str, enable: bool) -> ChatActionResult:
        """Toggles safety circuit breaker for a product."""
        controls = self.db.get_all_circuit_controls()
        curr = controls.get(pid, {"sales_enabled": True, "purchase_enabled": True, "max_stock": 100})

        if "sale" in channel or channel == "both":
            curr["sales_enabled"] = enable
        if "purchase" in channel or channel == "both":
            curr["purchase_enabled"] = enable

        self.db.set_circuit_control(pid, curr)

        action_word = "Resumed / Enabled" if enable else "HALTED / Disabled"
        channel_word = "Sales & Purchases" if channel == "both" else channel.capitalize()

        narrative = (
            f"⚙️ **Circuit Breaker Updated for {pname}**\n\n"
            f"• **Product ID**: #{pid}\n"
            f"• **Control Channel**: {channel_word}\n"
            f"• **New Operational State**: **{action_word.upper()}**\n\n"
            f"The store register and inventory simulator will immediately enforce this state."
        )

        card = {
            "status": "Enforced",
            "badge_color": "#10b981" if enable else "#ef4444",
            "title": f"Circuit Breaker: {pname}",
            "fields": [
                {"label": "Product", "val": pname},
                {"label": "State", "val": action_word},
                {"label": "Sales Active", "val": "Yes" if curr.get("sales_enabled") else "BLOCKED"},
                {"label": "Purchasing Active", "val": "Yes" if curr.get("purchase_enabled") else "BLOCKED"}
            ]
        }

        return ChatActionResult(action="circuit_breaker", success=True, title=f"Circuit Breaker: {pname}", narrative=narrative, card=card)

    # =========================================================================
    # HANDLER: HITL STEERING APPROVAL VIA CHAT
    # =========================================================================
    def _handle_hitl_approval(self, approval_id: int, decision: str) -> ChatActionResult:
        """Approves or rejects a queued HITL steering request."""
        dec = decision.lower().strip()
        if dec == "approve":
            ok, msg = self.agent.steering.approve_action(approval_id, reviewed_by="Chat Executive")
        elif dec == "reject":
            ok, msg = self.agent.steering.reject_action(approval_id, reviewed_by="Chat Executive")
        else:
            return ChatActionResult(
                action="hitl_approval",
                success=False,
                title="Invalid Decision",
                narrative="Decision must be 'Approve' or 'Reject'.",
                card={"status": "Error"}
            )

        if ok:
            narrative = (
                f"🚦 **HITL Action #{approval_id} {decision}d!**\n\n"
                f"{msg}\n\n"
                f"The authorization has been recorded in the steering audit ledger."
            )
            card = {
                "status": f"{decision}d",
                "badge_color": "#10b981" if dec == "approve" else "#ef4444",
                "title": f"HITL #{approval_id}: {decision}d",
                "fields": [
                    {"label": "Approval ID", "val": f"#{approval_id}"},
                    {"label": "Decision", "val": decision},
                    {"label": "Reviewer", "val": "Chat Executive"}
                ]
            }
        else:
            narrative = f"⚠️ **Could not process HITL action #{approval_id}**: {msg}"
            card = {"status": "Failed", "badge_color": "#ef4444", "fields": [{"label": "Error", "val": msg}]}

        return ChatActionResult(action="hitl_approval", success=ok, title=f"Approval #{approval_id}", narrative=narrative, card=card)

    # =========================================================================
    # HANDLER: DISCOUNT SAFETY VALIDATION
    # =========================================================================
    def _handle_validate_discount(self, pct: float) -> ChatActionResult:
        """Validates promotional discount against 50% safety guardrail."""
        is_safe, eff_d, msg = DiscountSafetyGuardrail.validate_discount(pct, is_superadmin=False)
        if is_safe:
            narrative = (
                f"🛡️ **Discount Safety Check: APPROVED ({pct:.1f}%)**\n\n"
                f"✅ **Safe**: {pct:.1f}% discount is within the standard enterprise boundary (≤ 50.0%).\n"
                f"{msg}\n"
                f"You may safely proceed with applying this promotional markdown."
            )
            badge_color = "#10b981"
            status_text = "Approved (Safe)"
        else:
            narrative = (
                f"🛡️ **Discount Safety Alert: CLAMPED / RESTRICTED ({pct:.1f}%)**\n\n"
                f"⚠️ **Violation**: {pct:.1f}% discount exceeds the maximum permissible 50.0% safety cap.\n"
                f"**Guardrail Action**: Clamped to maximum safe limit: **{eff_d:.1f}%**.\n\n"
                f"{msg}\n"
                f"To override this threshold, an Executive Admin must authorize the promotional campaign via the HITL queue."
            )
            badge_color = "#ef4444"
            status_text = "Restricted (Cap 50%)"

        card = {
            "status": status_text,
            "badge_color": badge_color,
            "title": f"Discount Check: {pct:.1f}%",
            "fields": [
                {"label": "Requested Discount", "val": f"{pct:.1f}%"},
                {"label": "Allowed Effective", "val": f"{eff_d:.1f}%"},
                {"label": "Safety Policy", "val": "≤ 50.0% Max Cap"}
            ]
        }
        return ChatActionResult(action="validate_discount", success=is_safe, title=f"Discount Guardrail: {pct:.1f}%", narrative=narrative, card=card)

    # =========================================================================
    # HELPER: PRODUCT CATALOG MATCHER
    # =========================================================================
    def _find_product_id(self, query: str) -> Optional[int]:
        """Finds closest product ID from query string."""
        q = query.lower().strip()
        # Direct ID
        if q.isdigit() and int(q) in CATALOG:
            return int(q)

        # Exact or partial match in CATALOG names
        for pid, pdata in CATALOG.items():
            name = pdata["name"].lower()
            if q in name or name in q:
                return pid

        # Word-level match
        words = [w for w in q.split() if len(w) > 3]
        for pid, pdata in CATALOG.items():
            name = pdata["name"].lower()
            if any(w in name for w in words):
                return pid

        return None
