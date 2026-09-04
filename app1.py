import streamlit as st
import pandas as pd
import random
import json
import time
import logging
from datetime import datetime
import plotly.express as px
from logger_config import setup_logging

# Initialize main application logger
logger = setup_logging("app_premium")

# Import decoupled custom structural logic dependencies
from database_manager import DatabaseManager
from simulation_engine import SimulationEngine
from insight_generator_ollama import LocalOllamaBoutiqueAnalyst

# Load the comprehensive 20-product array configuration modules
from catalog_config import CATALOG, generate_initial_inventory
from theme_manager import render_luxury_kpi_strip, inject_luxury_branding, render_animated_arena

from streamlit_lottie import st_lottie
from animation_assets import get_local_animation_pack

# Core Engine Global Persistence Instances Setup
db = DatabaseManager()
sim = SimulationEngine(CATALOG, db)


@st.cache_resource
def init_ollama():
    """
    Caches the local AI analyst instance to prevent re-initialization on every rerun.
    Uses llama3.1 model by default for the premium dashboard.
    """
    try:
        return LocalOllamaBoutiqueAnalyst(model_name="llama3.1")
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

# Navigation Menu Router Sidebar
st.sidebar.title("🎛️ Navigation Control")
view_selection = st.sidebar.radio(
    "Select View Module Layer:",
    ["📊 Strategy Analytics Dashboard", "⚡ Real-Time Operational Stream", "⚙️ Master Control Switchboard"]
)


# ==========================================
# MODULE 1: STRATEGY ANALYTICS DASHBOARD VIEW
# ==========================================
if view_selection == "📊 Strategy Analytics Dashboard":
    st.html("<h1 class='luxury-title text-4xl font-bold mb-1'>👗 Executive Strategy Analytics</h1>")
    st.caption("Deep-dive historical aggregations pulled directly out of your local SQLite database profile caches.")

    # Query completely dynamic datasets from DatabaseManager
    sales_history = db.fetch_logs("sales_ledger", limit=100)
    total_revenue_db = db.get_total_historical_revenue()
    avg_margin_db = db.get_average_gross_margin()
    competitor_pricing_data = db.fetch_dynamic_competitor_pricing()
    st_df = db.fetch_dynamic_sell_through_metrics()
    sentiment_metrics_data = db.fetch_dynamic_sentiment_metrics()
    broken_curves = db.calculate_dynamic_broken_curves()

    # Top KPI Metrics row bar built with TailwindCSS HTML
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.html(f'<div class="premium-card" style="border-left: 5px solid #10b981;"><p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Database Session Revenue</p><h3 class="text-3xl font-bold text-slate-800 mt-1">${total_revenue_db:,.2f}</h3></div>')
    with col_m2:
        st.html(f'<div class="premium-card" style="border-left: 5px solid #3b82f6;"><p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Achieved Real Gross Margin</p><h3 class="text-3xl font-bold text-slate-800 mt-1">{avg_margin_db:.1f}%</h3></div>')
    with col_m3:
        st.html(f'<div class="premium-card" style="border-left: 5px solid #f59e0b;"><p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Size Matrix Anomalies</p><h3 class="text-3xl font-bold text-slate-800 mt-1">{len(broken_curves)} Outages</h3></div>')

    st.markdown("<br>", unsafe_allow_html=True)
    left_pane, right_pane = st.columns(2)

    with left_pane:
        st.subheader("📈 Merchandise Sell-Through Velocity")
        fig_st = px.bar(st_df.head(8), x="sell_through_pct", y="product_name", color="status", orientation="h", template="simple_white",
                        color_discrete_map={"Hot Seller": "#2ecc71", "Healthy": "#3498db", "Dead Inventory Risk": "#e74c3c"})
        fig_st.update_layout(yaxis={'categoryorder': 'total ascending'}, height=360)
        st.plotly_chart(fig_st, use_container_width=True, key="dash_st_chart")

        st.subheader("🏬 Competitor Price Index Positioning")
        fig_comp = px.bar(competitor_pricing_data, x="pricing_index", y="product_name", color="position", orientation="h", template="simple_white",
                          color_discrete_map={"Market Aligned": "#34495e", "Underpriced Hazard": "#f1c40f", "Premium Positioned": "#9b59b6"})
        fig_comp.add_vline(x=100, line_width=2, line_dash="dash", line_color="#e74c3c")
        fig_comp.update_layout(height=360)
        st.plotly_chart(fig_comp, use_container_width=True, key="dash_comp_chart")

    with right_pane:
        st.subheader("🧵 Operations Sentiment Matrix")
        fig_sent = px.bar(sentiment_metrics_data, x="Average Sentiment Score", y="Operational Category", color="Status", orientation="h", template="simple_white",
                          color_discrete_map={"Optimal Positive Index": "#2c3e50", "Negative Volatility Alert": "#e74c3c"})
        fig_sent.update_layout(xaxis=dict(range=[-1.1, 1.1]), height=360)
        st.plotly_chart(fig_sent, use_container_width=True, key="dash_sentiment_chart")

        st.subheader("⚠️ Broken Size Curve Alerts")
        if not broken_curves:
            st.caption("✅ No dynamic size curves breaches discovered across active catalog lines.")
        else:
            for alert in broken_curves[:3]:
                sizes_str = ", ".join(alert['missing_core_sizes'])
                st.html(f"""
                <div class="metric-card">
                    <span class="badge-dead">Size Curve Gap</span>
                    <h4 style="margin: 10px 0 5px 0; color: #2c3e50;">{alert['product_name']}</h4>
                    <p style="font-size:0.92em; margin-bottom:8px; color: #333;"><b>Missing Sizes:</b> <code style="color:#b03a2e; font-weight:bold;">{sizes_str}</code> | <b>Stranded Stock:</b> {alert['stranded_stock_volume']} units</p>
                    <p style="font-size:0.85em; color:#555; background-color:#fff; padding:8px; border-radius:4px; border:1px solid #dee2e6;">💡 <b>Action:</b> {alert['remedy']}</p>
                </div>
                """)

    # Chat Copilot UI Workspace Form
    st.markdown("---")
    st.subheader("💬 Local Copilot Conversational Engine")
    with st.form(key="chat_f"):
        user_query = st.text_input("Ask your local boutique assistant:", placeholder="e.g., Summary of catalog fit or price indexing parameters?")
        submit_btn = st.form_submit_button("Ask Copilot Engine")

    if submit_btn and user_query:
        with st.spinner("Processing inquiry matrices locally..."):
            import ollama
            chat_context = {"sell_through": st_df.head(5).to_dict('records'), "competitors": competitor_pricing_data.head(5).to_dict('records')}
            res = ollama.chat(model="llama3.1", messages=[{"role": "user", "content": f"Context: {json.dumps(chat_context)} Question: {user_query}. Keep answers under 3 direct sentences."}])
            st.success("🤖 Copilot Matrix Response:")
            st.markdown(res['message']['content'])

# ==========================================
# MODULE 2: REAL-TIME OPERATIONAL STREAM VIEW
# ==========================================
elif view_selection == "⚡ Real-Time Operational Stream":
    st.html("<h1 class='luxury-title text-4xl font-bold mb-1'>⚡ Real-Time Operations Stream Ingestion</h1>")
    st.caption(
        "Live streaming engine backed by stable, inline native CSS layout indicators and relational data logging.")

    # Inline protection guardrail ensuring loop tracking index is initialized
    if "frame_counter" not in st.session_state:
        st.session_state.frame_counter = 0

    # Sidebar control elements for the simulation engine
    promo_discount = st.sidebar.slider("Active Flash Sale Markdown (%)", 0, 50, 0, step=10)
    stream_speed = st.sidebar.slider("Simulation Tick Speed (Secs)", 0.2, 2.0, 0.8)
    start_stream = st.sidebar.checkbox("▶️ Activate Real-Time Ingestion Loop", value=False)

    # Layout rendering placeholders to swap elements smoothly in-place without screen lag
    kpi_p = st.empty()
    animation_stage_p = st.empty()
    chart_p = st.empty()
    log_p = st.empty()

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

            # A. Draw Premium KPI Glassmorphic Cards via Theme Manager
            with kpi_p.container():
                low_stock_count = sum(1 for v in st.session_state.live_inventory.values() if v <= 15)
                badge_html = '<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-red-500 text-white animate-pulse">● LIVE STREAM</span>'
                st.markdown(f"""
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 my-4">
                    <div class="premium-card" style="border-left: 5px solid #10b981; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);"><p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Database Stream Revenue</p><h3 class="text-3xl font-bold mt-1">${current_total_revenue:,.2f}</h3></div>
                    <div class="premium-card" style="border-left: 5px solid #f59e0b; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);"><p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Safety Breaches</p><h3 class="text-3xl font-bold mt-1 text-amber-600">{low_stock_count} Styles</h3></div>
                    <div class="premium-card" style="border-left: 5px solid #3b82f6; background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);"><div class="flex justify-between items-center mb-1"><p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Engine Processing State</p>{badge_html}</div><p class="text-sm font-medium text-slate-700 mt-2 truncate">{event_text if event_text else "Scanning data pipelines..."}</p></div>
                </div>
                """, unsafe_allow_html=True)

            # B. CRASH-PROOF ANIMATION BANNER (Uses dynamic sprite animations from Theme Manager)
            with animation_stage_p.container():
                if event_pid:
                    c_qty = st.session_state.live_inventory.get(event_pid, 0)
                    m_qty = st.session_state.store_controls.get(event_pid, {}).get("max_stock", 100)
                    render_animated_arena(event_type, c_qty, m_qty)
                else:
                    # Fallback for idle state or errors
                    render_animated_arena("Idle", 0, 100)

            # C. Draw Minimalist Stock Charts with Fixed Y-Axis Layout Bounds
            with chart_p.container():
                inv_df = pd.DataFrame([{"Product": CATALOG[pid]["name"], "Stock Level": s} for pid, s in
                                       st.session_state.live_inventory.items()])
                fig_l = px.bar(inv_df, x="Product", y="Stock Level", text="Stock Level",
                               title="Live Warehouse Quantity On Hand Profiles", color_discrete_sequence=["#1e293b"])
                fig_l.update_layout(yaxis=dict(range=[0, 300], title=""), xaxis=dict(title="", tickangle=-30),
                                    template="simple_white", height=320,
                                    title_font=dict(family="Playfair Display", size=16))
                fig_l.update_traces(textposition='outside', marker_line_color='#0f172a', marker_line_width=1)
                st.plotly_chart(fig_l, use_container_width=True, key=f"ch_{time.time()}_{random.randint(0, 100)}")

            # D. Draw Relational Ledger Streaming Row Data Logs
            with log_p.container():
                cl, cr = st.columns(2)
                with cl:
                    st.markdown("### 📥 Live Sales Log (SQLite Table)")
                    if not live_sales_view.empty:
                        for _, row in live_sales_view.iterrows():
                            time_stamp = row["timestamp"].split()[-1]
                            st.info(
                                f"🟢 **{time_stamp}** | **{row['product_name']}** sold for **${row['total_revenue']:.2f}** ({row['campaign_name']})")
                    else:
                        st.caption("Awaiting incoming sales metrics...")
                with cr:
                    st.markdown("### 📤 Live Restocks Log (SQLite Table)")
                    if not live_purchases_view.empty:
                        for _, row in live_purchases_view.iterrows():
                            time_stamp = row["timestamp"].split()[-1]
                            st.markdown(
                                f"🔵 **{time_stamp}** | Received **{row['quantity']}x {row['product_name']}** (Cost: ${row['total_cost']:.2f})")
                    else:
                        st.caption("Awaiting incoming inventory arrivals...")

        # Dynamic throttling delay forces screen render frames to fully stabilize
        time.sleep(max(stream_speed, 0.4))

    if not start_stream:
        render_luxury_kpi_strip(db.get_total_historical_revenue(),
                                sum(1 for v in st.session_state.live_inventory.values() if v <= 15), "Engine Offline",
                                is_active=False)
        st.info(
            "💡 **System Engine Offline:** Check the activation box on the left sidebar to start the animated stream feed.")




# ==========================================
# MODULE 3: MASTER CONTROL SWITCHBOARD VIEW
# ==========================================
elif view_selection == "⚙️ Master Control Switchboard":
    st.markdown("<h1 class='luxury-title text-4xl font-bold mb-1'>⚙️ Operations Circuit Switchboard</h1>",
                unsafe_allow_html=True)
    st.caption("Manually enable/disable transactions or adjust maximum stock bounds across all 20 clothing styles.")

    st.markdown("---")
    active_controls = db.get_all_circuit_controls()
    categories = sorted(list(set(details["category"] for details in CATALOG.values())))
    tabs = st.tabs(categories)

    for idx, cat_name in enumerate(categories):
        with tabs[idx]:
            st.subheader(f"Inventory Circuits: {cat_name}")
            cat_pids = [pid for pid, details in CATALOG.items() if details["category"] == cat_name]

            for pid in cat_pids:
                col_name, col_sale, col_pur, col_max = st.columns([2, 1, 1, 1.5])
                current_settings = active_controls.get(pid, {"sales_enabled": True, "purchase_enabled": True,
                                                             "max_stock": 100})

                with col_name:
                    st.markdown(f"**{CATALOG[pid]['name']}** ({pid})")
                    current_qty = st.session_state.live_inventory.get(pid, 0)
                    st.caption(f"Warehouse Stock Balance: `{current_qty} Units`")

                with col_sale:
                    allow_sales = st.toggle("Allow Sales", value=current_settings["sales_enabled"], key=f"s_tgl_{pid}")
                    if allow_sales != current_settings["sales_enabled"]:
                        db.update_circuit_control(pid, "sales_enabled", allow_sales)
                        st.session_state.store_controls[pid]["sales_enabled"] = allow_sales
                        st.rerun()

                with col_pur:
                    allow_restock = st.toggle("Allow Restock", value=current_settings["purchase_enabled"],
                                              key=f"p_tgl_{pid}")
                    if allow_restock != current_settings["purchase_enabled"]:
                        db.update_circuit_control(pid, "purchase_enabled", allow_restock)
                        st.session_state.store_controls[pid]["purchase_enabled"] = allow_restock
                        st.rerun()

                with col_max:
                    max_cap = st.number_input("Max Capacity Cap", min_value=10, max_value=300,
                                              value=current_settings["max_stock"], step=10, key=f"m_in_{pid}")
                    if max_cap != current_settings["max_stock"]:
                        db.update_circuit_control(pid, "max_stock", max_cap)
                        st.session_state.store_controls[pid]["max_stock"] = max_cap
                        st.rerun()

                st.markdown("<hr style='margin: 0.5em 0; border: 0; border-top: 1px solid #eee;' />",
                            unsafe_allow_html=True)
