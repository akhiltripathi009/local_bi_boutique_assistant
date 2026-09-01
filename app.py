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

# 🔥 NEW: Load the updated 20-product array structure
from catalog_config import CATALOG, generate_initial_inventory

# Core Global Engine Initialization
db = DatabaseManager()
sim = SimulationEngine(CATALOG, db)


@st.cache_resource
def init_ollama(): return LocalOllamaBoutiqueAnalyst(model_name="llama3.2:3b")


local_analyst = init_ollama()

# UI Global Stylesheet Configs
st.markdown(
    "<style>.metric-card {background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 5px solid #2c3e50; margin-bottom: 15px;}</style>",
    unsafe_allow_html=True)

# app.py (Part 1 - Top Initialization Section)

# 🔥 FIX: Live inventory state initialization pulls directly from SQLite tables
# This ensures that if stock reaches 0 units, it stays 0 units across page refreshes!
if "live_inventory" not in st.session_state:
    db_inventory = db.get_current_stock_on_hand()

    if db_inventory and len(db_inventory) == len(CATALOG):
        st.session_state.live_inventory = db_inventory
    else:
        # Safe fallback generation logic if the database file is running for the very first time
        from catalog_config import generate_initial_inventory

        st.session_state.live_inventory = generate_initial_inventory()

# app.py (Part 1 - Initialization Section)

# Ensure the database schemas and defaults exist before checking state values
db = DatabaseManager()

# 🔥 FIX: Dynamically populate session state directly from SQLite instead of defaults
if "store_controls" not in st.session_state:
    db_settings = db.get_all_circuit_controls()

    # If the database returns records, use them. Otherwise, fall back to safe defaults.
    if db_settings and len(db_settings) == len(CATALOG):
        st.session_state.store_controls = db_settings
    else:
        # Fallback seeding logic if the database is completely pristine
        st.session_state.store_controls = {
            pid: {"sales_enabled": True, "purchase_enabled": True, "max_stock": 100}
            for pid in CATALOG
        }

# Update Navigation Controller menu options array in your sidebar layout row
st.sidebar.title("🎛️ Navigation Control")
view_selection = st.sidebar.radio(
    "Select View Module Layer:",
    ["📊 Strategy Analytics Dashboard", "⚡ Real-Time Operational Stream", "⚙️ Master Control Switchboard"]
)

# ==========================================
# MODULE 1: STRATEGY ANALYTICS DASHBOARD VIEW
# ==========================================
if view_selection == "📊 Strategy Analytics Dashboard":
    st.title("👗 Apparel Boutique Strategy Analytics")
    st.caption("Deep-dive historical aggregations pulled directly out of your local SQLite database profile caches.")

    # Delegate data pipeline fetches completely to DatabaseManager
    sales_history = db.fetch_logs("sales_ledger", limit=100)
    total_revenue_db = db.get_total_historical_revenue()
    avg_margin_db = db.get_average_gross_margin()
    competitor_pricing_data = db.fetch_dynamic_competitor_pricing()

    st_df = db.fetch_dynamic_sell_through_metrics()

    sentiment_metrics_data = db.fetch_dynamic_sentiment_metrics()

    broken_curves = db.calculate_dynamic_broken_curves()

    # Top Metric Bar UI Layout Element
    cm1, cm2, cm3 = st.columns(3)
    cm1.metric("Database Session Revenue", f"${total_revenue_db:,.2f}")
    cm2.metric("Achieved Real Gross Margin", f"{avg_margin_db:.1f}%")
    cm3.metric("Size Matrix Anomalies", f"{len(broken_curves)} Outages")

    st.markdown("---")
    left_p, right_p = st.columns(2)

    with left_p:
        st.subheader("📈 Merchandise Sell-Through Velocity")
        st.plotly_chart(px.bar(st_df, x="sell_through_pct", y="product_name", color="status", orientation="h",
                               template="simple_white"), use_container_width=True, key="ds_st")

        st.subheader("🏬 Competitor Price Index Positioning")
        fig_c = px.bar(competitor_pricing_data, x="pricing_index", y="product_name", color="position", orientation="h",
                       template="simple_white")
        fig_c.add_vline(x=100, line_width=2, line_dash="dash", line_color="#e74c3c")
        st.plotly_chart(fig_c, use_container_width=True, key="ds_comp")

    with right_p:
        st.subheader("🧵 Operations Sentiment Matrix")
        st.plotly_chart(
            px.bar(sentiment_metrics_data, x="Average Sentiment Score", y="Operational Category", color="Status",
                   orientation="h", template="simple_white"), use_container_width=True, key="ds_sent")

        st.subheader("⚠️ Broken Size Curve Alerts")
        for alert in broken_curves:
            sizes_str = ", ".join(alert['missing_core_sizes'])
            st.markdown(
                f'<div class="metric-card"><h4 style="color:#2c3e50;">{alert["product_name"]}</h4><p><b>Missing Sizes:</b> <code>{sizes_str}</code></p><p style="font-size:0.85em; background:#fff; padding:5px;">💡 {alert["remedy"]}</p></div>',
                unsafe_allow_html=True)

    # Chat Copilot UI Workspace
    st.markdown("---")
    st.subheader("💬 Local Copilot Conversational Engine")
    with st.form(key="chat_f"):
        user_query = st.text_input("Ask your local boutique assistant:",
                                   placeholder="e.g., Summary of pricing positions?")
        submit_btn = st.form_submit_button("Ask Copilot Engine")

    if submit_btn and user_query:
        with st.spinner("Processing..."):
            import ollama

            res = ollama.chat(model="llama3.2:3b", messages=[
                {"role": "user", "content": f"Context: {st_df.to_json()} Question: {user_query}"}])
            st.success("🤖 Copilot Matrix Response:")
            st.markdown(res['message']['content'])

# ==========================================
# MODULE 2: REAL-TIME OPERATIONAL STREAM VIEW
# ==========================================
elif view_selection == "⚡ Real-Time Operational Stream":
    st.title("⚡ Real-Time Operations Stream Ingestion")
    st.caption("Live streaming engine saving transaction parameters directly onto your permanent SQLite storage.")

    # 🔥 CRASH FIX: Safe inline fallback verification guardrail
    if "frame_counter" not in st.session_state:
        st.session_state.frame_counter = 0

    promo_discount = st.sidebar.slider("Active Flash Sale Markdown (%)", 0, 50, 0, step=10)
    stream_speed = st.sidebar.slider("Simulation Tick Speed (Secs)", 0.2, 2.0, 0.8)
    start_stream = st.sidebar.checkbox("▶️ Activate Real-Time Ingestion Loop", value=False)

    # Layout rendering placeholders to swap elements smoothly in-place without page jumping
    kpi_p = st.empty()
    chart_p = st.empty()
    log_p = st.empty()

    while start_stream:
        st.session_state.frame_counter += 1

        # 1. Execute simulation updates in background thread directly into the SQLite tables

        event_text, event_type = sim.process_tick(
            promo_discount,
            st.session_state.live_inventory
        )

        # 🔥 FIX: Initialize empty fallback dataframes so they are never undefined
        live_sales_view = pd.DataFrame()
        live_purchases_view = pd.DataFrame()
        current_total_revenue = db.get_total_historical_revenue()

        # 2. Throttles heavy layout re-renders to every 3rd simulation tick
        if st.session_state.frame_counter % 3 == 0:
            # Overwrite the empty dataframes with real data from the database
            live_sales_view = db.fetch_logs("sales_ledger", limit=5)
            live_purchases_view = db.fetch_logs("purchase_ledger", limit=5)

            # Redraw real-time KPI information badges
            with kpi_p.container():
                ck1, ck2, ck3 = st.columns(3)
                ck1.metric("Live Streaming Revenue (SQLite)", f"${current_total_revenue:,.2f}")
                ck2.metric("Low Stock Items (<15 units)",
                           sum(1 for v in st.session_state.live_inventory.values() if v <= 15))

                # Color-code block display logs based on simulation block outcomes
                if event_type == "Sale":
                    ck3.success(event_text)
                elif event_type == "Purchase":
                    ck3.info(event_text)
                elif "BLOCKED" in event_text:
                    ck3.warning(event_text)  # <-- Added warning display for blocks
                else:
                    ck3.write("⏱️ Background transactions running...")

            # Redraw structural live inventory bar charts with unique dynamic hashing keys
            with chart_p.container():
                inv_df = pd.DataFrame([{"Product": CATALOG[pid]["name"], "Stock Level": s} for pid, s in
                                       st.session_state.live_inventory.items()])
                fig_l = px.bar(inv_df, x="Product", y="Stock Level", text="Stock Level",
                               title="Real-Time Fluctuating Store Volumes")
                fig_l.update_layout(yaxis=dict(range=[0, 310]), template="simple_white", height=340)

                # Dynamic timestamp hashing fixes Streamlit Duplicate ID element exceptions safely
                st.plotly_chart(fig_l, use_container_width=True, key=f"ch_{time.time()}_{random.randint(0, 100)}")

        # Redraw streaming row ledgers directly out from the permanent hard-drive data matrices
        with log_p.container():
            cl, cr = st.columns(2)
            with cl:
                st.markdown("### 📥 Live Sales Log")
                if not live_sales_view.empty: st.dataframe(
                    live_sales_view[["timestamp", "product_name", "total_revenue", "gross_profit"]],
                    use_container_width=True, hide_index=True)
            with cr:
                st.markdown("### 📤 Live Restocks Log")
                if not live_purchases_view.empty: st.dataframe(
                    live_purchases_view[["timestamp", "product_name", "quantity", "total_cost"]],
                    use_container_width=True, hide_index=True)

        # 3. Dynamic throttling step forces the system screen execution frames to stabilize
        time.sleep(max(stream_speed, 0.6))

    if not start_stream:
        st.info(
            "💡 **System Engine Offline:** Check the activation box on the left sidebar to start the animated stream feed.")

# ==========================================
# MODULE 3: MASTER CONTROL SWITCHBOARD VIEW
# ==========================================
# ==========================================
# MODULE 3: MASTER CONTROL SWITCHBOARD VIEW
# ==========================================
elif view_selection == "⚙️ Master Control Switchboard":
    st.title("⚙️ Operations Circuit Master Switchboard")
    st.caption("Manually enable/disable transactions or adjust maximum stock bounds across all 20 clothing styles.")

    st.markdown("---")

    # Always pull a clean copy from the database file on page load
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
                    # Capture layout interaction input
                    allow_sales = st.toggle("Allow Sales", value=current_settings["sales_enabled"], key=f"s_tgl_{pid}")
                    if allow_sales != current_settings["sales_enabled"]:
                        db.update_circuit_control(pid, "sales_enabled", allow_sales)
                        st.rerun()

                with col_pur:
                    allow_restock = st.toggle("Allow Restock", value=current_settings["purchase_enabled"],
                                              key=f"p_tgl_{pid}")
                    if allow_restock != current_settings["purchase_enabled"]:
                        db.update_circuit_control(pid, "purchase_enabled", allow_restock)
                        st.rerun()

                with col_max:
                    max_cap = st.number_input("Max Capacity Cap", min_value=10, max_value=300,
                                              value=current_settings["max_stock"], step=10, key=f"m_in_{pid}")
                    if max_cap != current_settings["max_stock"]:
                        db.update_circuit_control(pid, "max_stock", max_cap)
                        st.rerun()

                st.markdown("<hr style='margin: 0.5em 0; border: 0; border-top: 1px solid #eee;' />",
                            unsafe_allow_html=True)
