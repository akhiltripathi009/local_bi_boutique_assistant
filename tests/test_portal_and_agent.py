"""
tests/test_portal_and_agent.py
==============================
Automated tests for:
1. Stock Transfer (Shop ⇄ Warehouse isolation).
2. Add New Product to catalog and stock.
3. Procurement Ordering in any quantity.
4. Custom Promotional Campaigns.
5. 20 Dummy Customers and Sale Attribution.
6. Shivi Deep Agent Opening/Closing routines, news, campaigns, sandbox, guardrails, and steering.
"""

from src.core.catalog import CATALOG
from src.deep_agent.orchestrator import ShiviDeepAgent
from src.deep_agent.guardrails import PIIGuardrail, DiscountSafetyGuardrail, ContentVoiceGuardrail
from src.deep_agent.delivery import EmailDeliveryService

def test_stock_transfers(db):
    """Tests bidirectional stock transfers and location isolation."""
    # Ensure warehouse stock is isolated
    shop_before = db.get_current_stock_on_hand().get("P001", 0)
    wh_before = db.get_warehouse_stock_on_hand().get("P001", 0)

    # 1. Transfer from Shop to Warehouse
    ok, msg = db.transfer_stock("P001", "M", "shop", "warehouse", 4)
    assert ok is True
    shop_after1 = db.get_current_stock_on_hand().get("P001", 0)
    wh_after1 = db.get_warehouse_stock_on_hand().get("P001", 0)
    assert shop_after1 == shop_before - 4
    assert wh_after1 == wh_before + 4

    # 2. Transfer from Warehouse to Shop
    ok2, msg2 = db.transfer_stock("P001", "M", "warehouse", "shop", 2)
    assert ok2 is True
    shop_after2 = db.get_current_stock_on_hand().get("P001", 0)
    wh_after2 = db.get_warehouse_stock_on_hand().get("P001", 0)
    assert shop_after2 == shop_after1 + 2
    assert wh_after2 == wh_after1 - 2

    # 3. Prevent transferring more than available
    fail_ok, fail_msg = db.transfer_stock("P001", "M", "shop", "warehouse", 9999)
    assert fail_ok is False
    assert "Insufficient stock" in fail_msg

    # 4. Check transfer log
    transfers_df = db.get_stock_transfers(limit=5)
    assert not transfers_df.empty
    assert len(transfers_df) >= 2


def test_add_new_product(db):
    """Tests dynamic product addition into catalog and inventory tables."""
    new_pid = "P999"
    ok, msg = db.add_new_product(
        product_id=new_pid,
        name="Cashmere Opera Coat",
        cost=85.0,
        price=295.0,
        color="#1a1a2e",
        category="Outerwear",
        initial_shop_stock={"S": 5, "M": 8, "L": 6, "XL": 4},
        initial_warehouse_stock={"S": 10, "M": 15, "L": 12, "XL": 8}
    )
    assert ok is True
    assert new_pid in CATALOG
    assert CATALOG[new_pid]["name"] == "Cashmere Opera Coat"

    # Verify stock in DB
    shop_stock = db.get_current_stock_on_hand()
    wh_stock = db.get_warehouse_stock_on_hand()
    assert shop_stock.get(new_pid) == 23
    assert wh_stock.get(new_pid) == 45


def test_procurement_order(db):
    """Tests ordering products in any quantity with destination routing."""
    wh_before = db.get_warehouse_stock_on_hand().get("P002", 0)
    ok, msg = db.order_product(
        product_id="P002",
        quantity=20,
        destination="warehouse",
        unit_cost=22.0,
        notes="Urgent replenishment"
    )
    assert ok is True
    wh_after = db.get_warehouse_stock_on_hand().get("P002", 0)
    assert wh_after == wh_before + 20

    # Verify purchase ledger record
    purchases = db.fetch_logs("purchase_ledger", limit=1)
    assert not purchases.empty
    assert purchases.iloc[0]["product_id"] == "P002"
    assert purchases.iloc[0]["quantity"] == 20


def test_campaigns(db):
    """Tests creating, retrieving, and updating promotional campaigns."""
    ok, msg = db.create_campaign(
        name="Winter Gala Markdown",
        description="Exclusive 30% discount on silk and outerwear",
        discount_pct=30.0,
        target_category="Outerwear",
        banner_tagline="Gala Splendor"
    )
    assert ok is True

    camps = db.get_all_campaigns()
    assert not camps.empty
    matched = camps[camps["name"] == "Winter Gala Markdown"]
    assert not matched.empty
    cid = int(matched.iloc[0]["id"])

    # Update status
    upd = db.update_campaign_status(cid, "Paused")
    assert upd is True


def test_20_dummy_customers_and_sales_attribution(db):
    """Ensures 20 dummy customers exist and customer attribution tracks correctly."""
    cust_df = db.get_all_customers()
    assert len(cust_df) >= 20
    first_cust = cust_df.iloc[0]
    cid = int(first_cust["id"])
    initial_spend = float(first_cust["total_spend"])

    # Record a customer-attributed sale
    db.save_sale({
        "timestamp": "2026-09-10 10:00:00",
        "product_id": "P001",
        "product_name": "Linen Wrap Dress",
        "quantity": 1,
        "unit_price": 95.0,
        "unit_cost": 35.0,
        "total_revenue": 95.0,
        "total_cost": 35.0,
        "gross_profit": 60.0,
        "is_promotional": 0,
        "campaign_name": "VIP Walk-in",
        "customer_id": cid,
        "customer_name": first_cust["name"],
        "customer_email": first_cust["email"],
        "customer_phone": first_cust["phone"],
        "size_purchased": "S",
        "channel": "In-Store Boutique"
    })

    # Verify customer spend updated
    updated_cust = db.get_customer_by_id(cid)
    assert updated_cust is not None
    assert updated_cust["total_spend"] == initial_spend + 95.0

    # Verify purchase history
    history = db.get_customer_purchase_history(cid)
    assert not history.empty
    assert history.iloc[0]["product_name"] == "Linen Wrap Dress"


def test_shivi_deep_agent_tasks(db):
    """Tests all autonomous routines of Shivi Deep Agent."""
    agent = ShiviDeepAgent(db)

    # 1. Opening Routine
    open_res = agent.run_opening_routine()
    assert open_res["success"] is True
    assert len(open_res["pdf_bytes"]) > 1000
    assert "Morning Opening Briefing" in open_res["summary"]

    # 2. Closing Routine
    close_res = agent.run_closing_routine()
    assert close_res["success"] is True
    assert len(close_res["pdf_bytes"]) > 1000

    # 3. Trending Fashion News Dispatch (Dry-run)
    news_res = agent.dispatch_trending_fashion_news(dry_run=True)
    assert news_res["success"] is True
    assert len(news_res["messages"]) > 0

    # 4. Campaign Launch Broadcast (Dry-run)
    camp_res = agent.broadcast_campaign_launch(dry_run=True)
    assert camp_res["success"] is True
    assert len(camp_res["messages"]) > 0

    # 5. Back-in-Stock Alerts (Dry-run)
    stock_res = agent.check_and_notify_back_in_stock(dry_run=True)
    assert stock_res["success"] is True

    # 6. Birthday Perks (Dry-run)
    bday_res = agent.dispatch_birthday_perks(days_ahead=365, dry_run=True)
    assert bday_res["success"] is True

    # 7. Python Sandbox
    sb_res = agent.run_sandbox_code("val = 10 * 5; print(f'Result: {val}')")
    assert sb_res["success"] is True
    assert "Result: 50" in sb_res["output"]


def test_shivi_guardrails():
    """Tests PII redaction and discount limits."""
    # PII Guardrail
    raw = "Reach Elena at elena.rostova@vogue.com or call +1-555-0101."
    sanitized = PIIGuardrail.redact_pii(raw)
    assert "elena.rostova@vogue.com" not in sanitized
    assert "+1-555-0101" not in sanitized

    # Discount Safety Guardrail
    safe_ok, safe_d, _ = DiscountSafetyGuardrail.validate_discount(25.0)
    assert safe_ok is True
    assert safe_d == 25.0

    unsafe_ok, clamped_d, _ = DiscountSafetyGuardrail.validate_discount(65.0)
    assert unsafe_ok is False
    assert clamped_d == 50.0

    # Brand Voice Guardrail
    voice_ok, _ = ContentVoiceGuardrail.validate_content("Experience fluid silk craftsmanship.")
    assert voice_ok is True
    voice_bad, _ = ContentVoiceGuardrail.validate_content("Buy our cheap knockoff trash.")
    assert voice_bad is False


def test_shivi_steering(db):
    """Tests Human-in-the-Loop steering approval queue."""
    agent = ShiviDeepAgent(db)

    # Queue an action
    qid = agent.steering.queue_action(
        action_type="test_high_impact",
        title="Test Action",
        description="Testing approval queue",
        payload={"amount": 100}
    )
    assert qid > 0

    queue = agent.steering.get_pending_queue()
    assert any(item["id"] == qid for item in queue)

    # Approve action
    appr_ok, _ = agent.steering.approve_action(qid, "Approved in test")
    assert appr_ok is True

    # Verify no longer pending
    queue_after = agent.steering.get_pending_queue()
    assert not any(item["id"] == qid for item in queue_after)
def test_automated_email_delivery():
    """Tests Gmail SMTP configuration loading, validation, and handshake safety."""
    # 0. Backup existing configuration to prevent wiping real user credentials
    orig_config = EmailDeliveryService.CONFIG_PATH.read_text(encoding="utf-8") if EmailDeliveryService.CONFIG_PATH.exists() else None
    orig_env = EmailDeliveryService.ENV_PATH.read_text(encoding="utf-8") if EmailDeliveryService.ENV_PATH.exists() else None

    try:
        # 1. Test default Gmail parameters
        conf = EmailDeliveryService.load_email_config()
        assert "smtp_host" in conf
        assert conf["smtp_host"] == "smtp.gmail.com"
        assert conf["smtp_port"] == 587

        # 2. Test saving and loading custom config
        test_conf = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "test_agent@gmail.com",
            "smtp_pass": "abcd efgh ijkl mnop",
            "smtp_from": "test_agent@gmail.com",
            "from_name": "Test Concierge",
            "admin_email": "admin_test@boutique.com",
            "auto_send_admin_audits": True,
            "auto_send_customer_emails": True
        }
        save_ok, _ = EmailDeliveryService.save_email_config(test_conf)
        assert save_ok is True

        reloaded = EmailDeliveryService.load_email_config()
        assert reloaded["smtp_user"] == "test_agent@gmail.com"
        assert reloaded["admin_email"] == "admin_test@boutique.com"
        assert reloaded["is_configured"] is True

        # 3. Test SMTP handshake failure on dummy credentials (safely caught without unhandled crash)
        conn_ok, conn_msg = EmailDeliveryService.test_smtp_connection(reloaded, to_email="admin_test@boutique.com")
        assert conn_ok is False
        assert "Authentication" in conn_msg or "SMTP" in conn_msg or "Connection" in conn_msg

        # 4. Test missing credentials guard
        unconfigured_ok, unconf_msg = EmailDeliveryService.send_smtp_email(
            to_email="test@test.com",
            subject="Test",
            html_body="<p>Test</p>",
            smtp_user="",
            smtp_password=""
        )
        assert unconfigured_ok is False
        assert "not configured" in unconf_msg

    finally:
        # 5. Restore original configuration
        import os
        for k in ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "SMTP_FROM", "ADMIN_EMAIL"]:
            os.environ.pop(k, None)

        if orig_config:
            EmailDeliveryService.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            EmailDeliveryService.CONFIG_PATH.write_text(orig_config, encoding="utf-8")
        elif EmailDeliveryService.ENV_EXAMPLE_PATH.exists():
            # If no backup existed, ensure example is copied to .env
            EmailDeliveryService.load_email_config()

        if orig_env:
            EmailDeliveryService.ENV_PATH.write_text(orig_env, encoding="utf-8")
        elif EmailDeliveryService.ENV_EXAMPLE_PATH.exists():
            import shutil
            shutil.copy(EmailDeliveryService.ENV_EXAMPLE_PATH, EmailDeliveryService.ENV_PATH)


def test_update_customer_contact(db):
    """Tests updating customer contact details and preferences."""
    cust_df = db.get_all_customers()
    assert not cust_df.empty
    cid = int(cust_df.iloc[0]["id"])
    orig_name = cust_df.iloc[0]["name"]

    # 1. Update contact details
    up_ok, up_msg = db.update_customer_contact(
        customer_id=cid,
        phone="+919876543210",
        email="updated.client@luxuryboutique.com",
        name="Elena Rostova-Updated",
        preferred_size="M",
        style_preference="Contemporary Mishika Couture",
        loyalty_tier="VIP Platinum",
        opt_in_whatsapp=1,
        opt_in_email=1
    )
    assert up_ok is True
    assert "Elena Rostova-Updated" in up_msg

    # Verify in DB
    updated = db.get_customer_by_id(cid)
    assert updated is not None
    assert updated["phone"] == "+919876543210"
    assert updated["email"] == "updated.client@luxuryboutique.com"
    assert updated["name"] == "Elena Rostova-Updated"
    assert updated["preferred_size"] == "M"
    assert updated["style_preference"] == "Contemporary Mishika Couture"

    # 2. Test non-existent customer
    fail_ok, fail_msg = db.update_customer_contact(
        customer_id=999999,
        phone="+12345",
        email="fake@fake.com"
    )
    assert fail_ok is False
    assert "not found" in fail_msg


def test_live_fashion_news_and_default_fallback(db):
    """Tests internet fashion news fetching and seamless default news fallback."""
    from unittest.mock import patch
    import urllib.error
    from src.deep_agent.subagents import TrendHunterSubagent

    th = TrendHunterSubagent(db)

    # 1. Test live news fetch (or clean fallback if offline environment)
    articles, src_label, is_live = th.fetch_live_fashion_news(limit=5)
    assert len(articles) >= 1
    assert "title" in articles[0]
    assert "source" in articles[0]

    # 2. Test draft generation
    drafts = th.curate_and_draft_fashion_news()
    assert len(drafts) >= 1
    assert "email_subject" in drafts[0]
    assert "email_html" in drafts[0]
    assert "whatsapp_text" in drafts[0]
    assert "news_source" in drafts[0]

    # 3. Test guaranteed fallback to default news upon network error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        fb_articles, fb_label, fb_is_live = th.fetch_live_fashion_news(limit=5)
        assert fb_is_live is False
        assert "Default Curated News" in fb_label
        assert len(fb_articles) == 5
        assert fb_articles[0]["source"] == "Mishika Luxury Curated"

        # Ensure drafts generate seamlessly with default news
        fb_drafts = th.curate_and_draft_fashion_news()
        assert len(fb_drafts) >= 1
        assert fb_drafts[0]["is_live_internet"] is False
        assert "DEFAULT CURATED" in fb_drafts[0]["email_html"]


