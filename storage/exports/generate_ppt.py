import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

# 1. Initialize Presentation
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

# Colors
C_DARK_BG   = RGBColor(15, 23, 42)      # #0F172A
C_LIGHT_BG  = RGBColor(248, 250, 252)   # #F8FAFC
C_WHITE     = RGBColor(255, 255, 255)
C_CARD_BG   = RGBColor(255, 255, 255)
C_CARD_BRD  = RGBColor(226, 232, 240)   # #E2E8F0
C_GOLD      = RGBColor(217, 119, 6)     # #D97706
C_EMERALD   = RGBColor(16, 185, 129)    # #10B981
C_BLUE      = RGBColor(37, 99, 235)     # #2563EB
C_PURPLE    = RGBColor(139, 92, 246)    # #8B5CF6
C_CRIMSON   = RGBColor(239, 68, 68)     # #EF4444
C_TEXT_DARK = RGBColor(15, 23, 42)      # #0F172A
C_TEXT_MUTED= RGBColor(100, 116, 139)   # #64748B
C_TEXT_LIGHT= RGBColor(241, 245, 249)   # #F1F5F9

def add_header(slide, title, category="MISHIKA FASHION LUXURY BOUTIQUE BI ASSISTANT"):
    tb_tag = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.3))
    tf_tag = tb_tag.text_frame
    tf_tag.word_wrap = True
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = category.upper()
    p_tag.font.size = Pt(10)
    p_tag.font.bold = True
    p_tag.font.color.rgb = C_GOLD
    
    tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.65), Inches(11.7), Inches(0.6))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = C_TEXT_DARK

def create_card(slide, left, top, width, height, bg_color=C_CARD_BG, border_color=C_CARD_BRD):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = border_color
    shape.line.width = Pt(1)
    return shape

# ==============================================================================
# SLIDE 1: TITLE SLIDE (Dark Luxury Theme)
# ==============================================================================
s1 = prs.slides.add_slide(blank_layout)
bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
bg1.fill.solid()
bg1.fill.fore_color.rgb = C_DARK_BG
bg1.line.fill.background()

tb = s1.shapes.add_textbox(Inches(1.2), Inches(1.5), Inches(10.9), Inches(4.5))
tf = tb.text_frame
tf.word_wrap = True

p0 = tf.paragraphs[0]
p0.text = "MISHIKA FASHION LUXURY BOUTIQUE"
p0.font.size = Pt(14)
p0.font.bold = True
p0.font.color.rgb = C_GOLD

p1 = tf.add_paragraph()
p1.text = "Local BI Assistant & Operations Engine"
p1.font.size = Pt(36)
p1.font.bold = True
p1.font.color.rgb = C_WHITE
p1.space_before = Pt(10)

p2 = tf.add_paragraph()
p2.text = "Enterprise-Grade Retail Intelligence, Real-Time Simulation & Privacy-First Local AI Copilot"
p2.font.size = Pt(18)
p2.font.color.rgb = RGBColor(148, 163, 184)
p2.space_before = Pt(14)

p3 = tf.add_paragraph()
p3.text = "• 100% Offline-First (Local Ollama Llama 3.2, SQLite & ReportLab)   • Zero Cloud Data Leakage\n• What-If Price Elasticity Simulator   • Dynamic 60 FPS Visual Pipeline   • Boardroom PDF Reports"
p3.font.size = Pt(13)
p3.font.color.rgb = C_EMERALD
p3.space_before = Pt(28)

badges = [
    ("Persistence", "SQLite (ACID Ledgers)"),
    ("Intelligence", "Ollama LLM (Offline RAG)"),
    ("Simulation", "Discrete Event Tick Engine"),
    ("Reporting", "ReportLab Platypus Engine"),
    ("Architecture", "Clean 'src/' Modular Layout")
]
for i, (b_title, b_val) in enumerate(badges):
    left = Inches(1.2 + i * 2.22)
    create_card(s1, left, Inches(5.8), Inches(2.08), Inches(0.95), bg_color=RGBColor(30, 41, 59), border_color=RGBColor(51, 65, 85))
    tb_b = s1.shapes.add_textbox(left, Inches(5.85), Inches(2.08), Inches(0.85))
    tf_b = tb_b.text_frame
    p_bt = tf_b.paragraphs[0]
    p_bt.text = b_title.upper()
    p_bt.font.size = Pt(9)
    p_bt.font.bold = True
    p_bt.font.color.rgb = C_GOLD
    p_bv = tf_b.add_paragraph()
    p_bv.text = b_val
    p_bv.font.size = Pt(10.5)
    p_bv.font.color.rgb = C_WHITE
    p_bv.space_before = Pt(2)

print('Built Slide 1')

# ==============================================================================
# SLIDE 2: EXECUTIVE SUMMARY & PROBLEM / SOLUTION
# ==============================================================================
s2 = prs.slides.add_slide(blank_layout)
add_header(s2, "Executive Overview: Modernizing Boutique Retail Intelligence")

c_prob = create_card(s2, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4))
tb_p = s2.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(5.0))
tf_p = tb_p.text_frame
tf_p.word_wrap = True

p = tf_p.paragraphs[0]
p.text = "🚨 Industry Bottlenecks & Challenges"
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = C_CRIMSON

points_p = [
    ("Cloud Privacy Hazards", "Exporting proprietary sales numbers and customer feedback to third-party cloud APIs poses serious compliance, privacy, and cost risks."),
    ("Blind Pricing & Margin Leakage", "Boutiques frequently underprice against luxury rivals without realizing it, forfeiting $1,000s in uncaptured monthly gross profit."),
    ("Broken Size Curves & Stranded Stock", "Running out of core sizes (S, M, L) halts sell-through while stranded fringe stock (XL) locks up valuable working capital."),
    ("Static Dashboards vs. Reality", "Traditional BI reports are backward-looking PDFs created days later, missing fast real-time store stockouts.")
]
for title, desc in points_p:
    p_t = tf_p.add_paragraph()
    p_t.text = f"• {title}"
    p_t.font.size = Pt(13)
    p_t.font.bold = True
    p_t.font.color.rgb = C_TEXT_DARK
    p_t.space_before = Pt(10)
    p_d = tf_p.add_paragraph()
    p_d.text = desc
    p_d.font.size = Pt(11)
    p_d.font.color.rgb = C_TEXT_MUTED

c_sol = create_card(s2, Inches(6.9), Inches(1.5), Inches(5.6), Inches(5.4))
tb_s = s2.shapes.add_textbox(Inches(7.1), Inches(1.7), Inches(5.2), Inches(5.0))
tf_s = tb_s.text_frame
tf_s.word_wrap = True

p = tf_s.paragraphs[0]
p.text = "✨ The Local BI Boutique Solution"
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = C_EMERALD

points_s = [
    ("100% Privacy-Preserving Offline Engine", "All computation, SQLite ledgers, ReportLab PDFs, and Ollama LLM inference execute entirely on-premise on local hardware."),
    ("Dynamic What-If Price Elasticity Simulator", "Simulates demand shifts across retail apparel categories and enables 1-click catalog repricing to capture market parity."),
    ("Automated Inventory Circuit Safeguards", "Enforces capacity limits and permits selective disabling of sales or restocks per SKU to prevent costly inventory bloat."),
    ("Boardroom Executive Audits & AI Copilot", "Generates comprehensive multi-horizon PDF audits and provides multi-persona AI advisory with full transcript export.")
]
for title, desc in points_s:
    p_t = tf_s.add_paragraph()
    p_t.text = f"• {title}"
    p_t.font.size = Pt(13)
    p_t.font.bold = True
    p_t.font.color.rgb = C_TEXT_DARK
    p_t.space_before = Pt(10)
    p_d = tf_s.add_paragraph()
    p_d.text = desc
    p_d.font.size = Pt(11)
    p_d.font.color.rgb = C_TEXT_MUTED

print('Built Slide 2')

# ==============================================================================
# SLIDE 3: SYSTEM ARCHITECTURE & DATA FLOW
# ==============================================================================
s3 = prs.slides.add_slide(blank_layout)
add_header(s3, "System Architecture: Decoupled Multi-Layer Data Flow")

layers = [
    ("1. Presentation Layer (Streamlit & Plotly)", "• 5 Modular System Views: Dashboard, Live Ops, Inventory, PDF, AI Studio\n• Responsive, ultra-compact KPI status strips (~52px) and 60 FPS Canvas arena\n• Interactive Plotly visual charts with selective inventory diff rendering", C_BLUE),
    ("2. Analytics & Intelligence Layer", "• CompetitorAnalyzer: Price elasticity modeling (E_cat) & Store CPI Index\n• AdvancedInventoryManager: Stockout velocity scoring & liquidation alerts\n• MarketingOptimizer: Campaign ROAS & SentimentTrackingEngine", C_PURPLE),
    ("3. Discrete Event Simulation Engine", "• Stochastic tick processor generating customer sales & inbound truck deliveries\n• Store Circuit Controls: Real-time capacity checks & product toggle gates\n• Dynamic Competitor Price Ingestion across 3 distinct retail brand tiers", C_GOLD),
    ("4. Persistence & Data Access (SQLite)", "• 5 ACID Ledgers: sales_ledger, purchase_ledger, size_matrix_stock, controls, benchmarks\n• Fully self-healing schemas: auto-repairs missing tables on initialization\n• Isolated storage architecture at storage/db/boutique_bi.db", C_DARK_BG),
    ("5. Privacy-First AI & PDF Reporting", "• Local Ollama RAG integration (Llama 3.2 / Mistral) with live context injection\n• ReportLab Platypus Engine with two-pass NumberedCanvas ('Page X of Y')\n• Automated 4-part executive audit narrative compilation & chat transcript export", C_EMERALD)
]

for i, (l_title, l_desc, l_accent) in enumerate(layers):
    top = Inches(1.4 + i * 1.15)
    create_card(s3, Inches(0.8), top, Inches(11.7), Inches(1.02))
    bar = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), top, Inches(0.12), Inches(1.02))
    bar.fill.solid()
    bar.fill.fore_color.rgb = l_accent
    bar.line.fill.background()
    
    tb_l = s3.shapes.add_textbox(Inches(1.1), top + Inches(0.08), Inches(11.2), Inches(0.85))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    p_h = tf_l.paragraphs[0]
    p_h.text = l_title
    p_h.font.size = Pt(13)
    p_h.font.bold = True
    p_h.font.color.rgb = l_accent
    
    p_d = tf_l.add_paragraph()
    p_d.text = l_desc
    p_d.font.size = Pt(10)
    p_d.font.color.rgb = C_TEXT_DARK
    p_d.space_before = Pt(2)

print('Built Slide 3')

# ==============================================================================
# SLIDE 4: MODULE 1 - EXECUTIVE STRATEGY DASHBOARD & REPRICING
# ==============================================================================
s4 = prs.slides.add_slide(blank_layout)
add_header(s4, "Module 1: Executive Strategy Dashboard & What-If Repricing")

cards_m1 = [
    ("📊 High-Level Financial Scorecard", "• Live Cumulative Sales Revenue: Authenticated transaction ledger aggregation.\n• Realized Gross Margin %: Tracks true profit margin after COGS deduction.\n• Size Curve Outages: Instant visibility into apparel styles with broken size runs.", Inches(0.8), Inches(1.4), Inches(5.6), Inches(2.7)),
    ("📈 2x2 Operational Diagnostics", "• Product Sales Velocity: Horizontal sell-through rate (STR %) benchmark.\n• Customer Sentiment Matrix: Polarity tracking (-1.0 to +1.0) by merchandise line.\n• Critical Size Curve Alerts: Pinpoints missing core sizes (S, M) and stranded stock units.", Inches(6.9), Inches(1.4), Inches(5.6), Inches(2.7)),
    ("🏬 Tri-Brand Competitor Benchmark", "• Multi-Competitor Matrix: Compares our retail price against Velvet & Vine (Luxury, +15-35%), Avenue Apparel (Mid-Tier, -5 to +8%), and Minimalist Thread (Budget, -15 to -30%).\n• Store Price Index (CPI): Calculates overall store market parity (100 = Market Parity).", Inches(0.8), Inches(4.35), Inches(5.6), Inches(2.7)),
    ("⚡ Interactive 'What-If' Repricing Simulator", "• Price Elasticity Modeling: Incorporates apparel category elasticities (Outerwear -1.10, Knitwear -1.25, Dresses -1.35, Bottoms -1.40, Tops -1.55).\n• Projections: Real-time demand volume delta, monthly gross profit gain, and new CPI.\n• 1-Click Catalog Repricing: Instantly commits new price to SQLite across the live store.", Inches(6.9), Inches(4.35), Inches(5.6), Inches(2.7))
]

for title, content, left, top, width, height in cards_m1:
    create_card(s4, left, top, width, height)
    tb_c = s4.shapes.add_textbox(left + Inches(0.2), top + Inches(0.2), width - Inches(0.4), height - Inches(0.4))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True
    p = tf_c.paragraphs[0]
    p.text = title
    p.font.size = Pt(13.5)
    p.font.bold = True
    p.font.color.rgb = C_BLUE
    p_body = tf_c.add_paragraph()
    p_body.text = content
    p_body.font.size = Pt(10.5)
    p_body.font.color.rgb = C_TEXT_DARK
    p_body.space_before = Pt(6)

print('Built Slide 4')

# ==============================================================================
# SLIDE 5: MODULE 2 - LIVE STORE OPERATIONS PIPELINE & ARENA
# ==============================================================================
s5 = prs.slides.add_slide(blank_layout)
add_header(s5, "Module 2: Real-Time Store Operations Pipeline & Dynamic Arena")

features_m2 = [
    ("⚡ Discrete Event Ingestion Engine", "• Continuously handles stochastic retail transactions (65% customer sales, 35% restocks).\n• Live database persistence: immediately logs buyer sales and supplier deliveries with zero lag.\n• Circuit breaker checks: rejects deliveries or purchases if controls are toggled off.", Inches(0.8), Inches(1.5), Inches(5.6), Inches(2.55)),
    ("🎮 60 FPS HTML5 Canvas Arena", "• Hardware-accelerated dynamic animation container with zero UI flicker.\n• Delivery Cargo Truck: Inbound arrival, warehouse docking, and crate transfer.\n• Luxury Shopper: Walk cycles, transaction sparkle physics, and revenue badges.\n• Dual Sine-Wave Liquid Tank: Mathematically models physical fluid stock volume.", Inches(6.9), Inches(1.5), Inches(5.6), Inches(2.55)),
    ("📊 Selective Inventory Diff Bar Chart", "• Performance Optimization: Re-renders the Plotly chart ONLY when inventory changes.\n• Preserves Zoom & Pan: Uses Plotly uirevision to prevent canvas reset flickering.\n• Real-Time Color Highlighting:\n   🟢 Emerald Green: Product just restocked by inbound truck shipment\n   🟡 Amber Gold: Product just purchased by a store shopper\n   🔴 Crimson: Critical safety stock breach (<= 15 units)\n   🔵 Luxury Slate: All stable, unchanged catalog lines", Inches(0.8), Inches(4.25), Inches(5.6), Inches(2.8)),
    ("📝 High-Density KPI Strip & Live Ledgers", "• 52px Ultra-Compact Header: Shows Total Revenue, Low Stock count, and Live status.\n• Dual Streaming Ledgers: Live Sales Log (product, price, timestamp) and Inbound Restocks Log (units, supplier cost).\n• Standby Pre-Loading: Pre-loads baseline charts and assets so the UI never flashes blank.", Inches(6.9), Inches(4.25), Inches(5.6), Inches(2.8))
]

for title, content, left, top, width, height in features_m2:
    create_card(s5, left, top, width, height)
    tb_c = s5.shapes.add_textbox(left + Inches(0.2), top + Inches(0.2), width - Inches(0.4), height - Inches(0.4))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True
    p = tf_c.paragraphs[0]
    p.text = title
    p.font.size = Pt(13.5)
    p.font.bold = True
    p.font.color.rgb = C_EMERALD
    p_body = tf_c.add_paragraph()
    p_body.text = content
    p_body.font.size = Pt(10.5)
    p_body.font.color.rgb = C_TEXT_DARK
    p_body.space_before = Pt(6)

print('Built Slide 5')

# ==============================================================================
# SLIDE 6: MODULE 3 - INVENTORY & CIRCUIT CONTROLS
# ==============================================================================
s6 = prs.slides.add_slide(blank_layout)
add_header(s6, "Module 3: Inventory Circuit Breakers & Capacity Enforcers")

features_m3 = [
    ("🛡️ Retail Circuit Breaker Switches", "• Independent Sales Toggle: Turn off 'Allow Sales' per style to reserve inventory for VIP previews, seasonal holds, or vendor recalls.\n• Procurement Gate: Turn off 'Allow Restocks' to block inbound vendor shipments.\n• Immediate Engine Guard: The simulation engine queries SQLite circuit settings on every tick, enforcing rules in real-time."),
    ("📦 Warehouse Capacity Limits (Ceilings)", "• Maximum Storage Ceilings: Prevents warehouse overfilling by establishing maximum unit thresholds (e.g., 100 or 150 units per style).\n• Intelligent Overfill Rejection: Automatically rejects delivery trucks when inventory reaches capacity, preventing working capital lockup.\n• Operational Alerts: Displays clear warning logs when shipments are turned away due to full capacity."),
    ("🧵 Granular Size-Matrix Stock Matrix", "• Multi-Variant Resolution: Tracks discrete unit stock across core apparel sizes (Small, Medium, Large, Extra Large).\n• Automated Size Curve Detection: Flags broken size curves whenever core sizes (S, M, L) drop to 0 while fringe sizes (XL) remain stranded.\n• Remediation Prescriptions: Suggests immediate corrective action (liquidation markdowns, emergency replenishment).")
]

for i, (title, content) in enumerate(features_m3):
    left = Inches(0.8 + i * 3.96)
    create_card(s6, left, Inches(1.5), Inches(3.76), Inches(5.4))
    tb_c = s6.shapes.add_textbox(left + Inches(0.2), Inches(1.7), Inches(3.36), Inches(5.0))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True
    p = tf_c.paragraphs[0]
    p.text = title
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_GOLD
    p_body = tf_c.add_paragraph()
    p_body.text = content
    p_body.font.size = Pt(11)
    p_body.font.color.rgb = C_TEXT_DARK
    p_body.space_before = Pt(8)

print('Built Slide 6')

# ==============================================================================
# SLIDE 7: MODULE 4 - BOARDROOM PDF REPORTING ENGINE
# ==============================================================================
s7 = prs.slides.add_slide(blank_layout)
add_header(s7, "Module 4: Boardroom-Grade PDF Reporting Engine (ReportLab)")

cols_m4 = [
    ("📄 Multi-Horizon Audit Periods", "• Daily Snapshot: Immediate 24-hour review of sales transactions, cash flow, and deliveries.\n• Weekly Performance Audit: Analyzes moving averages, velocity shifts, and replenishment spend.\n• Monthly Review: Strategic balance sheet review and gross margin tracking.\n• Complete All-Time Ledger: Comprehensive audit of entire historical database transactions.", Inches(0.8), Inches(1.5), Inches(5.6), Inches(2.6)),
    ("📑 ReportLab Platypus Architecture", "• Strict Flowable Layout: Structured tables, paragraph flowables, and clean spacers.\n• Two-Pass NumberedCanvas: Calculates exact total page counts ('Page X of Y') dynamically.\n• Micro-Card Bubble Architecture: Multi-page transcripts and audit ledgers break cleanly across pages with zero LayoutErrors.", Inches(6.9), Inches(1.5), Inches(5.6), Inches(2.6)),
    ("🤖 Embedded Local AI Commentary", "• Automated Executive Narrative: Synthesizes live SQLite audit ledgers into a 4-part boardroom narrative via local Ollama.\n• Financial Health Assessment: Revenue, COGS, realized gross margin %.\n• Velocity & Supply Chain: Highlights top performers and supply chain delivery status.\n• Strategic Actions: Prioritizes 3 immediate boardroom actions for the executive team.", Inches(0.8), Inches(4.3), Inches(5.6), Inches(2.7)),
    ("🏬 Section 6: Competitor Benchmark Table", "• Integrated Market Parity: Embeds a full competitor benchmark table into every executive audit.\n• Brand Benchmarks: Displays prices across Velvet & Vine, Avenue Apparel, and Minimalist Thread.\n• Underpriced Hazard Highlighting: Visual amber styling for items with Price Index < 92%.\n• Prescribed Actions: Specific repricing guidance embedded directly in the audit.", Inches(6.9), Inches(4.3), Inches(5.6), Inches(2.7))
]

for title, content, left, top, width, height in cols_m4:
    create_card(s7, left, top, width, height)
    tb_c = s7.shapes.add_textbox(left + Inches(0.2), top + Inches(0.2), width - Inches(0.4), height - Inches(0.4))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True
    p = tf_c.paragraphs[0]
    p.text = title
    p.font.size = Pt(13.5)
    p.font.bold = True
    p.font.color.rgb = C_PURPLE
    p_body = tf_c.add_paragraph()
    p_body.text = content
    p_body.font.size = Pt(10.5)
    p_body.font.color.rgb = C_TEXT_DARK
    p_body.space_before = Pt(6)

print('Built Slide 7')

# ==============================================================================
# SLIDE 8: MODULE 5 - AI COPILOT STUDIO & STRATEGIC RAG
# ==============================================================================
s8 = prs.slides.add_slide(blank_layout)
add_header(s8, "Module 5: Local AI Copilot Studio & Strategic Knowledge RAG")

features_m5 = [
    ("🦙 100% Offline Local LLM", "• Powered by local Ollama instances running llama3.2:3b or mistral:latest.\n• Zero API Keys & Zero Per-Token Costs: Completely offline, fast, and free to query.\n• Complete Privacy: Internal financial transactions and review sentiments never leave the machine."),
    ("👔 3 Executive Advisory Personas", "• Senior Merchandise Director: Focuses on sell-through rate (STR %), inventory turnover, GMROI, and working capital defense.\n• Pricing & Margin Strategist: Analyzes Competitor Price Index (CPI), eliminates underpriced hazards, and optimizes elasticity.\n• Mishika Fashion & Styling Curator: Assesses garment craftsmanship, customer feedback, and size curve harmony."),
    ("🔍 Live Knowledge Inspector & FAQs", "• Real-Time Context Cards: Shows the exact database payload injected into Ollama prompts (revenue, top sellers, broken curves, competitor hazards).\n• Tabbed Strategic FAQs: Pre-loaded questions across 4 strategic pillars (Financials, Inventory, Pricing, Sentiment).\n• 1-Click PDF Chat Export: Compiles formatted transcripts into executive PDF documents.")
]

for i, (title, content) in enumerate(features_m5):
    left = Inches(0.8 + i * 3.96)
    create_card(s8, left, Inches(1.5), Inches(3.76), Inches(5.4))
    tb_c = s8.shapes.add_textbox(left + Inches(0.2), Inches(1.7), Inches(3.36), Inches(5.0))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True
    p = tf_c.paragraphs[0]
    p.text = title
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_BLUE
    p_body = tf_c.add_paragraph()
    p_body.text = content
    p_body.font.size = Pt(11)
    p_body.font.color.rgb = C_TEXT_DARK
    p_body.space_before = Pt(8)

print('Built Slide 8')

# ==============================================================================
# SLIDE 9: COMPETITOR INTELLIGENCE & PRICE ELASTICITY MATH
# ==============================================================================
s9 = prs.slides.add_slide(blank_layout)
add_header(s9, "Competitor Intelligence & Price Elasticity Math")

c_cpi = create_card(s9, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4))
tb_cpi = s9.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(5.0))
tf_cpi = tb_cpi.text_frame
tf_cpi.word_wrap = True

p = tf_cpi.paragraphs[0]
p.text = "🏬 Multi-Brand Benchmark Tiers & CPI"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = C_GOLD

cpi_text = [
    ("Velvet & Vine Boutique (Luxury Designer)", "Prices range +15% to +35% above our baseline. Represents the high-end luxury ceiling."),
    ("Avenue Apparel (Contemporary Mid-Tier)", "Prices hover -5% to +8% around our baseline. Represents our primary direct retail peer."),
    ("Minimalist Thread Co. (Budget / Fast Fashion)", "Prices sit -15% to -30% below our baseline. Represents value and clearance baselines."),
    ("Competitor Price Index (CPI) Formula", "CPI = (Our Price / Average Market Price) * 100\n  • Underpriced Hazard: CPI < 92.0% (Margin Leakage)\n  • Market Aligned: 92.0% <= CPI <= 112.0% (Parity)\n  • Premium Positioned: CPI > 112.0% (Luxury Premium)")
]
for title, desc in cpi_text:
    p_t = tf_cpi.add_paragraph()
    p_t.text = f"• {title}"
    p_t.font.size = Pt(12)
    p_t.font.bold = True
    p_t.font.color.rgb = C_TEXT_DARK
    p_t.space_before = Pt(8)
    p_d = tf_cpi.add_paragraph()
    p_d.text = desc
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = C_TEXT_MUTED

c_ela = create_card(s9, Inches(6.9), Inches(1.5), Inches(5.6), Inches(5.4))
tb_ela = s9.shapes.add_textbox(Inches(7.1), Inches(1.7), Inches(5.2), Inches(5.0))
tf_ela = tb_ela.text_frame
tf_ela.word_wrap = True

p = tf_ela.paragraphs[0]
p.text = "📈 Category Price Elasticity Demand Math"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = C_BLUE

ela_text = [
    ("Category Price Elasticity Coefficients (E)", "Different fashion categories respond differently to price changes:\n  • Outerwear: E = -1.10 (Least elastic / Inelastic)\n  • Knitwear: E = -1.25\n  • Dresses: E = -1.35\n  • Bottoms: E = -1.40\n  • Tops: E = -1.55 (Most elastic / Highly sensitive)"),
    ("Volume Shift Formula", "pct_price_change = (new_price - old_price) / old_price\npct_volume_change = elasticity * pct_price_change\nprojected_units = round(base_volume * (1 + pct_volume_change))"),
    ("Financial Net Profit Optimization", "new_revenue = new_price * projected_units\nnew_cost = unit_cost * projected_units\nprofit_delta = (new_revenue - new_cost) - old_gross_profit\nIdentifies sweet-spot price increases where margin expansion outpaces volume drop.")
]
for title, desc in ela_text:
    p_t = tf_ela.add_paragraph()
    p_t.text = f"• {title}"
    p_t.font.size = Pt(12)
    p_t.font.bold = True
    p_t.font.color.rgb = C_TEXT_DARK
    p_t.space_before = Pt(8)
    p_d = tf_ela.add_paragraph()
    p_d.text = desc
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = C_TEXT_MUTED

print('Built Slide 9')

# ==============================================================================
# SLIDE 10: CLEAN MODULAR PROJECT ARCHITECTURE
# ==============================================================================
s10 = prs.slides.add_slide(blank_layout)
add_header(s10, "Enterprise Clean Project Architecture ('src/' Layout)")

c_tree = create_card(s10, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4), bg_color=C_DARK_BG, border_color=C_DARK_BG)
tb_tr = s10.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(5.0))
tf_tr = tb_tr.text_frame
tf_tr.word_wrap = True

p = tf_tr.paragraphs[0]
p.text = "📂 Modular Directory Blueprint"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = C_GOLD

tree_code = """local_bi_boutique_assistant/
│
├── 📂 src/                  # Production Python Package
│   ├── core/               # Config, logger, master catalog
│   ├── data/               # SQLite DatabaseManager & schema
│   ├── analytics/          # Competitor elasticity & inventory
│   ├── simulation/         # Real-time event stream engine
│   ├── ai/                 # Local Ollama RAG & prompt builder
│   ├── reporting/          # ReportLab Platypus PDF builder
│   └── ui/                 # Styling, CSS tokens & animations
│
├── 📂 storage/              # Runtime Storage (git-ignored)
│   ├── db/boutique_bi.db   # SQLite production database
│   └── exports/            # Generated boardroom PDFs
│
├── 📂 logs/                 # Rotated application logs
│   └── app.log
│
├── 📂 tests/                # Automated Regression Suite
│   └── test_*.py           # 7 Unit tests (elasticity, DB, PDF)
│
├── app.py                  # Primary Streamlit Entrypoint
├── run_tests.py            # 1-Click Automated Test Runner
├── run.bat / run.ps1       # Windows 1-Click Launchers
└── requirements.txt        # Verified Dependencies"""

p_c = tf_tr.add_paragraph()
p_c.text = tree_code
p_c.font.size = Pt(9.5)
p_c.font.name = "Consolas"
p_c.font.color.rgb = C_TEXT_LIGHT
p_c.space_before = Pt(8)

c_ben = create_card(s10, Inches(6.9), Inches(1.5), Inches(5.6), Inches(5.4))
tb_b = s10.shapes.add_textbox(Inches(7.1), Inches(1.7), Inches(5.2), Inches(5.0))
tf_b = tb_b.text_frame
tf_b.word_wrap = True

p = tf_b.paragraphs[0]
p.text = "🏛️ Architectural Design Principles"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = C_BLUE

principles = [
    ("Separation of Concerns (SoC)", "UI elements, business calculations, database queries, and AI prompt engineering are cleanly isolated in independent subpackages."),
    ("Zero Root Clutter", "All 13 legacy scripts and duplicate shims were eliminated from the root folder. Only clean entrypoints (app.py, run.bat) remain at the top level."),
    ("Storage & Log Segregation", "Databases and log files are isolated in storage/ and logs/, protected by comprehensive root .gitignore rules."),
    ("Deterministic Testing & Reliability", "A dedicated tests/ directory paired with run_tests.py verifies all calculations before production deployment.")
]
for title, desc in principles:
    p_t = tf_b.add_paragraph()
    p_t.text = f"• {title}"
    p_t.font.size = Pt(12)
    p_t.font.bold = True
    p_t.font.color.rgb = C_TEXT_DARK
    p_t.space_before = Pt(10)
    p_d = tf_b.add_paragraph()
    p_d.text = desc
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = C_TEXT_MUTED

print('Built Slide 10')

# ==============================================================================
# SLIDE 11: TESTING, VERIFICATION & 1-CLICK LAUNCHERS
# ==============================================================================
s11 = prs.slides.add_slide(blank_layout)
add_header(s11, "Verification & Deployment: 100% Passing Test Suite")

test_boxes = [
    ("🧪 Test Suite (run_tests.py)", "• Built with standard library unittest (zero extra runner dependencies required).\n• test_01_elasticity: Verifies demand curves, volume deltas, and profit calculations.\n• test_02_cpi_structure: Validates store-wide Price Index and hazard categorization.\n• test_03_database_initialization: Confirms self-healing table verification.\n• test_04_record_sale: Validates atomic inventory deductions and ledger logging.\n• test_05_update_catalog_price: Validates live catalog price updates.\n• test_06_chat_transcript_pdf: Verifies multi-turn chat PDF generation.\n• test_07_enterprise_pdf: Verifies multi-page financial audit PDF compilation.", Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4)),
    ("⚡ Deployment & 1-Click Launchers", "• Windows 1-Click Batch (run.bat):\n  - Automatically detects and activates .venv virtual environment.\n  - Launches Streamlit on port 8501 with dark luxury styling.\n\n• PowerShell 1-Click Script (run.ps1):\n  - Native PowerShell execution with color-coded status messages.\n\n• Manual Streamlit Command:\n  .\\.venv\\Scripts\\python.exe -m streamlit run app.py\n\n• Automated Test Execution:\n  .\\.venv\\Scripts\\python.exe run_tests.py\n\n• Test Result: 7/7 Tests Passed in 0.31s (100% Success Rate)", Inches(6.9), Inches(1.5), Inches(5.6), Inches(5.4))
]

for title, content, left, top, width, height in test_boxes:
    create_card(s11, left, top, width, height)
    tb_c = s11.shapes.add_textbox(left + Inches(0.2), top + Inches(0.2), width - Inches(0.4), height - Inches(0.4))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True
    p = tf_c.paragraphs[0]
    p.text = title
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_EMERALD
    p_body = tf_c.add_paragraph()
    p_body.text = content
    p_body.font.size = Pt(11)
    p_body.font.color.rgb = C_TEXT_DARK
    p_body.space_before = Pt(8)

print('Built Slide 11')

# ==============================================================================
# SLIDE 12: CONCLUSION & STRATEGIC IMPACT (Dark Hero Finale)
# ==============================================================================
s12 = prs.slides.add_slide(blank_layout)
bg12 = s12.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
bg12.fill.solid()
bg12.fill.fore_color.rgb = C_DARK_BG
bg12.line.fill.background()

tb_12 = s12.shapes.add_textbox(Inches(1.2), Inches(1.2), Inches(10.9), Inches(5.2))
tf_12 = tb_12.text_frame
tf_12.word_wrap = True

p = tf_12.paragraphs[0]
p.text = "CONCLUSION & STRATEGIC VALUE"
p.font.size = Pt(13)
p.font.bold = True
p.font.color.rgb = C_GOLD

p_main = tf_12.add_paragraph()
p_main.text = "Autonomous, Boardroom-Grade Retail Intelligence"
p_main.font.size = Pt(30)
p_main.font.bold = True
p_main.font.color.rgb = C_WHITE
p_main.space_before = Pt(8)

p_sub = tf_12.add_paragraph()
p_sub.text = "Mishika Fashion Boutique BI Assistant delivers an end-to-end operational intelligence system that bridges daily retail transactions with long-term strategic boardroom decisions."
p_sub.font.size = Pt(14)
p_sub.font.color.rgb = RGBColor(148, 163, 184)
p_sub.space_before = Pt(10)

val_cols = [
    ("🔒 Zero-Trust Privacy", "Complete data isolation. No proprietary sales, inventory, or margins are ever transmitted over external cloud networks."),
    ("💰 Margin Optimization", "Dynamic price elasticity modeling identifies and eliminates Underpriced Hazards against luxury competitors, boosting monthly profit."),
    ("⚙️ Operational Control", "Circuit breaker toggles and warehouse capacity limits prevent supply-chain overfill and broken size curve stockouts."),
    ("📑 Boardroom Ready", "Instant executive PDF generation and AI Copilot dialogue exports provide actionable intelligence for leadership teams.")
]

for i, (v_title, v_desc) in enumerate(val_cols):
    left = Inches(1.2 + i * 2.75)
    create_card(s12, left, Inches(4.2), Inches(2.6), Inches(2.3), bg_color=RGBColor(30, 41, 59), border_color=RGBColor(51, 65, 85))
    tb_v = s12.shapes.add_textbox(left + Inches(0.15), Inches(4.35), Inches(2.3), Inches(2.0))
    tf_v = tb_v.text_frame
    tf_v.word_wrap = True
    p_vt = tf_v.paragraphs[0]
    p_vt.text = v_title
    p_vt.font.size = Pt(12)
    p_vt.font.bold = True
    p_vt.font.color.rgb = C_GOLD
    p_vd = tf_v.add_paragraph()
    p_vd.text = v_desc
    p_vd.font.size = Pt(10)
    p_vd.font.color.rgb = C_WHITE
    p_vd.space_before = Pt(6)

print('Built Slide 12')

# Save Presentations
out_path1 = Path(r'c:\Users\akhil\Downloads\local_bi_boutique_assistant\storage\exports\Boutique_BI_Assistant_Presentation.pptx')
out_path2 = Path(r'c:\Users\akhil\Downloads\local_bi_boutique_assistant\Boutique_BI_Assistant_Presentation.pptx')

prs.save(str(out_path1))
prs.save(str(out_path2))

print('SUCCESS: Saved presentation to:')
print('  1.', out_path1)
print('  2.', out_path2)
