import json
import logging
import urllib.request
from typing import Dict, Any, List, Generator, Optional

try:
    import ollama
except ImportError:
    ollama = None
try:
    from src.core.logger import setup_logging
    from src.core.catalog import CATALOG
    from src.analytics.competitor import CompetitorAnalyzer
    from src.core.config import OLLAMA_BASE_URL, DEFAULT_OLLAMA_MODEL
except ImportError:
    from logger_config import setup_logging
    # CATALOG imported at top-level
    # CompetitorAnalyzer imported at top-level
    OLLAMA_BASE_URL = "http://localhost:11434"
    DEFAULT_OLLAMA_MODEL = "llama3.2:3b"


logger = setup_logging("insight_generator")

# Executive Advisory Personas for Mishika Fashion Boutique BI
PERSONAS = {
    "👔 Senior Merchandise Director": {
        "title": "Senior Merchandise Director",
        "badge": "Inventory & Financial Strategy",
        "description": "Boardroom-level retail executive focused on sell-through velocity, GMROI, stock turn, and cash-flow protection.",
        "prompt": (
            "You are the Senior Merchandise Director for Mishika Fashion Luxury Boutique. "
            "Your focus is rigorous retail math: sell-through rate (STR), stock-to-sales ratios, inventory turnover, "
            "and gross margin defense. Be decisive, data-driven, and boardroom-direct. "
            "Always cite exact product styles, inventory quantities, and margin percentages from the live data. "
            "End with 2-3 bold, high-priority Action Items."
        )
    },
    "🏷️ Pricing & Margin Strategist": {
        "title": "Pricing & Margin Strategist",
        "badge": "Competitive Pricing & Elasticity",
        "description": "Retail price analyst optimizing price parity against luxury competitors and eliminating underpricing hazards.",
        "prompt": (
            "You are the Chief Pricing & Margin Strategist for Mishika Fashion Luxury Boutique. "
            "Your focus is competitive price positioning, margin preservation, and price elasticity. "
            "Analyze market index benchmarks (100 = parity), identify Underpriced Hazards where we leave money on the table, "
            "and advise on markdown or promotional strategy. "
            "Always cite exact prices, competitor gaps, and projected margin impacts."
        )
    },
    "✨ Mishika Fashion & Styling Curator": {
        "title": "Mishika Fashion & Styling Curator",
        "badge": "Client Experience & Product Quality",
        "description": "Luxury brand curator evaluating customer review sentiment, fabric quality, and size curve harmony.",
        "prompt": (
            "You are the Executive Fashion Curator & Brand Experience Director for Mishika Fashion Luxury Boutique. "
            "Your focus is luxury craftsmanship, customer review sentiment, sizing consistency, and assortment harmony. "
            "Analyze customer feedback scores regarding fabric quality and fit, address broken size curves where core sizes (S/M/L) "
            "are missing, and recommend vendor quality standards or merchandising remedies."
        )
    }
}

PRESET_PROMPT_CHIPS = [
    {
        "label": "🎯 Autonomous Repricing Audit",
        "query": "Perform a comprehensive competitor price parity audit. Identify our most severe underpriced hazards against Velvet & Vine and Avenue Apparel, project our margin expansion upside, and provide exact dollar repricing recommendations."
    },
    {
        "label": "🚀 Top Margin Drivers",
        "query": "Which merchandise styles are generating our highest gross profit and margins, and how can we accelerate their momentum?"
    },
    {
        "label": "⚠️ Broken Size Curve Risks",
        "query": "Identify all products with broken size curves (missing S/M/L) and recommend liquidation or restock actions for the stranded fringe stock."
    },
    {
        "label": "🏷️ Competitor Pricing Hazards",
        "query": "Which products are currently flagged as 'Underpriced Hazard' against competitors, and what price adjustments do you recommend?"
    },
    {
        "label": "📦 48-Hour Restock Plan",
        "query": "Based on current sell-through velocity and safety stock thresholds (≤ 15 units), draft an emergency 48-hour procurement re-order list."
    },
    {
        "label": "📢 Dead Stock Clearance Plan",
        "query": "Identify styles categorized as 'Dead Inventory Risk' (STR ≤ 25%) and formulate a targeted promotional markdown plan to free up working capital."
    }
]

COPILOT_FAQS = {
    "📈 Financials & Margins": [
        "What is our cumulative revenue, gross profit, and realized margin % across all audited transactions?",
        "Which apparel styles are generating the highest gross profit and margins, and how can we scale them?",
        "How does our procurement spend compare against our total cost of goods sold (COGS)?"
    ],
    "⚠️ Inventory & Stock": [
        "Which merchandise styles are currently at or below safety stock limits (≤ 15 units)?",
        "What broken size curves (missing S, M, or L) exist and what is our stranded inventory volume?",
        "Draft an emergency 48-hour procurement re-order list for items near stock-out."
    ],
    "🏬 Competitor Pricing": [
        "What is our overall store Competitor Price Index (CPI) and total uncaptured margin opportunity?",
        "Which merchandise styles are currently flagged as 'Underpriced Hazard' against luxury competitors?",
        "Where are competitors charging significantly more than us and how much can we safely increase prices?",
        "Which styles command a premium price index above 112 without slowing down sell-through?"
    ],
    "🧵 Sentiment & Quality": [
        "What are customer reviews saying regarding fabric quality, fit, and sizing consistency?",
        "Which product categories have negative sentiment polarity alerts and need vendor inspection?",
        "Recommend a targeted seasonal clearance markdown plan for styles with low sell-through."
    ]
}


class LocalOllamaBoutiqueAnalyst:
    """
    Advanced AI business analyst leveraging local Ollama LLMs.
    Provides live RAG context synthesis, multi-turn streaming conversations,
    and specialized advisory personas.
    """
    def __init__(self, model_name: str = "llama3.2:3b"):
        self.model_name = model_name

    def get_available_models(self) -> List[str]:
        """
        Safely inspects the local Ollama instance and returns available chat models.
        Returns an empty list without noise if Ollama is not installed or running.
        """
        try:
            if ollama is None:
                return []
            res = ollama.list()
            # Handle both object attributes and dict-like structures
            model_list = []
            models_raw = getattr(res, 'models', res) if hasattr(res, 'models') else (res.get('models', []) if isinstance(res, dict) else [])
            for m in models_raw:
                name = getattr(m, 'model', None) or (m.get('model') if isinstance(m, dict) else str(m))
                if name and not any(skip in name.lower() for skip in ['embed', 'moondream']):
                    model_list.append(name)
            
            # Prioritize standard chat models if present
            if "llama3.2:3b" in model_list:
                model_list.remove("llama3.2:3b")
                model_list.insert(0, "llama3.2:3b")
            return model_list
        except Exception as e:
            logger.debug(f"Local Ollama daemon not active: {e}")
            return []

    def build_live_boutique_context(self, db) -> Dict[str, Any]:
        """
        Compiles a comprehensive, real-time retail intelligence payload directly from SQLite.
        """
        try:
            # CATALOG imported at top-level

            # 1. High-Level Financial Pulse
            total_rev = db.get_total_historical_revenue()
            avg_margin = db.get_average_gross_margin()

            # 2. Sell-Through Velocity
            st_df = db.fetch_dynamic_sell_through_metrics()
            hot_sellers = []
            dead_stock = []
            if not st_df.empty:
                hot_sellers = st_df[st_df["status"] == "Hot Seller"].head(5).to_dict("records")
                dead_stock = st_df[st_df["status"] == "Dead Inventory Risk"].head(5).to_dict("records")

            # 3. Live Stock Balances & Safety Breaches
            stock_on_hand = db.get_current_stock_on_hand()
            low_stock_alerts = []
            for pid, qty in stock_on_hand.items():
                if qty <= 15 and pid in CATALOG:
                    low_stock_alerts.append({
                        "product_id": pid,
                        "product_name": CATALOG[pid]["name"],
                        "category": CATALOG[pid]["category"],
                        "stock_balance": qty,
                        "unit_price": CATALOG[pid]["price"]
                    })

            # 4. Broken Size Curves & Stranded Stock
            broken_curves = db.calculate_dynamic_broken_curves()

            # 5. Competitor Pricing Intelligence & Brand Tier Benchmarks
            # CompetitorAnalyzer imported at top-level
            comp_df = db.fetch_dynamic_competitor_pricing()
            underpriced = []
            premium = []
            cpi_summary = {"store_cpi": 100.0, "total_margin_opportunity": 0.0}
            top_recs = []

            if not comp_df.empty:
                cpi_summary = CompetitorAnalyzer.get_store_cpi_metrics(comp_df)
                underpriced = comp_df[comp_df["position"] == "Underpriced Hazard"].head(5).to_dict("records")
                premium = comp_df[comp_df["position"] == "Premium Positioned"].head(5).to_dict("records")
                top_recs = CompetitorAnalyzer.get_top_repricing_recommendations(comp_df, limit=3)

            # 6. Customer Sentiment
            sent_df = db.fetch_dynamic_sentiment_metrics()
            sentiment_summary = sent_df.to_dict("records") if not sent_df.empty else []

            return {
                "financial_overview": {
                    "total_revenue_usd": round(total_rev, 2),
                    "average_gross_margin_pct": round(avg_margin, 1)
                },
                "hot_sellers": hot_sellers,
                "dead_stock_risks": dead_stock,
                "critical_low_stock_items": low_stock_alerts[:8],
                "broken_size_curve_outages": broken_curves[:5],
                "store_cpi": cpi_summary.get("store_cpi", 100.0),
                "total_margin_opportunity": cpi_summary.get("total_margin_opportunity", 0.0),
                "competitor_underpriced_hazards": underpriced,
                "competitor_premium_positioned": premium,
                "top_repricing_recs": top_recs,
                "customer_sentiment_pulse": sentiment_summary
            }
        except Exception as e:
            logger.error(f"Error compiling live boutique context: {e}")
            return {
                "error": f"Failed to query database context: {e}"
            }

    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """
        Converts the JSON context dict into high-density Markdown text for the LLM system prompt.
        """
        fin = context.get("financial_overview", {})
        lines = [
            "### CURRENT LIVE BOUTIQUE METRICS (REAL-TIME SQLITE DATA):",
            f"- **Total Revenue**: ${fin.get('total_revenue_usd', 0):,.2f}",
            f"- **Realized Gross Margin**: {fin.get('average_gross_margin_pct', 0):.1f}%",
            "",
            "#### 1. Top Moving Merchandise (Hot Sellers):"
        ]
        for m in context.get("hot_sellers", []):
            lines.append(f"  • {m.get('product_name')}: STR {m.get('sell_through_pct')}% ({m.get('status')})")

        lines.append("\n#### 2. Slow-Moving Inventory (Dead Stock Risk):")
        for m in context.get("dead_stock_risks", []):
            lines.append(f"  • {m.get('product_name')}: STR {m.get('sell_through_pct')}% ({m.get('status')})")

        lines.append("\n#### 3. Safety Stock Alerts (Stock ≤ 15 Units):")
        for s in context.get("critical_low_stock_items", []):
            lines.append(f"  • {s.get('product_name')} ({s.get('category')}): {s.get('stock_balance')} units remaining (Price: ${s.get('unit_price')})")

        lines.append("\n#### 4. Broken Size Curve Breaches (Missing Core Sizes):")
        for b in context.get("broken_size_curve_outages", []):
            missing = ", ".join(b.get('missing_core_sizes', []))
            lines.append(f"  • {b.get('product_name')}: Missing [{missing}] | Stranded Stock: {b.get('stranded_stock_volume')} units")

        lines.append(f"\n#### 5. Competitor Price Intelligence (Store CPI: {context.get('store_cpi', 100.0)}%):")
        lines.append(f"  • Total Uncaptured Margin Opportunity: ${context.get('total_margin_opportunity', 0):,.2f}")
        for u in context.get("competitor_underpriced_hazards", []):
            v_lux = u.get('velvet_vine_price', 0)
            v_mid = u.get('avenue_price', 0)
            lines.append(
                f"  • UNDERPRICED HAZARD: {u.get('product_name')} (Our Price: ${u.get('your_price'):.2f} vs "
                f"Velvet & Vine: ${v_lux:.2f}, Avenue: ${v_mid:.2f}, Market Avg: ${u.get('avg_market_price', 0):.2f}, "
                f"Index: {u.get('pricing_index')}%) -> Recommendation: {u.get('strategic_action')}"
            )
        for p in context.get("competitor_premium_positioned", []):
            lines.append(
                f"  • PREMIUM POSITIONED: {p.get('product_name')} (Our Price: ${p.get('your_price'):.2f} vs "
                f"Market Avg: ${p.get('avg_market_price', 0):.2f}, Index: {p.get('pricing_index')}%) -> Strategy: {p.get('strategic_action')}"
            )
        for r in context.get("top_repricing_recs", []):
            lines.append(
                f"  • REPRICING ACTION: {r.get('product_name')} -> Raise from ${r.get('current_price'):.2f} to ${r.get('recommended_price'):.2f} "
                f"(+${r.get('price_increase'):.2f}/unit, Est. Monthly Net Profit Gain: +${r.get('projected_monthly_profit_gain'):,.2f})"
            )

        lines.append("\n#### 6. Customer Sentiment by Category:")
        for sm in context.get("customer_sentiment_pulse", []):
            lines.append(f"  • {sm.get('Operational Category')}: Score {sm.get('Average Sentiment Score')} ({sm.get('Status')})")

        return "\n".join(lines)

    def stream_copilot_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        persona_key: str = "👔 Senior Merchandise Director",
        live_context: Optional[Dict[str, Any]] = None
    ) -> Generator[str, None, None]:
        """
        Streams AI response token-by-token using local Ollama.
        """
        active_model = model or self.model_name
        persona_info = PERSONAS.get(persona_key, PERSONAS["👔 Senior Merchandise Director"])
        
        context_str = self.format_context_for_prompt(live_context or {})
        system_instruction = (
            f"{persona_info['prompt']}\n\n"
            f"{context_str}\n\n"
            "INSTRUCTIONS:\n"
            "- Speak directly to the boutique owner/executive.\n"
            "- Always reference relevant numbers, styles, and percentages from the metrics above.\n"
            "- Format with clean headers, bullet points, and bold text for easy scanning.\n"
            "- Keep answers thorough yet concise (under 250 words unless asked for an exhaustive report)."
        )

        formatted_messages = [{"role": "system", "content": system_instruction}]
        
        # Append recent conversation history (last 8 messages for context window management)
        for msg in messages[-8:]:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        try:
            logger.info(f"Streaming Copilot response with model '{active_model}', persona '{persona_info['title']}'")
            response_stream = ollama.chat(
                model=active_model,
                messages=formatted_messages,
                stream=True,
                options={"temperature": 0.3}
            )
            for chunk in response_stream:
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token
        except Exception as e:
            err_msg = (
                f"\n\n❌ **Ollama Connection Notice**: Could not communicate with local model `{active_model}`.\n"
                f"*Details: {str(e)}*\n\n"
                "**Troubleshooting Steps:**\n"
                "1. Verify that Ollama is running in your terminal: `ollama serve`\n"
                f"2. Ensure the model is downloaded: `ollama pull {active_model}`\n"
                "3. Check your connection using the model selector above."
            )
            logger.error(f"Ollama streaming failure: {e}")
            yield err_msg

    def generate_boutique_strategy(self, consolidated_payload: Dict[str, Any]) -> str:
        """
        Legacy wrapper for backwards compatibility with batch health reports.
        """
        prompt = f"""
        You are an elite Retail Merchandise Manager specializing in luxury independent apparel boutiques.
        Analyze the verified processing metrics below and generate a business health report.

        DATA LIFECYCLE PAYLOAD:
        {json.dumps(consolidated_payload, indent=2)}

        REQUIRED MARKDOWN FORMAT FOR THE OWNER:
        Use clear headers and short, scannable summaries. Include:
        ### 1. Merchandise Performance & Sell-Through Velocity
        ### 2. Size Curve & Inventory Fragmentation Alerts
        ### 3. Quality & Fit Risk Assessment
        """
        try:
            logger.info(f"Generating strategy report using model: {self.model_name}")
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.2}
            )
            return response['message']['content']
        except Exception as e:
            err_msg = f"❌ Ollama Connection Error: {str(e)}. Please verify that `ollama serve` is running."
            logger.error(err_msg)
            return err_msg

    def generate_executive_audit_commentary(
        self,
        report_data: Dict[str, Any],
        timeframe_label: str = "Weekly",
        model: Optional[str] = None
    ) -> str:
        """
        Synthesizes aggregated audit metrics into a comprehensive, boardroom-level
        executive narrative using local Ollama.
        """
        active_model = model or self.model_name
        m = report_data.get("metrics", {})
        top_merch = report_data.get("top_merch", pd.DataFrame())
        broken = report_data.get("broken_curves", [])
        period_title = report_data.get("period_title", timeframe_label)

        # Convert top merch to summary text
        top_merch_str = ""
        if isinstance(top_merch, pd.DataFrame) and not top_merch.empty:
            for idx, row in top_merch.head(5).iterrows():
                top_merch_str += f"  • {row.get('product_name')}: {row.get('units_sold')} sold, ${row.get('revenue'):,.2f} rev, ${row.get('profit'):,.2f} profit ({row.get('margin_pct')}% margin)\n"
        else:
            top_merch_str = "  • No top merchandise sales records for this timeframe.\n"

        broken_str = ""
        if broken:
            for b in broken[:4]:
                missing = ", ".join(b.get("missing_core_sizes", []))
                broken_str += f"  • {b.get('product_name')}: Missing sizes [{missing}] | {b.get('stranded_stock_volume')} units stranded\n"
        else:
            broken_str = "  • All core size curves (S, M, L) maintained healthy balance.\n"

        comp_df = report_data.get("competitor_df", pd.DataFrame())
        comp_str = ""
        if isinstance(comp_df, pd.DataFrame) and not comp_df.empty:
            underpriced = comp_df[comp_df["position"] == "Underpriced Hazard"]
            if not underpriced.empty:
                for _, row in underpriced.head(3).iterrows():
                    comp_str += f"  • UNDERPRICED HAZARD: {row['product_name']} at ${row['your_price']:.2f} (Velvet & Vine: ${row.get('velvet_vine_price', 0):.2f}, Market Avg: ${row.get('avg_market_price', 0):.2f}, Margin Upside: +${row.get('margin_gap', 0):.2f}/unit)\n"
            else:
                comp_str = "  • All catalog lines positioned in competitive parity against luxury rivals.\n"
        else:
            comp_str = "  • Market competitor benchmarks tracking within nominal ranges.\n"

        prompt = f"""You are the Chief Merchandising & Financial Auditor for Mishika Fashion Luxury Boutique.
Analyze the following audited retail metrics for {period_title} and generate an authoritative, boardroom-level Executive Audit Commentary.

TIMEFRAME AUDITED: {period_title}
KEY FINANCIAL METRICS:
- Total Sales Revenue: ${m.get('total_revenue', 0):,.2f} ({m.get('transaction_count', 0):,} Transactions)
- Cost of Goods Sold (COGS): ${m.get('total_cogs', 0):,.2f} ({m.get('units_sold', 0):,} Units Sold)
- Net Gross Profit: ${m.get('gross_profit', 0):,.2f} (Realized Margin: {m.get('margin_pct', 0):.1f}%)
- Procurement Inbound Deliveries: +{m.get('units_restocked', 0):,} Units (${m.get('restock_spend', 0):,.2f} spend across {m.get('restock_count', 0):,} shipments)

TOP MERCHANDISE PERFORMERS:
{top_merch_str}

MARKET COMPETITOR PRICING POSITION:
{comp_str}

SIZE CURVE INTEGRITY & INVENTORY BREACHES:
{broken_str}

REQUIRED FORMAT (Use clean headers and bold bullet points with exact numbers):
### 1. Executive Summary & Financial Health
Provide an incisive assessment of revenue volume, realized gross margin percentage, and working capital efficiency.

### 2. Merchandising Velocity & Profitability Drivers
Highlight top moving styles, profitability anchors, and any lagging apparel categories.

### 3. Supply Chain Restocks & Inventory Risk Safeguards
Evaluate supply chain replenishment spend vs. sales volume, safety stock alerts, and remedies for broken size curves.

### 4. Strategic Pricing & Boardroom Recommendations
Evaluate competitor pricing gaps, underpriced hazard remedies, and provide 3 concrete, prioritized executive actions (re-orders, pricing adjustments, clearance markdowns) for the leadership team.
"""
        try:
            logger.info(f"Generating Executive Audit Commentary for '{timeframe_label}' using model '{active_model}'")
            res = ollama.chat(
                model=active_model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.25}
            )
            return res.get("message", {}).get("content", "")
        except Exception as e:
            err_msg = (
                f"### Executive Audit Commentary (Local Ollama Notice)\n\n"
                f"⚠️ *Could not generate automated AI narrative via model `{active_model}`: {str(e)}.*\n\n"
                f"**Financial Audit Snapshot:** Revenue: ${m.get('total_revenue', 0):,.2f} | "
                f"Gross Profit: ${m.get('gross_profit', 0):,.2f} ({m.get('margin_pct', 0):.1f}% Margin) | "
                f"Units Sold: {m.get('units_sold', 0):,} | Inbound Deliveries: +{m.get('units_restocked', 0):,} Units."
            )
            logger.error(f"Failed to generate audit commentary: {e}")
            return err_msg


def generate_executive_audit_commentary(
    report_data: Dict[str, Any],
    timeframe_label: str = "Weekly",
    model: Optional[str] = None
) -> str:
    """
    Standalone module-level helper to generate executive audit commentary.
    Instantiates an analyst directly to bypass any stale Streamlit object caches.
    """
    analyst = LocalOllamaBoutiqueAnalyst(model_name=model or "llama3.2:3b")
    return analyst.generate_executive_audit_commentary(
        report_data=report_data,
        timeframe_label=timeframe_label,
        model=model
    )
