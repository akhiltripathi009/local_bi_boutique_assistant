"""
src/ui/deep_agent_view.py
=========================
Renders the Enterprise Command Center for Shivi - AI Deep Boutique Agent:
1. Executive action dispatchers (Opening/Closing PDFs, Trending News, Campaign Blasts, Back-in-Stock).
2. Live Hierarchical Plan & Todo Progress Tracker.
3. Multi-Channel Communications Preview Hub (HTML Luxury Email + WhatsApp mobile bubbles).
4. Safe Python Analysis Sandbox.
5. Human-in-the-Loop (HITL) Steering Approval Queue.
6. Guardrails & PII Shield Inspector.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any

from src.deep_agent.guardrails import PIIGuardrail, DiscountSafetyGuardrail
from src.deep_agent.delivery import WhatsAppDeliveryService, EmailDeliveryService

def render_shivi_deep_agent_view(db, agent):
    """Renders the comprehensive Deep Agent Command Center for Shivi."""
    # Header Banner
    st.html("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <div>
            <h1 class='luxury-title text-3xl font-bold mb-0' style='margin:0;'>🧠 Shivi — Enterprise AI Deep Boutique Agent</h1>
            <p style='font-size:13px; color:#64748b; margin:2px 0 0 0;'>Autonomous retail operations, boardroom PDF audits, fashion trend curation via Email & WhatsApp, campaign broadcasts, and execution sandboxes.</p>
        </div>
        <div style="text-align:right;">
            <span style="background:#ecfdf5; color:#059669; border:1px solid #a7f3d0; padding:4px 10px; border-radius:9999px; font-size:11px; font-weight:700;">🟢 SHIVI DEEP AGENT ACTIVE</span>
        </div>
    </div>
    """)

    # Top Status Strip
    st_c1, st_c2, st_c3, st_c4 = st.columns(4)
    memories = agent.memory.recall_recent_memories(limit=50)
    pending_approvals = agent.steering.get_pending_queue()

    with st_c1:
        st.html("""
        <div class="premium-card" style="border-left: 4px solid #10b981; padding:12px 14px;">
            <p style="font-size:11px; text-transform:uppercase; font-weight:700; color:#64748b; margin:0;">Enterprise Guardrails</p>
            <h4 style="font-size:16px; font-weight:800; color:#059669; margin:4px 0 2px 0;">🛡️ Active & Enforced</h4>
            <span style="font-size:10.5px; color:#64748b;">PII Redaction & &le;50% Discount Cap</span>
        </div>
        """)
    with st_c2:
        st.html(f"""
        <div class="premium-card" style="border-left: 4px solid #3b82f6; padding:12px 14px;">
            <p style="font-size:11px; text-transform:uppercase; font-weight:700; color:#64748b; margin:0;">Episodic Memory & Skills</p>
            <h4 style="font-size:16px; font-weight:800; color:#2563eb; margin:4px 0 2px 0;">🧠 {len(memories)} Memories</h4>
            <span style="font-size:10.5px; color:#64748b;">4 Pre-Compiled Domain Skills Loaded</span>
        </div>
        """)
    with st_c3:
        st.html("""
        <div class="premium-card" style="border-left: 4px solid #8b5cf6; padding:12px 14px;">
            <p style="font-size:11px; text-transform:uppercase; font-weight:700; color:#64748b; margin:0;">Execution Environment</p>
            <h4 style="font-size:16px; font-weight:800; color:#7c3aed; margin:4px 0 2px 0;">⚡ Python Sandbox</h4>
            <span style="font-size:10.5px; color:#64748b;">5 Core Tools & Sandbox Ready</span>
        </div>
        """)
    with st_c4:
        st.html(f"""
        <div class="premium-card" style="border-left: 4px solid #f59e0b; padding:12px 14px;">
            <p style="font-size:11px; text-transform:uppercase; font-weight:700; color:#64748b; margin:0;">HITL Steering Queue</p>
            <h4 style="font-size:16px; font-weight:800; color:#d97706; margin:4px 0 2px 0;">🚦 {len(pending_approvals)} Approvals</h4>
            <span style="font-size:10.5px; color:#64748b;">Human Oversight Gatekeeper</span>
        </div>
        """)

    st.markdown("<br style='margin:4px 0;'>", unsafe_allow_html=True)

    # ========================================================
    # 1-CLICK AUTONOMOUS ACTION TRIGGERS
    # ========================================================
    st.markdown("<h3 style='font-size:16px; font-weight:700; color:#0f172a; margin-bottom:8px;'>⚡ Shivi 1-Click Operational Dispatchers</h3>", unsafe_allow_html=True)

    b_col1, b_col2, b_col3, b_col4, b_col5, b_col6 = st.columns(6)

    with b_col1:
        if st.button("🌅 Morning Opening", use_container_width=True, help="Audits stock, checks campaigns & birthdays, generates Opening PDF"):
            with st.spinner("Shivi executing morning opening procedure..."):
                res = agent.run_opening_routine()
                st.session_state.shivi_last_result = res
                st.session_state.shivi_last_pdf = res.get("pdf_bytes")
                st.session_state.shivi_last_pdf_name = res.get("report_name")
                st.session_state.shivi_action_tag = "opening"
                st.rerun()

    with b_col2:
        if st.button("🌆 Evening Closing", use_container_width=True, help="Reconciles daily sales, audits transfers, generates Closing Audit PDF"):
            with st.spinner("Shivi compiling evening financial closing audit..."):
                res = agent.run_closing_routine()
                st.session_state.shivi_last_result = res
                st.session_state.shivi_last_pdf = res.get("pdf_bytes")
                st.session_state.shivi_last_pdf_name = res.get("report_name")
                st.session_state.shivi_action_tag = "closing"
                st.rerun()

    with b_col3:
        if st.button("📰 Fashion News", use_container_width=True, help="Curates trending fashion news and dispatches to patrons via Email & WhatsApp"):
            with st.spinner("Shivi researching Mishika trends and preparing newsletters..."):
                res = agent.dispatch_trending_fashion_news(dry_run=False)
                st.session_state.shivi_last_result = res
                st.session_state.shivi_action_tag = "fashion_news"
                st.rerun()

    with b_col4:
        if st.button("📢 Launch Campaign", use_container_width=True, help="Crafts promotional copy and broadcasts campaign alerts to patrons"):
            with st.spinner("Shivi formulating campaign launch broadcast..."):
                res = agent.broadcast_campaign_launch(dry_run=False)
                st.session_state.shivi_last_result = res
                st.session_state.shivi_action_tag = "campaign"
                st.rerun()

    with b_col5:
        if st.button("🔔 Restock Alert", use_container_width=True, help="Scans restocked products and alerts interested clients with 24-hr reserve hold"):
            with st.spinner("Shivi scanning inventory for restocked styles..."):
                res = agent.check_and_notify_back_in_stock(dry_run=False)
                st.session_state.shivi_last_result = res
                st.session_state.shivi_action_tag = "back_in_stock"
                st.rerun()

    with b_col6:
        if st.button("🎂 Birthday Perks", use_container_width=True, help="Finds upcoming birthdays and dispatches 25% birthday vouchers"):
            with st.spinner("Shivi identifying celebrating clients and drafting vouchers..."):
                res = agent.dispatch_birthday_perks(dry_run=False)
                st.session_state.shivi_last_result = res
                st.session_state.shivi_action_tag = "birthday"
                st.rerun()

    # ========================================================
    # LIVE HIERARCHICAL PLAN & TODO LIST TRACKER
    # ========================================================
    if "shivi_last_result" in st.session_state and "plan" in st.session_state.shivi_last_result:
        plan_data = st.session_state.shivi_last_result["plan"]
        st.markdown(f"<h4 style='font-size:15px; font-weight:700; color:#0f172a; margin-top:16px;'>📋 Active Execution Plan: {plan_data['goal']}</h4>", unsafe_allow_html=True)
        
        plan_cols = st.columns(len(plan_data["items"]))
        for i, step in enumerate(plan_data["items"]):
            with plan_cols[i]:
                status_color = "#10b981" if step["status"] == "Completed" else ("#f59e0b" if step["status"] == "In Progress" else "#94a3b8")
                st.html(f"""
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-top:3px solid {status_color}; border-radius:8px; padding:10px; height:100%;">
                    <div style="font-size:10px; font-weight:700; color:#64748b; text-transform:uppercase;">Step {step['step_id']} • {step['subagent']}</div>
                    <div style="font-size:12px; font-weight:700; color:#0f172a; margin:3px 0;">{step['title']}</div>
                    <div style="font-size:10.5px; color:#475569; margin-bottom:4px;">{step['description']}</div>
                    <span style="font-size:9.5px; font-weight:700; background:#f1f5f9; color:{status_color}; padding:1px 6px; border-radius:4px;">{step['status'].upper()}</span>
                </div>
                """)

    # PDF Download Banner (If PDF was generated by Opening/Closing routine)
    if "shivi_last_pdf" in st.session_state and st.session_state.shivi_last_pdf:
        st.markdown("<br style='margin:4px 0;'>", unsafe_allow_html=True)
        pdf_col1, pdf_col2 = st.columns([3, 1])
        with pdf_col1:
            st.success(f"📄 **Boardroom PDF Ready:** `{st.session_state.get('shivi_last_pdf_name', 'Audit_Report.pdf')}` compiled autonomously by Shivi.")
        with pdf_col2:
            st.download_button(
                label="📥 Download Official PDF",
                data=st.session_state.shivi_last_pdf,
                file_name=st.session_state.get('shivi_last_pdf_name', 'Audit_Report.pdf'),
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

    st.markdown("<hr style='margin:16px 0; border:0; border-top:1px solid #e2e8f0;'>", unsafe_allow_html=True)

    # ========================================================
    # DEEP AGENT WORKSPACE TABS
    # ========================================================
    shivi_tab1, shivi_tab2, shivi_tab3, shivi_tab4, shivi_tab5 = st.tabs([
        "📱 Client Previews (Email & WhatsApp)",
        "⚙️ Automated Email Setup & Testing",
        "🧪 Safe Python Analysis Sandbox",
        "🚦 HITL Steering Approval Queue",
        "🛡️ Guardrails & PII Shield Inspector"
    ])

    # ----------------------------------------------------
    # TAB 1: MULTI-CHANNEL CLIENT PREVIEWS
    # ----------------------------------------------------
    with shivi_tab1:
        st.markdown("<h4 style='font-size:15px; font-weight:700; color:#0f172a; margin-top:0;'>📱 Outbound Customer Communications Hub</h4>", unsafe_allow_html=True)
        st.caption("Live rendering of personalized luxury HTML Email newsletters and formatted WhatsApp chat bubbles drafted by Shivi.")

        preview_messages = []
        if "shivi_last_result" in st.session_state and "messages" in st.session_state.shivi_last_result:
            preview_messages = st.session_state.shivi_last_result["messages"]
        else:
            # Generate sample preview messages
            preview_messages = agent.trend_subagent.curate_and_draft_fashion_news()

        # Fashion News Topic Filter Choices
        TOPIC_CHOICES = {
            "🌟 All Runway Trends (Auto-Rotate)": None,
            "👗 Paris & Milan Haute Couture": "paris haute couture fashion week runway",
            "💎 Quiet Luxury & Bespoke Tailoring": "quiet luxury bespoke tailoring fashion",
            "🧣 Cashmere, Silk & Fine Knitwear": "designer silk cashmere knitwear fashion",
            "✨ High Fashion Evening Wear & Galas": "high fashion evening wear red carpet",
            "🏖️ Resort Wear & Bohemian Elegance": "luxury resort wear bohemian fashion"
        }

        # Fashion News Source Status Banner & Live Explorer
        is_live = preview_messages[0].get("is_live_internet", False) if preview_messages else False
        news_src_label = preview_messages[0].get("news_source", "Curated News") if preview_messages else "Curated News"

        if is_live:
            st.html(f"""
            <div style="background:#ecfdf5; border:1px solid #a7f3d0; border-left:4px solid #10b981; padding:10px 14px; border-radius:8px; margin-bottom:12px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:18px;">🌐</span>
                    <div>
                        <span style="font-size:12.5px; font-weight:800; color:#065f46;">{news_src_label}</span>
                        <span style="font-size:11px; color:#047857; margin-left:6px;">• Connected to Live RSS Runway Wire</span>
                        <div style="font-size:11px; color:#475569; margin-top:2px;">Real-time runway headlines are actively synthesized into customer communications. If network fails, default news displays automatically.</div>
                    </div>
                </div>
            </div>
            """)
        else:
            st.html(f"""
            <div style="background:#fffbeb; border:1px solid #fde68a; border-left:4px solid #f59e0b; padding:10px 14px; border-radius:8px; margin-bottom:12px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:18px;">📦</span>
                    <div>
                        <span style="font-size:12.5px; font-weight:800; color:#92400e;">Default Curated News Active (Offline Safe Mode)</span>
                        <span style="font-size:11px; color:#b45309; margin-left:6px;">• Fault-Tolerant Atelier Fallback</span>
                        <div style="font-size:11px; color:#475569; margin-top:2px;">Internet feeds unavailable or offline. Shivi seamlessly displays high-fidelity default luxury themes with zero disruption.</div>
                    </div>
                </div>
            </div>
            """)

        # Topic Selector + Interactive Refresh Button
        n_col1, n_col2 = st.columns([3.2, 1.2])
        with n_col1:
            chosen_topic = st.selectbox(
                "Curate Fashion News by Runway Theme:",
                list(TOPIC_CHOICES.keys()),
                key="shivi_fashion_news_topic"
            )
        with n_col2:
            st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
            refresh_news_clicked = st.button("🔄 Refresh Live News", type="primary", use_container_width=True, help="Re-query internet fashion trends or switch to fresh stories")
            st.markdown("</div>", unsafe_allow_html=True)

        if refresh_news_clicked:
            with st.spinner("Fetching latest fashion trends and formulating newsletters..."):
                query_filter = TOPIC_CHOICES.get(chosen_topic)
                refreshed = agent.trend_subagent.curate_and_draft_fashion_news(query=query_filter, randomize=True)
                if "shivi_last_result" not in st.session_state or not isinstance(st.session_state.shivi_last_result, dict):
                    st.session_state.shivi_last_result = {}
                st.session_state.shivi_last_result["messages"] = refreshed
                top_story = refreshed[0].get("article_title", "Latest Trends") if refreshed else "Fresh Trends"
                st.session_state["shivi_news_refreshed_toast"] = f"✅ Refreshed at {datetime.now().strftime('%H:%M:%S')}: Loaded fresh story '{top_story[:45]}...'"
                st.rerun()

        if "shivi_news_refreshed_toast" in st.session_state:
            st.success(st.session_state.pop("shivi_news_refreshed_toast"))

        with st.expander("📰 Latest Fashion Headlines & Sources Explorer", expanded=False):
            st.caption(f"Active Source: **{news_src_label}** • {len(preview_messages)} distinct stories curated for VIP client communications")
            for m in preview_messages:
                t = m.get("article_title") or m.get("email_subject", "Fashion News")
                src = m.get("article_source", "Fashion Wire")
                lnk = m.get("article_link", "#")
                st.markdown(f"- **[{t}]({lnk})** — *{src}* <span style='font-size:11px; color:#64748b;'>(Assigned to {m['customer_name']})</span>", unsafe_allow_html=True)

        if preview_messages:
            cust_names = [m["customer_name"] for m in preview_messages]
            sel_recipient_idx = st.selectbox(
                "Select Recipient to Preview Formatted Dispatch:",
                range(len(cust_names)),
                format_func=lambda i: f"{cust_names[i]} ({preview_messages[i].get('masked_email', '')} | {preview_messages[i].get('masked_phone', '')})",
                key="shivi_preview_recipient_select"
            )
            msg = preview_messages[sel_recipient_idx]

            pv_email, pv_wa = st.columns(2)

            with pv_email:
                st.markdown("##### 📧 Luxury HTML Email Newsletter")
                st.caption(f"Subject: **{msg.get('email_subject', 'Boutique Alert')}**")

                email_conf = EmailDeliveryService.load_email_config()
                is_email_active = email_conf.get("is_configured", False)

                if is_email_active:
                    st.html(f"""
                    <div style="display:flex; align-items:center; gap:6px; background:#ecfdf5; border:1px solid #a7f3d0; padding:6px 12px; border-radius:6px; margin-bottom:8px;">
                        <span style="font-size:13px;">🟢</span>
                        <div>
                            <span style="font-size:11.5px; font-weight:700; color:#065f46;">Gmail SMTP Active & Authenticated</span>
                            <div style="font-size:10.5px; color:#047857;">Sending directly from <b>{email_conf.get('smtp_user')}</b> (TLS:587)</div>
                        </div>
                    </div>
                    """)
                else:
                    st.html("""
                    <div style="display:flex; align-items:center; gap:6px; background:#fffbeb; border:1px solid #fde68a; padding:6px 12px; border-radius:6px; margin-bottom:8px;">
                        <span style="font-size:13px;">⚠️</span>
                        <div>
                            <span style="font-size:11.5px; font-weight:700; color:#92400e;">Gmail App Password Pending</span>
                            <div style="font-size:10.5px; color:#78350f;">Activate your Gmail App Password in Tab 2 to send directly to inboxes.</div>
                        </div>
                    </div>
                    """)

                # Render clean responsive HTML container
                st.html(f"""
                <div style="border:1px solid #cbd5e1; border-radius:12px; overflow:hidden; box-shadow:0 2px 4px rgba(0,0,0,0.04);">
                    <div style="background:#f1f5f9; padding:8px 12px; border-bottom:1px solid #cbd5e1; font-size:11px; color:#64748b;">
                        <b>To:</b> {msg.get('customer_name')} &lt;{msg.get('customer_email')}&gt;
                    </div>
                    <div style="padding:8px;">
                        {msg.get('email_html', '')}
                    </div>
                </div>
                """)

                # Real Dispatch Action Buttons
                email_to = msg.get('customer_email', '')
                email_sub = msg.get('email_subject', 'Boutique Alert')
                email_html = msg.get('email_html', '')
                plain_body = f"Dear {msg.get('customer_name')},\n\nCheck out our latest boutique updates and new arrivals.\n\nWarm regards,\nMishika Fashion Boutique Concierge"
                mailto_link = EmailDeliveryService.generate_mailto_link(email_to, email_sub, plain_body)

                st.markdown("<div style='margin-top:10px;'>", unsafe_allow_html=True)
                
                if is_email_active:
                    # 1. Direct Send Real Email Button via SMTP
                    if st.button(f"🚀 Send Real Email via Gmail SMTP to {msg.get('customer_name')}", type="primary", use_container_width=True, key=f"send_smtp_single_{sel_recipient_idx}"):
                        with st.spinner(f"Sending real email via Gmail SMTP to {email_to}..."):
                            success, err_msg = EmailDeliveryService.send_smtp_email(
                                to_email=email_to,
                                subject=email_sub,
                                html_body=email_html,
                                plain_body=plain_body
                            )
                            if success:
                                db.save_agent_communication({
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "customer_id": msg.get("customer_id"),
                                    "customer_name": msg.get("customer_name"),
                                    "channel": "Email",
                                    "message_type": "Marketing",
                                    "subject": email_sub,
                                    "content": email_html,
                                    "status": f"Sent (Gmail SMTP to {email_to})"
                                })
                                st.success(f"✅ Real email successfully delivered to {email_to} via Gmail SMTP!")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to send email: {err_msg}")

                    # 2. Batch Broadcast Button
                    b_c1, b_c2 = st.columns([1.5, 1.2])
                    with b_c1:
                        if st.button("📢 Send to ALL VIP Clients via Gmail SMTP", use_container_width=True, key="send_all_smtp_btn"):
                            with st.spinner(f"Dispatched batch email to {len(preview_messages)} clients via Gmail SMTP..."):
                                count_ok = 0
                                for m_item in preview_messages:
                                    t_email = m_item.get("customer_email")
                                    if t_email:
                                        s_ok, _ = EmailDeliveryService.send_smtp_email(
                                            to_email=t_email,
                                            subject=m_item.get("email_subject", email_sub),
                                            html_body=m_item.get("email_html", email_html)
                                        )
                                        if s_ok:
                                            count_ok += 1
                                            db.save_agent_communication({
                                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                "customer_id": m_item.get("customer_id"),
                                                "customer_name": m_item.get("customer_name"),
                                                "channel": "Email",
                                                "message_type": "Marketing",
                                                "subject": m_item.get("email_subject", email_sub),
                                                "content": m_item.get("email_html", email_html),
                                                "status": f"Sent (Gmail SMTP to {t_email})"
                                            })
                                st.success(f"🎉 Successfully delivered {count_ok} real emails to VIP patrons via Gmail SMTP!")
                                st.rerun()
                    with b_c2:
                        st.link_button(f"✉️ Open Draft in Email Client", mailto_link, use_container_width=True)
                else:
                    st.link_button(f"✉️ Open Draft in Email Client ({email_to})", mailto_link, use_container_width=True)
                    st.info("💡 Gmail SMTP is not yet active. Please activate your Google App Password in Tab 2.")

                st.markdown("</div>", unsafe_allow_html=True)

            with pv_wa:
                st.markdown("##### 💬 WhatsApp Mobile Chat Bubble")
                st.caption(f"Recipient: **{msg.get('customer_phone', '')}**")
                # Render WhatsApp chat container with authentic mobile styling
                wa_body = msg.get('whatsapp_text', '').replace('\n', '<br/>')
                st.html(f"""
                <div style="max-width:380px; margin:0 auto; background:#e5ddd5; border-radius:16px; border:2px solid #cbd5e1; overflow:hidden; box-shadow:0 4px 10px rgba(0,0,0,0.08);">
                    <div style="background:#075e54; color:#ffffff; padding:10px 14px; display:flex; align-items:center; gap:8px;">
                        <span style="font-size:18px;">👗</span>
                        <div>
                            <div style="font-size:13px; font-weight:700;">Mishika Fashion Boutique</div>
                            <div style="font-size:10px; opacity:0.85;">Official Concierge • Online</div>
                        </div>
                    </div>
                    <div style="padding:14px; background: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png');">
                        <div style="background:#dcf8c6; padding:10px 12px; border-radius:8px; font-size:12.5px; color:#111b21; line-height:1.5; box-shadow:0 1px 2px rgba(0,0,0,0.1);">
                            {wa_body}
                            <div style="text-align:right; font-size:9.5px; color:#667781; margin-top:4px;">
                                {datetime.now().strftime('%I:%M %p')} ✓✓
                            </div>
                        </div>
                    </div>
                </div>
                """)
                # Real Dispatch Action Button
                wa_phone = msg.get('customer_phone', '')
                raw_wa_text = msg.get('whatsapp_text', '')
                wa_me_link = WhatsAppDeliveryService.generate_wa_me_link(wa_phone, raw_wa_text)
                st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
                st.link_button(f"📲 Send Real WhatsApp via wa.me ({wa_phone})", wa_me_link, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Live Test to User's Own Device Expander
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🚀 Send Live Test Message to Your Own Phone or Email", expanded=False):
                st.caption("Test real-time delivery right now to your personal phone or email using Shivi's drafted message.")
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    st.markdown("**Test via WhatsApp:**")
                    my_phone = st.text_input("Your WhatsApp Number (e.g. +91 9876543210 or +1 555...):", value="", key="test_my_phone_input", placeholder="+919876543210")
                    if my_phone:
                        my_wa_link = WhatsAppDeliveryService.generate_wa_me_link(my_phone, raw_wa_text)
                        st.link_button("📲 Launch WhatsApp with Drafted Text", my_wa_link, use_container_width=True)
                with t_col2:
                    st.markdown("**Test via Email:**")
                    default_test_email = email_conf.get("admin_email") or email_conf.get("smtp_user") or ""
                    my_email = st.text_input("Your Email Address:", value=default_test_email, key="test_my_email_input", placeholder="you@company.com")
                    if my_email:
                        if is_email_active:
                            if st.button(f"🚀 Send Real Test Email to {my_email} Now", type="primary", key="send_test_my_email_btn"):
                                with st.spinner(f"Sending real email via Gmail SMTP to {my_email}..."):
                                    s_ok, s_msg = EmailDeliveryService.send_smtp_email(
                                        to_email=my_email,
                                        subject=email_sub,
                                        html_body=email_html,
                                        plain_body=plain_body
                                    )
                                    if s_ok:
                                        st.success(f"✅ Real email delivered to {my_email} via Gmail SMTP!")
                                    else:
                                        st.error(f"❌ Error sending test email: {s_msg}")
                        my_mail_link = EmailDeliveryService.generate_mailto_link(my_email, email_sub, plain_body)
                        st.link_button("✉️ Open Pre-Filled Draft in Email App", my_mail_link, use_container_width=True)

            with st.expander("🔌 Automated Background Sending Guide (SMTP & Twilio / Meta Cloud API)", expanded=False):
                st.markdown("""
                **How automated background delivery operates in Shivi:**
                * **1-Click Direct Sending (No Setup Required)**: The `wa.me` WhatsApp links and `mailto:` links above work immediately in your browser on desktop and mobile without needing any paid APIs or setup.
                * **Autonomous Email (SMTP)**: Provide your SMTP server credentials in your `.env` file (`SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_USER`, `SMTP_PASS`). Shivi can autonomously send full HTML emails directly to customer inboxes via standard TLS/SSL.
                * **Autonomous WhatsApp (Twilio / Meta API)**: Provide `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_WHATSAPP_FROM` in your `.env`. Shivi can programmatically deliver background WhatsApp broadcasts directly to patrons.
                * **Audit Logging**: Every outgoing dispatch (whether manual, simulated, or automated) is permanently logged in the SQLite `agent_communications` ledger below.
                """)

        # Outgoing Communication Dispatch Ledger
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h5 style='font-size:14px; font-weight:700; color:#1e293b;'>📋 Dispatched Customer Communications History</h5>", unsafe_allow_html=True)
        comms_df = db.get_agent_communications(limit=25)
        if not comms_df.empty:
            display_c = comms_df[["timestamp", "customer_name", "channel", "message_type", "subject", "status"]].rename(columns={
                "timestamp": "Timestamp",
                "customer_name": "Recipient Patron",
                "channel": "Channel",
                "message_type": "Category",
                "subject": "Subject / Direct Message",
                "status": "Delivery Status"
            })
            st.dataframe(display_c, hide_index=True, width="stretch")
        else:
            st.caption("No communications recorded yet.")

    # ----------------------------------------------------
    # TAB 2: AUTOMATED EMAIL SETUP & TESTING
    # ----------------------------------------------------
    with shivi_tab2:
        st.markdown("<h4 style='font-size:15px; font-weight:700; color:#0f172a; margin-top:0;'>⚙️ Autonomous Email Gateway Settings</h4>", unsafe_allow_html=True)
        st.caption("Configure Gmail App Password or SMTP credentials for fully automated background email dispatching.")

        curr_conf = EmailDeliveryService.load_email_config()
        is_active = curr_conf.get("is_configured", False)

        # Status Callout
        if is_active:
            st.html(f"""
            <div style="background:#ecfdf5; border-left:4px solid #059669; padding:10px 16px; border-radius:8px; margin-bottom:16px;">
                <span style="font-size:13px; color:#065f46; font-weight:600;">
                    🟢 Automated Email Gateway Active: Authenticated as <b>{curr_conf.get('smtp_user')}</b> via {curr_conf.get('smtp_host')}:{curr_conf.get('smtp_port')}.
                </span>
            </div>
            """)
        else:
            st.html("""
            <div style="background:#fffbeb; border-left:4px solid #f59e0b; padding:10px 16px; border-radius:8px; margin-bottom:16px;">
                <span style="font-size:13px; color:#92400e; font-weight:600;">
                    ⚠️ Automated Email Pending: Please enter your Gmail address and 16-character App Password below to enable autonomous background email sending.
                </span>
            </div>
            """)

        # Gmail Quick Step-by-Step Guide Expander
        with st.expander("📖 Step-by-Step Guide: How to Generate a Gmail App Password in 60 Seconds", expanded=not is_active):
            st.markdown("""
            Google requires a dedicated **16-character App Password** to allow third-party apps like Shivi to send emails securely via SMTP:
            
            1. Go to your **[Google Account Security & 2-Step Verification](https://myaccount.google.com/signinoptions/two-step-verification)** and make sure 2-Step Verification is **ON**.
            2. Go directly to **[Google App Passwords](https://myaccount.google.com/apppasswords)**.
            3. Under **App name**, type **`Shivi Boutique Agent`** and click **Create**.
            4. Google will display a yellow box with a **16-character password** (e.g., `abcd efgh ijkl mnop`).
            5. Copy that 16-character code and paste it into the **Gmail App Password** field below!
            """)

        # Settings Form
        with st.form("shivi_email_config_form"):
            cf_col1, cf_col2 = st.columns(2)
            with cf_col1:
                f_user = st.text_input("Gmail Address / Sender Email:", value=curr_conf.get("smtp_user", ""), placeholder="your_boutique@gmail.com")
                f_pass = st.text_input("16-Character Gmail App Password:", value=curr_conf.get("smtp_pass", ""), type="password", placeholder="xxxx xxxx xxxx xxxx")
            with cf_col2:
                f_admin = st.text_input("Admin Email (Receives Morning & Evening PDF Audits):", value=curr_conf.get("admin_email", ""), placeholder="admin@yourboutique.com")
                f_from_name = st.text_input("Sender Display Name:", value=curr_conf.get("from_name", "Mishika Fashion Boutique Concierge"))

            with st.expander("🛠️ Advanced SMTP Server Settings (Pre-configured for Gmail)", expanded=False):
                adv_c1, adv_c2 = st.columns(2)
                with adv_c1:
                    f_host = st.text_input("SMTP Host:", value=curr_conf.get("smtp_host", "smtp.gmail.com"))
                with adv_c2:
                    f_port = st.number_input("SMTP Port:", value=int(curr_conf.get("smtp_port", 587)), min_value=1, max_value=65535)

            st.markdown("##### 🤖 Autonomous Dispatch Policies")
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                f_auto_admin = st.checkbox("Automatically email Morning & Evening PDF Audits to Admin", value=curr_conf.get("auto_send_admin_audits", True))
            with p_col2:
                f_auto_cust = st.checkbox("Automatically email Fashion News & Campaigns to Customers", value=curr_conf.get("auto_send_customer_emails", True))

            save_submitted = st.form_submit_button("💾 Save & Activate Email Settings", type="primary", use_container_width=True)
            if save_submitted:
                new_c = {
                    "smtp_host": f_host.strip(),
                    "smtp_port": int(f_port),
                    "smtp_user": f_user.strip(),
                    "smtp_pass": f_pass.strip(),
                    "smtp_from": f_user.strip(),
                    "from_name": f_from_name.strip(),
                    "admin_email": f_admin.strip(),
                    "auto_send_admin_audits": f_auto_admin,
                    "auto_send_customer_emails": f_auto_cust
                }
                ok, msg = EmailDeliveryService.save_email_config(new_c)
                if ok:
                    st.success("✅ " + msg)
                    st.rerun()
                else:
                    st.error("❌ " + msg)

        # Connection Test Tool
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 🧪 Test SMTP Connection & Send Verification Email")
        st.caption("Send a live test verification email right now to confirm your credentials are working properly.")
        
        t_col_in, t_col_btn = st.columns([3, 1])
        with t_col_in:
            test_target = st.text_input("Send Test Verification Email To:", value=curr_conf.get("admin_email") or curr_conf.get("smtp_user") or "", placeholder="test@yourdomain.com", key="smtp_test_target_input")
        with t_col_btn:
            st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
            test_clicked = st.button("🧪 Send Test Email", key="run_smtp_test_btn", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        if test_clicked:
            if not curr_conf.get("smtp_user") or not curr_conf.get("smtp_pass"):
                st.warning("⚠️ Please save your Gmail Address and 16-character App Password before testing.")
            elif not test_target:
                st.warning("⚠️ Please enter a recipient email address for the test.")
            else:
                with st.spinner("Connecting to SMTP server and transmitting verification email..."):
                    test_ok, test_feedback = EmailDeliveryService.test_smtp_connection(curr_conf, to_email=test_target)
                    if test_ok:
                        st.success(test_feedback)
                    else:
                        st.error(test_feedback)

    # ----------------------------------------------------
    # TAB 3: SAFE PYTHON ANALYSIS SANDBOX
    # ----------------------------------------------------
    with shivi_tab3:
        st.markdown("<h4 style='font-size:15px; font-weight:700; color:#0f172a; margin-top:0;'>🧪 Shivi Data Science Execution Sandbox</h4>", unsafe_allow_html=True)
        st.caption("Safely execute Python analysis scripts with direct access to live store stock, sell-through velocity, and financial margins.")

        # Preset Sandbox Scripts
        presets = {
            "📈 Top 5 Margin Styles": (
                "# Calculate top 5 highest profit styles from sales ledger\n"
                "sales = db.fetch_logs('sales_ledger', limit=100)\n"
                "if not sales.empty:\n"
                "    top = sales.groupby('product_name')['gross_profit'].sum().sort_values(ascending=False).head(5)\n"
                "    print('Top 5 Profit Generating Styles:')\n"
                "    for name, profit in top.items():\n"
                "        print(f'  - {name}: ${profit:,.2f}')\n"
                "else:\n"
                "    print('No sales recorded yet.')"
            ),
            "📦 Days of Inventory Remaining (DOI)": (
                "# Estimate inventory runway based on current stock\n"
                "stock = db.get_current_stock_on_hand()\n"
                "wh = db.get_warehouse_stock_on_hand()\n"
                "print('Total Boutique Inventory Position:')\n"
                "print(f'  - Shop Floor Units: {sum(stock.values()):,}')\n"
                "print(f'  - Warehouse Reserve Units: {sum(wh.values()):,}')\n"
                "print(f'  - Total Enterprise Units: {sum(stock.values()) + sum(wh.values()):,}')"
            ),
            "🎂 Upcoming Birthday VIPs": (
                "# Query upcoming VIP birthdays within next 14 days\n"
                "bdays = db.get_upcoming_birthday_customers(days_ahead=14)\n"
                "print(f'Found {len(bdays)} VIP clients celebrating in next 14 days:')\n"
                "for b in bdays:\n"
                "    print(f'  - {b[\"name\"]} ({b[\"loyalty_tier\"]}): DOB {b[\"dob\"]} (in {b[\"days_until\"]} days)')"
            ),
            "⚠️ Low Stock & Warehouse Restock Need": (
                "# Identify styles on shop floor needing warehouse restocking (<= 15 units)\n"
                "shop_stock = db.get_current_stock_on_hand()\n"
                "wh_stock = db.get_warehouse_stock_on_hand()\n"
                "low_stock = {k: v for k, v in shop_stock.items() if v <= 15}\n"
                "print(f'Shop Styles Requiring Restock (<= 15 units): {len(low_stock)}')\n"
                "if low_stock:\n"
                "    for name, qty in list(low_stock.items())[:5]:\n"
                "        wh_qty = wh_stock.get(name, 0)\n"
                "        print(f'  - {name}: Shop Floor={qty} units | Warehouse Reserve={wh_qty} units')\n"
                "else:\n"
                "    print('All shop floor merchandise is safely stocked above minimum safety levels.')"
            ),
            "👥 VIP Patron Loyalty Tier Breakdown": (
                "# Analyze customer segmentation and lifetime spend by loyalty tier\n"
                "custs = db.get_all_customers()\n"
                "if not custs.empty:\n"
                "    print('VIP Patron Loyalty Tier Breakdown:')\n"
                "    summary = custs.groupby('loyalty_tier').agg(\n"
                "        client_count=('id', 'count'),\n"
                "        avg_spend=('total_spend', 'mean')\n"
                "    ).reset_index()\n"
                "    for _, row in summary.iterrows():\n"
                "        print(f\"  - {row['loyalty_tier']}: {int(row['client_count'])} clients (Avg Spend: ${row['avg_spend']:,.2f})\")\n"
                "else:\n"
                "    print('No customer profiles recorded.')"
            ),
            "🏷️ Active Campaigns & Discount Breakdown": (
                "# Audit live promotional campaigns and discount tiers\n"
                "camps = db.get_all_campaigns()\n"
                "if not camps.empty:\n"
                "    print('Registered Boutique Marketing Campaigns:')\n"
                "    for _, c in camps.iterrows():\n"
                "        status = '🟢 ACTIVE' if c['status'] == 'Active' else '⚪ ' + c['status']\n"
                "        print(f\"  - [{status}] {c['name']} ({c['discount_pct']}% Off) - Category: {c['target_category']}\")\n"
                "else:\n"
                "    print('No promotional campaigns registered.')"
            )
        }

        preset_options = list(presets.keys())

        # Callback triggered immediately when user selects a different preset from the dropdown
        def _on_sandbox_preset_selected():
            chosen = st.session_state.get("shivi_preset_select")
            if chosen and chosen in presets:
                st.session_state.shivi_sandbox_editor = presets[chosen]
                st.session_state.shivi_active_preset_name = chosen

        # Initialize session state tracking
        if "shivi_active_preset_name" not in st.session_state:
            st.session_state.shivi_active_preset_name = preset_options[0]
            st.session_state.shivi_sandbox_editor = presets[preset_options[0]]

        # Synchronize in case selection was updated or restored
        if "shivi_preset_select" in st.session_state:
            curr_sel = st.session_state.shivi_preset_select
            if curr_sel != st.session_state.shivi_active_preset_name and curr_sel in presets:
                st.session_state.shivi_sandbox_editor = presets[curr_sel]
                st.session_state.shivi_active_preset_name = curr_sel

        col_pre1, col_pre2 = st.columns([3.8, 1.2])
        with col_pre1:
            sel_preset = st.selectbox(
                "Load Analytical Script Preset:",
                preset_options,
                key="shivi_preset_select",
                on_change=_on_sandbox_preset_selected
            )
        with col_pre2:
            st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
            if st.button("🔄 Reload Preset", use_container_width=True, help="Reset editor to the selected preset template"):
                st.session_state.shivi_sandbox_editor = presets[sel_preset]
                st.session_state.shivi_active_preset_name = sel_preset
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        code_input = st.text_area(
            "Python Script:",
            height=200,
            key="shivi_sandbox_editor",
            help="Write or edit custom Python scripts. You have direct access to 'db', 'pd', 'np', 'datetime', and 'math'."
        )

        btn_c1, btn_c2 = st.columns([1.6, 3.4])
        with btn_c1:
            exec_clicked = st.button("▶️ Execute Script in Sandbox", type="primary", key="shivi_exec_sandbox_btn", use_container_width=True)
        with btn_c2:
            if st.session_state.get("shivi_last_sandbox_result"):
                if st.button("🧹 Clear Output", key="shivi_clear_sandbox_btn"):
                    st.session_state.shivi_last_sandbox_result = None
                    st.rerun()

        if exec_clicked:
            with st.spinner("Executing script in Shivi's sandbox..."):
                sb_result = agent.run_sandbox_code(code_input)
                st.session_state.shivi_last_sandbox_result = sb_result

        if st.session_state.get("shivi_last_sandbox_result"):
            sb_result = st.session_state["shivi_last_sandbox_result"]
            if sb_result.get("success"):
                st.success(f"Execution completed in {sb_result.get('duration_sec', 0.0)}s")
                st.code(sb_result.get("output", "No output produced."), language="text")
            else:
                st.error(f"Execution failed: {sb_result.get('error')}")
                if sb_result.get("output"):
                    st.code(sb_result["output"], language="text")

    # ----------------------------------------------------
    # TAB 4: HITL STEERING APPROVAL QUEUE
    # ----------------------------------------------------
    with shivi_tab4:
        st.markdown("<h4 style='font-size:15px; font-weight:700; color:#0f172a; margin-top:0;'>🚦 Human-in-the-Loop Steering Approval Queue</h4>", unsafe_allow_html=True)
        st.caption("High-impact operations (mass customer dispatches, large inventory shifts, high discounts) require explicit administrative authorization.")

        approvals = agent.steering.get_pending_queue()
        if approvals:
            for item in approvals:
                st.html(f"""
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid #f59e0b; border-radius:8px; padding:12px 16px; margin-bottom:12px;">
                    <div style="display:flex; justify-content:space-between;">
                        <h5 style="margin:0; font-size:14px; font-weight:700; color:#0f172a;">Action #{item['id']} • {item['title']}</h5>
                        <span style="background:#fef3c7; color:#b45309; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700;">PENDING REVIEW</span>
                    </div>
                    <p style="font-size:12px; color:#475569; margin:6px 0;">{item['description']}</p>
                    <p style="font-size:11px; color:#94a3b8; margin:0;">Requested by <b>{item['requested_by']}</b> at {item['timestamp']}</p>
                </div>
                """)
                act_c1, act_c2 = st.columns([1, 1])
                with act_c1:
                    if st.button(f"✅ Approve & Execute #{item['id']}", key=f"appr_{item['id']}", type="primary"):
                        ok, msg = agent.steering.approve_action(item['id'], "Approved by administrator")
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                with act_c2:
                    if st.button(f"❌ Reject Action #{item['id']}", key=f"rej_{item['id']}"):
                        ok, msg = agent.steering.reject_action(item['id'], "Rejected by administrator")
                        if ok:
                            st.info(msg)
                            st.rerun()
                        else:
                            st.error(msg)
        else:
            st.info("✅ **No pending approvals in queue.** All operational parameters are within safe automated thresholds.")

    # ----------------------------------------------------
    # TAB 5: GUARDRAILS & PII SHIELD INSPECTOR
    # ----------------------------------------------------
    with shivi_tab5:
        st.markdown("<h4 style='font-size:15px; font-weight:700; color:#0f172a; margin-top:0;'>🛡️ Guardrails & PII Masking Live Inspector</h4>", unsafe_allow_html=True)
        st.caption("Demonstrates Shivi's enterprise safety shields: real-time PII detection/redaction and promotional discount boundaries.")

        col_pii, col_disc = st.columns(2)

        with col_pii:
            st.markdown("##### 🔒 Real-Time PII Redaction Demonstration")
            sample_text = st.text_area(
                "Input text containing sensitive client data:",
                value="Contact VIP patron Elena Rostova at elena.rostova@vogue-elegance.com or call her private line +1-555-0101 regarding her reserved linen gown.",
                height=110,
                key="shivi_pii_input"
            )
            redacted_result = PIIGuardrail.redact_pii(sample_text)
            st.markdown("**Sanitized Public/Telemetry Output:**")
            st.code(redacted_result, language="text")

        with col_disc:
            st.markdown("##### 🏷️ Promotional Discount Cap Validator")
            test_discount = st.number_input("Test Promotional Discount (%):", min_value=0.0, max_value=90.0, value=65.0, step=5.0)
            is_safe, eff_d, d_msg = DiscountSafetyGuardrail.validate_discount(test_discount)
            if is_safe:
                st.success(f"✅ Approved: {eff_d:.1f}% discount is within safe boundaries.")
            else:
                st.warning(f"⚠️ Guardrail Interception: Clamped from {test_discount:.1f}% to {eff_d:.1f}% (Cap: 50.0%).")
            st.caption(d_msg)
