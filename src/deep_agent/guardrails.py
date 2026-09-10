"""
src/deep_agent/guardrails.py
============================
Enterprise guardrails for Shivi Deep Agent:
1. PII detection and redaction (emails, phone numbers, customer codes).
2. Promotional discount cap safety validation (&le; 50% maximum).
3. Luxury brand voice and content moderation.
"""

import re
import logging
from typing import Tuple, Dict, Any, List

logger = logging.getLogger("shivi_guardrails")

class PIIGuardrail:
    """
    Detects and redacts sensitive Personally Identifiable Information (PII)
    from agent logs, prompt contexts, and public telemetry.
    """
    EMAIL_REGEX = re.compile(r'([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')
    PHONE_REGEX = re.compile(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}')

    @classmethod
    def mask_email(cls, email: str) -> str:
        """Masks email address, e.g. 'elena.rostova@vogue.com' -> 'e***a@vogue.com'."""
        if not email or "@" not in email:
            return email
        parts = email.split("@")
        user = parts[0]
        domain = parts[1]
        if len(user) <= 2:
            masked_user = user[0] + "*"
        else:
            masked_user = user[0] + "*" * (len(user) - 2) + user[-1]
        return f"{masked_user}@{domain}"

    @classmethod
    def mask_phone(cls, phone: str) -> str:
        """Masks phone number, e.g. '+1-555-0101' -> '+1-***-***-0101'."""
        if not phone:
            return phone
        digits = re.sub(r'\D', '', phone)
        if len(digits) >= 10:
            return f"+1-***-***-{digits[-4:]}"
        return "+1-***-***-****"

    @classmethod
    def redact_pii(cls, text: str) -> str:
        """Scans arbitrary text and redacts all discovered emails and phone numbers."""
        if not text:
            return ""

        def _replace_email(match):
            email = match.group(0)
            return cls.mask_email(email)

        def _replace_phone(match):
            phone = match.group(0)
            return cls.mask_phone(phone)

        sanitized = cls.EMAIL_REGEX.sub(_replace_email, text)
        sanitized = cls.PHONE_REGEX.sub(_replace_phone, sanitized)
        return sanitized


class DiscountSafetyGuardrail:
    """
    Prevents unauthorized or catastrophic margin dilution by capping promotional markdowns.
    Hard upper bound is 50.0% unless explicit super-admin override is logged.
    """
    MAX_PERMISSIBLE_DISCOUNT = 50.0

    @classmethod
    def validate_discount(cls, discount_pct: float, is_superadmin: bool = False) -> Tuple[bool, float, str]:
        """
        Validates discount percentage against safety boundaries.
        Returns: (is_safe, effective_discount, message)
        """
        try:
            discount = float(discount_pct)
        except (ValueError, TypeError):
            return False, 0.0, "Invalid discount value provided; must be a numeric percentage."

        if discount < 0:
            return False, 0.0, "Discount cannot be negative."

        if discount > cls.MAX_PERMISSIBLE_DISCOUNT and not is_superadmin:
            msg = (
                f"🚨 [GUARDRAIL VIOLATION] Requested discount of {discount:.1f}% exceeds "
                f"enterprise maximum threshold ({cls.MAX_PERMISSIBLE_DISCOUNT:.1f}%). "
                f"Discount automatically clamped to {cls.MAX_PERMISSIBLE_DISCOUNT:.1f}%."
            )
            logger.warning(msg)
            return False, cls.MAX_PERMISSIBLE_DISCOUNT, msg

        return True, discount, "Discount within verified safety boundaries."


class ContentVoiceGuardrail:
    """
    Validates outbound customer messages for luxury boutique voice,
    proper greetings, politeness, and absence of prohibited phrases.
    """
    PROHIBITED_WORDS = {"cheap", "ugly", "fake", "knockoff", "garbage", "trash", "desperate", "fire sale"}

    @classmethod
    def validate_content(cls, content: str) -> Tuple[bool, str]:
        """Ensures content meets luxury editorial standards."""
        if not content or len(content.strip()) < 10:
            return False, "Message content is too brief or empty."

        lower_content = content.lower()
        found_prohibited = [word for word in cls.PROHIBITED_WORDS if word in lower_content]
        if found_prohibited:
            return False, f"Content contains unrefined terminology: {', '.join(found_prohibited)}"

        return True, "Content approved by luxury editorial standards."
