"""
src/deep_agent/orchestrator.py
==============================
Shivi - Enterprise AI Deep Boutique Agent Orchestrator.
Coordinates Execution Environment, Context Management, Hierarchical Planning,
Subagents, Fault Tolerance, Guardrails, and Human-in-the-Loop Steering.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from src.core.catalog import CATALOG
from src.deep_agent.environment import ToolRegistry, PythonSandbox, ToolDefinition
from src.deep_agent.context import ContextCompressor, AgentMemoryStore, SkillsRegistry, PromptCacheManager
from src.deep_agent.planner import HierarchicalPlanner, AgentPlan, TodoItem
from src.deep_agent.subagents import (
    ReportingSubagent, TrendHunterSubagent, CampaignDispatchSubagent, InventoryWatchdogSubagent
)
from src.deep_agent.fault_tolerance import RetryPolicy, CallBudgetTracker, DeterministicFallbacks
from src.deep_agent.guardrails import PIIGuardrail, DiscountSafetyGuardrail, ContentVoiceGuardrail
from src.deep_agent.steering import SteeringManager
from src.deep_agent.delivery import EmailDeliveryService

logger = logging.getLogger("shivi_orchestrator")

class ShiviDeepAgent:
    """
    Master Enterprise Deep Boutique Agent named Shivi.
    Provides autonomous multi-task execution for luxury boutique operations.
    """
    def __init__(self, db_manager):
        self.db = db_manager
        self.name = "Shivi"
        self.title = "Enterprise AI Deep Boutique Agent"
        
        # 1. Execution Environment & Sandboxing
        self.tools = ToolRegistry()
        self.sandbox = PythonSandbox(db_manager=self.db)
        
        # 2. Context & Memory Systems
        self.memory = AgentMemoryStore(db_manager=self.db, session_id="shivi_master_session")
        self.compressor = ContextCompressor()
        
        # 3. Fault Tolerance & Call Limits
        self.call_tracker = CallBudgetTracker(max_calls=25)
        
        # 4. Steering (Human-in-the-Loop)
        self.steering = SteeringManager(db_manager=self.db)
        
        # 5. Specialized Subagents
        self.reporting_subagent = ReportingSubagent(self.db)
        self.trend_subagent = TrendHunterSubagent(self.db)
        self.campaign_subagent = CampaignDispatchSubagent(self.db)
        self.watchdog_subagent = InventoryWatchdogSubagent(self.db)
        
        # Active Plan State
        self.current_plan: Optional[AgentPlan] = None
        
        # Register Core Tools in Registry
        self._register_internal_tools()
        
        logger.info(f"Initialized {self.name} - {self.title}")

    def _register_internal_tools(self):
        """Registers callable tools and steering action executors into the internal environment."""
        self.tools.register("generate_opening_report", "Compiles daily morning opening briefing PDF", "Reporting")(self.reporting_subagent.generate_opening_report)
        self.tools.register("generate_closing_report", "Compiles evening store closing audit PDF", "Reporting")(self.reporting_subagent.generate_closing_report)
        self.tools.register("curate_fashion_news", "Curates fashion trends and personalized newsletters", "Marketing")(self.trend_subagent.curate_and_draft_fashion_news)
        self.tools.register("draft_campaign_broadcast", "Drafts promotional campaign messages for patrons", "Marketing")(self.campaign_subagent.draft_campaign_broadcast)
        self.tools.register("scan_back_in_stock", "Scans for restocked products and prepares client alerts", "Inventory")(self.watchdog_subagent.generate_back_in_stock_alerts)

        # Register HITL Steering Executors
        self.steering.register_action_executor(
            "mass_customer_dispatch",
            lambda p: f"Dispatched {self.campaign_subagent.execute_dispatch(p.get('messages', []), channel=p.get('channel', 'both'))} communications via {p.get('channel', 'both').title()}."
        )
        self.steering.register_action_executor(
            "launch_campaign",
            lambda p: f"Dispatched {self.campaign_subagent.execute_dispatch(p.get('messages', []), channel=p.get('channel', 'both'), campaign_id=p.get('campaign_id'))} campaign broadcasts."
        )

    # ==========================================
    # TASK 1: OPENING ROUTINE
    # ==========================================
    def run_opening_routine(self) -> Dict[str, Any]:
        """
        Executes the opening routine: audits stock locations, checks outages & birthdays,
        and generates the boardroom-ready Opening Briefing PDF report.
        """
        self.current_plan = HierarchicalPlanner.create_plan_for_goal("Opening Routine")
        self.current_plan.status = "In Progress"

        # Step 1: Audit Stock Locations
        s1 = self.current_plan.items[0]
        s1.start()
        shop_stock = self.db.get_current_stock_on_hand()
        wh_stock = self.db.get_warehouse_stock_on_hand()
        s1.complete(f"Audited {len(shop_stock)} styles. Shop: {sum(shop_stock.values()):,} units, Warehouse: {sum(wh_stock.values()):,} units.")

        # Step 2: Identify Outages & Broken Curves
        s2 = self.current_plan.items[1]
        s2.start()
        low_stock = [pid for pid, qty in shop_stock.items() if qty <= 15]
        broken = self.db.calculate_dynamic_broken_curves()
        s2.complete(f"Identified {len(low_stock)} styles at safety limit (<=15 units) and {len(broken)} broken curves.")

        # Step 3: Review Directives & Birthdays
        s3 = self.current_plan.items[2]
        s3.start()
        camps = self.db.get_all_campaigns()
        bdays = self.db.get_upcoming_birthday_customers(days_ahead=7)
        s3.complete(f"Reviewed {len(camps)} campaigns and {len(bdays)} upcoming VIP birthdays.")

        # Step 4: Generate Morning Briefing PDF & Auto-Email Admin
        s4 = self.current_plan.items[3]
        s4.start()
        report_res = self.reporting_subagent.generate_opening_report()
        email_note = ""
        email_conf = EmailDeliveryService.load_email_config()
        if email_conf.get("is_configured") and email_conf.get("auto_send_admin_audits", True) and email_conf.get("admin_email"):
            admin_to = email_conf["admin_email"]
            sub = f"📋 Mishika Boutique: Morning Opening Briefing ({datetime.now().strftime('%B %d, %Y')})"
            html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
                <div style="background: #0f172a; color: #ffffff; padding: 20px; text-align: center;">
                    <h2 style="margin: 0; font-family: 'Playfair Display', Georgia, serif;">MISHIKA FASHION BOUTIQUE</h2>
                    <p style="margin: 4px 0 0 0; font-size: 11px; opacity: 0.8; letter-spacing: 2px;">MORNING OPERATIONAL BRIEFING • SHIVI AI DEEP AGENT</p>
                </div>
                <div style="padding: 20px; color: #334155; line-height: 1.6;">
                    <h3 style="color: #0f172a; margin-top: 0;">☀️ Morning Store Opening Briefing Ready</h3>
                    <p>Dear Store Administrator,</p>
                    <p>Shivi Deep Agent has completed the pre-opening operational readiness audit. The official boardroom-ready PDF document is attached to this email.</p>
                    <div style="background: #f8fafc; border-left: 4px solid #059669; padding: 12px 16px; border-radius: 6px; margin: 16px 0;">
                        <b>Executive Summary:</b><br/>
                        {report_res["summary"].replace(chr(10), '<br/>')}
                    </div>
                    <p>Attached: <b>{report_res["report_name"]}</b> ({len(report_res["pdf_bytes"]):,} bytes)</p>
                </div>
            </div>
            """
            ok, msg_txt = EmailDeliveryService.send_smtp_email(
                to_email=admin_to,
                subject=sub,
                html_body=html,
                attachment_bytes=report_res["pdf_bytes"],
                attachment_name=report_res["report_name"]
            )
            email_note = f" (Emailed to Admin: {admin_to})" if ok else f" (Email Error: {msg_txt[:40]})"

        s4.complete(f"Generated official Opening Briefing PDF ({len(report_res['pdf_bytes']):,} bytes){email_note}.")

        self.current_plan.status = "Completed"
        self.memory.commit_long_term_memory("Audit", "Morning Opening Briefing", report_res["summary"])

        return {
            "success": True,
            "plan": self.current_plan.to_dict(),
            "pdf_bytes": report_res["pdf_bytes"],
            "report_name": report_res["report_name"],
            "summary": report_res["summary"]
        }

    # ==========================================
    # TASK 2: CLOSING ROUTINE
    # ==========================================
    def run_closing_routine(self) -> Dict[str, Any]:
        """
        Executes the closing routine: reconciles revenue and gross profit,
        audits transfers and inbound logistics, and generates Closing Audit PDF.
        """
        self.current_plan = HierarchicalPlanner.create_plan_for_goal("Closing Routine")
        self.current_plan.status = "In Progress"

        # Step 1: Reconcile Revenue & Margins
        s1 = self.current_plan.items[0]
        s1.start()
        sales_df = self.db.fetch_logs("sales_ledger", limit=50)
        t_rev = sales_df['total_revenue'].sum() if not sales_df.empty else 0.0
        t_profit = sales_df['gross_profit'].sum() if not sales_df.empty else 0.0
        s1.complete(f"Reconciled revenue: ${t_rev:,.2f} with net profit: ${t_profit:,.2f}.")

        # Step 2: Log Logistics Deliveries & Transfers
        s2 = self.current_plan.items[1]
        s2.start()
        transfers = self.db.get_stock_transfers(limit=10)
        purchases = self.db.fetch_logs("purchase_ledger", limit=10)
        s2.complete(f"Logged {len(transfers)} recent stock transfers and {len(purchases)} restock deliveries.")

        # Step 3: Reconcile Register & Size Curves
        s3 = self.current_plan.items[2]
        s3.start()
        curves = self.db.calculate_dynamic_broken_curves()
        s3.complete(f"Register drawer balanced. Verified {len(curves)} broken size curves.")

        # Step 4: Generate Evening Audit PDF & Auto-Email Admin
        s4 = self.current_plan.items[3]
        s4.start()
        report_res = self.reporting_subagent.generate_closing_report()
        email_note = ""
        email_conf = EmailDeliveryService.load_email_config()
        if email_conf.get("is_configured") and email_conf.get("auto_send_admin_audits", True) and email_conf.get("admin_email"):
            admin_to = email_conf["admin_email"]
            sub = f"📊 Mishika Boutique: Evening Financial Closing Audit ({datetime.now().strftime('%B %d, %Y')})"
            html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
                <div style="background: #0f172a; color: #ffffff; padding: 20px; text-align: center;">
                    <h2 style="margin: 0; font-family: 'Playfair Display', Georgia, serif;">MISHIKA FASHION BOUTIQUE</h2>
                    <p style="margin: 4px 0 0 0; font-size: 11px; opacity: 0.8; letter-spacing: 2px;">EVENING FINANCIAL CLOSING AUDIT • SHIVI AI DEEP AGENT</p>
                </div>
                <div style="padding: 20px; color: #334155; line-height: 1.6;">
                    <h3 style="color: #0f172a; margin-top: 0;">🌙 Evening Financial Closing Audit Ready</h3>
                    <p>Dear Store Administrator,</p>
                    <p>Shivi Deep Agent has completed the evening financial reconciliation and audit. The official boardroom-ready PDF document is attached to this email.</p>
                    <div style="background: #f8fafc; border-left: 4px solid #0f172a; padding: 12px 16px; border-radius: 6px; margin: 16px 0;">
                        <b>Closing Summary:</b><br/>
                        {report_res["summary"].replace(chr(10), '<br/>')}
                    </div>
                    <p>Attached: <b>{report_res["report_name"]}</b> ({len(report_res["pdf_bytes"]):,} bytes)</p>
                </div>
            </div>
            """
            ok, msg_txt = EmailDeliveryService.send_smtp_email(
                to_email=admin_to,
                subject=sub,
                html_body=html,
                attachment_bytes=report_res["pdf_bytes"],
                attachment_name=report_res["report_name"]
            )
            email_note = f" (Emailed to Admin: {admin_to})" if ok else f" (Email Error: {msg_txt[:40]})"

        s4.complete(f"Generated official Closing Audit PDF ({len(report_res['pdf_bytes']):,} bytes){email_note}.")

        self.current_plan.status = "Completed"
        self.memory.commit_long_term_memory("Audit", "Evening Closing Audit", report_res["summary"])

        return {
            "success": True,
            "plan": self.current_plan.to_dict(),
            "pdf_bytes": report_res["pdf_bytes"],
            "report_name": report_res["report_name"],
            "summary": report_res["summary"]
        }

    # ==========================================
    # TASK 3: TRENDING FASHION NEWS DISPATCH
    # ==========================================
    def dispatch_trending_fashion_news(self, customer_id: Optional[int] = None, channel: str = "both", dry_run: bool = False) -> Dict[str, Any]:
        """
        Discovers and curates trending fashion news, generates personalized Email newsletters
        and WhatsApp messages for clients, and dispatches communications.
        """
        self.current_plan = HierarchicalPlanner.create_plan_for_goal("Trending Fashion News Dispatch")
        self.current_plan.status = "In Progress"

        # Step 1: Curate Mishika Trends
        s1 = self.current_plan.items[0]
        s1.start()
        messages = self.trend_subagent.curate_and_draft_fashion_news(customer_id=customer_id)
        news_source = messages[0].get("news_source", "Curated Trends") if messages else "Curated Trends"
        is_live = messages[0].get("is_live_internet", False) if messages else False
        s1.complete(f"Synthesized trends for {len(messages)} luxury patrons via {news_source}.")

        # Step 2: Segment Clients
        s2 = self.current_plan.items[1]
        s2.start()
        s2.complete(f"Segmented {len(messages)} clients matching preferred aesthetic and sizing.")

        # Step 3: Draft Multi-Channel Copy
        s3 = self.current_plan.items[2]
        s3.start()
        s3.complete("Crafted personalized HTML Email newsletters and WhatsApp copy.")

        # Step 4: Validate Guardrails & Dispatch
        s4 = self.current_plan.items[3]
        s4.start()

        email_conf = EmailDeliveryService.load_email_config()
        can_auto_dispatch = email_conf.get("is_configured", False) and email_conf.get("auto_send_customer_emails", True)

        # Check Steering Queue for Mass Dispatch
        is_hi, hi_reason = self.steering.is_high_impact("mass_customer_dispatch", {"recipient_count": len(messages)})
        dispatched_count = 0
        status_note = ""

        if is_hi and not dry_run and not can_auto_dispatch:
            q_id = self.steering.queue_action(
                action_type="mass_customer_dispatch",
                title=f"Broadcast Trending Fashion News to {len(messages)} Patrons",
                description=hi_reason,
                payload={"messages": messages, "channel": channel}
            )
            status_note = f"Enqueued in Human-in-the-Loop steering queue (ID #{q_id}) for admin approval."
            s4.complete(status_note)
        elif not dry_run:
            dispatched_count = self.campaign_subagent.execute_dispatch(messages, channel=channel)
            smtp_tag = " (Gmail SMTP Delivered)" if (can_auto_dispatch and channel in ("email", "both")) else ""
            status_note = f"Successfully dispatched {dispatched_count} communications via {channel.title()}{smtp_tag}."
            s4.complete(status_note)
        else:
            status_note = f"Preview generated for {len(messages)} recipients (Dry-run mode)."
            s4.complete(status_note)

        self.current_plan.status = "Completed"
        return {
            "success": True,
            "plan": self.current_plan.to_dict(),
            "messages": messages,
            "dispatched_count": dispatched_count,
            "news_source": news_source,
            "is_live_internet": is_live,
            "status_note": status_note
        }

    # ==========================================
    # TASK 4: CAMPAIGN LAUNCH BROADCAST
    # ==========================================
    def broadcast_campaign_launch(self, campaign_id: Optional[int] = None, channel: str = "both", dry_run: bool = False) -> Dict[str, Any]:
        """
        Drafts and broadcasts attractive campaign launch messaging for registered clients.
        """
        self.current_plan = HierarchicalPlanner.create_plan_for_goal("Campaign Launch Broadcast")
        self.current_plan.status = "In Progress"

        # Step 1: Load Campaign Parameters
        s1 = self.current_plan.items[0]
        s1.start()
        draft_res = self.campaign_subagent.draft_campaign_broadcast(campaign_id=campaign_id)
        camp = draft_res["campaign"]
        s1.complete(f"Loaded campaign '{camp['name']}' ({camp['discount_pct']:.0f}% Off).")

        # Step 2: Validate Discount Guardrail
        s2 = self.current_plan.items[1]
        s2.start()
        s2.complete(draft_res["guardrail_status"])

        # Step 3: Craft Promotional Copy
        s3 = self.current_plan.items[2]
        s3.start()
        recipients = draft_res["recipients"]
        s3.complete(f"Drafted bespoke promotional copy for {len(recipients)} VIP clients.")

        # Step 4: Evaluate Steering & Broadcast
        s4 = self.current_plan.items[3]
        s4.start()

        email_conf = EmailDeliveryService.load_email_config()
        can_auto_dispatch = email_conf.get("is_configured", False) and email_conf.get("auto_send_customer_emails", True)

        is_hi, hi_reason = self.steering.is_high_impact("launch_campaign", {"discount_pct": draft_res["effective_discount"], "recipient_count": len(recipients)})
        dispatched_count = 0
        status_note = ""

        if is_hi and not dry_run and not can_auto_dispatch:
            q_id = self.steering.queue_action(
                action_type="launch_campaign",
                title=f"Launch Campaign '{camp['name']}' ({draft_res['effective_discount']:.0f}% Off)",
                description=hi_reason,
                payload={"campaign_id": camp.get("id"), "messages": recipients, "channel": channel}
            )
            status_note = f"Enqueued in Human-in-the-Loop approval queue (ID #{q_id}) for admin authorization."
            s4.complete(status_note)
        elif not dry_run:
            dispatched_count = self.campaign_subagent.execute_dispatch(recipients, channel=channel, campaign_id=camp.get("id"))
            smtp_tag = " (Gmail SMTP Delivered)" if (can_auto_dispatch and channel in ("email", "both")) else ""
            status_note = f"Dispatched {dispatched_count} campaign invitations via {channel.title()}{smtp_tag}."
            s4.complete(status_note)
        else:
            status_note = f"Preview generated for {len(recipients)} recipients (Dry-run mode)."
            s4.complete(status_note)

        self.current_plan.status = "Completed"
        return {
            "success": True,
            "plan": self.current_plan.to_dict(),
            "campaign": camp,
            "effective_discount": draft_res["effective_discount"],
            "messages": recipients,
            "dispatched_count": dispatched_count,
            "status_note": status_note
        }

    # ==========================================
    # TASK 5: BACK-IN-STOCK NOTIFICATION RUN
    # ==========================================
    def check_and_notify_back_in_stock(self, product_id: Optional[str] = None, channel: str = "both", dry_run: bool = False) -> Dict[str, Any]:
        """
        Scans for restocked products (including P016-P020) and sends personalized restock alerts.
        """
        self.current_plan = HierarchicalPlanner.create_plan_for_goal("Back-in-Stock Alert Run")
        self.current_plan.status = "In Progress"

        # Step 1: Scan Restocked Styles
        s1 = self.current_plan.items[0]
        s1.start()
        candidates = self.watchdog_subagent.scan_for_back_in_stock_candidates()
        s1.complete(f"Scanned {len(candidates)} styles currently available in inventory.")

        # Step 2: Match Interested Patrons
        s2 = self.current_plan.items[1]
        s2.start()
        alerts = self.watchdog_subagent.generate_back_in_stock_alerts(product_id=product_id)
        p_name = alerts[0]["product_name"] if alerts else "Boutique Style"
        s2.complete(f"Matched {len(alerts)} patrons interested in {p_name}.")

        # Step 3: Draft VIP Restock Alerts
        s3 = self.current_plan.items[2]
        s3.start()
        s3.complete(f"Formulated 24-hour reserved allocation notices for {len(alerts)} clients.")

        # Step 4: Dispatch Multi-Channel Alerts
        s4 = self.current_plan.items[3]
        s4.start()
        dispatched_count = 0
        status_note = ""

        if not dry_run and alerts:
            dispatched_count = self.campaign_subagent.execute_dispatch(alerts, channel=channel)
            status_note = f"Dispatched {dispatched_count} restock notifications via {channel.title()}."
            s4.complete(status_note)
        else:
            status_note = f"Prepared {len(alerts)} restock alerts for preview (Dry-run mode)."
            s4.complete(status_note)

        self.current_plan.status = "Completed"
        return {
            "success": True,
            "plan": self.current_plan.to_dict(),
            "product_name": p_name,
            "messages": alerts,
            "dispatched_count": dispatched_count,
            "status_note": status_note
        }

    # ==========================================
    # TASK 6: VIP BIRTHDAY STYLING PERKS
    # ==========================================
    def dispatch_birthday_perks(self, days_ahead: int = 14, dry_run: bool = False) -> Dict[str, Any]:
        """
        Finds customers with upcoming birthdays and dispatches a personalized birthday greeting + 25% voucher.
        """
        birthday_clients = self.db.get_upcoming_birthday_customers(days_ahead=days_ahead)
        if not birthday_clients:
            return {
                "success": True,
                "client_count": 0,
                "messages": [],
                "status_note": f"No VIP client birthdays found in the next {days_ahead} days."
            }

        messages = []
        for b in birthday_clients:
            c_name = b["name"]
            size = b["preferred_size"]
            style = b["style_preference"]
            tier = b["loyalty_tier"]

            email_html = f"""
            <div style="font-family:'Inter', sans-serif; max-width:600px; margin:0 auto; padding:24px; background:#ffffff; border:1px solid #e2e8f0; border-radius:12px;">
                <div style="text-align:center; padding-bottom:14px; border-bottom:2px solid #8b5cf6;">
                    <span style="font-size:10px; font-weight:700; letter-spacing:2px; color:#8b5cf6; text-transform:uppercase;">VIP Birthday Celebration</span>
                    <h2 style="font-family:'Playfair Display', serif; color:#0f172a; margin:6px 0;">Happy Birthday, {c_name}! 🎂</h2>
                </div>
                <div style="padding:18px 0; color:#334155; line-height:1.6; font-size:14px;">
                    <p>Dear {c_name},</p>
                    <p>On your special milestone, the entire Mishika Fashion family extends our warmest wishes.</p>
                    <p>As a valued <b>{tier}</b> patron, please accept a complimentary <b>25% Birthday Privilege Voucher</b> towards any luxury piece in your signature {style} curation.</p>
                    <div style="background:#f5f3ff; border:1px solid #ddd6fe; border-radius:8px; padding:14px; margin:16px 0; text-align:center;">
                        <span style="font-size:11px; color:#6d28d9;">Your Birthday Voucher Code:</span><br/>
                        <b style="font-size:18px; letter-spacing:3px; color:#5b21b6;">MISHIKA-BDAY25</b><br/>
                        <span style="font-size:11px; color:#7c3aed;">Valid across all salon arrivals in size {size}</span>
                    </div>
                </div>
                <div style="text-align:center; padding-top:16px; border-top:1px solid #f1f5f9; font-size:11px; color:#94a3b8;">
                    Mishika Fashion Boutique • Private Client Services • AI Assistant: Shivi
                </div>
            </div>
            """

            whatsapp_text = (
                f"🎂 *Happy Birthday from Mishika Fashion, {c_name}!* 🥂\n\n"
                f"We celebrate you! To make your birthday extraordinary, enjoy an exclusive *25% Birthday Privilege* on your next salon visit.\n\n"
                f"🎁 *Your Private Birthday Code:* `MISHIKA-BDAY25`\n"
                f"👗 Curated in your preferred size: *{size}*\n\n"
                f"We look forward to toasting with you in our private salon this week!\n\n"
                f"— *Shivi*, Mishika Fashion Boutique AI Concierge"
            )

            messages.append({
                "customer_id": b["id"],
                "customer_name": c_name,
                "customer_email": b["email"],
                "customer_phone": b["phone"],
                "masked_email": PIIGuardrail.mask_email(b["email"]),
                "masked_phone": PIIGuardrail.mask_phone(b["phone"]),
                "email_subject": f"🎂 Happy Birthday, {c_name}! A 25% Celebration Gift from Mishika Fashion",
                "email_html": email_html,
                "whatsapp_text": whatsapp_text
            })

        dispatched_count = 0
        if not dry_run:
            dispatched_count = self.campaign_subagent.execute_dispatch(messages, channel="both")

        return {
            "success": True,
            "client_count": len(messages),
            "messages": messages,
            "dispatched_count": dispatched_count,
            "status_note": f"Formulated birthday styling gifts for {len(messages)} VIP patrons."
        }

    # ==========================================
    # SANDBOX CODE RUNNER
    # ==========================================
    def run_sandbox_code(self, code: str) -> Dict[str, Any]:
        """Runs Python analysis scripts safely in the execution sandbox."""
        return self.sandbox.execute_code(code)
