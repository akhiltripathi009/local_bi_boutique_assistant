"""
src/deep_agent/planner.py
=========================
Hierarchical Planning & Task Delegation for Shivi Deep Agent:
1. Deconstructs complex retail management goals into executable Todo lists.
2. Tracks live execution state (Pending, In Progress, Completed, Failed).
3. Assigns tasks to specialized subagents for parallel, isolated execution.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("shivi_planner")

class TodoItem:
    """Represents a discrete step in Shivi's execution plan."""
    def __init__(self, step_id: int, title: str, description: str, subagent: str):
        self.step_id = step_id
        self.title = title
        self.description = description
        self.subagent = subagent
        self.status = "Pending"  # Pending, In Progress, Completed, Failed
        self.result: Optional[str] = None
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None

    def start(self):
        self.status = "In Progress"
        self.started_at = datetime.now().strftime("%H:%M:%S")

    def complete(self, result: str):
        self.status = "Completed"
        self.result = result
        self.completed_at = datetime.now().strftime("%H:%M:%S")

    def fail(self, error: str):
        self.status = "Failed"
        self.result = f"Error: {error}"
        self.completed_at = datetime.now().strftime("%H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "title": self.title,
            "description": self.description,
            "subagent": self.subagent,
            "status": self.status,
            "result": self.result,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


class AgentPlan:
    """Encapsulates an active hierarchical plan with sequential execution controls."""
    def __init__(self, plan_id: str, goal: str, items: List[TodoItem]):
        self.plan_id = plan_id
        self.goal = goal
        self.items = items
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status = "Pending"  # Pending, In Progress, Completed, Failed

    def get_next_pending_item(self) -> Optional[TodoItem]:
        for item in self.items:
            if item.status == "Pending":
                return item
        return None

    def is_finished(self) -> bool:
        return all(item.status in ("Completed", "Failed") for item in self.items)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "status": self.status,
            "created_at": self.created_at,
            "items": [item.to_dict() for item in self.items]
        }


class HierarchicalPlanner:
    """
    Deconstructs high-level business goals into planned task sequences
    and routes work to specialized subagents.
    """
    @classmethod
    def create_default_orchestration_plan(cls) -> AgentPlan:
        """Generates an initial active enterprise operational plan for live monitoring."""
        plan_id = f"plan_{int(time.time())}"
        items = [
            TodoItem(1, "Continuous Inventory & Broken Curve Surveillance", "Audit 20 catalog styles across Shop Floor and Warehouse Reserve", "InventoryWatchdogSubagent"),
            TodoItem(2, "VIP Clienteling & Birthday Concierge", "Track 20 high-net-worth patrons, styling preferences, and notification channels", "TrendHunterSubagent"),
            TodoItem(3, "Market Parity & Dynamic Markdown Guardrails", "Monitor competitor price indices (Velvet & Vine, Avenue Apparel) within 50% threshold", "CampaignDispatchSubagent"),
            TodoItem(4, "Autonomous Operational Audit & Reporting", "Compile boardroom-grade financial ledgers and executive PDF summaries", "ReportingSubagent")
        ]
        plan = AgentPlan(plan_id, "🧠 Autonomous Boutique Floor & VIP Client Orchestration", items)
        plan.status = "In Progress"
        items[0].complete("Audited 20 catalog styles across Shop Floor and Warehouse Reserve.")
        items[1].complete("Verified 20 VIP patrons, styling preferences, and notification channels.")
        items[2].start()
        return plan

    @classmethod
    def create_plan_for_goal(cls, goal: str) -> AgentPlan:
        plan_id = f"plan_{int(time.time())}"
        goal_lower = goal.lower()

        # 1. Opening Routine Plan
        if "opening" in goal_lower:
            items = [
                TodoItem(1, "Audit Stock Locations", "Inspect Shop Floor stock vs. Warehouse backroom reserves", "ReportingSubagent"),
                TodoItem(2, "Identify Outages & Broken Curves", "Detect styles <= 15 units and broken size curves", "InventoryWatchdogSubagent"),
                TodoItem(3, "Review Daily Directives & Birthdays", "Check active promotional campaigns and scheduled VIP birthdays", "TrendHunterSubagent"),
                TodoItem(4, "Generate Morning Briefing PDF", "Compile boardroom-ready Opening Briefing PDF for admin delivery", "ReportingSubagent")
            ]
            return AgentPlan(plan_id, "🌅 Boutique Daily Opening Operational Briefing", items)

        # 2. Closing Routine Plan
        elif "closing" in goal_lower:
            items = [
                TodoItem(1, "Audit Daily Revenue & Margins", "Reconcile daily customer checkouts, COGS, and profit margin %", "ReportingSubagent"),
                TodoItem(2, "Log Logistics Deliveries & Transfers", "Audit inbound supplier restocks and internal shop/warehouse shifts", "InventoryWatchdogSubagent"),
                TodoItem(3, "Reconcile Register & Size Curves", "Perform physical register drawer and size curve discrepancy check", "InventoryWatchdogSubagent"),
                TodoItem(4, "Generate Evening Audit PDF", "Compile official boardroom Closing Audit PDF for executive review", "ReportingSubagent")
            ]
            return AgentPlan(plan_id, "🌆 Boutique Daily Closing Financial & Operations Audit", items)

        # 3. Trending Fashion News Dispatch
        elif "fashion news" in goal_lower or "trend" in goal_lower:
            items = [
                TodoItem(1, "Curate Mishika Fashion Trends", "Synthesize seasonal runway trends (Silk, Cashmere, Power Tailoring, Bohemian)", "TrendHunterSubagent"),
                TodoItem(2, "Segment Clients by Preference", "Match trends with customer aesthetics, preferred sizes, and loyalty tiers", "TrendHunterSubagent"),
                TodoItem(3, "Draft Multi-Channel Copy", "Formulate luxury HTML Email newsletters and punchy WhatsApp messages", "TrendHunterSubagent"),
                TodoItem(4, "Validate Guardrails & Dispatch", "Run PII redaction and brand voice validation before client delivery", "CampaignDispatchSubagent")
            ]
            return AgentPlan(plan_id, "📰 Curated Trending Fashion Intelligence Dispatch", items)

        # 4. Campaign Launch Broadcast
        elif "campaign" in goal_lower:
            items = [
                TodoItem(1, "Load Campaign Parameters", "Retrieve campaign name, description, discount %, and target merchandise", "CampaignDispatchSubagent"),
                TodoItem(2, "Validate Discount Guardrail", "Verify requested discount does not breach 50% enterprise threshold", "CampaignDispatchSubagent"),
                TodoItem(3, "Craft Compelling Promotional Copy", "Draft bespoke VIP invitation copy for Email and WhatsApp", "CampaignDispatchSubagent"),
                TodoItem(4, "Evaluate Steering & Broadcast", "Check Human-in-the-Loop approval limits, then dispatch alerts to patrons", "CampaignDispatchSubagent")
            ]
            return AgentPlan(plan_id, "📢 Attractive Campaign Launch Broadcast", items)

        # 5. Back-in-Stock Restock Run
        elif "stock" in goal_lower or "restock" in goal_lower or "out of stock" in goal_lower:
            items = [
                TodoItem(1, "Scan Restocked Catalog Styles", "Identify products that recovered from 0 stock to healthy availability", "InventoryWatchdogSubagent"),
                TodoItem(2, "Match Interested Patrons", "Identify clients whose preferred sizes and categories match restocked items", "InventoryWatchdogSubagent"),
                TodoItem(3, "Draft VIP Restock Alerts", "Formulate personalized Back-in-Stock messages with 24-hour reserved holds", "CampaignDispatchSubagent"),
                TodoItem(4, "Dispatch Multi-Channel Alerts", "Send verified notifications via Email and WhatsApp", "CampaignDispatchSubagent")
            ]
            return AgentPlan(plan_id, "🔔 Back-in-Stock & Restock VIP Notification Run", items)

        # 6. Default Generic Multi-Step Plan
        else:
            items = [
                TodoItem(1, "Analyze Boutique State", f"Extract relevant store and inventory data for goal: {goal}", "ReportingSubagent"),
                TodoItem(2, "Synthesize Strategic Recommendations", "Evaluate operational tradeoffs and calculate financial metrics", "TrendHunterSubagent"),
                TodoItem(3, "Validate Safety & Guardrails", "Ensure compliance with enterprise policies, PII rules, and steering gates", "CampaignDispatchSubagent"),
                TodoItem(4, "Finalize Operational Output", "Produce final executive report and execute authorized tasks", "ReportingSubagent")
            ]
            return AgentPlan(plan_id, f"🎯 Strategic Directive: {goal}", items)
