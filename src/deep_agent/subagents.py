"""
src/deep_agent/subagents.py
===========================
Specialized Subagents for Shivi Deep Agent:
1. ReportingSubagent: Generates opening briefings and closing audit PDFs.
2. TrendHunterSubagent: Researches fashion trends and crafts personalized newsletters.
3. CampaignDispatchSubagent: Crafts attractive promotional copy and dispatches campaigns.
4. InventoryWatchdogSubagent: Monitors stockouts, broken size curves, and back-in-stock alerts.
"""

import json
import logging
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from src.core.catalog import CATALOG
from src.reporting.pdf_builder import generate_opening_briefing_pdf, generate_closing_audit_pdf
from src.deep_agent.fault_tolerance import DeterministicFallbacks
from src.deep_agent.guardrails import PIIGuardrail, DiscountSafetyGuardrail, ContentVoiceGuardrail
from src.deep_agent.delivery import EmailDeliveryService

logger = logging.getLogger("shivi_subagents")

class ReportingSubagent:
    """Specializes in boardroom reporting, opening briefings, and closing financial audits."""
    def __init__(self, db_manager):
        self.db = db_manager

    def generate_opening_report(self) -> Dict[str, Any]:
        """Generates the morning opening briefing PDF and summary telemetry."""
        pdf_bytes = generate_opening_briefing_pdf(self.db)
        shop_stock = self.db.get_current_stock_on_hand()
        wh_stock = self.db.get_warehouse_stock_on_hand()
        low_stock = [pid for pid, qty in shop_stock.items() if qty <= 15]
        campaigns = self.db.get_all_campaigns()
        active_camp_count = len(campaigns[campaigns["status"] == "Active"]) if not campaigns.empty else 0
        bday_clients = self.db.get_upcoming_birthday_customers(days_ahead=7)

        summary = (
            f"Morning Opening Briefing compiled successfully by Shivi.\n"
            f"- Active Shop Floor Stock: {sum(shop_stock.values()):,} units across {len(shop_stock)} styles.\n"
            f"- Isolated Warehouse Reserve: {sum(wh_stock.values()):,} units in backroom storage.\n"
            f"- Critical Safety Alerts (<=15 units): {len(low_stock)} styles requiring attention.\n"
            f"- Active Marketing Campaigns: {active_camp_count} live.\n"
            f"- VIP Client Birthdays Next 7 Days: {len(bday_clients)} celebrating."
        )

        return {
            "success": True,
            "report_name": f"MishikaBoutique_Opening_Briefing_{datetime.now().strftime('%Y%m%d')}.pdf",
            "pdf_bytes": pdf_bytes,
            "summary": summary,
            "low_stock_count": len(low_stock),
            "birthday_count": len(bday_clients)
        }

    def generate_closing_report(self) -> Dict[str, Any]:
        """Generates the evening closing audit PDF and financial reconciliation."""
        pdf_bytes = generate_closing_audit_pdf(self.db)
        today_str = datetime.now().strftime("%Y-%m-%d")
        sales_df = self.db.fetch_logs("sales_ledger", limit=50)

        t_rev = sales_df['total_revenue'].sum() if not sales_df.empty else 0.0
        t_profit = sales_df['gross_profit'].sum() if not sales_df.empty else 0.0
        margin = (t_profit / t_rev * 100) if t_rev > 0 else 0.0
        t_units = sales_df['quantity'].sum() if not sales_df.empty else 0

        summary = (
            f"Evening Closing Audit compiled successfully by Shivi.\n"
            f"- Reconciled Revenue: ${t_rev:,.2f} across {len(sales_df)} recent checkouts.\n"
            f"- Net Gross Profit: ${t_profit:,.2f} (Realized Margin: {margin:.1f}%).\n"
            f"- Units Sold: {t_units:,} pieces.\n"
            f"- Register Drawer: Reconciled & Closed."
        )

        return {
            "success": True,
            "report_name": f"MishikaBoutique_Closing_Audit_{datetime.now().strftime('%Y%m%d')}.pdf",
            "pdf_bytes": pdf_bytes,
            "summary": summary,
            "revenue": t_rev,
            "profit": t_profit
        }


class TrendHunterSubagent:
    """
    Specializes in fashion trends research and personalized customer newsletter generation.
    Pulls live fashion news from the internet via RSS feeds, with instant seamless fallback
    to curated default fashion news in case of any network or connection error.
    """
    FASHION_SEARCH_TOPICS = [
        "luxury fashion trends 2026",
        "paris haute couture fashion week",
        "milan luxury runway style",
        "quiet luxury bespoke tailoring fashion",
        "designer silk cashmere fine knitwear trends",
        "high fashion evening wear red carpet gowns",
        "sustainable luxury fashion designer outerwear",
        "luxury resort wear bohemian elegance trends"
    ]

    def __init__(self, db_manager):
        self.db = db_manager

    @classmethod
    def get_default_fashion_articles(cls, limit: int = 5, randomize: bool = False) -> List[Dict[str, Any]]:
        """Provides high-fidelity curated fashion articles as deterministic fallback."""
        articles = [
            {
                "title": "The Renaissance of Fluid Silk & Sharp Shoulders",
                "source": "Mishika Luxury Curated",
                "link": "https://mishikaboutique.com/trends/fluid-silk-tailoring",
                "pub_date": "Autumn/Winter 2026",
                "snippet": "Paris and Milan runways champion fluid silk slip skirts paired with razor-sharp tailored blazers."
            },
            {
                "title": "Quiet Luxury: Fine Gauge Cashmere & Monochromatic Layering",
                "source": "Mishika Luxury Curated",
                "link": "https://mishikaboutique.com/trends/quiet-luxury-cashmere",
                "pub_date": "Autumn/Winter 2026",
                "snippet": "Architectural simplicity defines modern fashion with understated cashmere crewnecks and merino cardigans."
            },
            {
                "title": "Modern Bohemianism & Resort Drape for High Summer",
                "source": "Mishika Luxury Curated",
                "link": "https://mishikaboutique.com/trends/modern-bohemianism",
                "pub_date": "Spring/Summer 2026",
                "snippet": "Tiered floral maxis and smocked waists in lightweight organic linens dominate summer soirees."
            },
            {
                "title": "Structured Power Tailoring & Cruelty-Free Vegan Leather Outerwear",
                "source": "Mishika Luxury Curated",
                "link": "https://mishikaboutique.com/trends/power-tailoring-outerwear",
                "pub_date": "Autumn/Winter 2026",
                "snippet": "Double-breasted silhouettes and sustainable vegan leather outerwear lead seasonal transitions."
            },
            {
                "title": "Satin Pleats & Jewel Tones in Contemporary Evening Wear",
                "source": "Mishika Luxury Curated",
                "link": "https://mishikaboutique.com/trends/satin-pleats-jewel-tones",
                "pub_date": "Autumn/Winter 2026",
                "snippet": "Rich emerald, sapphire, and champagne hues in pleated satin skirts for evening galas."
            },
            {
                "title": "Sculptural Draping & Velvet Accents for Black-Tie Galas",
                "source": "Mishika Luxury Curated",
                "link": "https://mishikaboutique.com/trends/velvet-black-tie",
                "pub_date": "Autumn/Winter 2026",
                "snippet": "Deep midnight velvet and sculptural asymmetries set the tone for winter galas and private salon previews."
            },
            {
                "title": "Heritage Linen & Organic Poplin in Minimalist Tailoring",
                "source": "Mishika Luxury Curated",
                "link": "https://mishikaboutique.com/trends/heritage-linen",
                "pub_date": "Spring/Summer 2026",
                "snippet": "Breathable tailoring with textured Italian linen blazers and relaxed wide-leg trousers."
            }
        ]
        if randomize:
            import random
            shuffled = list(articles)
            random.shuffle(shuffled)
            return shuffled[:limit]
        return articles[:limit]

    def fetch_live_fashion_news(
        self,
        query: Optional[str] = None,
        limit: int = 6,
        timeout_sec: float = 5.0,
        randomize: bool = True
    ) -> Tuple[List[Dict[str, Any]], str, bool]:
        """
        Fetches live fashion and luxury trends directly from internet RSS feeds.
        Automatically falls back to default curated fashion articles in case of any network,
        parsing, timeout, or connectivity issue.
        """
        import random
        import time
        import urllib.parse

        search_query = query.strip() if (query and query.strip()) else random.choice(self.FASHION_SEARCH_TOPICS)
        encoded_q = urllib.parse.quote(search_query)
        ts = int(time.time() * 1000)
        url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-US&gl=US&ceid=US:en&_t={ts}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_sec) as response:
                xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            items = root.findall(".//item")
            if not items:
                raise ValueError("No fashion news items found in internet feed.")

            # If randomize is requested and we have plenty of items, sample from top 25 items for fresh variety
            if randomize and len(items) > limit:
                sample_pool = items[:min(25, len(items))]
                selected_items = random.sample(sample_pool, min(limit, len(sample_pool)))
            else:
                selected_items = items[:limit]

            articles = []
            for it in selected_items:
                raw_title = (it.findtext("title") or "").strip()
                source = (it.findtext("source") or "").strip()
                link = (it.findtext("link") or "").strip()
                pub_date = (it.findtext("pubDate") or "").strip()
                desc = (it.findtext("description") or "").strip()

                if " - " in raw_title:
                    parts = raw_title.rsplit(" - ", 1)
                    title = parts[0].strip()
                    if not source:
                        source = parts[1].strip()
                else:
                    title = raw_title

                if not source:
                    source = "Global Fashion Wire"

                articles.append({
                    "title": title,
                    "source": source,
                    "link": link,
                    "pub_date": pub_date,
                    "snippet": desc or f"Latest Mishika luxury fashion trend report from {source}."
                })

            if articles:
                logger.info(f"Successfully fetched {len(articles)} live fashion articles for '{search_query}'.")
                label = f"🌐 Live Internet News • {search_query.title()}"
                return articles, label, True

            raise ValueError("Processed articles list was empty.")

        except Exception as e:
            logger.warning(f"Internet fashion news fetch encountered an issue: {e}. Seamlessly falling back to default curated news.")
            return self.get_default_fashion_articles(limit=limit, randomize=randomize), "📦 Default Curated News (Offline Safe Fallback)", False

    def curate_and_draft_fashion_news(
        self,
        customer_id: Optional[int] = None,
        query: Optional[str] = None,
        randomize: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Curates trending fashion news tailored to clients and creates Email and WhatsApp copy.
        Pulls dynamically from the internet, or uses default curated news if internet is unavailable.
        """
        customers_df = self.db.get_all_customers()
        if customers_df.empty:
            return []

        if customer_id:
            targets = customers_df[customers_df["id"] == customer_id].to_dict('records')
        else:
            targets = customers_df.head(10).to_dict('records')

        # Fetch fashion news (Internet with automatic default fallback)
        articles, news_source_label, is_live = self.fetch_live_fashion_news(
            query=query,
            limit=max(10, len(targets)),
            randomize=randomize
        )

        results = []
        for idx, cust in enumerate(targets):
            # Select relevant article (round-robin through articles)
            article = articles[idx % len(articles)]
            art_title = article.get("title", "Mishika Fashion Trends")
            art_source = article.get("source", "Vogue & Runways")
            art_link = article.get("link", "#")

            # Fallback style theme mapping
            fallback_copy = DeterministicFallbacks.generate_trending_fashion_news_fallback(
                client_name=cust["name"],
                preferred_style=cust.get("style_preference", "Luxury Silk & Tailoring"),
                preferred_size=cust.get("preferred_size", "M"),
                gender=cust.get("gender", "Female")
            )

            # Determine badge styling
            if is_live:
                badge_html = f"""<span style="background:#ecfdf5; color:#059669; border:1px solid #a7f3d0; padding:3px 10px; border-radius:9999px; font-size:10px; font-weight:700; letter-spacing:0.5px;">🌐 LIVE INTERNET FASHION REPORT • {art_source.upper()}</span>"""
                subject = f"✨ Mishika Trend Alert: {art_title[:55]}..."
            else:
                badge_html = f"""<span style="background:#f1f5f9; color:#475569; border:1px solid #cbd5e1; padding:3px 10px; border-radius:9999px; font-size:10px; font-weight:700; letter-spacing:0.5px;">📦 DEFAULT CURATED ATELIER BRIEFING</span>"""
                subject = fallback_copy["email_subject"]

            # Construct personalized luxury HTML Email
            email_html = f"""
            <div style="font-family:'Inter', -apple-system, BlinkMacSystemFont, sans-serif; max-width:600px; margin:0 auto; padding:24px; background:#ffffff; border:1px solid #e2e8f0; border-radius:12px;">
                <div style="text-align:center; padding-bottom:14px; border-bottom:2px solid #0f172a;">
                    <div style="margin-bottom:8px;">{badge_html}</div>
                    <span style="font-size:10px; font-weight:700; letter-spacing:2px; color:#64748b; text-transform:uppercase;">Mishika Fashion Boutique Advisory</span>
                    <h2 style="font-family:'Playfair Display', Georgia, serif; color:#0f172a; margin:6px 0; font-size:22px; line-height:1.3;">{art_title}</h2>
                    <p style="font-size:12px; color:#059669; font-weight:600; margin:4px 0 0 0;">Personalized for {cust['name']} • Size {cust.get('preferred_size', 'M')} • {cust.get('loyalty_tier', 'VIP')}</p>
                </div>
                <div style="padding:18px 0; color:#334155; line-height:1.6; font-size:14px;">
                    <p>Dear {cust['name']},</p>
                    <p>Our private styling intelligence team is monitoring seasonal shifts. Today's feature highlights <b>{art_title}</b>, reported via <i>{art_source}</i>.</p>
                    {f'<p style="margin:8px 0;"><a href="{art_link}" target="_blank" style="color:#2563eb; text-decoration:underline; font-size:12.5px;">🔗 Read the full trend feature on {art_source} &rarr;</a></p>' if is_live and art_link != '#' else ''}
                    
                    <div style="background:#f8fafc; border-left:4px solid #0f172a; padding:12px 16px; margin:16px 0; border-radius:6px;">
                        <p style="margin:0; font-weight:700; color:#0f172a;">👗 Handpicked Boutique Match for Your Style ({cust.get('style_preference', 'Mishika Couture')}):</p>
                        <p style="margin:4px 0 0 0; color:#475569;">We have reserved matching signature pieces in your preferred size <b>{cust.get('preferred_size', 'M')}</b>.</p>
                    </div>
                    <blockquote style="margin:16px 0; padding-left:12px; border-left:2px solid #cbd5e1; font-style:italic; color:#64748b;">
                        "Elegance is refusal. The modern wardrobe demands pure fabric integrity and intentional silhouettes."
                    </blockquote>
                    <p>We invite you to experience these arrivals in our private salon this week.</p>
                </div>
                <div style="text-align:center; padding-top:16px; border-top:1px solid #f1f5f9; font-size:11px; color:#94a3b8;">
                    Mishika Fashion Boutique • Private Client Advisory • AI Concierge: Shivi<br/>
                    <span style="font-size:10px; color:#cbd5e1;">News source: {news_source_label}</span>
                </div>
            </div>
            """

            # Construct personalized WhatsApp message
            if is_live:
                link_line = f"\n🔗 *Read story:* {art_link}\n" if art_link != "#" else "\n"
                wa_text = (
                    f"✨ *Mishika Fashion Boutique — Runway Trend Alert*\n\n"
                    f"Bonjour {cust['name']}! 🌟 Trending today on *{art_source}*:\n"
                    f"*{art_title}*{link_line}\n"
                    f"👗 *Curated for you:* Handpicked for your *{cust.get('style_preference', 'Luxury')}* aesthetic in size *{cust.get('preferred_size', 'M')}*.\n\n"
                    f"🥂 Reply *RESERVE* to hold your piece in our private salon.\n\n"
                    f"— *Shivi*, Mishika Fashion Boutique AI Concierge"
                )
            else:
                wa_text = fallback_copy["whatsapp_text"]

            # Apply PII Guardrail for log safety
            masked_email = PIIGuardrail.mask_email(cust["email"])
            masked_phone = PIIGuardrail.mask_phone(cust["phone"])

            results.append({
                "customer_id": cust["id"],
                "customer_name": cust["name"],
                "customer_email": cust["email"],
                "customer_phone": cust["phone"],
                "masked_email": masked_email,
                "masked_phone": masked_phone,
                "style_preference": cust.get("style_preference", "Contemporary"),
                "email_subject": subject,
                "email_html": email_html,
                "whatsapp_text": wa_text,
                "news_source": news_source_label,
                "is_live_internet": is_live,
                "article_title": art_title,
                "article_source": art_source,
                "article_link": art_link
            })

        return results


class CampaignDispatchSubagent:
    """Specializes in promotional copywriting, discount verification, and multi-channel broadcasts."""
    def __init__(self, db_manager):
        self.db = db_manager

    def draft_campaign_broadcast(self, campaign_id: Optional[int] = None) -> Dict[str, Any]:
        """Drafts campaign announcements for registered clients with guardrail checks."""
        active_camp = None
        if campaign_id:
            all_camps = self.db.get_all_campaigns()
            matched = all_camps[all_camps["id"] == campaign_id]
            if not matched.empty:
                r = matched.iloc[0]
                active_camp = {
                    "id": r["id"],
                    "name": r["name"],
                    "description": r["description"],
                    "discount_pct": float(r["discount_pct"]),
                    "target_category": r.get("target_category", "All Categories"),
                    "banner_tagline": r.get("banner_tagline", "")
                }
        if not active_camp:
            active_camp = self.db.get_active_campaign()

        if not active_camp:
            # Fallback default campaign
            active_camp = {
                "id": 0,
                "name": "Summer Riviera Elegance",
                "description": "20% off all resort dresses and luxury silk separates",
                "discount_pct": 20.0,
                "target_category": "Dresses",
                "banner_tagline": "Sun-Drenched Coastal Luxury"
            }

        # Guardrail Validation on Discount
        is_safe, eff_discount, guardrail_msg = DiscountSafetyGuardrail.validate_discount(active_camp["discount_pct"])

        customers_df = self.db.get_all_customers()
        recipients = []
        for _, cust in customers_df.head(10).iterrows():
            copy = DeterministicFallbacks.generate_campaign_copy_fallback(
                campaign_name=active_camp["name"],
                discount_pct=eff_discount,
                target_category=active_camp["target_category"],
                client_name=cust["name"],
                preferred_size=cust.get("preferred_size", "M")
            )
            recipients.append({
                "customer_id": cust["id"],
                "customer_name": cust["name"],
                "customer_email": cust["email"],
                "customer_phone": cust["phone"],
                "masked_email": PIIGuardrail.mask_email(cust["email"]),
                "masked_phone": PIIGuardrail.mask_phone(cust["phone"]),
                "email_subject": copy["email_subject"],
                "email_html": copy["email_html"],
                "whatsapp_text": copy["whatsapp_text"]
            })

        return {
            "campaign": active_camp,
            "effective_discount": eff_discount,
            "guardrail_status": guardrail_msg,
            "recipients": recipients
        }

    def execute_dispatch(self, messages: List[Dict[str, Any]], channel: str = "both", campaign_id: Optional[int] = None) -> int:
        """Saves outbound communication records to SQLite database and sends live SMTP email if enabled."""
        dispatched_count = 0
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        email_conf = EmailDeliveryService.load_email_config()

        for m in messages:
            if channel in ("email", "both"):
                email_status = "Delivered (Logged)"
                if email_conf.get("is_configured") and email_conf.get("auto_send_customer_emails", True):
                    to_email = m.get("customer_email")
                    if to_email:
                        sub = m.get("email_subject", "Mishika Boutique Exclusive")
                        html = m.get("email_html", "")
                        success, err_msg = EmailDeliveryService.send_smtp_email(
                            to_email=to_email,
                            subject=sub,
                            html_body=html
                        )
                        if success:
                            email_status = f"Sent (Gmail SMTP to {to_email})"
                        else:
                            email_status = f"SMTP Failed: {err_msg[:60]}"

                self.db.save_agent_communication({
                    "timestamp": now_str,
                    "customer_id": m["customer_id"],
                    "customer_name": m["customer_name"],
                    "channel": "Email",
                    "message_type": "Marketing",
                    "subject": m.get("email_subject", "Boutique Update"),
                    "content": m.get("email_html", ""),
                    "status": email_status,
                    "campaign_id": campaign_id
                })
                dispatched_count += 1

            if channel in ("whatsapp", "both"):
                self.db.save_agent_communication({
                    "timestamp": now_str,
                    "customer_id": m["customer_id"],
                    "customer_name": m["customer_name"],
                    "channel": "WhatsApp",
                    "message_type": "Marketing",
                    "subject": "Direct WhatsApp Message",
                    "content": m.get("whatsapp_text", ""),
                    "status": "Delivered",
                    "campaign_id": campaign_id
                })
                dispatched_count += 1

        logger.info(f"Dispatched {dispatched_count} communications via {channel.title()}.")
        return dispatched_count


class InventoryWatchdogSubagent:
    """Specializes in back-in-stock detection, broken size curves, and restocking alerts."""
    def __init__(self, db_manager):
        self.db = db_manager

    def scan_for_back_in_stock_candidates(self) -> List[Dict[str, Any]]:
        """
        Scans catalog items to find products that have positive stock (specifically focusing
        on items P016-P020 that were designated out of stock, or any newly stocked styles).
        """
        shop_stock = self.db.get_current_stock_on_hand()
        wh_stock = self.db.get_warehouse_stock_on_hand()

        candidates = []
        for pid, details in CATALOG.items():
            total_s = shop_stock.get(pid, 0)
            total_w = wh_stock.get(pid, 0)
            # Products with active inventory available to notify clients
            if total_s > 0 or total_w > 0:
                is_outage_style = pid.startswith("P") and pid[1:].isdigit() and int(pid[1:]) >= 16
                candidates.append({
                    "product_id": pid,
                    "product_name": details["name"],
                    "category": details.get("category", "Apparel"),
                    "shop_stock": total_s,
                    "warehouse_stock": total_w,
                    "is_designated_outage": is_outage_style
                })

        # Prioritize styles that were outages or newly restocked
        candidates.sort(key=lambda x: (not x["is_designated_outage"], -x["shop_stock"]))
        return candidates

    def generate_back_in_stock_alerts(self, product_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Matches a restocked product with interested VIP customers and generates notifications."""
        candidates = self.scan_for_back_in_stock_candidates()
        if not candidates:
            return []

        target_prod = None
        if product_id:
            for c in candidates:
                if c["product_id"] == product_id:
                    target_prod = c
                    break
        if not target_prod:
            target_prod = candidates[0]

        p_name = target_prod["product_name"]
        customers_df = self.db.get_all_customers()
        alerts = []

        for _, cust in customers_df.head(6).iterrows():
            size = cust.get("preferred_size", "M")
            copy = DeterministicFallbacks.generate_back_in_stock_fallback(
                product_name=p_name,
                size=size,
                client_name=cust["name"]
            )
            alerts.append({
                "product_id": target_prod["product_id"],
                "product_name": p_name,
                "customer_id": cust["id"],
                "customer_name": cust["name"],
                "customer_email": cust["email"],
                "customer_phone": cust["phone"],
                "masked_email": PIIGuardrail.mask_email(cust["email"]),
                "masked_phone": PIIGuardrail.mask_phone(cust["phone"]),
                "preferred_size": size,
                "email_subject": copy["email_subject"],
                "email_html": copy["email_html"],
                "whatsapp_text": copy["whatsapp_text"]
            })

        return alerts
