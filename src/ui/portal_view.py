"""
src/ui/portal_view.py
=====================
Renders the Boutique Operations Portal view:
1. Stock Transfer between Shop Floor and Warehouse Storage (isolated backroom).
2. Register New Product into Catalog and Inventory.
3. Procurement Re-Ordering for any product in any quantity.
4. Custom Promotional Campaigns Launchpad.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from datetime import datetime

from src.core.catalog import CATALOG

def render_boutique_portal_view(db):
    """Renders the comprehensive Boutique Operations Portal."""
    st.html("<h1 class='luxury-title text-3xl font-bold mb-1'>📦 Boutique Operations & Stock Portal</h1>")
    st.caption("Manage isolated warehouse backroom inventory, add new catalog collections, procurement re-ordering, and sales campaigns.")

    # Portal Notice
    st.html("""
    <div style="background:#f8fafc; border-left:4px solid #0f172a; padding:10px 16px; border-radius:8px; margin: 10px 0 16px 0;">
        <span style="font-size:13px; color:#334155; line-height:1.5;">
            <b>📌 Isolated Backroom Inventory Architecture:</b> Items in the <b>Warehouse</b> are strictly isolated from the <b>Shop Floor</b>.
            Warehouse items are <i>never</i> displayed to shoppers or eligible for store checkouts until formally transferred to the shop floor.
        </span>
    </div>
    """)

    # Portal Sub-Tabs
    tab_transfer, tab_add_prod, tab_order, tab_campaigns = st.tabs([
        "🔄 Stock Transfer (Shop ⇄ Warehouse)",
        "➕ Add New Product",
        "📋 Procurement Re-Ordering",
        "🚀 Custom Campaigns Hub"
    ])

    # ========================================================
    # TAB 1: STOCK MOVEMENT (SHOP ⇄ WAREHOUSE)
    # ========================================================
    with tab_transfer:
        st.markdown("<h3 style='font-size:17px; font-weight:700; color:#0f172a; margin-bottom:6px;'>🔄 Move Inventory Between Locations</h3>", unsafe_allow_html=True)
        
        shop_stock = db.get_current_stock_on_hand()
        wh_stock = db.get_warehouse_stock_on_hand()

        # Top location summary KPI cards
        k1, k2, k3 = st.columns(3)
        with k1:
            st.html(f"""
            <div class="premium-card" style="border-left: 4px solid #10b981; padding:14px;">
                <p style="font-size:11px; text-transform:uppercase; font-weight:700; color:#64748b; margin:0;">Active Shop Floor Stock</p>
                <h3 style="font-size:22px; font-weight:800; color:#0f172a; margin:4px 0;">{sum(shop_stock.values()):,} Units</h3>
                <span style="font-size:11px; color:#059669; font-weight:600;">Available for Shopper Checkout</span>
            </div>
            """)
        with k2:
            st.html(f"""
            <div class="premium-card" style="border-left: 4px solid #3b82f6; padding:14px;">
                <p style="font-size:11px; text-transform:uppercase; font-weight:700; color:#64748b; margin:0;">Isolated Warehouse Reserve</p>
                <h3 style="font-size:22px; font-weight:800; color:#0f172a; margin:4px 0;">{sum(wh_stock.values()):,} Units</h3>
                <span style="font-size:11px; color:#2563eb; font-weight:600;">Hidden from Shop Floor Display</span>
            </div>
            """)
        with k3:
            transfers_df = db.get_stock_transfers(limit=100)
            st.html(f"""
            <div class="premium-card" style="border-left: 4px solid #8b5cf6; padding:14px;">
                <p style="font-size:11px; text-transform:uppercase; font-weight:700; color:#64748b; margin:0;">Logged Stock Transfers</p>
                <h3 style="font-size:22px; font-weight:800; color:#0f172a; margin:4px 0;">{len(transfers_df)} Transfers</h3>
                <span style="font-size:11px; color:#7c3aed; font-weight:600;">Full Audit Ledger Verified</span>
            </div>
            """)

        st.markdown("<br style='margin:4px 0;'>", unsafe_allow_html=True)
        col_ctrl, col_matrix = st.columns([1.8, 2.2])

        with col_ctrl:
            st.markdown("<div style='background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:18px;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='font-size:14px; font-weight:700; color:#1e293b; margin-top:0;'>📦 Transfer Execution Console</h4>", unsafe_allow_html=True)

            p_options = list(CATALOG.keys())
            selected_pid = st.selectbox(
                "Select Product Style to Move:",
                p_options,
                format_func=lambda x: f"{x} - {CATALOG[x]['name']} (Shop: {shop_stock.get(x, 0)} | WH: {wh_stock.get(x, 0)})",
                key="portal_transfer_pid"
            )

            direction_choice = st.radio(
                "Transfer Direction:",
                [
                    "🏪 Shop Floor ➔ 🏭 Warehouse Reserve",
                    "🏭 Warehouse Reserve ➔ 🏪 Shop Floor"
                ],
                key="portal_transfer_dir"
            )
            src_loc = "shop" if "Shop Floor ➔" in direction_choice else "warehouse"
            dst_loc = "warehouse" if src_loc == "shop" else "shop"

            size_col, qty_col = st.columns(2)
            with size_col:
                selected_size = st.selectbox(
                    "Size Variant:",
                    ["ALL", "S", "M", "L", "XL"],
                    key="portal_transfer_size"
                )
            with qty_col:
                transfer_qty = st.number_input(
                    "Total Quantity:",
                    min_value=1,
                    max_value=5000,
                    value=10,
                    step=1,
                    key="portal_transfer_qty"
                )

            transfer_notes = st.text_input(
                "Movement Reason / Notes:",
                value="Routine stock balancing",
                key="portal_transfer_notes"
            )

            if st.button("🚀 Execute Stock Movement", type="primary", use_container_width=True, key="portal_exec_transfer_btn"):
                success, msg = db.transfer_stock(
                    product_id=selected_pid,
                    size_variant=selected_size,
                    source=src_loc,
                    destination=dst_loc,
                    quantity=transfer_qty,
                    notes=transfer_notes,
                    performed_by="Portal Operations Manager"
                )
                if success:
                    st.success(msg)
                    # Synchronize live session inventory
                    st.session_state.live_inventory = db.get_current_stock_on_hand()
                    st.rerun()
                else:
                    st.error(msg)

            st.markdown("</div>", unsafe_allow_html=True)

        with col_matrix:
            st.markdown("<h4 style='font-size:14px; font-weight:700; color:#1e293b; margin-top:0;'>📊 Dual-Location Inventory Comparison</h4>", unsafe_allow_html=True)
            comparison_rows = []
            for pid, details in CATALOG.items():
                s_qty = shop_stock.get(pid, 0)
                w_qty = wh_stock.get(pid, 0)
                comparison_rows.append({
                    "Style Code": pid,
                    "Product Name": details["name"],
                    "Department": details.get("category", "Apparel"),
                    "Shop Floor (Units)": s_qty,
                    "Warehouse Reserve (Units)": w_qty,
                    "Total Stock": s_qty + w_qty
                })
            comp_df = pd.DataFrame(comparison_rows)
            st.dataframe(comp_df, hide_index=True, width="stretch", height=320)

        # Recent Transfer Log
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size:15px; font-weight:700; color:#1e293b;'>📋 Stock Movement Audit History</h4>", unsafe_allow_html=True)
        if not transfers_df.empty:
            display_transfers = transfers_df[["timestamp", "product_id", "product_name", "size_variant", "source_location", "dest_location", "quantity", "performed_by", "notes"]].rename(columns={
                "timestamp": "Timestamp",
                "product_id": "Code",
                "product_name": "Product Name",
                "size_variant": "Size",
                "source_location": "From",
                "dest_location": "To",
                "quantity": "Units",
                "performed_by": "Authorized By",
                "notes": "Movement Notes"
            })
            st.dataframe(display_transfers.head(15), hide_index=True, width="stretch")
        else:
            st.info("No stock movements recorded yet. Use the console above to transfer units.")

    # ========================================================
    # TAB 2: ADD NEW PRODUCT
    # ========================================================
    with tab_add_prod:
        st.markdown("<h3 style='font-size:17px; font-weight:700; color:#0f172a; margin-bottom:6px;'>➕ Register New Luxury Merchandise Style</h3>", unsafe_allow_html=True)
        st.caption("Register a new apparel style into the boutique catalog, configure wholesale cost and retail MSRP, and allocate initial floor & warehouse reserves.")

        # Compute next recommended Product ID
        existing_p_numbers = [int(p[1:]) for p in CATALOG.keys() if p.startswith("P") and p[1:].isdigit()]
        next_pid_num = max(existing_p_numbers) + 1 if existing_p_numbers else 21
        recommended_pid = f"P{next_pid_num:03d}"

        with st.form(key="add_new_product_form"):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                new_pid = st.text_input("Product ID Code:", value=recommended_pid, help="Unique identifier, e.g. P021")
                new_pname = st.text_input("Product Style Name:", placeholder="e.g. Velvet Evening Gown", help="Full commercial apparel name")
                new_cat = st.selectbox("Merchandise Category:", ["Dresses", "Outerwear", "Knitwear", "Bottoms", "Tops", "Eveningwear", "Accessories", "Footwear"])

            with col_p2:
                new_cost = st.number_input("Wholesale Unit Cost ($):", min_value=1.0, max_value=500.0, value=45.0, step=5.0)
                new_price = st.number_input("Retail MSRP Price ($):", min_value=1.0, max_value=1500.0, value=145.0, step=5.0)
                new_color = st.color_picker("Brand Palette Hex Color:", value="#4a154b")

            st.markdown("##### 📦 Initial Sizing Allocations")
            sc1, sc2, sc3, sc4 = st.columns(4)
            with sc1:
                shop_s = st.number_input("Shop Floor Size S:", min_value=0, max_value=2000, value=8)
                wh_s = st.number_input("Warehouse Size S:", min_value=0, max_value=2000, value=15)
            with sc2:
                shop_m = st.number_input("Shop Floor Size M:", min_value=0, max_value=2000, value=12)
                wh_m = st.number_input("Warehouse Size M:", min_value=0, max_value=2000, value=20)
            with sc3:
                shop_l = st.number_input("Shop Floor Size L:", min_value=0, max_value=2000, value=10)
                wh_l = st.number_input("Warehouse Size L:", min_value=0, max_value=2000, value=18)
            with sc4:
                shop_xl = st.number_input("Shop Floor Size XL:", min_value=0, max_value=2000, value=6)
                wh_xl = st.number_input("Warehouse Size XL:", min_value=0, max_value=2000, value=12)

            submit_prod = st.form_submit_button("✨ Register Product into Boutique Catalog", type="primary", use_container_width=True)

            if submit_prod:
                initial_shop_map = {"S": shop_s, "M": shop_m, "L": shop_l, "XL": shop_xl}
                initial_wh_map = {"S": wh_s, "M": wh_m, "L": wh_l, "XL": wh_xl}
                success, msg = db.add_new_product(
                    product_id=new_pid,
                    name=new_pname,
                    cost=new_cost,
                    price=new_price,
                    color=new_color,
                    category=new_cat,
                    initial_shop_stock=initial_shop_map,
                    initial_warehouse_stock=initial_wh_map
                )
                if success:
                    st.success(msg)
                    st.session_state.live_inventory = db.get_current_stock_on_hand()
                    st.session_state.store_controls = db.get_all_circuit_controls()
                    st.rerun()
                else:
                    st.error(msg)

    # ========================================================
    # TAB 3: PROCUREMENT RE-ORDERING
    # ========================================================
    with tab_order:
        st.markdown("<h3 style='font-size:17px; font-weight:700; color:#0f172a; margin-bottom:6px;'>📋 Order Products in Any Quantity</h3>", unsafe_allow_html=True)
        st.caption("Place supplier procurement replenishment orders for any style in the catalog. Route stock directly to warehouse backroom or shop floor racks.")

        col_ord1, col_ord2 = st.columns([1.8, 2.2])
        with col_ord1:
            st.markdown("<div style='background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:18px;'>", unsafe_allow_html=True)
            p_order_list = list(CATALOG.keys())
            order_pid = st.selectbox(
                "Select Product to Order:",
                p_order_list,
                format_func=lambda x: f"{x} - {CATALOG[x]['name']} (${CATALOG[x]['price']:.2f})",
                key="procure_order_pid"
            )

            p_selected = CATALOG[order_pid]
            order_qty = st.number_input(
                "Procurement Order Quantity:",
                min_value=1,
                max_value=1000,
                value=25,
                step=5,
                key="procure_order_qty"
            )

            dest_choice = st.radio(
                "Receiving Destination:",
                [
                    "🏭 Warehouse Storage (Recommended Reserve)",
                    "🏪 Direct to Shop Floor Racks"
                ],
                key="procure_dest_choice"
            )
            order_dest = "warehouse" if "Warehouse" in dest_choice else "shop"

            unit_cost_val = st.number_input(
                "Supplier Unit Cost ($):",
                min_value=1.0,
                max_value=500.0,
                value=float(p_selected["cost"]),
                step=1.0,
                key="procure_unit_cost"
            )
            total_spend_preview = round(unit_cost_val * order_qty, 2)
            st.markdown(f"<p style='font-size:13px; color:#059669; font-weight:700;'>Total Purchase Value: ${total_spend_preview:,.2f}</p>", unsafe_allow_html=True)

            order_notes = st.text_input("Purchase Order Reference / Notes:", value="Seasonal restock batch", key="procure_notes")

            if st.button("🚚 Place Procurement Restock Order", type="primary", use_container_width=True, key="procure_submit_btn"):
                success, msg = db.order_product(
                    product_id=order_pid,
                    quantity=order_qty,
                    destination=order_dest,
                    unit_cost=unit_cost_val,
                    notes=order_notes
                )
                if success:
                    st.success(msg)
                    st.session_state.live_inventory = db.get_current_stock_on_hand()
                    st.rerun()
                else:
                    st.error(msg)

            st.markdown("</div>", unsafe_allow_html=True)

        with col_ord2:
            st.markdown("<h4 style='font-size:14px; font-weight:700; color:#1e293b; margin-top:0;'>📦 Inbound Delivery Log Preview</h4>", unsafe_allow_html=True)
            purchases_df = db.fetch_logs("purchase_ledger", limit=15)
            if not purchases_df.empty:
                display_p = purchases_df[["timestamp", "product_name", "quantity", "total_cost"]].rename(columns={
                    "timestamp": "Arrival Time",
                    "product_name": "Product Style Name",
                    "quantity": "Quantity Received",
                    "total_cost": "Total Spend ($)"
                })
                st.dataframe(display_p, hide_index=True, width="stretch", height=320)
            else:
                st.caption("No inbound orders found.")

    # ========================================================
    # TAB 4: CUSTOM CAMPAIGNS HUB
    # ========================================================
    with tab_campaigns:
        st.markdown("<h3 style='font-size:17px; font-weight:700; color:#0f172a; margin-bottom:6px;'>🚀 Launch Custom Sales Campaigns</h3>", unsafe_allow_html=True)
        st.caption("Design promotional campaigns with Name, Description, and Discounts. Shivi Deep Agent will autonomously craft and broadcast messages to patrons.")

        col_camp_form, col_camp_list = st.columns([1.8, 2.2])

        with col_camp_form:
            st.markdown("<div style='background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:18px;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='font-size:14px; font-weight:700; color:#1e293b; margin-top:0;'>📣 Create Campaign</h4>", unsafe_allow_html=True)

            with st.form(key="create_campaign_form"):
                camp_name = st.text_input("Campaign Name:", placeholder="e.g. Spring Silk Soirée")
                camp_desc = st.text_area("Campaign Description & VIP Offering:", placeholder="Describe the commercial offer, styling advice, and promotional hook.")
                camp_disc = st.slider("Promotional Discount (%):", min_value=5, max_value=50, value=20, step=5, help="Discount capped at 50% by enterprise safety guardrails")
                camp_cat = st.selectbox("Target Department:", ["All Categories", "Dresses", "Outerwear", "Knitwear", "Bottoms", "Tops"])
                camp_tagline = st.text_input("Campaign Luxury Tagline:", placeholder="e.g. Fluid Silk Meets Architectural Drape")

                launch_btn = st.form_submit_button("🚀 Launch Campaign & Alert Shivi", type="primary", use_container_width=True)

                if launch_btn:
                    success, msg = db.create_campaign(
                        name=camp_name,
                        description=camp_desc,
                        discount_pct=float(camp_disc),
                        target_category=camp_cat,
                        banner_tagline=camp_tagline,
                        launched_by="Marketing Director"
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            st.markdown("</div>", unsafe_allow_html=True)

        with col_camp_list:
            st.markdown("<h4 style='font-size:14px; font-weight:700; color:#1e293b; margin-top:0;'>📋 Active & Historical Campaigns</h4>", unsafe_allow_html=True)
            all_campaigns = db.get_all_campaigns()
            if not all_campaigns.empty:
                for _, c in all_campaigns.iterrows():
                    c_status = c["status"]
                    status_badge = "<span style='background:#ecfdf5; color:#059669; padding:2px 8px; border-radius:9999px; font-size:11px; font-weight:700;'>ACTIVE</span>" if c_status == "Active" else "<span style='background:#f1f5f9; color:#64748b; padding:2px 8px; border-radius:9999px; font-size:11px; font-weight:700;'>PAUSED</span>"
                    st.html(f"""
                    <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid #f59e0b; border-radius:8px; padding:12px 14px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h5 style="margin:0; font-size:14px; font-weight:700; color:#0f172a;">{c['name']}</h5>
                            <div>{status_badge}</div>
                        </div>
                        <p style="font-size:12px; color:#64748b; margin:4px 0;"><b>Discount:</b> {c['discount_pct']:.0f}% Off | <b>Target:</b> {c.get('target_category', 'All')} | <b>Tagline:</b> <i>{c.get('banner_tagline', '')}</i></p>
                        <p style="font-size:12px; color:#334155; margin:4px 0 0 0;">{c['description']}</p>
                    </div>
                    """)
            else:
                st.caption("No campaigns created yet.")
