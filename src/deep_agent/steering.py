"""
src/deep_agent/steering.py
==========================
Human-in-the-Loop (HITL) Steering & Governance for Shivi Deep Agent:
1. Intercepts high-impact actions and enqueues them for administrator approval.
2. Prevents unilateral execution of large bulk messages, high discounts, or massive stock transfers.
3. Provides full audit trail of approval timestamps and reviewer notes.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Callable

from src.core.constants import ApprovalStatus, Actors

logger = logging.getLogger("shivi_steering")

class SteeringManager:
    """
    Manages human-in-the-loop (HITL) approval workflows and safety gating for Shivi Deep Agent.
    
    Working:
    - Evaluates planned actions against strict impact thresholds (mass messaging, large procurement orders,
      high discount markdowns).
    - Automatically enqueues high-impact actions into the SQLite approval queue rather than executing immediately.
    - Executes registered callback handlers upon verified executive approval.
    
    Why Required:
    - Provides enterprise AI governance: autonomous agents can act freely on low-risk operational tasks
      (inventory audits, birthday lookups) while requiring human executive oversight on capital-allocating
      or brand-impacting actions.
    """
    # Thresholds defining high-impact operations requiring explicit review
    MASS_DISPATCH_THRESHOLD = 5         # Messages to >= 5 customers
    LARGE_TRANSFER_THRESHOLD = 40       # Transfers of >= 40 units
    LARGE_PROCUREMENT_COST = 1000.0     # Procurement spend >= $1,000
    HIGH_DISCOUNT_THRESHOLD = 30.0      # Markdowns >= 30%

    def __init__(self, db_manager):
        self.db = db_manager
        self._action_executors: Dict[str, Callable] = {}

    def register_action_executor(self, action_type: str, executor: Callable):
        """Registers a callback handler to execute an action once approved."""
        self._action_executors[action_type] = executor

    def is_high_impact(self, action_type: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determines whether a planned agent action requires human approval.
        """
        if action_type == "mass_customer_dispatch":
            count = payload.get("recipient_count", 0)
            if count >= self.MASS_DISPATCH_THRESHOLD:
                return True, f"Mass broadcast to {count} customers exceeds threshold of {self.MASS_DISPATCH_THRESHOLD} recipients."

        elif action_type == "stock_transfer":
            qty = payload.get("quantity", 0)
            if qty >= self.LARGE_TRANSFER_THRESHOLD:
                return True, f"Stock transfer of {qty} units exceeds safety threshold of {self.LARGE_TRANSFER_THRESHOLD} units."

        elif action_type == "procurement_order":
            qty = payload.get("quantity", 0)
            cost = payload.get("total_cost", 0.0)
            if cost >= self.LARGE_PROCUREMENT_COST or qty >= self.LARGE_TRANSFER_THRESHOLD:
                return True, f"Procurement order spend (${cost:,.2f}) or quantity ({qty}) exceeds steering limits."

        elif action_type == "launch_campaign":
            discount = payload.get("discount_pct", 0.0)
            if discount >= self.HIGH_DISCOUNT_THRESHOLD:
                return True, f"Promotional markdown of {discount:.0f}% meets high-impact discount threshold (&ge; {self.HIGH_DISCOUNT_THRESHOLD:.0f}%)."

        return False, "Standard operational action; automated execution permitted."

    def queue_action(self, action_type: str, title: str, description: str, payload: Dict[str, Any]) -> int:
        """Enqueues an action for administrator approval."""
        q_id = self.db.add_to_approval_queue(
            action_type=action_type,
            title=title,
            description=description,
            payload=payload,
            requested_by=Actors.DEEP_AGENT
        )
        logger.info(f"Queued action #{q_id} for Human-in-the-Loop review: [{action_type}] {title}")
        return q_id

    def get_pending_queue(self) -> List[Dict[str, Any]]:
        """Returns all actions awaiting administrator approval."""
        return self.db.get_pending_approvals()

    def approve_action(self, approval_id: int, review_notes: str = "") -> Tuple[bool, str]:
        """Approves a queued action and executes it if an executor is registered."""
        approvals = self.get_pending_queue()
        matched = [a for a in approvals if a["id"] == approval_id]
        if not matched:
            return False, f"Approval request #{approval_id} not found or already processed."

        action_item = matched[0]
        action_type = action_item["action_type"]
        payload = action_item["payload"]

        # Execute action handler if registered
        executor = self._action_executors.get(action_type)
        exec_msg = ""
        if executor:
            try:
                exec_result = executor(payload)
                exec_msg = f" Action executed: {exec_result}"
            except Exception as e:
                logger.error(f"Failed to execute approved action #{approval_id}: {e}")
                exec_msg = f" Action execution encountered error: {str(e)}"

        self.db.update_approval_status(approval_id, ApprovalStatus.APPROVED, review_notes + exec_msg)
        return True, f"Action #{approval_id} successfully approved.{exec_msg}"

    def reject_action(self, approval_id: int, review_notes: str = "") -> Tuple[bool, str]:
        """Rejects a queued action with optional reason."""
        success = self.db.update_approval_status(approval_id, ApprovalStatus.REJECTED, review_notes)
        if success:
            return True, f"Action #{approval_id} rejected by administrator."
        return False, f"Failed to reject action #{approval_id}."
