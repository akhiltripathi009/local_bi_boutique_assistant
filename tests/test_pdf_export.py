from src.reporting.pdf_builder import generate_chat_transcript_pdf, generate_enterprise_pdf

def test_chat_transcript_pdf_generation():
    """Tests chat export to PDF with metadata and multi-turn bubbles."""
    messages = [
        {"role": "user", "content": "What is our Competitor Price Index?"},
        {"role": "assistant", "content": "Our store CPI is currently 96.4%, with ,420 uncaptured margin opportunity."}
    ]
    meta = {
        "persona": "Pricing & Margin Strategist",
        "cpi": 96.4,
        "margin_gap": 1420.0
    }
    pdf_bytes = generate_chat_transcript_pdf(messages, meta)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")

def test_enterprise_pdf_generation(test_db):
    """Tests enterprise audit PDF generation with mock database."""
    pdf_bytes = generate_enterprise_pdf(test_db, report_type="weekly")
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
