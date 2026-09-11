"""
tests/test_ui_and_agent_verification.py
========================================
Comprehensive verification of all Shivi Deep Agent UI elements and routes.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from src.server.app import app

client = TestClient(app)

# 1. Test index.html contains all required UI elements
resp = client.get("/")
assert resp.status_code == 200, f"Index failed: {resp.status_code}"
html = resp.text

required_elements = [
    "agent-status-strip",
    "agent-metric-memories",
    "agent-metric-approvals",
    "agent-dispatchers-grid",
    "morning_opening",
    "evening_closing",
    "fashion_news",
    "campaign_launch",
    "restock",
    "birthday",
    "agent-pdf-banner",
    "agent-pdf-download-btn",
    "agent-subtabs-nav",
    "subtab-client-previews",
    "subtab-email-gateway",
    "subtab-guardrails-inspector",
    "agent-news-topic-select",
    "btn-refresh-news",
    "agent-news-status-banner",
    "agent-news-headlines-list",
    "agent-preview-recipient-select",
    "agent-email-preview-body",
    "btn-agent-send-smtp",
    "btn-agent-mailto",
    "agent-wa-bubble-text",
    "btn-agent-wa-me",
    "agent-test-my-phone",
    "agent-test-my-email",
    "agent-comms-table-tbody",
    "agent-email-gateway-banner",
    "email-cfg-user",
    "email-cfg-pass",
    "email-cfg-admin",
    "btn-save-email-config",
    "btn-run-email-test",
    "agent-pii-input",
    "agent-pii-output",
    "agent-discount-input",
    "agent-discount-slider",
    "agent-discount-feedback",
    "btn-toggle-theme"
]

for el in required_elements:
    assert el in html, f"Missing element in index.html: {el}"

print(f"✓ Verified all {len(required_elements)} DOM IDs and elements in index.html")

# 2. Test js/app.js loads
resp_js = client.get("/js/app.js")
assert resp_js.status_code == 200
js = resp_js.text
functions = [
    "initTheme",
    "setTheme",
    "toggleTheme",
    "switchAgentSubTab",
    "loadAgentData",
    "triggerAgentAction",
    "loadAgentNewsPreview",
    "onAgentTopicChanged",
    "refreshAgentNews",
    "onAgentRecipientChanged",
    "renderAgentRecipientPreview",
    "sendCurrentRecipientEmail",
    "sendBatchEmails",
    "launchTestMyWhatsApp",
    "sendTestMyEmail",
    "loadAgentCommunications",
    "loadAgentEmailConfig",
    "saveEmailConfiguration",
    "runEmailConnectionTest",
    "runPIIRedaction",
    "runDiscountValidation"
]

for fn in functions:
    assert fn in js, f"Missing function in app.js: {fn}"

print(f"✓ Verified all {len(functions)} Shivi controller functions in app.js")

# 3. Test API status and metrics
status = client.get("/api/agent/status").json()
assert status["success"] is True
assert status["skills_count"] == 4
assert status["tools_count"] == 5
print("✓ Verified /api/agent/status metrics: 4 skills, 5 tools")

# 4. Test API news preview
news = client.get("/api/agent/news-preview").json()
assert news["success"] is True
assert len(news["messages"]) > 0
print(f"✓ Verified /api/agent/news-preview with {len(news['messages'])} messages")

# 5. Test PII redaction
pii = client.post("/api/agent/guardrails/redact-pii", json={"text": "Call me at +1-555-0101 or test@example.com"}).json()
assert pii["success"] is True
assert "+1-555-0101" not in pii["sanitized_text"]
print("✓ Verified /api/agent/guardrails/redact-pii")

# 6. Test discount validation
disc = client.post("/api/agent/guardrails/validate-discount", json={"discount_pct": 65.0}).json()
assert disc["is_safe"] is False
assert disc["effective_discount"] == 50.0
print("✓ Verified /api/agent/guardrails/validate-discount clamped to 50.0%")

print("\n★ ALL SHIVI DEEP AGENT VERIFICATION CHECKS PASSED!")
