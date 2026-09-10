"""
src/deep_agent/delivery.py
==========================
Outbound communication dispatch gateways for Shivi Deep Agent:
1. WhatsApp Web / Mobile Click-to-Chat (wa.me) instant launcher.
2. Standard RFC2368 mailto: launcher.
3. Live SMTP Email Gateway (Gmail, SendGrid, AWS SES, standard TLS/SSL).
4. Automated API Hooks for Twilio and Meta WhatsApp Business Cloud API.
"""

import re
import os
import ssl
import json
import smtplib
import logging
import urllib.parse
import urllib.request
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("shivi_delivery")


class WhatsAppDeliveryService:
    """Handles WhatsApp message generation and live delivery protocols."""

    @staticmethod
    def clean_phone_number(phone: str) -> str:
        """Strips formatting to produce pure international digits (e.g., '+1-555-0101' -> '15550101')."""
        if not phone:
            return ""
        return re.sub(r'\D', '', phone)

    @classmethod
    def generate_wa_me_link(cls, phone: str, text: str) -> str:
        """
        Generates an official WhatsApp Click-to-Chat URL.
        Clicking this link opens WhatsApp Web or the WhatsApp mobile app pre-loaded with
        the exact recipient phone number and curated message text.
        Works without any paid API keys or enterprise registration.
        """
        clean_phone = cls.clean_phone_number(phone)
        encoded_text = urllib.parse.quote(text)
        return f"https://wa.me/{clean_phone}?text={encoded_text}"

    @classmethod
    def send_via_twilio(cls, to_phone: str, message: str, account_sid: str = "", auth_token: str = "", from_number: str = "") -> Tuple[bool, str]:
        """Sends automated WhatsApp message via Twilio API if credentials provided."""
        account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID", "")
        auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN", "")
        from_number = from_number or os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

        if not account_sid or not auth_token:
            return False, "Twilio credentials not configured. Use WhatsApp Web (wa.me) 1-click link instead."

        try:
            clean_to = cls.clean_phone_number(to_phone)
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            data = urllib.parse.urlencode({
                "From": from_number,
                "To": f"whatsapp:+{clean_to}",
                "Body": message
            }).encode("utf-8")

            req = urllib.request.Request(url, data=data, method="POST")
            import base64
            auth_header = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
            req.add_header("Authorization", f"Basic {auth_header}")

            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                sid = result.get("sid", "Sent")
                logger.info(f"Twilio WhatsApp dispatched successfully. SID: {sid}")
                return True, f"Delivered via Twilio (SID: {sid})"
        except Exception as e:
            logger.error(f"Twilio WhatsApp dispatch failed: {e}")
            return False, str(e)


from email.mime.application import MIMEApplication
from pathlib import Path

class EmailDeliveryService:
    """Handles Email message generation, configuration, and live SMTP dispatch."""
    
    CONFIG_PATH = Path("storage/config/email_config.json")
    ENV_PATH = Path(".env")
    ENV_EXAMPLE_PATH = Path(".env.example")

    @classmethod
    def load_email_config(cls) -> Dict[str, Any]:
        """
        Loads email configuration from storage/config/email_config.json, .env, and .env.example.
        Provides sensible Gmail defaults and auto-synchronizes detected credentials.
        """
        config = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "",
            "smtp_pass": "",
            "smtp_from": "",
            "from_name": "Mishika Fashion Boutique Concierge",
            "admin_email": "",
            "auto_send_admin_audits": True,
            "auto_send_customer_emails": True,
            "is_configured": False
        }

        # 1. Load from storage/config/email_config.json if it exists
        try:
            if cls.CONFIG_PATH.exists():
                with open(cls.CONFIG_PATH, "r", encoding="utf-8") as f:
                    file_conf = json.load(f)
                    config.update(file_conf)
        except Exception as e:
            logger.warning(f"Failed to read {cls.CONFIG_PATH}: {e}")

        # 2. Check .env and .env.example files directly
        env_files = [cls.ENV_PATH, cls.ENV_EXAMPLE_PATH]
        for env_file in env_files:
            try:
                if env_file.exists():
                    with open(env_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                k, v = line.split("=", 1)
                                k = k.strip()
                                v = v.strip().strip("'\"")
                                if k == "SMTP_HOST" and v:
                                    config["smtp_host"] = v
                                elif k == "SMTP_PORT" and v:
                                    try:
                                        config["smtp_port"] = int(v)
                                    except ValueError:
                                        pass
                                elif k == "SMTP_USER" and v and (not config["smtp_user"] or "@" in v):
                                    config["smtp_user"] = v
                                elif k == "SMTP_PASS" and v and not config["smtp_pass"]:
                                    config["smtp_pass"] = v
                                elif k == "SMTP_FROM" and v and not config["smtp_from"]:
                                    config["smtp_from"] = v
                                elif k == "SMTP_FROM_NAME" and v:
                                    config["from_name"] = v
                                elif k == "ADMIN_EMAIL" and v and not config["admin_email"]:
                                    config["admin_email"] = v
                                elif k == "AUTO_SEND_ADMIN_AUDITS" and v:
                                    config["auto_send_admin_audits"] = v.lower() in ("true", "1", "yes")
                                elif k == "AUTO_SEND_CUSTOMER_EMAILS" and v:
                                    config["auto_send_customer_emails"] = v.lower() in ("true", "1", "yes")
            except Exception as e:
                logger.warning(f"Failed to parse {env_file}: {e}")

        # 3. Check environment variables (runtime os.environ overrides)
        if os.getenv("SMTP_HOST"):
            config["smtp_host"] = os.getenv("SMTP_HOST")
        if os.getenv("SMTP_PORT"):
            try:
                config["smtp_port"] = int(os.getenv("SMTP_PORT"))
            except ValueError:
                pass
        if os.getenv("SMTP_USER"):
            config["smtp_user"] = os.getenv("SMTP_USER")
        if os.getenv("SMTP_PASS"):
            config["smtp_pass"] = os.getenv("SMTP_PASS")
        if os.getenv("SMTP_FROM"):
            config["smtp_from"] = os.getenv("SMTP_FROM")
        if os.getenv("SMTP_FROM_NAME"):
            config["from_name"] = os.getenv("SMTP_FROM_NAME")
        if os.getenv("ADMIN_EMAIL"):
            config["admin_email"] = os.getenv("ADMIN_EMAIL")
        if os.getenv("AUTO_SEND_ADMIN_AUDITS"):
            config["auto_send_admin_audits"] = os.getenv("AUTO_SEND_ADMIN_AUDITS").lower() in ("true", "1", "yes")
        if os.getenv("AUTO_SEND_CUSTOMER_EMAILS"):
            config["auto_send_customer_emails"] = os.getenv("AUTO_SEND_CUSTOMER_EMAILS").lower() in ("true", "1", "yes")

        # Determine if fully configured
        clean_pwd = config.get("smtp_pass", "").replace(" ", "")
        config["is_configured"] = bool(config.get("smtp_host") and config.get("smtp_user") and clean_pwd and "@" in config.get("smtp_user", ""))

        # Sync os.environ for other modules if configured
        if config["is_configured"]:
            os.environ["SMTP_HOST"] = str(config.get("smtp_host", "smtp.gmail.com"))
            os.environ["SMTP_PORT"] = str(config.get("smtp_port", 587))
            os.environ["SMTP_USER"] = str(config.get("smtp_user", ""))
            os.environ["SMTP_PASS"] = str(config.get("smtp_pass", ""))
            os.environ["ADMIN_EMAIL"] = str(config.get("admin_email", ""))

        return config

    @classmethod
    def save_email_config(cls, new_config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Persists email configuration to storage/config/email_config.json and updates .env file.
        """
        try:
            # 1. Save JSON
            cls.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(cls.CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(new_config, f, indent=2)

            # 2. Update/create .env file
            env_content = (
                f"# Mishika Fashion Boutique - Automated Email Settings\n"
                f"SMTP_HOST={new_config.get('smtp_host', 'smtp.gmail.com')}\n"
                f"SMTP_PORT={new_config.get('smtp_port', 587)}\n"
                f"SMTP_USER={new_config.get('smtp_user', '')}\n"
                f"SMTP_PASS={new_config.get('smtp_pass', '')}\n"
                f"SMTP_FROM={new_config.get('smtp_from', new_config.get('smtp_user', ''))}\n"
                f"SMTP_FROM_NAME={new_config.get('from_name', 'Mishika Fashion Boutique Concierge')}\n"
                f"ADMIN_EMAIL={new_config.get('admin_email', '')}\n"
                f"AUTO_SEND_ADMIN_AUDITS={'true' if new_config.get('auto_send_admin_audits') else 'false'}\n"
                f"AUTO_SEND_CUSTOMER_EMAILS={'true' if new_config.get('auto_send_customer_emails') else 'false'}\n"
            )
            with open(cls.ENV_PATH, "w", encoding="utf-8") as f:
                f.write(env_content)

            # Also set os.environ so current process has immediate access
            os.environ["SMTP_HOST"] = str(new_config.get("smtp_host", "smtp.gmail.com"))
            os.environ["SMTP_PORT"] = str(new_config.get("smtp_port", 587))
            os.environ["SMTP_USER"] = str(new_config.get("smtp_user", ""))
            os.environ["SMTP_PASS"] = str(new_config.get("smtp_pass", ""))
            os.environ["SMTP_FROM"] = str(new_config.get("smtp_from", new_config.get("smtp_user", "")))
            os.environ["ADMIN_EMAIL"] = str(new_config.get("admin_email", ""))

            logger.info("Saved automated email settings to storage and .env")
            return True, "Email settings successfully saved and activated."
        except Exception as e:
            logger.error(f"Failed to save email settings: {e}")
            return False, f"Error saving email settings: {str(e)}"

    @staticmethod
    def generate_mailto_link(to_email: str, subject: str, plain_text_body: str) -> str:
        """Generates an RFC2368 mailto: URL."""
        encoded_subject = urllib.parse.quote(subject)
        encoded_body = urllib.parse.quote(plain_text_body)
        return f"mailto:{to_email}?subject={encoded_subject}&body={encoded_body}"

    @classmethod
    def test_smtp_connection(cls, config: Dict[str, Any], to_email: Optional[str] = None) -> Tuple[bool, str]:
        """
        Tests the SMTP connection handshake and optionally sends a verification test email.
        """
        host = config.get("smtp_host", "smtp.gmail.com")
        port = int(config.get("smtp_port", 587))
        user = config.get("smtp_user", "").strip()
        pwd = config.get("smtp_pass", "").strip().replace(" ", "")  # Strip whitespace from 16-char Gmail app password
        from_name = config.get("from_name", "Mishika Fashion Boutique Concierge")
        target_email = to_email or config.get("admin_email") or user

        if not host:
            return False, "SMTP Host is missing."
        if not user:
            return False, "Gmail username / email address is missing."
        if not pwd:
            return False, "Gmail App Password is missing."
        if not target_email:
            return False, "Target test email recipient is missing."

        try:
            context = ssl.create_default_context()
            if port == 465:
                server = smtplib.SMTP_SSL(host, port, context=context, timeout=12)
            else:
                server = smtplib.SMTP(host, port, timeout=12)
                server.starttls(context=context)

            server.login(user, pwd)

            # Send a live verification test email
            test_subject = "✨ Shivi Deep Agent: Automated Email Verification Success"
            test_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
                <div style="background: #0f172a; color: #ffffff; padding: 24px; text-align: center;">
                    <h2 style="margin: 0; font-family: 'Playfair Display', Georgia, serif; letter-spacing: 1px;">MISHIKA FASHION BOUTIQUE</h2>
                    <p style="margin: 4px 0 0 0; font-size: 12px; opacity: 0.8; letter-spacing: 2px;">SHIVI AI CONCIERGE • VERIFICATION CONFIRMATION</p>
                </div>
                <div style="padding: 24px; background: #ffffff; color: #334155; line-height: 1.6;">
                    <h3 style="color: #059669; margin-top: 0;">🎉 Automated Email Gateway Connected!</h3>
                    <p>This verification email confirms that <b>Shivi Deep Agent</b> has successfully established a secure TLS connection with your Gmail account (<code>{user}</code>).</p>
                    <div style="background: #f8fafc; border-left: 4px solid #059669; padding: 12px 16px; border-radius: 6px; margin: 16px 0;">
                        <b>Verified Gateway Details:</b><br/>
                        • Host: <code>{host}:{port}</code> (STARTTLS)<br/>
                        • Dispatcher: <code>{from_name}</code><br/>
                        • Verified at: <code>{datetime.now().strftime('%B %d, %Y - %I:%M:%S %p')}</code>
                    </div>
                    <p>All autonomous dispatches (Morning Opening Briefings, Evening Closing Audits, Trending News, and Promotional Campaigns) will now deliver smoothly.</p>
                </div>
                <div style="background: #f1f5f9; padding: 12px 24px; text-align: center; font-size: 11px; color: #64748b;">
                    Sent autonomously by Shivi Deep Agent • Local BI Boutique Assistant
                </div>
            </div>
            """
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = test_subject
            msg["From"] = f"{from_name} <{user}>"
            msg["To"] = target_email
            msg.attach(MIMEText("Shivi Deep Agent email verification successful.", "plain", "utf-8"))
            msg.attach(MIMEText(test_html, "html", "utf-8"))

            server.sendmail(user, [target_email], msg.as_string())
            server.quit()
            logger.info(f"Verification test email sent successfully to {target_email}")
            return True, f"✅ Handshake successful! Verification email delivered to {target_email}."
        except smtplib.SMTPAuthenticationError as auth_err:
            msg = f"❌ Authentication failed (535): Please verify your Gmail address and ensure you are using a 16-character Google App Password (not your standard password). Error: {auth_err}"
            logger.error(msg)
            return False, msg
        except Exception as e:
            msg = f"❌ SMTP Connection Error: {str(e)}"
            logger.error(msg)
            return False, msg

    @classmethod
    def send_smtp_email(
        cls,
        to_email: str,
        subject: str,
        html_body: str,
        plain_body: Optional[str] = None,
        attachment_bytes: Optional[bytes] = None,
        attachment_name: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Sends a live HTML email (with optional PDF attachment) via standard SMTP server.
        Falls back to stored/environment configuration if credentials are not passed.
        """
        conf = cls.load_email_config()
        host = conf.get("smtp_host", "smtp.gmail.com") if smtp_host is None else smtp_host
        port = int(conf.get("smtp_port", 587) if smtp_port is None else smtp_port)
        user = conf.get("smtp_user", "") if smtp_user is None else smtp_user
        raw_pwd = conf.get("smtp_pass", "") if smtp_password is None else smtp_password
        pwd = raw_pwd.strip().replace(" ", "")
        sender = (conf.get("smtp_from", user) if from_email is None else from_email) or user
        disp_name = (conf.get("from_name", "Mishika Fashion Boutique Concierge") if from_name is None else from_name)

        if not host or not user or not pwd:
            return False, "SMTP credentials not configured. Please enter your Gmail address & App Password in the Settings tab."

        try:
            # Construct message with mixed multipart if attachment is present
            if attachment_bytes and attachment_name:
                msg = MIMEMultipart("mixed")
                msg["Subject"] = subject
                msg["From"] = f"{disp_name} <{sender}>"
                msg["To"] = to_email

                alt_part = MIMEMultipart("alternative")
                if plain_body:
                    alt_part.attach(MIMEText(plain_body, "plain", "utf-8"))
                if html_body:
                    alt_part.attach(MIMEText(html_body, "html", "utf-8"))
                msg.attach(alt_part)

                pdf_part = MIMEApplication(attachment_bytes, Name=attachment_name)
                pdf_part["Content-Disposition"] = f'attachment; filename="{attachment_name}"'
                msg.attach(pdf_part)
            else:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"{disp_name} <{sender}>"
                msg["To"] = to_email

                if plain_body:
                    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
                if html_body:
                    msg.attach(MIMEText(html_body, "html", "utf-8"))

            context = ssl.create_default_context()
            if port == 465:
                with smtplib.SMTP_SSL(host, port, context=context, timeout=15) as server:
                    server.login(user, pwd)
                    server.sendmail(sender, [to_email], msg.as_string())
            else:
                with smtplib.SMTP(host, port, timeout=15) as server:
                    server.starttls(context=context)
                    server.login(user, pwd)
                    server.sendmail(sender, [to_email], msg.as_string())

            logger.info(f"Live SMTP email sent successfully to {to_email}")
            return True, f"Email delivered successfully to {to_email} via {host}"
        except Exception as e:
            logger.error(f"Live SMTP dispatch error: {e}")
            return False, f"SMTP Error: {str(e)}"

