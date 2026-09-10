"""
src/deep_agent/context.py
=========================
Context Management for Shivi Deep Agent:
1. Context compression & summarization for token optimization.
2. Episodic and semantic memory management (working memory + SQLite long-term store).
3. Dynamic skills registry for specialized domain knowledge.
4. Prompt caching and system prompt assembly.
"""

import json
import logging
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("shivi_context")

class ContextCompressor:
    """
    Compresses voluminous transactional ledgers, inventory states, and CRM tables
    into concise, high-density token summaries for LLM prompt ingestion.
    """
    @staticmethod
    def summarize_sales_state(sales_df: pd.DataFrame) -> str:
        """Compresses sales records into an executive operational overview."""
        if sales_df.empty:
            return "No sales transactions recorded in current period."
        total_rev = sales_df['total_revenue'].sum()
        total_profit = sales_df['gross_profit'].sum()
        margin = (total_profit / total_rev * 100) if total_rev > 0 else 0
        units = sales_df['quantity'].sum()
        top_sellers = sales_df.groupby('product_name')['quantity'].sum().sort_values(ascending=False).head(3)
        top_str = ", ".join([f"{name} ({qty} sold)" for name, qty in top_sellers.items()])
        return f"Total Revenue: ${total_rev:,.2f} | Net Profit: ${total_profit:,.2f} ({margin:.1f}% Margin) | Units Sold: {units} | Top Movers: {top_str}"

    @staticmethod
    def summarize_inventory_state(shop_stock: Dict[str, int], wh_stock: Dict[str, int]) -> str:
        """Summarizes dual-location inventory distribution."""
        total_shop = sum(shop_stock.values())
        total_wh = sum(wh_stock.values())
        low_stock = [pid for pid, qty in shop_stock.items() if qty <= 15]
        return f"Shop Floor Stock: {total_shop:,} units | Warehouse Reserve: {total_wh:,} units | Styles <= 15 units: {len(low_stock)} ({', '.join(low_stock[:5])})"

    @staticmethod
    def summarize_customers(customers_df: pd.DataFrame) -> str:
        """Summarizes VIP customer demographics and loyalty tiers."""
        if customers_df.empty:
            return "No customer profiles registered."
        vip_count = len(customers_df[customers_df['loyalty_tier'] == 'VIP Platinum'])
        gold_count = len(customers_df[customers_df['loyalty_tier'] == 'Gold'])
        silver_count = len(customers_df[customers_df['loyalty_tier'] == 'Silver'])
        total_spend = customers_df['total_spend'].sum()
        return f"20 VIP Registered Clients | Platinum: {vip_count}, Gold: {gold_count}, Silver: {silver_count} | Cumulative Client Spend: ${total_spend:,.2f}"


class AgentMemoryStore:
    """
    Episodic and Semantic memory store for Shivi.
    Maintains active working memory in-memory and persists permanent memories to SQLite.
    """
    def __init__(self, db_manager, session_id: str = "session_master"):
        self.db = db_manager
        self.session_id = session_id
        self._working_memory: Dict[str, Any] = {}

    def set_working_memory(self, key: str, value: Any):
        """Sets temporary session-scoped working memory."""
        self._working_memory[key] = value

    def get_working_memory(self, key: str, default=None) -> Any:
        return self._working_memory.get(key, default)

    def commit_long_term_memory(self, memory_type: str, key: str, value: str):
        """Persists a key insight, strategic decision, or audit outcome to SQLite."""
        try:
            self.db.save_agent_memory(self.session_id, memory_type, key, value)
            logger.info(f"Committed long-term memory: [{memory_type}] {key}")
        except Exception as e:
            logger.error(f"Error persisting memory: {e}")

    def recall_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves historical memories for contextual grounding."""
        try:
            return self.db.get_agent_memories(self.session_id, limit=limit)
        except Exception:
            return []


class SkillsRegistry:
    """
    Registry of pre-compiled domain skills with instructions, heuristics, and prompt fragments.
    """
    SKILLS = {
        "MerchandiseAuditSkill": {
            "name": "Merchandise Financial & Inventory Audit",
            "description": "Calculates sell-through velocity, GMROI, stock-to-sales ratios, and size curve harmony.",
            "heuristics": [
                "Always separate Shop Floor inventory (active sales) from Warehouse reserve.",
                "Flag any core size outage (S, M, L) as a Broken Size Curve.",
                "Recommend immediate warehouse replenishment when shop stock is <= 15 units."
            ]
        },
        "FashionTrendCurationSkill": {
            "name": "Mishika Fashion Trend Curation & Client Matching",
            "description": "Discovers current fashion trends and matches them with boutique styles and individual client preferences.",
            "heuristics": [
                "Tailor trends to client preferences (e.g. Silk & Linen, Tailored Power Suits, Boho Resort, Minimalist Cashmere).",
                "Craft distinct formats: Rich editorial HTML for Email; concise, emoji-rich copy for WhatsApp.",
                "Highlight direct styling recommendations with boutique catalog styles."
            ]
        },
        "CampaignCopywritingSkill": {
            "name": "Luxury Campaign Copywriting & Marketing Blasts",
            "description": "Formulates compelling, high-conversion promotional copy without cheapening brand prestige.",
            "heuristics": [
                "Never use clearance or cheap vocabulary; emphasize exclusivity, luxury craftsmanship, and seasonal urgency.",
                "Strictly respect the 50% discount cap guardrail.",
                "Include clear call-to-action and boutique contact details."
            ]
        },
        "StockSafetyWatchdogSkill": {
            "name": "Inventory Watchdog & Back-in-Stock Alerts",
            "description": "Monitors stockout recovery, detects restocked styles, and alerts interested clients.",
            "heuristics": [
                "Identify clients whose preferred size matches the restocked product.",
                "Give VIP Platinum clients early access notifications before general broadcast."
            ]
        }
    }

    @classmethod
    def get_skill(cls, skill_name: str) -> Optional[Dict[str, Any]]:
        return cls.SKILLS.get(skill_name)

    @classmethod
    def list_skills(cls) -> List[Dict[str, Any]]:
        return [{"id": k, **v} for k, v in cls.SKILLS.items()]


class PromptCacheManager:
    """
    Pre-compiles immutable prompt prefixes for Shivi Deep Agent to optimize latency and consistency.
    """
    BASE_SYSTEM_PROMPT = (
        "You are Shivi, an enterprise-grade autonomous AI Deep Boutique Agent for Mishika Fashion Luxury Boutique.\n"
        "You operate with rigorous commercial retail math, impeccable Mishika luxury brand voice, and absolute data fidelity.\n"
        "You have direct access to live SQLite databases for sales, inventory, warehouse backroom stock, and VIP customer CRM.\n"
        "You enforce PII protection, discount safety guardrails (<= 50%), and human-in-the-loop steering on high-impact actions.\n"
        "Always be decisive, precise, and boardroom-direct."
    )

    @classmethod
    def get_system_prompt(cls, active_skills: Optional[List[str]] = None) -> str:
        prompt = cls.BASE_SYSTEM_PROMPT
        if active_skills:
            prompt += "\n\nACTIVE SPECIALIZED SKILLS:\n"
            for s in active_skills:
                skill_info = SkillsRegistry.get_skill(s)
                if skill_info:
                    prompt += f"- {skill_info['name']}: {skill_info['description']}\n"
        return prompt
