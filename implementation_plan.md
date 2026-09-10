# Implementation Plan: AI-Powered Enterprise PDF Audits & Interactive FAQs for Copilot Studio

This plan introduces two major enhancements to the **Boutique AI Copilot Studio**:
1. **Ollama-Powered Enterprise PDF Audit Reports**: Generate Weekly, Monthly, or Comprehensive Strategic Analysis reports where local Ollama synthesizes live store ledgers into executive commentary, compiled into boardroom-grade downloadable PDFs via ReportLab.
2. **Interactive Categorized FAQ Knowledge Hub**: A curated repository of executive boutique questions organized by domain (Financials, Inventory, Competitor Pricing, Customer Sentiment) that users can ask with 1 click.

---

## User Review Required

> [!IMPORTANT]
> **Ollama Executive Commentary in PDF**:
> When generating an AI audit report, local Ollama (`llama3.2:3b` or `mistral:latest`) will analyze the selected timeframe's sales, COGS, margins, restocks, size curves, and competitor pricing to write a structured executive commentary. This narrative will be permanently embedded in the generated PDF alongside the audited tables and financial scorecard.

> [!NOTE]
> **Report Timeframe Scopes**:
> - 📅 **Weekly Audit**: Analyzes the last 7 calendar days.
> - 🗓️ **Monthly Audit**: Analyzes the last 30 calendar days.
> - 📊 **Comprehensive Strategic Analysis**: Full all-time database synthesis with deep multi-angle retail recommendations.

---

## Proposed Changes

### 1. AI Strategic Report Generator ([insight_generator_ollama.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/insight_generator_ollama.py))
- **Add `generate_executive_audit_commentary(report_data, timeframe_label, model)`**:
  - Takes the aggregated financial metrics, top sellers, dead stock, restock spend, broken curves, and competitor positions from `fetch_report_datasets`.
  - Prompts Ollama with a specialized Boardroom Executive Auditor prompt.
  - Generates four structured commentary sections:
    1. *Executive Summary & Financial Health Assessment*
    2. *Merchandising Sell-Through & Margin Diagnoses*
    3. *Inventory Safeguards, Safety Stock & Curve Outages*
    4. *Strategic Pricing & Actionable Next Steps*
  - Returns formatted commentary for on-screen preview and PDF compilation.
- **Add Curated FAQ Knowledge Bank (`COPILOT_FAQS`)**:
  - Organized by 4 strategic boutique themes:
    - 📈 **Financial & Profit Margins**
    - ⚠️ **Inventory & Safety Stock**
    - 🏬 **Pricing & Market Competitors**
    - 🧵 **Customer Sentiment & Assortment**

---

### 2. PDF Reporting Engine ([pdf_generator.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/pdf_generator.py))
- **Add `"monthly"` Scope to `fetch_report_datasets(db, report_type)`**:
  - Filters sales and purchase ledgers for the preceding 30 days (`days=29`).
- **Support AI Commentary in `generate_enterprise_pdf(db, report_type, ai_commentary=None)`**:
  - When `ai_commentary` is supplied, dynamically construct a branded **"AI Executive Strategic Advisory & Analysis"** section in the PDF flowable story:
    - Slate and gold callout banner with model attribution tag (`"Synthesized by Local Ollama Llama-3.2"`).
    - Formatted paragraphs, bold highlights, and clean typography.
  - Retains all corporate letterhead branding, 4-card KPI scorecard, top 10 merchandise table, supply chain restock audit log, and two-pass `Page X of Y` footers.

---

### 3. AI Copilot Studio UI ([app1.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/app1.py))
- **Add Interactive FAQ Knowledge Hub**:
  - Positioned above the chat input with category tabs:
    - 📈 *Financials* | ⚠️ *Inventory* | 🏬 *Pricing* | 🧵 *Sentiment*
  - Interactive pill buttons for each FAQ. Clicking an FAQ immediately routes the question into the live Copilot chat stream.
- **Add AI Executive Strategic Audit Hub in Studio**:
  - Radio toggle for report timeframe: **Weekly Audit (7 Days)**, **Monthly Audit (30 Days)**, or **Comprehensive Strategic Analysis**.
  - **"🚀 Generate AI Strategic Audit Report"** button.
  - Live on-screen scorecard & executive commentary preview card.
  - Instant **📥 Download Enterprise Audit PDF** button with branded filename.

---

## Verification Plan

### Automated Verification
1. **Ollama Commentary Unit Test**:
   - Verify `generate_executive_audit_commentary` produces valid structured text for weekly and monthly scopes:
     ```powershell
     .\.venv\Scripts\python.exe -c "from database_manager import DatabaseManager; from pdf_generator import fetch_report_datasets; from insight_generator_ollama import LocalOllamaBoutiqueAnalyst; db = DatabaseManager(); a = LocalOllamaBoutiqueAnalyst(); d = fetch_report_datasets(db, 'weekly'); c = a.generate_executive_audit_commentary(d, 'Weekly'); print('Weekly commentary generated, length:', len(c))"
     ```
2. **Monthly & AI PDF Generation Test**:
   - Verify PDF compilation with AI commentary for monthly scope:
     ```powershell
     .\.venv\Scripts\python.exe -c "from database_manager import DatabaseManager; from pdf_generator import generate_enterprise_pdf; db = DatabaseManager(); pdf = generate_enterprise_pdf(db, 'monthly', ai_commentary='Test AI executive analysis commentary.'); print('Monthly PDF generated successfully! Size:', len(pdf), 'bytes')"
     ```
3. **App Compilation Test**:
   - Verify `app1.py` compiles cleanly without import or syntax errors:
     ```powershell
     .\.venv\Scripts\python.exe -c "import app1; print('app1 compiled cleanly!')"
     ```

### Manual Verification
1. Run `streamlit run app1.py` and navigate to **🤖 AI Copilot Studio**.
2. Test the **Interactive FAQs**: Click questions across all 4 categories and verify the AI streams real-time responses with live data.
3. Test the **AI Report Generator**:
   - Select **Monthly Audit**.
   - Click **Generate AI Strategic Audit Report**.
   - Verify the on-screen executive narrative preview.
   - Click **Download Enterprise PDF Report** and open the PDF to confirm the AI commentary is rendered with professional letterhead and tables.
