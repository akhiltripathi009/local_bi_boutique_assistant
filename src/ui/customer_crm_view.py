"""
src/ui/customer_crm_view.py
===========================
Renders the VIP Customer Directory and CRM Ledger:
1. 20 seeded VIP boutique customers with complete demographic and sizing profiles.
2. Full purchase history ledger for individual patrons.
3. Upcoming birthdays and styling preferences.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

def render_customer_crm_view(db):
    """Renders the VIP Customer Directory & CRM Ledger."""
    st.html("<h1 class='luxury-title text-3xl font-bold mb-1'>👥 VIP Customer Directory & CRM</h1>")
    st.caption("20 authenticated VIP boutique clients with detailed profiles, style aesthetics, size curves, and attributed transaction ledgers.")

    # Guardrail Notice
    st.html("""
    <div style="background:#f8fafc; border-left:4px solid #8b5cf6; padding:10px 16px; border-radius:8px; margin: 10px 0 16px 0;">
        <span style="font-size:13px; color:#334155; line-height:1.5;">
            <b>🔒 Strict Data Integrity & Customer Attribution:</b> All historical database transactions are preserved 100% intact.
            All newly simulated boutique purchases are strictly routed and attributed to these 20 registered VIP patrons.
        </span>
    </div>
    """)

    customers_df = db.get_all_customers()
    if customers_df.empty:
        st.warning("No customer records found.")
        return

    # Top KPI strip
    k1, k2, k3, k4 = st.columns(4)
    total_cust = len(customers_df)
    plat_count = len(customers_df[customers_df["loyalty_tier"] == "VIP Platinum"])
    total_spend = customers_df["total_spend"].sum()
    bday_upcoming = db.get_upcoming_birthday_customers(days_ahead=14)

    with k1:
        st.html(f"""
        <div class="premium-card" style="border-left: 4px solid #8b5cf6; padding:12px 14px;">
            <p style="font-size:11px; text-transform:uppercase; font-weight:700; color:#64748b; margin:0;">Total VIP Patrons</p>
            <h3 style="font-size:20px; font-weight:800; color:#0f172a; margin:4px 0;">{total_cust} Clients</h3>
            <span style="font-size:11px; color:#7c3aed; font-weight:600;">Full Profiles Active</span>
        </div>
        """)
    with k2:
        st.html(f"""
        <div class="premium-card" style="border-left: 4px solid #10b981; padding:12px 14px;">
            <p style="font-size:11px; text-transform:uppercase; font-weight:700; color:#64748b; margin:0;">Platinum Tier</p>
            <h3 style="font-size:20px; font-weight:800; color:#0f172a; margin:4px 0;">{plat_count} Elite</h3>
            <span style="font-size:11px; color:#059669; font-weight:600;">Top Value Segment</span>
        </div>
        """)
    with k3:
        st.html(f"""
        <div class="premium-card" style="border-left: 4px solid #3b82f6; padding:12px 14px;">
            <p style="font-size:11px; text-transform:uppercase; font-weight:700; color:#64748b; margin:0;">Cumulative Patron Spend</p>
            <h3 style="font-size:20px; font-weight:800; color:#0f172a; margin:4px 0;">${total_spend:,.2f}</h3>
            <span style="font-size:11px; color:#2563eb; font-weight:600;">Lifetime Value Tracked</span>
        </div>
        """)
    with k4:
        st.html(f"""
        <div class="premium-card" style="border-left: 4px solid #f59e0b; padding:12px 14px;">
            <p style="font-size:11px; text-transform:uppercase; font-weight:700; color:#64748b; margin:0;">Upcoming Birthdays (14D)</p>
            <h3 style="font-size:20px; font-weight:800; color:#0f172a; margin:4px 0;">{len(bday_upcoming)} Celebrating</h3>
            <span style="font-size:11px; color:#d97706; font-weight:600;">Birthday Perks Ready</span>
        </div>
        """)

    st.markdown("<br style='margin:4px 0;'>", unsafe_allow_html=True)

    # Tabs for Directory & Individual Inspection
    tab_dir, tab_detail = st.tabs(["📋 Complete Client Directory", "🔍 Client Profile & Transaction Ledger"])

    with tab_dir:
        # Search & Filter Toolbar
        f1, f2, f3 = st.columns([2, 1.5, 1.5])
        with f1:
            search_query = st.text_input("🔍 Search Client by Name or Email:", placeholder="Type to filter...")
        with f2:
            tier_options = ["All Tiers"] + sorted(list(customers_df["loyalty_tier"].unique()))
            selected_tier = st.selectbox("Filter Loyalty Tier:", tier_options)
        with f3:
            size_options = ["All Sizes", "S", "M", "L", "XL"]
            selected_size = st.selectbox("Filter Preferred Size:", size_options)

        filtered_df = customers_df.copy()
        if search_query:
            filtered_df = filtered_df[
                filtered_df["name"].str.contains(search_query, case=False, na=False) |
                filtered_df["email"].str.contains(search_query, case=False, na=False)
            ]
        if selected_tier != "All Tiers":
            filtered_df = filtered_df[filtered_df["loyalty_tier"] == selected_tier]
        if selected_size != "All Sizes":
            filtered_df = filtered_df[filtered_df["preferred_size"] == selected_size]

        display_cols = ["customer_code", "name", "phone", "email", "dob", "preferred_size", "gender", "style_preference", "loyalty_tier", "total_spend", "purchase_count"]
        col_rename = {
            "customer_code": "Client Code",
            "name": "Full Name",
            "phone": "Phone (WhatsApp)",
            "email": "Email Address",
            "dob": "Date of Birth",
            "preferred_size": "Size",
            "gender": "Gender",
            "style_preference": "Style Aesthetic",
            "loyalty_tier": "Loyalty Tier",
            "total_spend": "Total Spend ($)",
            "purchase_count": "Orders"
        }
        st.dataframe(
            filtered_df[display_cols].rename(columns=col_rename),
            hide_index=True,
            width="stretch",
            height=380
        )

    with tab_detail:
        # Client Detail Dropdown
        client_options = customers_df["id"].tolist()
        client_map = {row["id"]: f"{row['customer_code']} - {row['name']} ({row['loyalty_tier']})" for _, row in customers_df.iterrows()}
        selected_cid = st.selectbox(
            "Select Client to Inspect Purchase Ledger:",
            client_options,
            format_func=lambda x: client_map.get(x, f"Client {x}"),
            key="crm_detail_client_select"
        )

        cust_profile = db.get_customer_by_id(selected_cid)
        if cust_profile:
            p_col1, p_col2 = st.columns([1.5, 2.5])

            with p_col1:
                tier_color = "#8b5cf6" if cust_profile["loyalty_tier"] == "VIP Platinum" else ("#d97706" if cust_profile["loyalty_tier"] == "Gold" else "#64748b")
                st.html(f"""
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-top:4px solid {tier_color}; border-radius:12px; padding:16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0; font-size:16px; font-weight:800; color:#0f172a;">{cust_profile['name']}</h4>
                        <span style="background:#f5f3ff; color:{tier_color}; border:1px solid #ddd6fe; padding:2px 8px; border-radius:9999px; font-size:11px; font-weight:700;">{cust_profile['loyalty_tier']}</span>
                    </div>
                    <p style="font-size:11.5px; color:#64748b; margin:4px 0 12px 0;">{cust_profile['customer_code']} • Client Since {cust_profile['joined_date']}</p>
                    
                    <div style="font-size:12.5px; color:#334155; line-height:1.7;">
                        <div><b>📱 Phone:</b> {cust_profile['phone']}</div>
                        <div><b>📧 Email:</b> {cust_profile['email']}</div>
                        <div><b>🎂 Birth Date:</b> {cust_profile['dob']}</div>
                        <div><b>👗 Preferred Size:</b> <span style="font-weight:700; color:#0f172a;">{cust_profile['preferred_size']}</span> ({cust_profile['gender']})</div>
                        <div><b>✨ Style Preference:</b> {cust_profile['style_preference']}</div>
                    </div>
                    <hr style="margin:12px 0; border:0; border-top:1px solid #e2e8f0;">
                    <div style="display:flex; justify-content:space-between;">
                        <div>
                            <span style="font-size:10.5px; color:#64748b; text-transform:uppercase;">Total Spend</span>
                            <div style="font-size:16px; font-weight:800; color:#059669;">${cust_profile['total_spend']:,.2f}</div>
                        </div>
                        <div>
                            <span style="font-size:10.5px; color:#64748b; text-transform:uppercase;">Orders</span>
                            <div style="font-size:16px; font-weight:800; color:#0f172a;">{cust_profile['purchase_count']} Checkouts</div>
                        </div>
                    </div>
                </div>
                """)

            with p_col2:
                st.markdown("<h4 style='font-size:15px; font-weight:700; color:#1e293b; margin-top:0;'>🛍️ Purchase History Ledger</h4>", unsafe_allow_html=True)
                history_df = db.get_customer_purchase_history(selected_cid)
                if not history_df.empty:
                    display_history = history_df.rename(columns={
                        "timestamp": "Purchase Date",
                        "product_name": "Product Style",
                        "quantity": "Qty",
                        "unit_price": "Price ($)",
                        "total_revenue": "Total ($)",
                        "campaign_name": "Campaign",
                        "size_purchased": "Size",
                        "channel": "Channel"
                    })
                    st.dataframe(display_history, hide_index=True, width="stretch")
                else:
                    st.info(f"No recent purchases recorded yet for {cust_profile['name']}. Start the Live Store Operations stream or place an order to see transactions appear.")

            # Customer Edit Section
            st.markdown("<hr style='margin:18px 0; border:0; border-top:1px solid #e2e8f0;'>", unsafe_allow_html=True)
            with st.expander(f"✏️ Update Contact Details & Preferences for {cust_profile['name']}", expanded=True):
                st.caption("Modify customer phone number (for WhatsApp dispatches), email address, preferred size, or loyalty tier. Changes take effect immediately across all deep agent operations.")
                with st.form(f"edit_cust_form_{selected_cid}"):
                    e_c1, e_c2 = st.columns(2)
                    with e_c1:
                        new_name = st.text_input("Customer Name:", value=cust_profile["name"])
                        new_phone = st.text_input("WhatsApp Phone Number (with Country Code):", value=cust_profile["phone"], help="Used for WhatsApp broadcasts and wa.me click-to-chat links")
                        new_email = st.text_input("Email Address:", value=cust_profile["email"], help="Used for automated SMTP and mailto newsletters")
                    with e_c2:
                        size_idx = ["S", "M", "L", "XL"].index(cust_profile["preferred_size"]) if cust_profile["preferred_size"] in ["S", "M", "L", "XL"] else 1
                        new_size = st.selectbox("Preferred Size:", ["S", "M", "L", "XL"], index=size_idx)
                        
                        tier_list = ["Silver", "Gold", "VIP Platinum"]
                        tier_idx = tier_list.index(cust_profile["loyalty_tier"]) if cust_profile["loyalty_tier"] in tier_list else 1
                        new_tier = st.selectbox("Loyalty Tier:", tier_list, index=tier_idx)
                        
                        new_style = st.text_input("Style Preference / Aesthetic:", value=cust_profile["style_preference"])

                    st.markdown("##### 📲 Notification Preferences")
                    o_c1, o_c2 = st.columns(2)
                    with o_c1:
                        new_opt_wa = st.checkbox("Opt-in for WhatsApp Notifications", value=bool(cust_profile.get("opt_in_whatsapp", 1)))
                    with o_c2:
                        new_opt_em = st.checkbox("Opt-in for Email Newsletters & Campaigns", value=bool(cust_profile.get("opt_in_email", 1)))

                    submit_update = st.form_submit_button("💾 Save Updated Contact Details", type="primary", use_container_width=True)
                    if submit_update:
                        if not new_phone.strip():
                            st.error("Phone number cannot be empty.")
                        elif not new_email.strip() or "@" not in new_email:
                            st.error("Please provide a valid email address.")
                        else:
                            up_ok, up_msg = db.update_customer_contact(
                                customer_id=selected_cid,
                                phone=new_phone.strip(),
                                email=new_email.strip(),
                                name=new_name.strip(),
                                preferred_size=new_size,
                                style_preference=new_style.strip(),
                                loyalty_tier=new_tier,
                                opt_in_whatsapp=1 if new_opt_wa else 0,
                                opt_in_email=1 if new_opt_em else 0
                            )
                            if up_ok:
                                st.success("✅ " + up_msg)
                                st.rerun()
                            else:
                                st.error("❌ " + up_msg)
