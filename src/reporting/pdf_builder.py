import re
"""
pdf_generator.py
Generates boardroom-ready Enterprise PDF reports for Sales, Purchases, and Inventory.
Supports Daily, Weekly, and Complete (All-Time) audits with professional typography,
executive scorecards, two-pass page numbering, and detailed financial tables.
"""
import io
import os
import sqlite3
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, HRFlowable, Flowable, PageBreak
)
from reportlab.pdfgen import canvas
try:
    from src.core.logger import setup_logging
    from src.core.catalog import CATALOG
    from src.analytics.competitor import CompetitorAnalyzer
    from src.core.config import DB_PATH, EXPORTS_DIR
except ImportError:
    from logger_config import setup_logging
    # CATALOG imported at top-level
    # CompetitorAnalyzer imported at top-level
    DB_PATH = "boutique_bi.db"
    EXPORTS_DIR = "."


logger = setup_logging("pdf_generator")


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas renderer to compute total page count and draw
    a professional running footer on every page ("Page X of Y").
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_running_footer(num_pages)
            super().showPage()
        super().save()

    def draw_running_footer(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Footer divider line
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(36, 36, self._pagesize[0] - 36, 36)

        # Footer text
        self.drawString(36, 24, "Mishika Fashion LUXURY BOUTIQUE  •  CONFIDENTIAL & PROPRIETARY AUDIT REPORT")
        self.drawRightString(self._pagesize[0] - 36, 24, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def fetch_report_datasets(db, report_type: str) -> Dict[str, Any]:
    """
    Queries sales and procurement ledgers from SQLite filtered by the specified timeframe.
    
    Args:
        db: DatabaseManager instance.
        report_type (str): 'daily', 'weekly', or 'complete'.

    Returns:
        Dict[str, Any]: Extracted datasets, metadata, and financial KPI metrics.
    """
    conn = sqlite3.connect(db.db_path)
    report_type = report_type.lower().strip()

    # Determine reference date bounds from the database
    latest_sale_date_row = pd.read_sql("SELECT MAX(date(timestamp)) as max_date FROM sales_ledger", conn)
    max_date_str = latest_sale_date_row.iloc[0]['max_date'] if not latest_sale_date_row.empty and latest_sale_date_row.iloc[0]['max_date'] else datetime.now().strftime("%Y-%m-%d")
    max_date = datetime.strptime(max_date_str, "%Y-%m-%d")

    if report_type == "daily":
        start_date_str = max_date.strftime("%Y-%m-%d")
        end_date_str = max_date.strftime("%Y-%m-%d")
        period_title = f"Daily Operations Audit ({max_date.strftime('%B %d, %Y')})"
        sales_query = "SELECT * FROM sales_ledger WHERE date(timestamp) = ? ORDER BY id DESC"
        purchases_query = "SELECT * FROM purchase_ledger WHERE date(timestamp) = ? ORDER BY id DESC"
        sales_df = pd.read_sql(sales_query, conn, params=(start_date_str,))
        purchases_df = pd.read_sql(purchases_query, conn, params=(start_date_str,))
        # If no purchases on that exact single day, query last 3 days for context
        if purchases_df.empty:
            purchases_df = pd.read_sql("SELECT * FROM purchase_ledger ORDER BY id DESC LIMIT 15", conn)
    elif report_type == "weekly":
        start_date = max_date - timedelta(days=6)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = max_date.strftime("%Y-%m-%d")
        period_title = f"Weekly Operations Audit ({start_date.strftime('%b %d')} - {max_date.strftime('%b %d, %Y')})"
        sales_query = "SELECT * FROM sales_ledger WHERE date(timestamp) BETWEEN ? AND ? ORDER BY id DESC"
        purchases_query = "SELECT * FROM purchase_ledger WHERE date(timestamp) BETWEEN ? AND ? ORDER BY id DESC"
        sales_df = pd.read_sql(sales_query, conn, params=(start_date_str, end_date_str))
        purchases_df = pd.read_sql(purchases_query, conn, params=(start_date_str, end_date_str))
    elif report_type in ("monthly", "month"):
        start_date = max_date - timedelta(days=29)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = max_date.strftime("%Y-%m-%d")
        period_title = f"Monthly Strategic Operations Audit ({start_date.strftime('%b %d')} - {max_date.strftime('%b %d, %Y')})"
        sales_query = "SELECT * FROM sales_ledger WHERE date(timestamp) BETWEEN ? AND ? ORDER BY id DESC"
        purchases_query = "SELECT * FROM purchase_ledger WHERE date(timestamp) BETWEEN ? AND ? ORDER BY id DESC"
        sales_df = pd.read_sql(sales_query, conn, params=(start_date_str, end_date_str))
        purchases_df = pd.read_sql(purchases_query, conn, params=(start_date_str, end_date_str))
    else:  # Complete / All-Time
        min_date_row = pd.read_sql("SELECT MIN(date(timestamp)) as min_date FROM sales_ledger", conn)
        min_date_str = min_date_row.iloc[0]['min_date'] if not min_date_row.empty and min_date_row.iloc[0]['min_date'] else "2026-01-01"
        start_date_str = min_date_str
        end_date_str = max_date_str
        period_title = f"Comprehensive Historical Audit ({min_date_str} to {max_date_str})"
        sales_df = pd.read_sql("SELECT * FROM sales_ledger ORDER BY id DESC", conn)
        purchases_df = pd.read_sql("SELECT * FROM purchase_ledger ORDER BY id DESC", conn)

    # Current stock on hand & controls
    inventory_dict = db.get_current_stock_on_hand()
    circuit_controls = db.get_all_circuit_controls()
    broken_curves = db.calculate_dynamic_broken_curves()
    competitor_df = db.fetch_dynamic_competitor_pricing()
    conn.close()

    # Calculate Key Financial Metrics
    total_rev = float(sales_df['total_revenue'].sum()) if not sales_df.empty else 0.0
    total_cogs = float(sales_df['total_cost'].sum()) if not sales_df.empty else 0.0
    gross_profit = float(sales_df['gross_profit'].sum()) if not sales_df.empty else 0.0
    margin_pct = (gross_profit / total_rev * 100) if total_rev > 0 else 54.2
    total_units_sold = int(sales_df['quantity'].sum()) if not sales_df.empty else 0
    total_units_restocked = int(purchases_df['quantity'].sum()) if not purchases_df.empty else 0
    total_restock_spend = float(purchases_df['total_cost'].sum()) if not purchases_df.empty else 0.0

    # Top selling merchandise aggregation
    if not sales_df.empty:
        top_merch = sales_df.groupby(["product_id", "product_name"]).agg(
            units_sold=('quantity', 'sum'),
            revenue=('total_revenue', 'sum'),
            profit=('gross_profit', 'sum')
        ).reset_index()
        top_merch['margin_pct'] = (top_merch['profit'] / top_merch['revenue'] * 100).round(1)
        top_merch = top_merch.sort_values(by="revenue", ascending=False).head(10)
    else:
        top_merch = pd.DataFrame(columns=["product_id", "product_name", "units_sold", "revenue", "profit", "margin_pct"])

    return {
        "report_type": report_type,
        "period_title": period_title,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "sales_df": sales_df,
        "purchases_df": purchases_df,
        "top_merch": top_merch,
        "inventory_dict": inventory_dict,
        "circuit_controls": circuit_controls,
        "broken_curves": broken_curves,
        "competitor_df": competitor_df,
        "metrics": {
            "total_revenue": total_rev,
            "total_cogs": total_cogs,
            "gross_profit": gross_profit,
            "margin_pct": margin_pct,
            "units_sold": total_units_sold,
            "units_restocked": total_units_restocked,
            "restock_spend": total_restock_spend,
            "transaction_count": len(sales_df),
            "restock_count": len(purchases_df)
        }
    }


def generate_enterprise_pdf(db, report_type: str = "weekly", ai_commentary: Optional[str] = None) -> bytes:
    """
    Compiles an executive-level PDF report from SQLite data into an in-memory bytes stream.
    Supports embedding local Ollama AI executive commentary and strategic recommendations.
    
    Args:
        db: Initialized DatabaseManager instance.
        report_type (str): 'daily', 'weekly', 'monthly', or 'complete'.
        ai_commentary (str, optional): Autonomous LLM executive summary and action items.
        
    Returns:
        bytes: Raw PDF document bytes ready for streaming download.
    """
    data = fetch_report_datasets(db, report_type)
    m = data["metrics"]

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    # Custom Luxury Brand Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a")
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569")
    )
    section_h2 = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=14,
        spaceAfter=6
    )
    card_label_style = ParagraphStyle(
        'CardLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#64748b")
    )
    card_value_style = ParagraphStyle(
        'CardVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=17,
        textColor=colors.HexColor("#0f172a")
    )
    card_sub_style = ParagraphStyle(
        'CardSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#94a3b8")
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1e293b")
    )
    cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0f172a")
    )
    cell_right = ParagraphStyle(
        'TableCellRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        alignment=2,
        textColor=colors.HexColor("#1e293b")
    )
    cell_right_bold = ParagraphStyle(
        'TableCellRightBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        alignment=2,
        textColor=colors.HexColor("#0f172a")
    )
    th_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.white
    )
    th_right = ParagraphStyle(
        'TableHeaderRight',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        alignment=2,
        textColor=colors.white
    )

    story = []

    # ==========================================
    # 1. LUXURY LETTERHEAD & REPORT METADATA HEADER
    # ==========================================
    gen_time = datetime.now().strftime("%b %d, %Y - %H:%M:%S")
    report_code = f"AUD-{data['report_type'].upper()}-{datetime.now().strftime('%Y%m%d%H%M')}"

    header_left = [
        Paragraph("Mishika Fashion LUXURY BOUTIQUE", ParagraphStyle('BrandTag', fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor('#d97706'), leading=10)),
        Paragraph("Executive Operations & Audit Report", title_style),
        Paragraph(data["period_title"], subtitle_style),
    ]

    header_right = [
        Paragraph(f"<b>Report Reference:</b> {report_code}", subtitle_style),
        Paragraph(f"<b>Audit Generated:</b> {gen_time}", subtitle_style),
        Paragraph("<b>Classification:</b> Executive Confidential", subtitle_style)
    ]

    header_table = Table(
        [[header_left, header_right]],
        colWidths=[330, 210]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e293b"), spaceAfter=12))

    # ==========================================
    # 2. EXECUTIVE FINANCIAL SCORECARD (4 KPI CARDS)
    # ==========================================
    story.append(Paragraph("1. Executive Financial Scorecard", section_h2))

    rev_card = [
        Paragraph("GROSS SALES REVENUE", card_label_style),
        Spacer(1, 2),
        Paragraph(f"${m['total_revenue']:,.2f}", card_value_style),
        Paragraph(f"{m['transaction_count']:,} Audited Transactions", card_sub_style)
    ]
    cogs_card = [
        Paragraph("COST OF GOODS (COGS)", card_label_style),
        Spacer(1, 2),
        Paragraph(f"${m['total_cogs']:,.2f}", card_value_style),
        Paragraph(f"{m['units_sold']:,} Total Units Sold", card_sub_style)
    ]
    profit_card = [
        Paragraph("NET GROSS PROFIT", card_label_style),
        Spacer(1, 2),
        Paragraph(f"${m['gross_profit']:,.2f}", card_value_style),
        Paragraph(f"Realized Margin: <b>{m['margin_pct']:.1f}%</b>", card_sub_style)
    ]
    restock_card = [
        Paragraph("SUPPLY CHAIN REPLENISHMENT", card_label_style),
        Spacer(1, 2),
        Paragraph(f"+{m['units_restocked']:,} Units", card_value_style),
        Paragraph(f"Procurement Spend: ${m['restock_spend']:,.2f}", card_sub_style)
    ]

    card_data = [[rev_card, cogs_card, profit_card, restock_card]]
    card_table = Table(card_data, colWidths=[135, 135, 135, 135])
    card_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(card_table)
    story.append(Spacer(1, 14))

    # Dynamic section index tracker
    s_idx = 2

    # ==========================================
    # 2.5 AI EXECUTIVE STRATEGIC COMMENTARY (IF PROVIDED)
    # ==========================================
    if ai_commentary and ai_commentary.strip():
        story.append(Paragraph(f"{s_idx}. AI Executive Strategic Synthesis (Local Ollama Intelligence)", section_h2))
        s_idx += 1

        ai_tag_style = ParagraphStyle(
            'AITag',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#4338ca")
        )
        ai_head_style = ParagraphStyle(
            'AIHead',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=6,
            spaceAfter=2
        )
        ai_p_style = ParagraphStyle(
            'AIPara',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11.5,
            textColor=colors.HexColor("#334155"),
            spaceBefore=2,
            spaceAfter=3
        )
        ai_bullet_style = ParagraphStyle(
            'AIBull',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11.5,
            textColor=colors.HexColor("#1e293b"),
            leftIndent=10,
            spaceBefore=1,
            spaceAfter=2
        )

        ai_flowables = [
            Paragraph("<b>AUTONOMOUS EXECUTIVE SYNTHESIS & STRATEGIC RECOMMENDATIONS</b>", ai_tag_style),
            Spacer(1, 3),
            HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#c7d2fe"), spaceAfter=6)
        ]

        for line in ai_commentary.splitlines():
            s = line.strip()
            if not s:
                continue
            s_fmt = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', s)
            if s_fmt.startswith("### "):
                title = s_fmt.replace("### ", "").strip()
                ai_flowables.append(Paragraph(f"<b>{title}</b>", ai_head_style))
            elif s_fmt.startswith(("- ", "* ", "• ")):
                bullet_text = s_fmt[2:].strip()
                ai_flowables.append(Paragraph(f"&bull; {bullet_text}", ai_bullet_style))
            else:
                ai_flowables.append(Paragraph(s_fmt, ai_p_style))

        c_table = Table([[ai_flowables]], colWidths=[540])
        c_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ('LINEBEFORE', (0, 0), (0, -1), 3.5, colors.HexColor("#4f46e5")),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(c_table)
        story.append(Spacer(1, 14))

    # ==========================================
    # 3. MERCHANDISE SALES PERFORMANCE TABLE
    # ==========================================
    story.append(Paragraph(f"{s_idx}. Top Merchandise Sales & Profitability Breakdown", section_h2))
    s_idx += 1

    sales_headers = [
        Paragraph("Rank", th_style),
        Paragraph("Product Style Name", th_style),
        Paragraph("Units Sold", th_right),
        Paragraph("Gross Revenue", th_right),
        Paragraph("Gross Profit", th_right),
        Paragraph("Margin %", th_right)
    ]
    table_rows = [sales_headers]

    top_merch_df = data["top_merch"]
    if not top_merch_df.empty:
        for idx, row in enumerate(top_merch_df.itertuples(), 1):
            table_rows.append([
                Paragraph(f"#{idx}", cell_style),
                Paragraph(f"<b>{row.product_name}</b> <font color='#64748b'>({row.product_id})</font>", cell_style),
                Paragraph(f"{row.units_sold:,}", cell_right),
                Paragraph(f"${row.revenue:,.2f}", cell_right_bold),
                Paragraph(f"${row.profit:,.2f}", cell_right),
                Paragraph(f"{row.margin_pct:.1f}%", cell_right_bold)
            ])
        # Summary Total Row
        table_rows.append([
            Paragraph("TOTAL", cell_bold),
            Paragraph("<b>Top Active Styles Combined</b>", cell_bold),
            Paragraph(f"<b>{top_merch_df['units_sold'].sum():,}</b>", cell_right_bold),
            Paragraph(f"<b>${top_merch_df['revenue'].sum():,.2f}</b>", cell_right_bold),
            Paragraph(f"<b>${top_merch_df['profit'].sum():,.2f}</b>", cell_right_bold),
            Paragraph(f"<b>{(top_merch_df['profit'].sum() / top_merch_df['revenue'].sum() * 100):.1f}%</b>", cell_right_bold)
        ])
    else:
        table_rows.append([
            Paragraph("-", cell_style),
            Paragraph("No transactions recorded during this operational timeframe.", cell_style),
            Paragraph("0", cell_right),
            Paragraph("$0.00", cell_right),
            Paragraph("$0.00", cell_right),
            Paragraph("0.0%", cell_right)
        ])

    merch_table = Table(table_rows, colWidths=[38, 202, 70, 80, 80, 70])
    merch_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]
    # Alternating row background
    for r in range(1, len(table_rows) - 1):
        if r % 2 == 0:
            merch_style.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor("#f8fafc")))
    # Total row styling
    if len(table_rows) > 2:
        merch_style.append(('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e2e8f0")))
        merch_style.append(('LINEABOVE', (0, -1), (-1, -1), 1.2, colors.HexColor("#0f172a")))

    merch_table.setStyle(TableStyle(merch_style))
    story.append(merch_table)
    story.append(Spacer(1, 14))

    # ==========================================
    # 4. PROCUREMENT & SUPPLY CHAIN RESTOCK AUDIT
    # ==========================================
    story.append(Paragraph(f"{s_idx}. Supply Chain Restock & Inbound Deliveries", section_h2))
    s_idx += 1

    purchase_headers = [
        Paragraph("Timestamp", th_style),
        Paragraph("Product Style Name", th_style),
        Paragraph("Units Received", th_right),
        Paragraph("Total Inbound Cost", th_right),
        Paragraph("Unit Cost Basis", th_right)
    ]
    pur_rows = [purchase_headers]
    purchases_df = data["purchases_df"]

    if not purchases_df.empty:
        # Display latest up to 10 purchases
        sample_pur = purchases_df.head(10)
        for _, row in sample_pur.iterrows():
            u_cost = (row['total_cost'] / row['quantity']) if row['quantity'] > 0 else 0.0
            pur_rows.append([
                Paragraph(str(row['timestamp']), cell_style),
                Paragraph(f"<b>{row['product_name']}</b> <font color='#64748b'>({row['product_id']})</font>", cell_style),
                Paragraph(f"+{row['quantity']:,} units", cell_right_bold),
                Paragraph(f"${row['total_cost']:,.2f}", cell_right),
                Paragraph(f"${u_cost:.2f}", cell_right)
            ])
        # Summary
        pur_rows.append([
            Paragraph("TOTAL", cell_bold),
            Paragraph(f"<b>Audited Inbound Shipments ({len(sample_pur)} shown of {len(purchases_df)})</b>", cell_bold),
            Paragraph(f"<b>+{sample_pur['quantity'].sum():,} units</b>", cell_right_bold),
            Paragraph(f"<b>${sample_pur['total_cost'].sum():,.2f}</b>", cell_right_bold),
            Paragraph("-", cell_right)
        ])
    else:
        pur_rows.append([
            Paragraph("-", cell_style),
            Paragraph("No procurement restocks logged in this timeframe.", cell_style),
            Paragraph("0", cell_right),
            Paragraph("$0.00", cell_right),
            Paragraph("-", cell_right)
        ])

    pur_table = Table(pur_rows, colWidths=[110, 200, 75, 85, 70])
    pur_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]
    for r in range(1, len(pur_rows) - 1):
        if r % 2 == 0:
            pur_style.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor("#f8fafc")))
    if len(pur_rows) > 2:
        pur_style.append(('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e2e8f0")))
        pur_style.append(('LINEABOVE', (0, -1), (-1, -1), 1.2, colors.HexColor("#0f172a")))

    pur_table.setStyle(TableStyle(pur_style))
    story.append(pur_table)
    story.append(Spacer(1, 14))

    # ==========================================
    # 5. INVENTORY HEALTH & SAFETY BREACH SUMMARY
    # ==========================================
    broken_curves = data["broken_curves"]
    inv_dict = data["inventory_dict"]
    low_stock_items = [
        (pid, CATALOG[pid]["name"], inv_dict.get(pid, 0), CATALOG[pid]["category"])
        for pid in CATALOG if inv_dict.get(pid, 0) <= 15
    ]

    story.append(Paragraph(f"{s_idx}. Critical Inventory & Safety Stock Outage Alerts", section_h2))

    alert_headers = [
        Paragraph("Alert Classification", th_style),
        Paragraph("Affected Merchandise Style", th_style),
        Paragraph("Current Balance", th_right),
        Paragraph("Prescribed Operational Remedy", th_style)
    ]
    alert_rows = [alert_headers]

    if low_stock_items or broken_curves:
        for pid, name, qty, cat in low_stock_items[:5]:
            alert_rows.append([
                Paragraph("<font color='#dc2626'><b>CRITICAL LOW STOCK</b></font>", cell_style),
                Paragraph(f"<b>{name}</b> ({pid})", cell_style),
                Paragraph(f"<b>{qty} units</b>", cell_right_bold),
                Paragraph("Trigger immediate supplier procurement reorder.", cell_style)
            ])
        for bc in broken_curves[:3]:
            sizes_str = ", ".join(bc['missing_core_sizes'])
            alert_rows.append([
                Paragraph("<font color='#d97706'><b>SIZE CURVE GAP</b></font>", cell_style),
                Paragraph(f"<b>{bc['product_name']}</b>", cell_style),
                Paragraph(f"{bc['stranded_stock_volume']} stranded", cell_right),
                Paragraph(f"Missing sizes: {sizes_str}. {bc['remedy']}", cell_style)
            ])
    else:
        alert_rows.append([
            Paragraph("<font color='#059669'><b>OPTIMAL</b></font>", cell_style),
            Paragraph("All catalog lines operating within safety parameters.", cell_style),
            Paragraph("OK", cell_right),
            Paragraph("No corrective actions required at this audit interval.", cell_style)
        ])

    alert_table = Table(alert_rows, colWidths=[120, 160, 90, 170])
    alert_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]
    for r in range(1, len(alert_rows)):
        if r % 2 == 0:
            alert_style.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor("#f8fafc")))
    alert_table.setStyle(TableStyle(alert_style))
    story.append(alert_table)
    story.append(Spacer(1, 14))

    # ==========================================
    # 6. COMPETITOR MARKET PRICING BENCHMARK & PARITY INDEX
    # ==========================================
    comp_df = data.get("competitor_df", pd.DataFrame())
    if isinstance(comp_df, pd.DataFrame) and not comp_df.empty:
        story.append(Paragraph(f"{s_idx}. Market Competitor Price Benchmark & Parity Index", section_h2))
        s_idx += 1

        # CompetitorAnalyzer imported at top-level
        cpi_meta = CompetitorAnalyzer.get_store_cpi_metrics(comp_df)
        cpi_val = cpi_meta.get("store_cpi", 100.0)
        opp_val = cpi_meta.get("total_margin_opportunity", 0.0)
        haz_val = cpi_meta.get("underpriced_count", 0)

        # Executive summary callout box
        cpi_summary_text = (
            f"<b>Store Competitor Price Index (CPI):</b> {cpi_val:.1f}% &nbsp;|&nbsp; "
            f"<b>Underpriced Hazards:</b> <font color='#b45309'><b>{haz_val} Styles</b></font> &nbsp;|&nbsp; "
            f"<b>Total Unearned Margin Opportunity:</b> <font color='#047857'><b>+${opp_val:,.2f}/mo</b></font>"
        )
        cpi_card = Table([[Paragraph(cpi_summary_text, cell_style)]], colWidths=[540])
        cpi_card.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('LINELEFT', (0, 0), (0, -1), 3.0, colors.HexColor("#0f172a")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ]))
        story.append(cpi_card)
        story.append(Spacer(1, 8))

        comp_headers = [
            Paragraph("Merchandise Style", th_style),
            Paragraph("Our Price", th_right),
            Paragraph("Market Avg", th_right),
            Paragraph("Velvet & Vine", th_right),
            Paragraph("Avenue App", th_right),
            Paragraph("Minimalist", th_right),
            Paragraph("Price Index", th_right),
            Paragraph("Strategic Action", th_style)
        ]
        comp_rows = [comp_headers]

        # Sort with underpriced hazards at the top, followed by premium, up to 12 rows
        sorted_comp = comp_df.sort_values(by="pricing_index", ascending=True).head(12)
        for _, r in sorted_comp.iterrows():
            pos_label = r.get("position", "Market Aligned")
            if pos_label == "Underpriced Hazard":
                status_html = f"<font color='#b45309'><b>UNDERPRICED</b></font><br/><font size=6 color='#64748b'>+${r.get('margin_gap', 0):.2f} upside</font>"
            elif pos_label == "Premium Positioned":
                status_html = "<font color='#7c3aed'><b>PREMIUM</b></font>"
            else:
                status_html = "<font color='#059669'><b>ALIGNED</b></font>"

            comp_rows.append([
                Paragraph(f"<b>{r.get('product_name')}</b><br/><font size=6 color='#64748b'>{r.get('category', 'Apparel')}</font>", cell_style),
                Paragraph(f"<b>${r.get('your_price', 0):.2f}</b>", cell_right_bold),
                Paragraph(f"${r.get('avg_market_price', 0):.2f}", cell_right),
                Paragraph(f"${r.get('velvet_vine_price', 0):.2f}", cell_right),
                Paragraph(f"${r.get('avenue_price', 0):.2f}", cell_right),
                Paragraph(f"${r.get('minimalist_price', 0):.2f}", cell_right),
                Paragraph(f"<b>{r.get('pricing_index', 100):.1f}%</b>", cell_right_bold),
                Paragraph(status_html, cell_style)
            ])

        comp_table = Table(comp_rows, colWidths=[130, 50, 55, 65, 55, 55, 50, 80])
        comp_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ]
        for idx, (_, r) in enumerate(sorted_comp.iterrows(), start=1):
            if r.get("position") == "Underpriced Hazard":
                comp_style.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor("#fef3c7")))
            elif r.get("position") == "Premium Positioned":
                comp_style.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor("#f3e8ff")))
            elif idx % 2 == 0:
                comp_style.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor("#f8fafc")))

        comp_table.setStyle(TableStyle(comp_style))
        story.append(comp_table)
        story.append(Spacer(1, 14))

    # ==========================================
    # 7. SIGN-OFF BLOCK
    # ==========================================
    sign_text = [
        Paragraph("<b>Audit Certification:</b> This financial & inventory audit report has been compiled directly from authenticated SQLite transaction ledgers and verified against boutique circuit controls.", subtitle_style),
        Spacer(1, 4),
        Paragraph("<b>Certified By:</b> Boutique BI Autonomous Intelligence Platform & Controller Office", subtitle_style)
    ]
    story.append(KeepTogether(sign_text))

    # Build PDF with custom NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_chat_transcript_pdf(
    messages: list,
    persona_title = "Senior Merchandise Director",
    persona_badge: str = "Strategic Advisory",
    model_name: str = "llama3.2:3b"
) -> bytes:
    if isinstance(persona_title, dict):
        d = persona_title
        persona_title = str(d.get("persona_title") or d.get("title") or d.get("persona") or "Senior Merchandise Director")
        persona_badge = str(d.get("persona_badge") or d.get("badge") or "Strategic Advisory")
        model_name = str(d.get("model_name") or d.get("model") or "llama3.2:3b")
    else:
        persona_title = str(persona_title)

    """
    Compiles a boardroom-ready PDF transcript of the active AI Copilot chat conversation.
    
    Args:
        messages (list): List of message dictionaries with 'role' and 'content'.
        persona_title (str): Title of the active advisory persona.
        persona_badge (str): Functional focus badge of the active persona.
        model_name (str): Local Ollama model used for reasoning.
        
    Returns:
        bytes: Raw PDF document bytes ready for streaming download.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ChatDocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a")
    )
    subtitle_style = ParagraphStyle(
        'ChatDocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569")
    )
    meta_tag_style = ParagraphStyle(
        'ChatMetaTag',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#d97706')
    )
    user_header_style = ParagraphStyle(
        'ChatUserHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1d4ed8")
    )
    user_body_style = ParagraphStyle(
        'ChatUserBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e293b")
    )
    bot_header_style = ParagraphStyle(
        'ChatBotHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#4338ca")
    )
    bot_heading_style = ParagraphStyle(
        'ChatBotHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=4,
        spaceAfter=2
    )
    bot_body_style = ParagraphStyle(
        'ChatBotBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#334155"),
        spaceBefore=2,
        spaceAfter=3
    )
    bot_bullet_style = ParagraphStyle(
        'ChatBotBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#1e293b"),
        leftIndent=10,
        spaceBefore=1,
        spaceAfter=2
    )

    story = []

    # 1. Letterhead
    gen_time = datetime.now().strftime("%b %d, %Y - %H:%M:%S")
    transcript_code = f"COPILOT-TRX-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    header_left = [
        Paragraph("MISHIKA FASHION LUXURY BOUTIQUE", meta_tag_style),
        Paragraph("AI Copilot Strategic Advisory Transcript", title_style),
        Paragraph(f"Executive Decision-Support Record &bull; {persona_title}", subtitle_style),
    ]

    header_right = [
        Paragraph(f"<b>Transcript Ref:</b> {transcript_code}", subtitle_style),
        Paragraph(f"<b>Export Timestamp:</b> {gen_time}", subtitle_style),
        Paragraph("<b>Classification:</b> Executive Confidential", subtitle_style)
    ]

    header_table = Table([[header_left, header_right]], colWidths=[340, 200])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e293b"), spaceAfter=10))

    # 2. Session Metadata Strip
    user_turns = sum(1 for m in messages if m.get("role") == "user")
    bot_turns = sum(1 for m in messages if m.get("role") == "assistant")
    session_info = [
        [
            Paragraph(f"<b>Advisory Role:</b> {persona_title} ({persona_badge})", subtitle_style),
            Paragraph(f"<b>Reasoning Model:</b> {model_name} (Ollama)", subtitle_style),
            Paragraph(f"<b>Interaction Volume:</b> {user_turns} Queries / {bot_turns} Responses", subtitle_style)
        ]
    ]
    info_table = Table(session_info, colWidths=[200, 180, 160])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#e2e8f0")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12))

    # 3. Message Sequence
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "").strip()
        if not content:
            continue

        if role == "user":
            user_flowables = [
                Paragraph("<b>👤 EXECUTIVE STRATEGIC INQUIRY</b>", user_header_style),
                Spacer(1, 2),
                HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#bfdbfe"), spaceAfter=4)
            ]
            for line in content.splitlines():
                if line.strip():
                    fmt_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line.strip())
                    user_flowables.append(Paragraph(fmt_line, user_body_style))

            u_table = Table([[user_flowables]], colWidths=[540])
            u_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
                ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#bfdbfe")),
                ('LINELEFT', (0, 0), (0, -1), 3.5, colors.HexColor("#2563eb")),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(u_table)
            story.append(Spacer(1, 8))

        elif role == "assistant":
            bot_flowables = [
                Paragraph(f"<b>🤖 COPILOT STRATEGIC ADVISORY &bull; {persona_title.upper()}</b>", bot_header_style),
                Spacer(1, 2),
                HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#c7d2fe"), spaceAfter=5)
            ]
            for line in content.splitlines():
                s = line.strip()
                if not s:
                    continue
                s_fmt = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', s)
                if s_fmt.startswith(("### ", "## ")):
                    heading_text = re.sub(r'^#+\s*', '', s_fmt).strip()
                    bot_flowables.append(Paragraph(f"<b>{heading_text}</b>", bot_heading_style))
                elif s_fmt.startswith(("- ", "* ", "• ")):
                    bullet_text = s_fmt[2:].strip()
                    bot_flowables.append(Paragraph(f"&bull; {bullet_text}", bot_bullet_style))
                else:
                    bot_flowables.append(Paragraph(s_fmt, bot_body_style))

            b_table = Table([[bot_flowables]], colWidths=[540])
            b_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
                ('LINELEFT', (0, 0), (0, -1), 3.5, colors.HexColor("#4f46e5")),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(b_table)
            story.append(Spacer(1, 10))

    # 4. Sign-off / Certification Block
    sign_text = [
        Paragraph("<b>Transcript Certification:</b> This advisory transcript was generated in real-time by the Mishika Fashion Boutique AI Copilot grounded in authenticated SQLite retail transactions, size curves, and competitor pricing indices.", subtitle_style),
        Spacer(1, 3),
        Paragraph("<b>Archival Office:</b> Mishika Fashion Autonomous Business Intelligence Platform & Executive Office", subtitle_style)
    ]
    story.append(KeepTogether(sign_text))

    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

