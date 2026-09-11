"""
src/server/routes/reports.py
============================
FastAPI route controller for Boardroom Executive PDF Reports and Presentation Exports.

Why Required:
- Luxury boutique owners, general managers, and board members need high-resolution,
  beautifully formatted reports (Morning Opening Briefings and Evening Closing Financial Audits)
  for daily operations and reconciliation.
- Exposes downloadable binary PDF streams generated dynamically via ReportLab and PowerPoint presentation decks.
"""

from fastapi import APIRouter, HTTPException
from starlette.responses import Response, FileResponse
from datetime import datetime
from pathlib import Path

from src.data.db_manager import DatabaseManager
from src.reporting.pdf_builder import generate_opening_briefing_pdf, generate_closing_audit_pdf
from src.core.constants import BrandDefaults

router = APIRouter(prefix="/api/reports", tags=["Boardroom Reports & Exports"])


def get_db() -> DatabaseManager:
    """
    Dependency provider for DatabaseManager.
    
    Returns:
        DatabaseManager: Initialized SQLite database manager.
    """
    return DatabaseManager()


@router.get("/opening-pdf")
def download_opening_briefing_pdf():
    """
    Generates and streams the official Mishika Luxury Boutique Opening Briefing PDF.
    
    Working:
    - Queries active inventory matrices, broken curves, and upcoming patron birthdays from SQLite.
    - Compiles an executive two-page boardroom PDF using ReportLab with custom color palettes.
    - Streams raw bytes as an `application/pdf` attachment.
    
    Why Required:
    - Delivered every morning to prepare sales associates, highlight low-stock styles,
      and flag VIP patron appointments before store doors unlock.
    """
    db = get_db()
    try:
        pdf_bytes = generate_opening_briefing_pdf(db)
        filename = f"MishikaBoutique_Opening_Briefing_{datetime.now().strftime('%Y%m%d')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Opening Briefing PDF: {e}")


@router.get("/closing-pdf")
def download_closing_audit_pdf():
    """
    Generates and streams the official Mishika Luxury Boutique Evening Closing Audit PDF.
    
    Working:
    - Reconciles daily transactional revenue, cost-of-goods-sold (COGS), net gross profit,
      and cash register drawers from `sales_ledger`.
    - Produces a timestamped audit PDF ready for accounting and ownership sign-off.
    
    Why Required:
    - Guarantees financial accountability and daily margin tracking at the close of retail hours.
    """
    db = get_db()
    try:
        pdf_bytes = generate_closing_audit_pdf(db)
        filename = f"MishikaBoutique_Closing_Audit_{datetime.now().strftime('%Y%m%d')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Closing Audit PDF: {e}")


@router.get("/presentation-pptx")
def download_presentation_deck():
    """
    Streams the official Boardroom Presentation slide deck (.pptx).
    
    Working:
    - Locates the pre-generated executive deck file in storage exports or root.
    - Streams file with PowerPoint MIME type headers.
    
    Why Required:
    - Enables store leadership to present the boutique's BI architecture and results
      to external stakeholders and investors.
    """
    p1 = Path("storage/exports/Boutique_BI_Assistant_Presentation.pptx")
    p2 = Path("Boutique_BI_Assistant_Presentation.pptx")
    
    target_path = p1 if p1.exists() else (p2 if p2.exists() else None)
    if not target_path:
        raise HTTPException(status_code=404, detail="Presentation deck file not found.")

    return FileResponse(
        path=str(target_path),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename="Mishika_Boutique_Executive_Presentation.pptx"
    )
