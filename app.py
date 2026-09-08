import streamlit as st
import pandas as pd
import random
import json
import time
import logging
from datetime import datetime
# pyrefly: ignore [missing-import]
import plotly.express as px
from src.core.logger import setup_logging

# Initialize main application logger
logger = setup_logging("app_premium")

# Import modular enterprise dependencies from src package
from src.data.db_manager import DatabaseManager
from src.simulation.engine import SimulationEngine
from src.ai.ollama_client import (
    LocalOllamaBoutiqueAnalyst, PERSONAS, PRESET_PROMPT_CHIPS, COPILOT_FAQS,
    generate_executive_audit_commentary
)

# Load the comprehensive 20-product array configuration modules
from src.core.catalog import CATALOG, generate_initial_inventory
from src.ui.theme import render_luxury_kpi_strip, inject_luxury_branding, render_animated_arena

# pyrefly: ignore [missing-import]
from streamlit_lottie import st_lottie
from src.ui.animations import get_local_animation_pack

# Import Enterprise PDF reporting engine
from src.reporting.pdf_builder import generate_enterprise_pdf, fetch_report_datasets, generate_chat_transcript_pdf
from src.analytics.competitor import CompetitorAnalyzer

# Core Engine Global Persistence Instances Setup
db = DatabaseManager()
sim = SimulationEngine(CATALOG, db)


def init_ollama():
    """
    Initializes the local AI analyst instance.
    Uses llama3.2:3b model by default for the premium dashboard.
    """
    try:
        return LocalOllamaBoutiqueAnalyst(model_name="llama3.2:3b")
    except Exception as e:
        logger.error(f"Failed to initialize Ollama premium analyst: {e}")
        return None


local_analyst = init_ollama()

# 🔥 DYNAMIC SCHEMA SAFEGUARD: Initialize memory states straight from SQLite tables
if "live_inventory" not in st.session_state:
    try:
        db_inventory = db.get_current_stock_on_hand()
        if db_inventory and len(db_inventory) == len(CATALOG):
            st.session_state.live_inventory = db_inventory
        else:
            st.session_state.live_inventory = generate_initial_inventory()
        logger.info("Live inventory state initialized (Premium).")
    except Exception as e:
        logger.error(f"Error initializing live inventory (Premium): {e}")
        st.session_state.live_inventory = generate_initial_inventory()

if "store_controls" not in st.session_state:
    try:
        db_settings = db.get_all_circuit_controls()
        if db_settings and len(db_settings) == len(CATALOG):
            st.session_state.store_controls = db_settings
        else:
            st.session_state.store_controls = {
                pid: {"sales_enabled": True, "purchase_enabled": True, "max_stock": 100}
                for pid in CATALOG
            }
        logger.info("Store controls state initialized (Premium).")
    except Exception as e:
        logger.error(f"Error initializing store controls (Premium): {e}")
        st.session_state.store_controls = {}

if "frame_counter" not in st.session_state:
    st.session_state.frame_counter = 0

# 🔥 INLINE BRANDING PASS: Force premium styles into the browser window immediately
inject_luxury_branding()

# Navigation Menu Router Sidebar with User-Friendly Labels
st.sidebar.title("🎛️ Boutique Portal")

# Copilot Conversational State Initialization
if "copilot_messages" not in st.session_state:
    st.session_state.copilot_messages = [
        {
            "role": "assistant",
            "content": (
                "👋 **Welcome to Mishika Fashion Boutique AI Copilot.** "
                "I have synthesized your live sales transactions, inventory balances, size curve integrity, "
                "and competitor pricing indices. Select a strategic prompt chip below or ask any question to begin."
            )
        }
    ]

if "copilot_persona" not in st.session_state:
    st.session_state.copilot_persona = "👔 Senior Merchandise Director"

if "copilot_model" not in st.session_state:
    st.session_state.copilot_model = "llama3.2:3b"

if "pending_copilot_query" not in st.session_state:
    st.session_state.pending_copilot_query = None

if "target_nav" in st.session_state and st.session_state.target_nav:
    st.session_state.main_nav_radio = st.session_state.pop("target_nav")

if "main_nav_radio" not in st.session_state:
    st.session_state.main_nav_radio = "📊 Executive Dashboard"

view_selection = st.sidebar.radio(
    "Navigate System View:",
    [
        "📊 Executive Dashboard",
        "⚡ Live Store Operations",
        "⚙️ Inventory & Controls",
        "📄 Executive PDF Reports",
        "🤖 AI Copilot Studio"
    ],
    key="main_nav_radio"
)


# ==========================================
# MODULE 1: EXECUTIVE DASHBOARD VIEW
# ==========================================
if view_selection == "📊 Executive Dashboard":
    # --- STEP 1.1: Render Executive Header & Quick-Start Guide Callout ---
    st.html("<h1 class='luxury-title text-3xl font-bold mb-1'>👗 Executive Strategy Dashboard</h1>")
    st.caption("High-level merchandise performance, profit margins, and competitive price positioning.")

    # First-Time User Quick-Start Guide Callout
    st.html("""
    <div style="background:#f1f5f9; border-left:4px solid #0f172a; padding:10px 16px; border-radius:8px; margin: 12px 0 16px 0;">
        <span style="font-size:13px; color:#334155; line-height:1.5;">
            <b>💡 Quick Overview:</b> Track daily revenue and profit margins at a glance. 
            <b>Product Sales Velocity</b> highlights your top moving items, while <b>Competitor Pricing</b> reveals where you are underpriced.
            Use <b>Size Outages</b> to spot where core sizes (S, M) are missing.
        </span>
    </div>
    """)

    # --- STEP 1.2: Query Live Operational Datasets from SQLite Database ---
    sales_history = db.fetch_logs("sales_ledger", limit=100)
    total_revenue_db = db.get_total_historical_revenue()
    avg_margin_db = db.get_average_gross_margin()
    competitor_pricing_data = db.fetch_dynamic_competitor_pricing()
    st_df = db.fetch_dynamic_sell_through_metrics()
    sentiment_metrics_data = db.fetch_dynamic_sentiment_metrics()
    broken_curves = db.calculate_dynamic_broken_curves()

    # --- STEP 1.3: Render High-Level Financial Scorecard Metrics ---
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.html(f'<div class="premium-card" style="border-left: 5px solid #10b981;"><p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Total Sales Revenue</p><h3 class="text-2xl font-bold text-slate-800 mt-1">${total_revenue_db:,.2f}</h3></div>')
    with col_m2:
        st.html(f'<div class="premium-card" style="border-left: 5px solid #3b82f6;"><p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Realized Gross Margin</p><h3 class="text-2xl font-bold text-slate-800 mt-1">{avg_margin_db:.1f}%</h3></div>')
    with col_m3:
        st.html(f'<div class="premium-card" style="border-left: 5px solid #f59e0b;"><p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Size Curve Outages</p><h3 class="text-2xl font-bold text-slate-800 mt-1">{len(broken_curves)} Styles</h3></div>')

    # --- STEP 1.4: Render 2x2 Operational Diagnostics (Velocity, Competitors, Sentiment, Size Curves) ---
    st.markdown("<br style='margin: 4px 0;'>", unsafe_allow_html=True)
    left_pane, right_pane = st.columns(2)

    with left_pane:
        # Compact Product Sales Velocity Chart (height=240)
        st.markdown("<h4 style='font-size:15px; font-weight:700; color:#1e293b; margin-bottom:4px;'>📈 Product Sales Velocity</h4>", unsafe_allow_html=True)
        fig_st = px.bar(
            st_df.head(6),
            x="sell_through_pct",
            y="product_name",
            color="status",
            orientation="h",
            template="simple_white",
            color_discrete_map={"Hot Seller": "#2ecc71", "Healthy": "#3498db", "Dead Inventory Risk": "#e74c3c"}
        )
        fig_st.update_layout(
            yaxis={'categoryorder': 'total ascending', 'title': ''},
            xaxis={'title': 'Sell-Through (%)'},
            height=240,
            margin=dict(l=10, r=10, t=25, b=25),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title="")
        )
        st.plotly_chart(fig_st, width="stretch", key="dash_st_chart")

        # Compact Competitor Price Benchmark Chart (height=240)
        st.markdown("<h4 style='font-size:15px; font-weight:700; color:#1e293b; margin-bottom:4px;'>🏬 Market Competitor Benchmark</h4>", unsafe_allow_html=True)
        fig_comp = px.bar(
            competitor_pricing_data.head(6),
            x="pricing_index",
            y="product_name",
            color="position",
            orientation="h",
            template="simple_white",
            color_discrete_map={"Market Aligned": "#1e293b", "Underpriced Hazard": "#f59e0b", "Premium Positioned": "#8b5cf6"}
        )
        fig_comp.add_vline(x=100, line_width=1.5, line_dash="dash", line_color="#ef4444")
        fig_comp.update_layout(
            yaxis={'title': ''},
            xaxis={'title': 'Market Pricing Index (100 = Parity)'},
            height=240,
            margin=dict(l=10, r=10, t=25, b=25),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title="")
        )
        st.plotly_chart(fig_comp, width="stretch", key="dash_comp_chart")

    with right_pane:
        # Compact Operations Sentiment Matrix Chart (height=240)
        st.markdown("<h4 style='font-size:15px; font-weight:700; color:#1e293b; margin-bottom:4px;'>🧵 Customer Category Sentiment</h4>", unsafe_allow_html=True)
        fig_sent = px.bar(
            sentiment_metrics_data,
            x="Average Sentiment Score",
            y="Operational Category",
            color="Status",
            orientation="h",
            template="simple_white",
            color_discrete_map={"Optimal Positive Index": "#2c3e50", "Negative Volatility Alert": "#e74c3c"}
        )
        fig_sent.update_layout(
            xaxis=dict(range=[-1.1, 1.1], title='Sentiment Score (-1.0 to +1.0)'),
            yaxis={'title': ''},
            height=240,
            margin=dict(l=10, r=10, t=25, b=25),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title="")
        )
        st.plotly_chart(fig_sent, width="stretch", key="dash_sentiment_chart")

        # Compact Broken Size Curve Alert Cards
        st.markdown("<h4 style='font-size:15px; font-weight:700; color:#1e293b; margin-bottom:4px;'>⚠️ Critical Size Curve Gaps</h4>", unsafe_allow_html=True)
        if not broken_curves:
            st.info("✅ All apparel lines maintain balanced size distributions across S, M, L, and XL.")
        else:
            for alert in broken_curves[:2]:
                sizes_str = ", ".join(alert['missing_core_sizes'])
                st.html(f"""
                <div class="metric-card" style="padding:12px 16px; margin-bottom:10px; border-left:4px solid #dc2626;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h5 style="margin:0; color:#1e293b; font-size:14px; font-weight:700;">{alert['product_name']}</h5>
                        <span class="badge-dead" style="font-size:11px;">Missing {sizes_str}</span>
                    </div>
                    <p style="font-size:12px; margin:6px 0; color:#475569;">
                        <b>Stranded Inventory:</b> {alert['stranded_stock_volume']} units | <b>Action:</b> {alert['remedy']}
                    </p>
                </div>
                """)

    # ==========================================
    # FULL COMPETITOR INTELLIGENCE & "WHAT-IF" REPRICING SUITE
    # ==========================================
    st.markdown("<br/>", unsafe_allow_html=True)
    cpi_metrics = CompetitorAnalyzer.get_store_cpi_metrics(competitor_pricing_data)
    
    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
        <h3 style="font-size:18px; font-weight:700; color:#0f172a; margin:0;">
            🏬 Competitor Intelligence & "What-If" Dynamic Repricing Suite
        </h3>
        <span style="font-size:11px; background:#eff6ff; color:#1e40af; border:1px solid #bfdbfe; padding:2px 8px; border-radius:999px; font-weight:600;">
            Tri-Brand Luxury Benchmarks Active
        </span>
    </div>
    <p style="font-size:12px; color:#64748b; margin:0 0 12px 0;">
        Real-time market price parity against luxury rivals (Velvet & Vine), contemporary peers (Avenue Apparel), and budget baselines (Minimalist Thread).
    </p>
    """, unsafe_allow_html=True)

    # 4 Executive KPI Metrics Cards
    kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
    with kpi_c1:
        st.html(f"""
        <div class="premium-card" style="border-left: 4px solid #3b82f6; padding:12px 14px;">
            <p style="font-size:11px; text-transform:uppercase; font-weight:600; color:#64748b; margin:0;">Store Price Index (CPI)</p>
            <h4 style="font-size:20px; font-weight:800; color:#0f172a; margin:4px 0 2px 0;">{cpi_metrics['store_cpi']:.1f}%</h4>
            <span style="font-size:11px; color:#3b82f6; font-weight:600;">{cpi_metrics['store_position']}</span>
        </div>
        """)
    with kpi_c2:
        st.html(f"""
        <div class="premium-card" style="border-left: 4px solid #f59e0b; padding:12px 14px;">
            <p style="font-size:11px; text-transform:uppercase; font-weight:600; color:#64748b; margin:0;">Underpriced Hazards</p>
            <h4 style="font-size:20px; font-weight:800; color:#d97706; margin:4px 0 2px 0;">{cpi_metrics['underpriced_count']} Styles</h4>
            <span style="font-size:11px; color:#d97706; font-weight:600;">Index &lt; 92% (Margin Leakage)</span>
        </div>
        """)
    with kpi_c3:
        st.html(f"""
        <div class="premium-card" style="border-left: 4px solid #8b5cf6; padding:12px 14px;">
            <p style="font-size:11px; text-transform:uppercase; font-weight:600; color:#64748b; margin:0;">Premium Positioned</p>
            <h4 style="font-size:20px; font-weight:800; color:#7c3aed; margin:4px 0 2px 0;">{cpi_metrics['premium_count']} Styles</h4>
            <span style="font-size:11px; color:#7c3aed; font-weight:600;">Index &gt; 112% (Luxury Premium)</span>
        </div>
        """)
    with kpi_c4:
        st.html(f"""
        <div class="premium-card" style="border-left: 4px solid #10b981; padding:12px 14px;">
            <p style="font-size:11px; text-transform:uppercase; font-weight:600; color:#64748b; margin:0;">Unearned Margin Upside</p>
            <h4 style="font-size:20px; font-weight:800; color:#059669; margin:4px 0 2px 0;">+${cpi_metrics['total_margin_opportunity']:,.2f}/mo</h4>
            <span style="font-size:11px; color:#059669; font-weight:600;">Safe Repricing Potential</span>
        </div>
        """)

    # Interactive Sub-Tabs for Matrix & Simulator
    bench_tab1, bench_tab2 = st.tabs([
        "📊 Multi-Competitor Market Matrix",
        "⚡ 'What-If' Price Elasticity & Repricing Simulator"
    ])

    with bench_tab1:
        # Category Filter and Multi-Bar Plotly Chart
        filt_col1, filt_col2 = st.columns([1.5, 3.5])
        with filt_col1:
            cats = ["All Categories"] + sorted(list(set(competitor_pricing_data["category"].dropna().unique())))
            selected_cat = st.selectbox("Filter Merchandise Category", cats, key="comp_cat_filter")
        
        filtered_comp_df = competitor_pricing_data.copy()
        if selected_cat != "All Categories":
            filtered_comp_df = filtered_comp_df[filtered_comp_df["category"] == selected_cat]

        # Multi-Competitor Grouped Bar Chart
        chart_data = []
        for _, row in filtered_comp_df.iterrows():
            chart_data.append({"Product": row["product_name"], "Competitor": "Mishika (Our Price)", "Price": row["your_price"]})
            chart_data.append({"Product": row["product_name"], "Competitor": "Velvet & Vine (Luxury)", "Price": row["velvet_vine_price"]})
            chart_data.append({"Product": row["product_name"], "Competitor": "Avenue Apparel (Mid-Tier)", "Price": row["avenue_price"]})
            chart_data.append({"Product": row["product_name"], "Competitor": "Minimalist Thread (Budget)", "Price": row["minimalist_price"]})
        
        comp_plot_df = pd.DataFrame(chart_data)
        fig_multi = px.bar(
            comp_plot_df,
            x="Product",
            y="Price",
            color="Competitor",
            barmode="group",
            template="simple_white",
            color_discrete_map={
                "Mishika (Our Price)": "#0f172a",
                "Velvet & Vine (Luxury)": "#8b5cf6",
                "Avenue Apparel (Mid-Tier)": "#f59e0b",
                "Minimalist Thread (Budget)": "#10b981"
            }
        )
        fig_multi.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=20, b=50),
            xaxis={'title': '', 'tickangle': -25},
            yaxis={'title': 'Price ($ USD)'},
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title="")
        )
        st.plotly_chart(fig_multi, width="stretch", key="dash_multi_comp_chart")

        # Detailed Searchable Ledger Table
        st.markdown("<h5 style='font-size:13px; font-weight:700; color:#334155; margin:8px 0 4px 0;'>📋 Competitor Price Parity Ledger</h5>", unsafe_allow_html=True)
        display_cols = [
            "product_name", "category", "your_price", "margin_pct",
            "velvet_vine_price", "avenue_price", "minimalist_price",
            "avg_market_price", "pricing_index", "position", "recommended_price", "strategic_action"
        ]
        col_rename = {
            "product_name": "Product Name",
            "category": "Category",
            "your_price": "Our Price ($)",
            "margin_pct": "Margin %",
            "velvet_vine_price": "Velvet & Vine ($)",
            "avenue_price": "Avenue App ($)",
            "minimalist_price": "Minimalist ($)",
            "avg_market_price": "Market Avg ($)",
            "pricing_index": "Price Index (%)",
            "position": "Market Position",
            "recommended_price": "Recommended ($)",
            "strategic_action": "Prescribed Action"
        }
        st.dataframe(
            filtered_comp_df[display_cols].rename(columns=col_rename),
            hide_index=True,
            width="stretch"
        )

    with bench_tab2:
        st.markdown("<p style='font-size:13px; color:#475569; margin-bottom:10px;'>Simulate the impact of price adjustments using retail category price elasticity. Test price hikes on underpriced products and calculate projected unit sales and monthly profit shifts before applying changes.</p>", unsafe_allow_html=True)
        
        sim_col1, sim_col2 = st.columns([1.6, 2.4])
        
        # Determine default selection: prioritize top underpriced hazard
        p_options = list(CATALOG.keys())
        default_idx = 0
        underpriced_pids = competitor_pricing_data[competitor_pricing_data["position"] == "Underpriced Hazard"]["product_id"].tolist()
        if underpriced_pids and underpriced_pids[0] in p_options:
            default_idx = p_options.index(underpriced_pids[0])
            
        with sim_col1:
            sel_pid = st.selectbox(
                "Select Merchandise Style to Reprice",
                p_options,
                format_func=lambda x: f"{x} - {CATALOG[x]['name']} (${CATALOG[x]['price']:.2f})",
                index=default_idx,
                key="reprice_sim_product"
            )
            
            p_info = CATALOG[sel_pid]
            p_name = p_info["name"]
            curr_price = float(p_info["price"])
            cost_basis = float(p_info["cost"])
            category = p_info.get("category", "Apparel")
            
            # Lookup competitor data for this product
            comp_match = competitor_pricing_data[competitor_pricing_data["product_id"] == sel_pid]
            if not comp_match.empty:
                r_comp = comp_match.iloc[0]
                rec_price = float(r_comp["recommended_price"])
                avg_market = float(r_comp["avg_market_price"])
                v_vine = float(r_comp["velvet_vine_price"])
                ave_app = float(r_comp["avenue_price"])
                mini = float(r_comp["minimalist_price"])
                curr_cpi = float(r_comp["pricing_index"])
            else:
                rec_price = curr_price
                avg_market = curr_price
                v_vine = round(curr_price * 1.25, 2)
                ave_app = round(curr_price * 1.02, 2)
                mini = round(curr_price * 0.78, 2)
                curr_cpi = 100.0

            st.html(f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px 14px; margin-top:8px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="font-size:12px; color:#64748b;">Current Price:</span>
                    <span style="font-size:12px; font-weight:700; color:#0f172a;">${curr_price:.2f}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="font-size:12px; color:#64748b;">Cost Basis / Margin:</span>
                    <span style="font-size:12px; font-weight:600; color:#059669;">${cost_basis:.2f} ({((curr_price-cost_basis)/curr_price*100):.1f}%)</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="font-size:12px; color:#64748b;">Velvet & Vine (Lux):</span>
                    <span style="font-size:12px; font-weight:600; color:#8b5cf6;">${v_vine:.2f}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="font-size:12px; color:#64748b;">Avenue Apparel (Mid):</span>
                    <span style="font-size:12px; font-weight:600; color:#f59e0b;">${ave_app:.2f}</span>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-size:12px; color:#64748b;">Minimalist Thread (Disc):</span>
                    <span style="font-size:12px; font-weight:600; color:#10b981;">${mini:.2f}</span>
                </div>
            </div>
            """)

        with sim_col2:
            min_slider = max(cost_basis + 2.0, round(curr_price * 0.70, 2))
            max_slider = round(curr_price * 1.50, 2)
            default_val = min(max_slider, max(min_slider, rec_price))
            
            sim_price = st.slider(
                f"Proposed Retail Price for '{p_name}' ($ USD)",
                min_value=float(min_slider),
                max_value=float(max_slider),
                value=float(default_val),
                step=1.0,
                key="reprice_slider"
            )
            
            # Execute Elasticity Simulation
            sim_res = CompetitorAnalyzer.simulate_price_elasticity(
                product_id=sel_pid,
                old_price=curr_price,
                new_price=sim_price,
                cost=cost_basis,
                base_volume=40,
                category=category,
                avg_market_price=avg_market
            )

            # Display 4 Projections
            pj1, pj2 = st.columns(2)
            with pj1:
                p_diff = sim_res["pct_price_change"]
                p_color = "#059669" if p_diff >= 0 else "#dc2626"
                st.html(f"""
                <div style="background:#f1f5f9; padding:10px; border-radius:8px; margin-bottom:8px;">
                    <p style="font-size:11px; text-transform:uppercase; color:#64748b; margin:0; font-weight:600;">Price Adjustment</p>
                    <h4 style="margin:2px 0; font-size:18px; font-weight:700; color:#0f172a;">${sim_price:.2f} <font size=2 color="{p_color}">({p_diff:+.1f}%)</font></h4>
                    <span style="font-size:11px; color:#64748b;">Delta: ${sim_price - curr_price:+.2f} / unit</span>
                </div>
                """)
            with pj2:
                v_diff = sim_res["pct_volume_change"]
                st.html(f"""
                <div style="background:#f1f5f9; padding:10px; border-radius:8px; margin-bottom:8px;">
                    <p style="font-size:11px; text-transform:uppercase; color:#64748b; margin:0; font-weight:600;">Demand Impact</p>
                    <h4 style="margin:2px 0; font-size:18px; font-weight:700; color:#0f172a;">{sim_res['projected_units']} units <font size=2 color="#64748b">({v_diff:+.1f}%)</font></h4>
                    <span style="font-size:11px; color:#64748b;">Baseline: 40 units/mo</span>
                </div>
                """)

            pj3, pj4 = st.columns(2)
            with pj3:
                profit_delta = sim_res["profit_delta"]
                profit_color = "#059669" if profit_delta >= 0 else "#dc2626"
                st.html(f"""
                <div style="background:#f1f5f9; padding:10px; border-radius:8px;">
                    <p style="font-size:11px; text-transform:uppercase; color:#64748b; margin:0; font-weight:600;">Monthly Gross Profit</p>
                    <h4 style="margin:2px 0; font-size:18px; font-weight:700; color:#0f172a;">${sim_res['new_gross_profit']:,.2f}</h4>
                    <span style="font-size:11px; color:{profit_color}; font-weight:700;">{profit_delta:+,.2f} Net Profit / mo</span>
                </div>
                """)
            with pj4:
                pos_badge_color = "#d97706" if sim_res["new_position"] == "Underpriced Hazard" else ("#7c3aed" if sim_res["new_position"] == "Premium Positioned" else "#059669")
                st.html(f"""
                <div style="background:#f1f5f9; padding:10px; border-radius:8px;">
                    <p style="font-size:11px; text-transform:uppercase; color:#64748b; margin:0; font-weight:600;">New Market CPI</p>
                    <h4 style="margin:2px 0; font-size:18px; font-weight:700; color:#0f172a;">{sim_res['new_cpi']:.1f}%</h4>
                    <span style="font-size:11px; color:{pos_badge_color}; font-weight:700;">{sim_res['new_position']}</span>
                </div>
                """)

            st.markdown("<div style='margin-top:12px;'>", unsafe_allow_html=True)
            apply_btn = st.button(
                f"⚡ Apply ${sim_price:.2f} Repricing to Catalog",
                key="btn_apply_repricing",
                type="primary",
                use_container_width=True
            )
            if apply_btn:
                ok = db.update_catalog_price(sel_pid, sim_price)
                if ok:
                    st.success(f"✅ Repricing confirmed! '{p_name}' retail price updated to ${sim_price:.2f}. Live boutique transactions and benchmark charts now reflect this price.")
                    st.rerun()
                else:
                    st.error("❌ Failed to update catalog price in database.")
            st.markdown("</div>", unsafe_allow_html=True)

    # AI Boutique Copilot Assistant
    st.markdown("---")
    cop_h1, cop_h2, cop_h3 = st.columns([2.6, 1.2, 1.2])
    with cop_h1:
        current_p_name = PERSONAS.get(st.session_state.copilot_persona, {}).get("title", "Merchandise Director")
        st.markdown(f"<h3 style='font-size:18px; font-weight:700; color:#0f172a; margin-bottom:2px;'>💬 Boutique AI Copilot ({current_p_name})</h3>", unsafe_allow_html=True)
        st.caption("Live streaming retail advisory synthesized directly from your real-time SQLite database.")
    with cop_h2:
        st.markdown("<div style='padding-top:4px;'>", unsafe_allow_html=True)
        dash_p_info = PERSONAS.get(st.session_state.copilot_persona, {})
        dash_chat_pdf = generate_chat_transcript_pdf(
            messages=st.session_state.copilot_messages,
            persona_title=dash_p_info.get("title", "Merchandise Director"),
            persona_badge=dash_p_info.get("badge", "Strategy"),
            model_name=st.session_state.copilot_model
        )
        st.download_button(
            label="📥 Export Chat (PDF)",
            data=dash_chat_pdf,
            file_name=f"MishikaFashion_Copilot_Chat_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            key="dash_export_chat_btn",
            help="Download the latest conversation transcript as an executive PDF",
            use_container_width=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with cop_h3:
        st.markdown("<div style='padding-top:4px;'>", unsafe_allow_html=True)
        if st.button("Open Studio ↗️", key="dash_open_studio", help="Switch to dedicated full-screen AI Studio", use_container_width=True):
            st.session_state.target_nav = "🤖 AI Copilot Studio"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 1-Click Executive Prompt Chips
    st.markdown("<div style='margin-bottom:6px;'>", unsafe_allow_html=True)
    chip_cols = st.columns(len(PRESET_PROMPT_CHIPS))
    for idx, chip in enumerate(PRESET_PROMPT_CHIPS):
        with chip_cols[idx]:
            if st.button(chip["label"], key=f"dash_chip_{idx}"):
                st.session_state.pending_copilot_query = chip["query"]
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Interactive Conversational Chat Stream
    dash_chat_box = st.container(height=320)
    with dash_chat_box:
        for msg in st.session_state.copilot_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if st.session_state.get("pending_copilot_query"):
            dash_query = st.session_state.pop("pending_copilot_query")
            st.session_state.copilot_messages.append({"role": "user", "content": dash_query})
            with st.chat_message("user"):
                st.markdown(dash_query)
            with st.chat_message("assistant"):
                live_ctx = local_analyst.build_live_boutique_context(db)
                stream_gen = local_analyst.stream_copilot_response(
                    messages=st.session_state.copilot_messages,
                    model=st.session_state.copilot_model,
                    persona_key=st.session_state.copilot_persona,
                    live_context=live_ctx
                )
                full_resp = st.write_stream(stream_gen)
                st.session_state.copilot_messages.append({"role": "assistant", "content": full_resp})

    dash_input = st.chat_input("Ask Copilot about inventory velocity, pricing anomalies, or margins...")
    if dash_input:
        st.session_state.pending_copilot_query = dash_input
        st.rerun()


# ==========================================
# MODULE 2: LIVE STORE OPERATIONS VIEW
# ==========================================
elif view_selection == "⚡ Live Store Operations":
    # --- STEP 2.1: Navigation Header & Guide Popover ---
    col_hdr1, col_hdr2 = st.columns([3.8, 1.2])
    with col_hdr1:
        st.html("<h2 class='luxury-title text-2xl font-bold' style='margin:0; padding:0;'>⚡ Live Store Operations Pipeline</h2>")
        st.caption("Simulate incoming retail transactions and supplier restocking in real-time.")
    with col_hdr2:
        with st.popover("💡 Guide & Legend"):
            st.markdown(r"""
            **How It Works:**
            - Check **▶️ Activate Live Operations Loop** in the sidebar.
            - **🟢 Green Shopper**: Buyer checkout events reducing inventory.
            - **🚚 Blue Cargo Truck**: Inbound shipments replenishing stock.
            - **Warehouse Stock Graph**: Selectively updates and highlights items as events settle.

            ---
            **Visual Highlighting Stock Graph:**
            - 🟢 **Emerald Green**: Product just restocked by shipment.
            - 🟡 **Amber Gold**: Product just purchased by a shopper.
            - 🔴 **Crimson**: Product stock below critical safety threshold.
            - 🔵 **Luxury Slate**: All unchanged, stable catalog styles.
            """)

    # --- STEP 2.2: Session State Initialization & In-Place Display Placeholders ---
    if "frame_counter" not in st.session_state:
        st.session_state.frame_counter = 0
    if "last_rendered_inventory" not in st.session_state:
        st.session_state.last_rendered_inventory = None

    # Sidebar control elements for the simulation engine
    st.sidebar.markdown("### ⚙️ Simulation Controls")
    promo_discount = st.sidebar.slider("Active Flash Sale Markdown (%)", 0, 50, 0, step=10)
    stream_speed = st.sidebar.slider("Simulation Tick Speed (Secs)", 0.1, 1.5, 0.35, step=0.05)
    start_stream = st.sidebar.checkbox("▶️ Activate Live Operations Loop", value=False)

    # Layout rendering placeholders to swap elements smoothly in-place without screen lag
    kpi_p = st.empty()
    animation_stage_p = st.empty()
    chart_p = st.empty()
    log_p = st.empty()

    # --- STEP 2.3: Real-Time Discrete Event Ingestion Loop ---
    while start_stream:
        st.session_state.frame_counter += 1

        # 1. Execute computational changes quietly in background thread directly into SQLite
        event_text, event_type, event_pid = sim.process_tick(promo_discount, st.session_state.live_inventory)

        # Pre-initialize blank fallbacks for skipped UI drawing frames
        live_sales_view = pd.DataFrame()
        live_purchases_view = pd.DataFrame()
        current_total_revenue = db.get_total_historical_revenue()

        # 2. 🔥 UI FLICKER FIX: Throttles layout re-renders to every 2nd simulation tick
        if st.session_state.frame_counter % 2 == 0:
            live_sales_view = db.fetch_logs("sales_ledger", limit=5)
            live_purchases_view = db.fetch_logs("purchase_ledger", limit=5)

            # A. Draw Ultra-Compact Luxury KPI Cards via Theme Manager
            with kpi_p.container():
                low_stock_count = sum(1 for v in st.session_state.live_inventory.values() if v <= 15)
                render_luxury_kpi_strip(
                    revenue=current_total_revenue,
                    low_stock=low_stock_count,
                    status_text=event_text if event_text else "Monitoring transaction channel...",
                    is_active=True
                )

            # B. CRASH-PROOF ANIMATION BANNER (Uses dynamic 60 FPS Canvas arena from Theme Manager)
            with animation_stage_p.container():
                if event_pid:
                    c_qty = st.session_state.live_inventory.get(event_pid, 0)
                    m_qty = st.session_state.store_controls.get(event_pid, {}).get("max_stock", 100)
                    prod_name = CATALOG.get(event_pid, {}).get("name", "")
                    price = CATALOG.get(event_pid, {}).get("price", 0.0)
                    render_animated_arena(
                        event_type,
                        c_qty,
                        m_qty,
                        product_name=prod_name,
                        unit_price=price,
                        event_text=event_text
                    )
                else:
                    render_animated_arena("Idle", 0, 100, event_text=event_text)

            # C. Selective-Update Stock Chart: Loads ONLY when inventory changes
            inventory_changed = (st.session_state.get("last_rendered_inventory") != st.session_state.live_inventory)
            if inventory_changed or st.session_state.frame_counter <= 2:
                st.session_state.last_rendered_inventory = dict(st.session_state.live_inventory)

                bar_colors = []
                inv_rows = []
                for pid, details in CATALOG.items():
                    s = st.session_state.live_inventory.get(pid, 0)
                    inv_rows.append({"Product": details["name"], "Stock Level": s})
                    # Highlight ONLY the merchandise style that just changed
                    if pid == event_pid:
                        if event_type == "Purchase":
                            bar_colors.append("#10b981")  # Active Restock (Emerald Green)
                        elif event_type == "Sale":
                            bar_colors.append("#f59e0b")  # Active Buyer Sale (Amber Gold)
                        else:
                            bar_colors.append("#6366f1")  # Active Event (Indigo)
                    elif s <= 15:
                        bar_colors.append("#ef4444")      # Safety stock breach (Crimson)
                    else:
                        bar_colors.append("#1e293b")      # Stable baseline (Luxury Slate)

                inv_df = pd.DataFrame(inv_rows)
                change_tag = f" • Latest Change: {CATALOG.get(event_pid, {}).get('name', '')} ({event_type})" if event_pid and event_type in ("Sale", "Purchase") else ""
                fig_l = px.bar(
                    inv_df,
                    x="Product",
                    y="Stock Level",
                    text="Stock Level",
                    title=f"Real-Time Warehouse Stock Levels{change_tag}",
                )
                fig_l.update_traces(
                    marker_color=bar_colors,
                    textposition='outside',
                    marker_line_color='#0f172a',
                    marker_line_width=1
                )
                fig_l.update_layout(
                    yaxis=dict(range=[0, 250], title="Units On Hand", fixedrange=True),
                    xaxis=dict(title="", tickangle=-30, fixedrange=True),
                    template="simple_white",
                    height=200,
                    margin=dict(l=10, r=10, t=25, b=20),
                    title_font=dict(family="Playfair Display", size=13),
                    uirevision="warehouse_stock_levels"  # Preserves chart state across updates without reload
                )
                with chart_p.container():
                    st.plotly_chart(
                        fig_l,
                        width="stretch",
                        config={"displayModeBar": False, "responsive": True}
                    )

            # D. Relational Ledger Streaming Row Data Logs
            with log_p.container():
                cl, cr = st.columns(2)
                with cl:
                    st.markdown("### 📥 Live Sales Log")
                    if not live_sales_view.empty:
                        for _, row in live_sales_view.iterrows():
                            time_stamp = row["timestamp"].split()[-1]
                            st.info(f"🟢 **{time_stamp}** | **{row['product_name']}** sold for **${row['total_revenue']:.2f}**")
                    else:
                        st.caption("Awaiting customer checkout events...")
                with cr:
                    st.markdown("### 📤 Inbound Restocks Log")
                    if not live_purchases_view.empty:
                        for _, row in live_purchases_view.iterrows():
                            time_stamp = row["timestamp"].split()[-1]
                            st.markdown(f"🔵 **{time_stamp}** | Received **{row['quantity']}x {row['product_name']}** (Cost: ${row['total_cost']:.2f})")
                    else:
                        st.caption("Awaiting inventory deliveries...")

        time.sleep(max(stream_speed, 0.15))

    if not start_stream:
        render_luxury_kpi_strip(
            db.get_total_historical_revenue(),
            sum(1 for v in st.session_state.live_inventory.values() if v <= 15),
            "Engine Standby",
            is_active=False
        )
        first_pid = next(iter(CATALOG.keys())) if CATALOG else None
        c_qty = st.session_state.live_inventory.get(first_pid, 0) if first_pid else 50
        m_qty = st.session_state.store_controls.get(first_pid, {}).get("max_stock", 100) if first_pid else 100
        p_name = CATALOG.get(first_pid, {}).get("name", "Boutique Apparel") if first_pid else "Boutique Apparel"
        render_animated_arena("Idle", c_qty, m_qty, product_name=p_name, event_text="Simulation Standby - Activate Loop to Start")

        # Baseline Warehouse Stock Levels Chart (Rendered in Standby so chart is pre-loaded)
        inv_df = pd.DataFrame([{"Product": CATALOG[pid]["name"], "Stock Level": s} for pid, s in st.session_state.live_inventory.items()])
        fig_standby = px.bar(
            inv_df,
            x="Product",
            y="Stock Level",
            text="Stock Level",
            title="Real-Time Warehouse Stock Levels (Standby Baseline)",
        )
        bar_colors = ["#ef4444" if s <= 15 else "#1e293b" for s in st.session_state.live_inventory.values()]
        fig_standby.update_traces(
            marker_color=bar_colors,
            textposition='outside',
            marker_line_color='#0f172a',
            marker_line_width=1
        )
        fig_standby.update_layout(
            yaxis=dict(range=[0, 250], title="Units On Hand", fixedrange=True),
            xaxis=dict(title="", tickangle=-30, fixedrange=True),
            template="simple_white",
            height=200,
            margin=dict(l=10, r=10, t=25, b=20),
            title_font=dict(family="Playfair Display", size=13),
            uirevision="warehouse_stock_levels"
        )
        st.plotly_chart(fig_standby, width="stretch", config={"displayModeBar": False, "responsive": True})

        st.info("💡 **Simulation Standby:** Check **▶️ Activate Live Operations Loop** on the left sidebar to start streaming transactions.")


# ==========================================
# MODULE 3: INVENTORY & CIRCUIT CONTROLS VIEW
# ==========================================
elif view_selection == "⚙️ Inventory & Controls":
    # --- STEP 3.1: Inventory & Circuit Controls Header & Manager Guide ---
    st.markdown("<h1 class='luxury-title text-3xl font-bold mb-1'>⚙️ Inventory & Circuit Controls</h1>", unsafe_allow_html=True)
    st.caption("Manage operational safeguards, toggle sales, and configure maximum stock boundaries per product.")

    # Control Panel Quick-Start Guide Callout
    st.html("""
    <div style="background:#f1f5f9; border-left:4px solid #f59e0b; padding:10px 16px; border-radius:8px; margin: 12px 0 16px 0;">
        <span style="font-size:13px; color:#334155; line-height:1.5;">
            <b>💡 Control Panel Guide:</b> Turn off <b>Allow Sales</b> to pause purchases for out-of-stock or reserved styles.
            Turn off <b>Allow Restock</b> to prevent supplier replenishment. Use the filter below to quickly isolate styles with low stock.
        </span>
    </div>
    """)

    # --- STEP 3.2: Store Manager Filter Toolbar (Low Stock Isolator) ---
    col_filt1, col_filt2 = st.columns([1, 2])
    with col_filt1:
        low_stock_only = st.toggle("⚠️ Show Low Stock Only (≤ 15 Units)", value=False)

    # --- STEP 3.3: Category-Tabbed Circuit Controls Switchboard ---
    active_controls = db.get_all_circuit_controls()
    categories = sorted(list(set(details["category"] for details in CATALOG.values())))
    tabs = st.tabs(categories)

    for idx, cat_name in enumerate(categories):
        with tabs[idx]:
            cat_pids = [pid for pid, details in CATALOG.items() if details["category"] == cat_name]
            if low_stock_only:
                cat_pids = [pid for pid in cat_pids if st.session_state.live_inventory.get(pid, 0) <= 15]

            if not cat_pids:
                st.info(f"✅ No items in '{cat_name}' are currently below safety stock limits.")
            else:
                for pid in cat_pids:
                    col_name, col_sale, col_pur, col_max = st.columns([2, 1, 1, 1.5])
                    current_settings = active_controls.get(pid, {"sales_enabled": True, "purchase_enabled": True, "max_stock": 100})
                    current_qty = st.session_state.live_inventory.get(pid, 0)

                    with col_name:
                        stock_tag = f"<span style='color:#dc2626; font-weight:bold;'>⚠️ Low ({current_qty} units)</span>" if current_qty <= 15 else f"<span style='color:#059669;'>{current_qty} Units</span>"
                        st.markdown(f"**{CATALOG[pid]['name']}** <span style='font-size:12px; color:#64748b;'>({pid})</span>", unsafe_allow_html=True)
                        st.caption(f"Warehouse Balance: {stock_tag}", unsafe_allow_html=True)

                    with col_sale:
                        allow_sales = st.toggle("Sales", value=current_settings["sales_enabled"], key=f"s_tgl_{pid}")
                        if allow_sales != current_settings["sales_enabled"]:
                            db.update_circuit_control(pid, "sales_enabled", allow_sales)
                            st.session_state.store_controls[pid]["sales_enabled"] = allow_sales
                            st.rerun()

                    with col_pur:
                        allow_restock = st.toggle("Restock", value=current_settings["purchase_enabled"], key=f"p_tgl_{pid}")
                        if allow_restock != current_settings["purchase_enabled"]:
                            db.update_circuit_control(pid, "purchase_enabled", allow_restock)
                            st.session_state.store_controls[pid]["purchase_enabled"] = allow_restock
                            st.rerun()

                    with col_max:
                        max_cap = st.number_input(
                            "Max Cap",
                            min_value=10,
                            max_value=300,
                            value=current_settings["max_stock"],
                            step=10,
                            key=f"m_in_{pid}"
                        )
                        if max_cap != current_settings["max_stock"]:
                            db.update_circuit_control(pid, "max_stock", max_cap)
                            st.session_state.store_controls[pid]["max_stock"] = max_cap
                            st.rerun()

                    st.markdown("<hr style='margin: 0.35em 0; border: 0; border-top: 1px solid #f1f5f9;' />", unsafe_allow_html=True)


# ==========================================
# MODULE 4: EXECUTIVE PDF REPORTS VIEW
# ==========================================
elif view_selection == "📄 Executive PDF Reports":
    # --- STEP 4.1: Executive PDF Reporting Hub Header & User Guide ---
    st.markdown("<h1 class='luxury-title text-3xl font-bold mb-1'>📄 Executive PDF Audit Reports</h1>", unsafe_allow_html=True)
    st.caption("Generate official boardroom-ready PDF audits of sales revenue, profit margins, and supply chain restocks.")

    # Enterprise Reporting Hub Quick-Start Callout
    st.html("""
    <div style="background:#f1f5f9; border-left:4px solid #059669; padding:10px 16px; border-radius:8px; margin: 12px 0 16px 0;">
        <span style="font-size:13px; color:#334155; line-height:1.5;">
            <b>💡 Enterprise Reporting Hub:</b> Select a timeframe below (Daily, Weekly, or Complete All-Time).
            The system queries your SQLite transaction database, aggregates financial margins, and creates an official boardroom PDF document with letterhead branding.
        </span>
    </div>
    """)

    # --- STEP 4.2: Timeframe Horizon Scope Selector ---
    col_scope, col_btn = st.columns([2, 1])
    with col_scope:
        scope_choice = st.radio(
            "Select Audit Timeframe Scope:",
            ["Daily Audit (Latest Operating Day)", "Weekly Audit (Last 7 Days)", "Monthly Audit (Last 30 Days)", "Complete Audit (All-Time Database)"],
            horizontal=True
        )

    scope_key = "daily" if "Daily" in scope_choice else ("weekly" if "Weekly" in scope_choice else ("monthly" if "Monthly" in scope_choice else "complete"))

    # --- STEP 4.3: Real-Time Audit Metrics Extraction from SQLite ---
    with st.spinner("Compiling executive report metrics..."):
        report_data = fetch_report_datasets(db, scope_key)
        m = report_data["metrics"]

    # --- STEP 4.4: Live On-Screen Scorecard Preview ---
    st.markdown("### 📊 Executive Financial Scorecard Preview")
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.html(f'<div class="premium-card" style="border-left: 4px solid #10b981;"><p class="text-xs uppercase font-semibold text-gray-400">Total Revenue</p><h3 class="text-xl font-bold text-slate-800 mt-1">${m["total_revenue"]:,.2f}</h3><p class="text-xs text-gray-500 mt-1">{m["transaction_count"]:,} Sales</p></div>')
    with sc2:
        st.html(f'<div class="premium-card" style="border-left: 4px solid #3b82f6;"><p class="text-xs uppercase font-semibold text-gray-400">Cost of Goods</p><h3 class="text-xl font-bold text-slate-800 mt-1">${m["total_cogs"]:,.2f}</h3><p class="text-xs text-gray-500 mt-1">{m["units_sold"]:,} Units Sold</p></div>')
    with sc3:
        st.html(f'<div class="premium-card" style="border-left: 4px solid #059669;"><p class="text-xs uppercase font-semibold text-gray-400">Net Gross Profit</p><h3 class="text-xl font-bold text-emerald-600 mt-1">${m["gross_profit"]:,.2f}</h3><p class="text-xs text-emerald-700 font-semibold mt-1">Margin: {m["margin_pct"]:.1f}%</p></div>')
    with sc4:
        st.html(f'<div class="premium-card" style="border-left: 4px solid #d97706;"><p class="text-xs uppercase font-semibold text-gray-400">Procurement Inbound</p><h3 class="text-xl font-bold text-amber-600 mt-1">+{m["units_restocked"]:,} Units</h3><p class="text-xs text-gray-500 mt-1">Spend: ${m["restock_spend"]:,.2f}</p></div>')

    st.markdown("<br style='margin: 6px 0;'>", unsafe_allow_html=True)

    # Detailed Preview Tabs
    tab_merch, tab_restock = st.tabs(["🏆 Top Selling Merchandise Preview", "🚚 Inbound Supply Deliveries Preview"])
    with tab_merch:
        if not report_data["top_merch"].empty:
            preview_merch = report_data["top_merch"].rename(columns={
                "product_id": "Style Code",
                "product_name": "Product Style Name",
                "units_sold": "Units Sold",
                "revenue": "Gross Revenue ($)",
                "profit": "Gross Profit ($)",
                "margin_pct": "Margin (%)"
            })
            st.dataframe(preview_merch, width="stretch", hide_index=True)
        else:
            st.caption("No sales transactions found for the selected timeframe.")

    with tab_restock:
        if not report_data["purchases_df"].empty:
            preview_pur = report_data["purchases_df"].head(10)[["timestamp", "product_name", "quantity", "total_cost"]].rename(columns={
                "timestamp": "Arrival Time",
                "product_name": "Product Style Name",
                "quantity": "Units Restocked",
                "total_cost": "Procurement Cost ($)"
            })
            st.dataframe(preview_pur, width="stretch", hide_index=True)
        else:
            st.caption("No restock shipments found for the selected timeframe.")

    # PDF Compilation & One-Click Download Button
    st.markdown("---")
    col_down_left, col_down_right = st.columns([2, 1])
    with col_down_left:
        st.markdown(f"**Ready to Export:** `{report_data['period_title']}`")
        st.caption("Includes official corporate letterhead, executive scorecard, audited sales tables, and safety stock outage reports.")

    with col_down_right:
        pdf_bytes = generate_enterprise_pdf(db, scope_key)
        filename = f"HauteBoutique_{scope_key.capitalize()}_Audit_{datetime.now().strftime('%Y%m%d')}.pdf"
        st.download_button(
            label=f"📥 Download Enterprise PDF Report",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            type="primary",
            width="stretch"
        )


# ==========================================
# MODULE 5: AI COPILOT STUDIO VIEW
# ==========================================
elif view_selection == "🤖 AI Copilot Studio":
    # --- STEP 5.1: Top Command Control Bar (Persona, Model, Status, Reset, PDF Export) ---
    st.html("<h1 class='luxury-title text-3xl font-bold mb-1'>🤖 Mishika Fashion Boutique AI Copilot Studio</h1>")
    st.caption("Dedicated retail intelligence command center powered by real-time SQLite database context and local Ollama reasoning.")

    # Top Control Bar: Persona, Model, Status, Clear & Export
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4, ctrl_col5 = st.columns([2.3, 1.4, 0.9, 0.9, 1.3])
    with ctrl_col1:
        persona_keys = list(PERSONAS.keys())
        current_p_idx = persona_keys.index(st.session_state.copilot_persona) if st.session_state.copilot_persona in persona_keys else 0
        chosen_persona = st.selectbox(
            "Strategic Advisory Persona:",
            options=persona_keys,
            index=current_p_idx,
            key="studio_persona_select"
        )
        if chosen_persona != st.session_state.copilot_persona:
            st.session_state.copilot_persona = chosen_persona
            st.rerun()

    with ctrl_col2:
        available_models = local_analyst.get_available_models()
        model_idx = available_models.index(st.session_state.copilot_model) if st.session_state.copilot_model in available_models else 0
        chosen_model = st.selectbox(
            "Local Ollama Model:",
            options=available_models,
            index=model_idx,
            key="studio_model_select"
        )
        if chosen_model != st.session_state.copilot_model:
            st.session_state.copilot_model = chosen_model

    with ctrl_col3:
        st.markdown("<div style='padding-top:28px;'><span style='background:#ecfdf5; color:#059669; border:1px solid #a7f3d0; padding:6px 8px; border-radius:8px; font-size:11.5px; font-weight:600; white-space:nowrap;'>🟢 Active</span></div>", unsafe_allow_html=True)

    with ctrl_col4:
        st.markdown("<div style='padding-top:24px;'>", unsafe_allow_html=True)
        if st.button("🧹 Reset", key="studio_clear_btn", help="Clear conversation history", use_container_width=True):
            st.session_state.copilot_messages = [{
                "role": "assistant",
                "content": f"👋 **{PERSONAS[st.session_state.copilot_persona]['title']} active.** Real-time store transactions and stock balances loaded. What strategic priority shall we evaluate?"
            }]
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with ctrl_col5:
        st.markdown("<div style='padding-top:24px;'>", unsafe_allow_html=True)
        studio_p_info = PERSONAS.get(st.session_state.copilot_persona, {})
        studio_chat_pdf = generate_chat_transcript_pdf(
            messages=st.session_state.copilot_messages,
            persona_title=studio_p_info.get("title", "Strategic Advisor"),
            persona_badge=studio_p_info.get("badge", "Advisory"),
            model_name=st.session_state.copilot_model
        )
        st.download_button(
            label="📥 Export Chat (PDF)",
            data=studio_chat_pdf,
            file_name=f"MishikaFashion_Copilot_Chat_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            help="Download the latest conversation transcript as an enterprise PDF report",
            key="studio_export_chat_btn",
            use_container_width=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # --- STEP 5.2: Active Advisory Persona Callout Banner ---
    active_p = PERSONAS[st.session_state.copilot_persona]
    st.html(f"""
    <div style="background:#f8fafc; border-left:4px solid #0f172a; padding:10px 16px; border-radius:8px; margin: 6px 0 16px 0;">
        <span style="font-size:13px; color:#334155; line-height:1.5;">
            <b>Active Advisory Role:</b> {active_p['title']} ({active_p['badge']}) — <i>{active_p['description']}</i>
        </span>
    </div>
    """)

    # --- STEP 5.3: Two-Column Studio Layout (Knowledge Inspector & Workbench) ---
    left_inspect, right_studio = st.columns([0.38, 0.62], gap="large")

    # Fetch live RAG context
    live_ctx = local_analyst.build_live_boutique_context(db)
    fin = live_ctx.get("financial_overview", {})

    with left_inspect:
        st.markdown("<h4 style='font-size:15px; font-weight:700; color:#1e293b; margin-bottom:8px;'>🔍 Live Store Knowledge Inspector</h4>", unsafe_allow_html=True)
        st.caption("The live datasets automatically synthesized and fed into Copilot system prompts.")

        # Card 1: Financial Health
        st.html(f"""
        <div class="premium-card" style="padding:12px 14px; margin-bottom:12px; border-left:4px solid #10b981;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <b style="font-size:13px; color:#0f172a;">📊 Financial Health</b>
                <span style="font-size:11px; color:#059669; font-weight:600;">Margin {fin.get('average_gross_margin_pct', 0):.1f}%</span>
            </div>
            <p style="font-size:12px; color:#475569; margin:6px 0 0 0;">
                Revenue: <b>${fin.get('total_revenue_usd', 0):,.2f}</b> | Est COGS: <b>${(fin.get('total_revenue_usd', 0) * (1 - fin.get('average_gross_margin_pct', 54.2)/100)):,.2f}</b>
            </p>
        </div>
        """)

        # Card 2: Sell-Through Velocity
        hot_s = live_ctx.get("hot_sellers", [])
        dead_s = live_ctx.get("dead_stock_risks", [])
        hot_names = ", ".join([f"{x['product_name']} ({x['sell_through_pct']}%)" for x in hot_s[:3]]) if hot_s else "None"
        dead_names = ", ".join([f"{x['product_name']} ({x['sell_through_pct']}%)" for x in dead_s[:3]]) if dead_s else "None"

        st.html(f"""
        <div class="premium-card" style="padding:12px 14px; margin-bottom:12px; border-left:4px solid #3b82f6;">
            <b style="font-size:13px; color:#0f172a;">⚡ Sell-Through Velocity</b>
            <p style="font-size:12px; color:#475569; margin:4px 0 2px 0;">
                <span style="color:#059669; font-weight:bold;">● Hot Sellers:</span> {hot_names}
            </p>
            <p style="font-size:12px; color:#475569; margin:2px 0 0 0;">
                <span style="color:#dc2626; font-weight:bold;">● Dead Stock:</span> {dead_names}
            </p>
        </div>
        """)

        # Card 3: Stock Outages & Size Curve Gaps
        low_stocks = live_ctx.get("critical_low_stock_items", [])
        broken = live_ctx.get("broken_size_curve_outages", [])
        low_str = ", ".join([f"{x['product_name']} ({x['stock_balance']}u)" for x in low_stocks[:3]]) if low_stocks else "All balanced"
        broken_str = ", ".join([f"{x['product_name']} (Missing {','.join(x['missing_core_sizes'])})" for x in broken[:2]]) if broken else "Curves balanced"

        st.html(f"""
        <div class="premium-card" style="padding:12px 14px; margin-bottom:12px; border-left:4px solid #f59e0b;">
            <b style="font-size:13px; color:#0f172a;">⚠️ Critical Stock & Curve Alerts</b>
            <p style="font-size:12px; color:#475569; margin:4px 0 2px 0;">
                <span style="color:#d97706; font-weight:bold;">● Low Stock (≤15u):</span> {low_str}
            </p>
            <p style="font-size:12px; color:#475569; margin:2px 0 0 0;">
                <span style="color:#dc2626; font-weight:bold;">● Broken Curves:</span> {broken_str}
            </p>
        </div>
        """)

        # Card 4: Competitor Pricing & Sentiment
        under_p = live_ctx.get("competitor_underpriced_hazards", [])
        store_cpi_val = live_ctx.get("store_cpi", 100.0)
        margin_opp_val = live_ctx.get("total_margin_opportunity", 0.0)
        under_str = ", ".join([f"{x['product_name']} (${x['your_price']} vs ${x.get('avg_market_price', 0):.2f})" for x in under_p[:2]]) if under_p else "Parity maintained"

        st.html(f"""
        <div class="premium-card" style="padding:12px 14px; margin-bottom:12px; border-left:4px solid #8b5cf6;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <b style="font-size:13px; color:#0f172a;">🏬 Competitor Intelligence</b>
                <span style="font-size:11px; color:#7c3aed; font-weight:600;">CPI {store_cpi_val:.1f}%</span>
            </div>
            <p style="font-size:12px; color:#475569; margin:4px 0 2px 0;">
                <span style="color:#d97706; font-weight:bold;">● Underpriced ({len(under_p)}):</span> {under_str}
            </p>
            <p style="font-size:12px; color:#475569; margin:2px 0 0 0;">
                <span style="color:#059669; font-weight:bold;">● Repricing Upside:</span> +${margin_opp_val:,.2f}/mo
            </p>
        </div>
        """)

    with right_studio:
        # --- STEP 5.4: Strategic Advisory Workbench Header & Quick Export Action ---
        bench_hdr1, bench_hdr2 = st.columns([3, 1.2])
        with bench_hdr1:
            st.markdown("<h4 style='font-size:15px; font-weight:700; color:#1e293b; margin-bottom:2px;'>💬 Strategic Advisory Workbench</h4>", unsafe_allow_html=True)
            st.caption("Ask inquiries, explore scenarios, or click prompt chips to launch deep-dive audits.")
        with bench_hdr2:
            st.download_button(
                label="📥 Export Chat",
                data=studio_chat_pdf,
                file_name=f"MishikaFashion_Copilot_Chat_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                key="workbench_quick_export_btn",
                help="Download active conversation transcript as an enterprise PDF report",
                use_container_width=True
            )

        # --- STEP 5.5: 1-Click Executive Prompt Chips Toolbar ---
        st.markdown("<div style='margin-bottom:8px;'>", unsafe_allow_html=True)
        chip_cols = st.columns(len(PRESET_PROMPT_CHIPS))
        for idx, chip in enumerate(PRESET_PROMPT_CHIPS):
            with chip_cols[idx]:
                if st.button(chip["label"], key=f"studio_chip_{idx}"):
                    st.session_state.pending_copilot_query = chip["query"]
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # --- STEP 5.6: Strategic Retail FAQs Explorer (Categorized Across 4 Pillars) ---
        if COPILOT_FAQS:
            with st.expander("💡 Strategic Retail FAQs (Click any question to ask Copilot)", expanded=False):
                faq_tabs = st.tabs(list(COPILOT_FAQS.keys()))
                for tab_idx, (cat_name, questions) in enumerate(COPILOT_FAQS.items()):
                    with faq_tabs[tab_idx]:
                        for q_idx, q in enumerate(questions):
                            if st.button(f"❓ {q}", key=f"faq_btn_{tab_idx}_{q_idx}", use_container_width=True):
                                st.session_state.pending_copilot_query = q
                                st.rerun()

        # --- STEP 5.7: Streaming Conversational Chat via Local Ollama ---
        chat_container = st.container(height=480)
        with chat_container:
            for msg in st.session_state.copilot_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            # Process pending query if present
            if st.session_state.get("pending_copilot_query"):
                user_query = st.session_state.pop("pending_copilot_query")
                st.session_state.copilot_messages.append({"role": "user", "content": user_query})
                with st.chat_message("user"):
                    st.markdown(user_query)

                with st.chat_message("assistant"):
                    stream_gen = local_analyst.stream_copilot_response(
                        messages=st.session_state.copilot_messages,
                        model=st.session_state.copilot_model,
                        persona_key=st.session_state.copilot_persona,
                        live_context=live_ctx
                    )
                    full_resp = st.write_stream(stream_gen)
                    st.session_state.copilot_messages.append({"role": "assistant", "content": full_resp})

        # Chat Input Bar
        studio_input = st.chat_input("Inquire with your Boutique Copilot about inventory, pricing, or margin...")
        if studio_input:
            st.session_state.pending_copilot_query = studio_input
            st.rerun()

    # --- STEP 5.8: Executive AI Strategic Audit & Enterprise PDF Generator ---
    st.markdown("---")
    st.html("<h2 class='luxury-title text-2xl font-bold mb-1'>📑 Executive AI Audit & Enterprise PDF Generator</h2>")
    st.caption("Synthesize live retail performance ledgers into an executive-grade strategic narrative using local Ollama and compile directly into an enterprise-level PDF.")

    audit_col1, audit_col2 = st.columns([2.5, 1.5], gap="large")
    with audit_col1:
        rep_scope = st.selectbox(
            "Select Audit Timeframe Horizon:",
            [
                "Weekly Operations Audit (Last 7 Days)",
                "Monthly Strategic Audit (Last 30 Days)",
                "Comprehensive Strategic Analysis (All-Time Database)"
            ],
            key="studio_pdf_scope_select"
        )
        scope_code = "weekly" if "Weekly" in rep_scope else ("monthly" if "Monthly" in rep_scope else "complete")

    with audit_col2:
        st.markdown("<div style='padding-top: 28px;'>", unsafe_allow_html=True)
        gen_clicked = st.button("🚀 Generate AI Strategic Audit", type="primary", use_container_width=True, key="studio_gen_ai_btn")
        st.markdown("</div>", unsafe_allow_html=True)

    if gen_clicked:
        with st.spinner(f"Synthesizing {rep_scope} with {st.session_state.copilot_model} and compiling enterprise PDF..."):
            try:
                rep_data = fetch_report_datasets(db, scope_code)
                if generate_executive_audit_commentary:
                    ai_commentary = generate_executive_audit_commentary(
                        report_data=rep_data,
                        timeframe_label=rep_scope,
                        model=st.session_state.copilot_model
                    )
                elif hasattr(local_analyst, "generate_executive_audit_commentary"):
                    ai_commentary = local_analyst.generate_executive_audit_commentary(
                        report_data=rep_data,
                        timeframe_label=rep_scope,
                        model=st.session_state.copilot_model
                    )
                else:
                    import src.ai.ollama_client as ig_mod
                    importlib.reload(ig_mod)
                    fresh_analyst = ig_mod.LocalOllamaBoutiqueAnalyst(model_name=st.session_state.copilot_model)
                    ai_commentary = fresh_analyst.generate_executive_audit_commentary(
                        report_data=rep_data,
                        timeframe_label=rep_scope,
                        model=st.session_state.copilot_model
                    )
                pdf_bytes = generate_enterprise_pdf(
                    db=db,
                    report_type=scope_code,
                    ai_commentary=ai_commentary
                )
                st.session_state.last_ai_audit = {
                    "pdf_bytes": pdf_bytes,
                    "commentary": ai_commentary,
                    "scope_label": rep_scope,
                    "scope_code": scope_code,
                    "model": st.session_state.copilot_model,
                    "timestamp": datetime.now().strftime("%B %d, %Y - %H:%M:%S")
                }
                st.success("Enterprise Audit Report compiled successfully!")
            except Exception as e:
                logger.error(f"Error generating AI strategic audit: {e}")
                st.error(f"Failed to generate report: {e}")

    # Display Last Generated Report Preview & Download if available
    if "last_ai_audit" in st.session_state and st.session_state.last_ai_audit:
        audit_res = st.session_state.last_ai_audit
        st.markdown("<br>", unsafe_allow_html=True)

        down_col_left, down_col_right = st.columns([2.5, 1.5])
        with down_col_left:
            st.markdown(f"**Latest Generated Report:** `{audit_res['scope_label']}`")
            st.caption(f"Synthesized by **{audit_res['model']}** on {audit_res['timestamp']}. Fully verified against SQLite transaction ledgers.")
        with down_col_right:
            dl_filename = f"HauteBoutique_AI_Audit_{audit_res['scope_code']}_{datetime.now().strftime('%Y%m%d')}.pdf"
            st.download_button(
                label="📥 Download Enterprise PDF",
                data=audit_res["pdf_bytes"],
                file_name=dl_filename,
                mime="application/pdf",
                type="primary",
                use_container_width=True,
                key="studio_dl_ai_pdf_btn"
            )

        with st.expander("👁️ Review AI Executive Commentary Preview", expanded=True):
            st.markdown(audit_res["commentary"])