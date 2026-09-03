import streamlit as st
import pandas as pd
import random
import json
import time
from datetime import datetime
import plotly.express as px

# Import decoupled custom structural logic dependencies
from database_manager import DatabaseManager
from simulation_engine import SimulationEngine
from insight_generator_ollama import LocalOllamaBoutiqueAnalyst

# Load the comprehensive 20-product array configuration modules
from catalog_config import CATALOG, generate_initial_inventory
from theme_manager import render_luxury_kpi_strip, inject_luxury_branding

from streamlit_lottie import st_lottie
from animation_assets import get_local_animation_pack

# Core Engine Global Persistence Instances Setup
db = DatabaseManager()
sim = SimulationEngine(CATALOG, db)


@st.cache_resource
def init_ollama():
    return LocalOllamaBoutiqueAnalyst(model_name="llama3.1")


local_analyst = init_ollama()

# 🔥 DYNAMIC SCHEMA SAFEGUARD: Initialize memory states straight from SQLite tables
if "live_inventory" not in st.session_state:
    db_inventory = db.get_current_stock_on_hand()
    if db_inventory and len(db_inventory) == len(CATALOG):
        st.session_state.live_inventory = db_inventory
    else:
        st.session_state.live_inventory = generate_initial_inventory()

if "store_controls" not in st.session_state:
    db_settings = db.get_all_circuit_controls()
    if db_settings and len(db_settings) == len(CATALOG):
        st.session_state.store_controls = db_settings
    else:
        st.session_state.store_controls = {
            pid: {"sales_enabled": True, "purchase_enabled": True, "max_stock": 100}
            for pid in CATALOG
        }

if "frame_counter" not in st.session_state:
    st.session_state.frame_counter = 0

# 🔥 INLINE BRANDING PASS: Force premium styles into the browser window immediately
st.markdown("""
    <link href="https://jsdelivr.net" rel="stylesheet">
    <link href="https://googleapis.com" rel="stylesheet">

    <style>
    html, body, [class*="st-text"], .stMarkdown { font-family: 'Inter', sans-serif; color: #1e293b; }
    h1, h2, h3, .luxury-title { font-family: 'Playfair Display', serif !important; color: #0f172a !important; }

    .premium-card {
        background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03); position: relative; overflow: hidden;
    }
    .metric-card {
        background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 5px solid #2c3e50; margin-bottom: 15px;
    }
    .badge-dead { background-color: #fdebd0; color: #b03a2e; padding: 4px 8px; border-radius: 4px; font-weight: bold; }

    /* 2D Sprite Animation Keyframes */
    @keyframes driveIn {
        0% { transform: translateX(-150px); opacity: 0; }
        45% { transform: translateX(180px); opacity: 1; }
        75% { transform: translateX(180px); opacity: 1; }
        100% { transform: translateX(600px); opacity: 0; }
    }
    @keyframes walkAndShop {
        0% { transform: translateX(500px); opacity: 0; }
        45% { transform: translateX(250px); opacity: 1; }
        75% { transform: translateX(250px); opacity: 1; }
        100% { transform: translateX(-100px); opacity: 0; }
    }
    @keyframes fillWave {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .animate-truck { animation: driveIn 2.5s cubic-bezier(0.25, 1, 0.5, 1) forwards; }
    .animate-shopper { animation: walkAndShop 2.5s cubic-bezier(0.25, 1, 0.5, 1) forwards; }

    .liquid-tank {
        position: relative; width: 100px; height: 100px; background: #e2e8f0; border-radius: 50%; overflow: hidden; border: 3px solid #1e293b;
    }
    .liquid-wave {
        position: absolute; width: 200%; height: 200%; background: #2c3e50; left: -50%; border-radius: 38%;
        animation: fillWave 6s infinite linear; transition: top 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }
    </style>
""", unsafe_allow_html=True)

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
    st.markdown("<h1 class='luxury-title text-4xl font-bold mb-1'>👗 Executive Strategy Analytics</h1>", unsafe_allow_html=True)
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
        st.markdown(f'<div class="premium-card" style="border-left: 5px solid #10b981;"><p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Database Session Revenue</p><h3 class="text-3xl font-bold text-slate-800 mt-1">${total_revenue_db:,.2f}</h3></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="premium-card" style="border-left: 5px solid #3b82f6;"><p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Achieved Real Gross Margin</p><h3 class="text-3xl font-bold text-slate-800 mt-1">{avg_margin_db:.1f}%</h3></div>', unsafe_allow_html=True)
    with col_m3:
        st.markdown(f'<div class="premium-card" style="border-left: 5px solid #f59e0b;"><p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Size Matrix Anomalies</p><h3 class="text-3xl font-bold text-slate-800 mt-1">{len(broken_curves)} Outages</h3></div>', unsafe_allow_html=True)

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
                st.markdown(f"""
                <div class="metric-card">
                    <span class="badge-dead">Size Curve Gap</span>
                    <h4 style="margin: 10px 0 5px 0; color: #2c3e50;">{alert['product_name']}</h4>
                    <p style="font-size:0.92em; margin-bottom:8px; color: #333;"><b>Missing Sizes:</b> <code style="color:#b03a2e; font-weight:bold;">{sizes_str}</code> | <b>Stranded Stock:</b> {alert['stranded_stock_volume']} units</p>
                    <p style="font-size:0.85em; color:#555; background-color:#fff; padding:8px; border-radius:4px; border:1px solid #dee2e6;">💡 <b>Action:</b> {alert['remedy']}</p>
                </div>
                """, unsafe_allow_html=True)

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
    # Load premium global fonts and visual element overrides
    inject_luxury_branding()

    st.markdown("<h1 class='luxury-title text-4xl font-bold mb-1'>⚡ Real-Time Operations Stream Ingestion</h1>",
                unsafe_allow_html=True)
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
        event_text, event_type = sim.process_tick(promo_discount, st.session_state.live_inventory)

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

            # B. CRASH-PROOF ANIMATION BANNER (Uses clean styled HTML panels that load instantly offline)
            with animation_stage_p.container():
                if event_type == "Purchase":
                    status_banner_html = """
                    <div class="w-full flex items-center justify-between p-4 rounded-xl border-l-4 border-blue-500 shadow-sm" style="background-color:#eff6ff; animation: fadeIn 0.3s ease-out;">
                        <div class="flex items-center space-x-3">
                            <span style="font-size: 2.25rem; animation: subtle-pulse 1.5s infinite;">🚚</span>
                            <div>
                                <h4 class="font-bold text-blue-900 font-sans" style="margin:0; font-size:14px;">B2B REQUISITION INTAKE ACTIVE</h4>
                                <p class="text-xs text-blue-700" style="margin:2px 0 0 0;">Fulfillment truck arrived. Stocking +20 units evenly split across grid matrices.</p>
                            </div>
                        </div>
                        <span class="text-xs font-mono font-bold px-2 py-1 bg-blue-200 text-blue-800 rounded">STOCK INCREASE</span>
                    </div>
                    """
                elif event_type == "Sale":
                    status_banner_html = """
                    <div class="w-full flex items-center justify-between p-4 rounded-xl border-l-4 border-emerald-500 shadow-sm" style="background-color:#ecfdf5; animation: fadeIn 0.3s ease-out;">
                        <div class="flex items-center space-x-3">
                            <span style="font-size: 2.25rem; animation: subtle-pulse 1.5s infinite;">🚶‍♂️</span>
                            <div>
                                <h4 class="font-bold text-emerald-900 font-sans" style="margin:0; font-size:14px;">CUSTOMER TRANSACTION PROCESSED</h4>
                                <p class="text-xs text-emerald-700" style="margin:2px 0 0 0;">Shopper checkout complete. Deducting 1 unit from size inventory allocation maps.</p>
                            </div>
                        </div>
                        <span class="text-xs font-mono font-bold px-2 py-1 bg-emerald-200 text-emerald-800 rounded">VAULT REVENUE YIELD</span>
                    </div>
                    """
                else:
                    status_banner_html = """
                    <div class="w-full flex items-center justify-between p-4 rounded-xl border-l-4 border-slate-400 shadow-sm" style="background-color:#f8fafc;">
                        <div class="flex items-center space-x-3">
                            <span style="font-size: 2.25rem;">⏱️</span>
                            <div>
                                <h4 class="font-bold text-slate-700 font-sans" style="margin:0; font-size:14px;">SYSTEM CORE SCANNING...</h4>
                                <p class="text-xs text-slate-500" style="margin:2px 0 0 0;">Monitoring point-of-sale logs and vendor lines for real-time traffic events.</p>
                            </div>
                        </div>
                        <span class="text-xs font-mono text-slate-400">IDLE SCURRY</span>
                    </div>
                    """
                st.markdown(status_banner_html, unsafe_allow_html=True)

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
        inject_luxury_branding()
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
