"""
src/deep_agent/fault_tolerance.py
=================================
Fault Tolerance & Resilience for Shivi Deep Agent:
1. Retries with exponential backoff for external/model calls.
2. Call limits and iteration caps to prevent runaway agent loops.
3. Deterministic algorithmic fallbacks when local Ollama models are busy, offline, or throttling.
"""

import time
import logging
from typing import Callable, Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("shivi_fault_tolerance")

class RetryPolicy:
    """Executes callables with exponential backoff and error logging."""
    @staticmethod
    def execute_with_retry(func: Callable, max_retries: int = 3, initial_delay: float = 0.5, backoff_factor: float = 2.0, *args, **kwargs) -> Any:
        delay = initial_delay
        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt}/{max_retries} failed for {func.__name__}: {e}")
                if attempt < max_retries:
                    time.sleep(delay)
                    delay *= backoff_factor
        logger.error(f"All {max_retries} retry attempts failed for {func.__name__}.")
        raise last_exception


class CallBudgetTracker:
    """Enforces execution limits and prevents runaway autonomous loops."""
    def __init__(self, max_calls: int = 15):
        self.max_calls = max_calls
        self.current_calls = 0

    def record_call(self) -> bool:
        """Returns True if call is within budget, False if limit exceeded."""
        self.current_calls += 1
        if self.current_calls > self.max_calls:
            logger.error(f"Shivi Deep Agent call budget exceeded: {self.current_calls}/{self.max_calls}")
            return False
        return True

    def reset(self):
        self.current_calls = 0


class DeterministicFallbacks:
    """
    High-fidelity deterministic fallback engines ensuring 100% uptime and resilience
    even if the local Ollama LLM is offline, busy, or throttling.
    """
    @staticmethod
    def generate_trending_fashion_news_fallback(client_name: str, preferred_style: str, preferred_size: str, gender: str) -> Dict[str, str]:
        """Generates luxury trend briefing tailored to customer attributes."""
        trend_themes = {
            "Luxury Silk & Tailoring": {
                "theme": "The Renaissance of Fluid Silk & Sharp Shoulders",
                "trend_desc": "Paris and Milan runways are championing fluid silk slip skirts paired with razor-sharp tailored blazers.",
                "item_match": "Silk Slip Skirt (P002) paired with Tailored Double-Breasted Blazer (P010)",
                "quote": "Elegance is refusal. The modern wardrobe demands pure fabric integrity."
            },
            "Minimalist Knitwear": {
                "theme": "Quiet Luxury: Fine Gauge Cashmere & Monochromes",
                "trend_desc": "Architectural simplicity defines 2026 fashion. Understated cashmere crewnecks and merino cardigans in oat and charcoal are dominating street style.",
                "item_match": "Cashmere Crewneck Sweater (P005) & Merino Wool Cardigan (P014)",
                "quote": "Luxury whispers through touch, not loud logos."
            },
            "Bohemian Maxi & Dresses": {
                "theme": "Modern Bohemianism & Resort Drape",
                "trend_desc": "Tiered floral maxis and smocked waists are taking over summer soirees with lightweight organic linens.",
                "item_match": "Boho Floral Maxi Dress (P009) & Linen Wrap Dress (P001)",
                "quote": "Free-spirited silhouette meets bespoke tailoring."
            },
            "Tailored Outerwear & Blazers": {
                "theme": "Structured Power Tailoring & Heritage Trenches",
                "trend_desc": "Double-breasted silhouettes and cruelty-free vegan leather outerwear lead autumn transitions.",
                "item_match": "Vegan Leather Trench Coat (P008) & Double-Breasted Blazer (P010)",
                "quote": "Commanding presence through impeccable drape and proportion."
            }
        }

        chosen = trend_themes.get(preferred_style, trend_themes["Luxury Silk & Tailoring"])

        # 1. Luxury Email Newsletter (HTML)
        email_content = f"""
        <div style="font-family:'Inter', sans-serif; max-width:600px; margin:0 auto; padding:24px; background:#ffffff; border:1px solid #e2e8f0; border-radius:12px;">
            <div style="text-align:center; padding-bottom:16px; border-bottom:2px solid #0f172a;">
                <span style="font-size:10px; font-weight:700; letter-spacing:2px; color:#64748b; text-transform:uppercase;">Mishika Fashion Boutique Curated Intelligence</span>
                <h2 style="font-family:'Playfair Display', serif; color:#0f172a; margin:6px 0;">{chosen['theme']}</h2>
                <p style="font-size:12px; color:#059669; font-weight:600;">Personalized for {client_name} • Size {preferred_size}</p>
            </div>
            <div style="padding:18px 0; color:#334155; line-height:1.6; font-size:14px;">
                <p>Dear {client_name},</p>
                <p>{chosen['trend_desc']}</p>
                <div style="background:#f8fafc; border-left:4px solid #0f172a; padding:12px 16px; margin:16px 0; border-radius:6px;">
                    <p style="margin:0; font-weight:700; color:#0f172a;">👗 Handpicked Boutique Match for You:</p>
                    <p style="margin:4px 0 0 0; color:#475569;"><b>{chosen['item_match']}</b> — Hand-selected in your preferred size <b>{preferred_size}</b>.</p>
                </div>
                <blockquote style="margin:16px 0; padding-left:12px; border-left:2px solid #cbd5e1; font-style:italic; color:#64748b;">
                    "{chosen['quote']}"
                </blockquote>
                <p>We invite you to experience these curated arrivals in our private salon this week.</p>
            </div>
            <div style="text-align:center; padding-top:16px; border-top:1px solid #f1f5f9; font-size:11px; color:#94a3b8;">
                Mishika Fashion Boutique • Private Client Advisory • AI Assistant: Shivi
            </div>
        </div>
        """

        # 2. Punchy WhatsApp Message
        whatsapp_content = (
            f"✨ *Mishika Fashion Private Styling Note for {client_name}*\n\n"
            f"Bonjour {client_name}! 🌟 Paris runways are buzzing with *{chosen['theme']}*.\n\n"
            f"👗 *Curated for your aesthetic:* We have reserved our latest *{chosen['item_match']}* in your signature size *{preferred_size}*.\n\n"
            f"🥂 Reply *RESERVE* or visit our private salon today to experience the collection before public release.\n\n"
            f"— *Shivi*, Mishika Fashion Boutique AI Concierge"
        )

        return {
            "email_subject": f"✨ Curated Mishika Fashion Alert: {chosen['theme']}",
            "email_html": email_content,
            "whatsapp_text": whatsapp_content
        }

    @staticmethod
    def generate_campaign_copy_fallback(campaign_name: str, discount_pct: float, target_category: str, client_name: str, preferred_size: str) -> Dict[str, str]:
        """Generates campaign launch copy for email and whatsapp."""
        email_content = f"""
        <div style="font-family:'Inter', sans-serif; max-width:600px; margin:0 auto; padding:24px; background:#ffffff; border:1px solid #e2e8f0; border-radius:12px;">
            <div style="text-align:center; padding-bottom:16px; border-bottom:2px solid #d97706;">
                <span style="font-size:10px; font-weight:700; letter-spacing:2px; color:#d97706; text-transform:uppercase;">VIP Privileged Access</span>
                <h2 style="font-family:'Playfair Display', serif; color:#0f172a; margin:6px 0;">{campaign_name}</h2>
                <div style="display:inline-block; background:#fef3c7; color:#b45309; padding:4px 14px; border-radius:9999px; font-size:14px; font-weight:800; margin-top:4px;">
                    {discount_pct:.0f}% PRIVILEGED SAVINGS
                </div>
            </div>
            <div style="padding:18px 0; color:#334155; line-height:1.6; font-size:14px;">
                <p>Dear {client_name},</p>
                <p>As one of our esteemed patrons, we are delighted to grant you first-access to our newest seasonal initiative: <b>{campaign_name}</b>.</p>
                <p>Enjoy an exclusive <b>{discount_pct:.0f}% celebratory markdown</b> across our hand-tailored {target_category} collection, curated specifically for your wardrobe palette.</p>
                <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:8px; padding:12px 16px; margin:14px 0; text-align:center;">
                    <span style="font-size:12px; color:#92400e;">Exclusive VIP Invitation Code:</span><br/>
                    <b style="font-size:18px; letter-spacing:3px; color:#78350f;">MISHIKA-{int(discount_pct)}VIP</b>
                </div>
                <p>Available in your preferred size <b>{preferred_size}</b> while limited salon inventory endures.</p>
            </div>
            <div style="text-align:center; padding-top:16px; border-top:1px solid #f1f5f9; font-size:11px; color:#94a3b8;">
                Mishika Fashion Boutique • Private Client Services • AI Assistant: Shivi
            </div>
        </div>
        """

        whatsapp_content = (
            f"🎉 *Exclusive Invitation for {client_name}* 🥂\n\n"
            f"Dear {client_name}, we are thrilled to launch *{campaign_name}* with an exclusive *{discount_pct:.0f}% VIP markdown* on our finest {target_category}!\n\n"
            f"🔑 *Your VIP Access Code:* `MISHIKA-{int(discount_pct)}VIP`\n"
            f"📏 Available in your preferred size: *{preferred_size}*\n\n"
            f"Show this message in-store or tap the link to shop your private curation before public announcement!\n\n"
            f"— *Shivi*, Mishika Fashion Boutique AI Concierge"
        )

        return {
            "email_subject": f"🥂 Privileged Invitation: {campaign_name} ({discount_pct:.0f}% VIP Access)",
            "email_html": email_content,
            "whatsapp_text": whatsapp_content
        }

    @staticmethod
    def generate_back_in_stock_fallback(product_name: str, size: str, client_name: str) -> Dict[str, str]:
        """Generates back-in-stock notification copy."""
        email_content = f"""
        <div style="font-family:'Inter', sans-serif; max-width:600px; margin:0 auto; padding:24px; background:#ffffff; border:1px solid #e2e8f0; border-radius:12px;">
            <div style="text-align:center; padding-bottom:14px; border-bottom:2px solid #059669;">
                <span style="font-size:10px; font-weight:700; letter-spacing:2px; color:#059669; text-transform:uppercase;">VIP RESTOCK NOTIFICATION</span>
                <h2 style="font-family:'Playfair Display', serif; color:#0f172a; margin:6px 0;">It's Back: {product_name}</h2>
            </div>
            <div style="padding:18px 0; color:#334155; line-height:1.6; font-size:14px;">
                <p>Dear {client_name},</p>
                <p>We are thrilled to inform you that our highly sought-after <b>{product_name}</b> in your size <b>{size}</b> has just returned to our boutique vault.</p>
                <div style="background:#ecfdf5; border:1px solid #a7f3d0; border-radius:8px; padding:12px 16px; margin:14px 0;">
                    <p style="margin:0; font-weight:700; color:#065f46;">✨ Reserved Allocation Active:</p>
                    <p style="margin:4px 0 0 0; color:#047857;">We have placed a 24-hour courtesy hold on 1 unit in size {size} exclusively for your account.</p>
                </div>
                <p>Reply to this notice or visit our salon to complete your styling look.</p>
            </div>
            <div style="text-align:center; padding-top:16px; border-top:1px solid #f1f5f9; font-size:11px; color:#94a3b8;">
                Mishika Fashion Boutique • Private Client Services • AI Assistant: Shivi
            </div>
        </div>
        """

        whatsapp_content = (
            f"🔔 *Back in Stock Alert for {client_name}* ✨\n\n"
            f"Good news! The *{product_name}* that was previously unavailable has just been restocked in your size *{size}*.\n\n"
            f"🔒 We have reserved 1 piece under your name for the next 24 hours.\n\n"
            f"Reply *CLAIM* to confirm your piece or visit our boutique today.\n\n"
            f"— *Shivi*, Mishika Fashion Boutique AI Concierge"
        )

        return {
            "email_subject": f"🔔 Restock Alert: {product_name} (Size {size}) Has Returned",
            "email_html": email_content,
            "whatsapp_text": whatsapp_content
        }
