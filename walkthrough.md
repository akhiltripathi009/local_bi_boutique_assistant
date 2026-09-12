# Walkthrough: Master Circuit Controls Switchboard & Boutique Suite

## Root Cause Analysis & Fix: Master Circuit Controls Switchboard

### 1. Root Cause Analysis
When switching to the **⚙️ Inventory & Circuit Controls** tab (`tab-inventory`), the switchboard table was remaining stuck on `Loading circuit controls...`. Investigation revealed two primary issues:
1. **Missing Method in `switchTab`**: In [web/js/app.js](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/web/js/app.js), `switchTab('tab-inventory')` called `this.loadInventoryData()` and `this.loadCircuitControls()`. However, `loadInventoryData()` had not been defined on `App`. When the user selected the tab, a JavaScript runtime error (`TypeError: this.loadInventoryData is not a function`) halted execution, preventing `this.loadCircuitControls()` from running.
2. **Missing Startup Preload**: In `App.init()`, only `loadDashboardData()` and `loadCopilotMetadata()` were invoked; inventory controls were not pre-loaded.
3. **Browser Asset Caching**: `index.html` was referencing `app.js?v=2.3.2`, causing client browsers to reuse previous cached scripts.

### 2. Changes Implemented
- **[web/js/app.js](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/web/js/app.js)**:
  - Added `loadInventoryData()` to fetch `/api/inventory/overview` and populate both inventory totals and the Dual-Location Catalog table (`#inventory-table-tbody`).
  - Added `quickTransferModal()` for immediate inter-location stock relocations from depot to floor.
  - Hardened `renderCircuitControlsTable()` with `(item.missing_sizes || []).join(', ')` defensive fallback.
  - Added `this.loadInventoryData()` and `this.loadCircuitControls()` directly into `App.init()` so data renders immediately without waiting for tab clicks.
- **[web/index.html](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/web/index.html)**:
  - Bumped script query string to `?v=2.4.2` across `api.js`, `charts.js`, `tour.js`, and `app.js` to eliminate browser caching delays.

### 3. Verification
- Backend endpoint `GET /api/inventory/controls` verified returning 20 products with size matrices and circuit breakers.
- Backend endpoint `GET /api/inventory/overview` verified returning 16,718 shop units and 1,767 warehouse units.
- All test suites (`tests/test_missing_segments.py` and `tests/test_ui_and_agent_verification.py`) passed 100%.

---

## Root Cause Analysis & Fix: Executive PDF Report Section

### 1. Root Cause Analysis
When navigating to the **📄 Executive PDF Reports** tab (`tab-reports`), the section appeared completely empty / blank due to a critical DOM nesting issue:
1. **Unclosed `<section id="tab-agent">` Tag**: In [web/index.html](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/web/index.html), the preceding section (`#tab-agent`) was missing its closing `</section>` tag. As a result, `<section id="tab-reports">` was parsed by the browser DOM as a nested child of `#tab-agent`. Whenever any tab other than Shivi Deep Agent was selected, `#tab-agent` received `.tab-content:not(.active)` with `display: none;`, completely hiding the nested `#tab-reports` section and resulting in a blank screen.
2. **No Embedded PDF Viewer**: Originally, the report tab only contained raw summary text cards and download links without an embedded document viewport (`<iframe>`).
3. **`Content-Disposition: attachment` Header**: The FastAPI backend routes (`/enterprise-pdf`, `/opening-pdf`, `/closing-pdf`) returned hardcoded `Content-Disposition: attachment`, preventing modern browsers from rendering vector PDFs inside iframes.
4. **Missing Preload in `App.init()`**: `this.loadReportPreview('daily')` was not called during application startup.

### 2. Changes Implemented
- **[src/server/routes/reports.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/src/server/routes/reports.py)**:
  - Updated `/enterprise-pdf`, `/opening-pdf`, and `/closing-pdf` to support an optional `download: bool = False` query parameter.
  - When viewed in the browser or embedded in an iframe (the default `download=False`), headers output `Content-Disposition: inline; filename=...`, enabling full vector PDF rendering with pan, zoom, and print inside the DOM.
  - When the user clicks an explicit download action (`download=True`), headers output `Content-Disposition: attachment; filename=...`.
- **[web/index.html](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/web/index.html)**:
  - Added an **Interactive Live Executive PDF Document Viewer** card featuring:
    - Live ReportLab Platypus compilation status and active document filename badge (`MishikaBoutique_Daily_Audit.pdf`).
    - Full-height interactive PDF viewport `<iframe id="report-pdf-iframe" class="report-pdf-frame" src="/api/reports/enterprise-pdf?scope=daily">`.
    - Document action bar: **🔄 Recompile**, **🖨️ Print**, **↗️ Full Window**, and **📥 Download PDF**.
  - Retained the **Live On-Screen Scorecard Preview** (Total Revenue, COGS, Net Gross Profit, Procurement Inbound) and audited merchandise ledgers beneath the document viewer.
  - Bumped version cache busters to `?v=2.4.3` on `style.css`, `api.js`, `charts.js`, `tour.js`, and `app.js`.
- **[web/js/app.js](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/web/js/app.js)**:
  - Enhanced `loadReportPreview(scope)` to dynamically update the embedded PDF iframe `src` with a cache-buster timestamp and update document labels.
  - Added `refreshReportPdf()`, `printReportPdf()`, `openReportPdfNewTab()`, and `downloadEnterpriseReport()`.
  - Added `this.loadReportPreview('daily')` directly to `App.init()` for immediate startup preloading.
- **[web/css/style.css](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/web/css/style.css)**:
  - Added luxury styles for `.subtabs-bar`, `.subtab-btn` (with active gold glow and light/dark theme adaptation), and `.report-pdf-frame` (760px responsive height).
- **[web/js/api.js](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/web/js/api.js)**:
  - Updated `getEnterprisePdfUrl(scope, download)`, `getOpeningPdfUrl(download)`, and `getClosingPdfUrl(download)`.

### 3. Verification
- `GET /api/reports/enterprise-pdf?scope=daily`: verified HTTP 200 with `Content-Disposition: inline`.
- `GET /api/reports/enterprise-pdf?scope=daily&download=true`: verified HTTP 200 with `Content-Disposition: attachment`.
- `GET /api/reports/preview?scope=daily`: verified HTTP 200 with $331,084.50 revenue, $178,737.50 profit, 10 top merch rows, and 10 restock rows.
- Automated tests (`test_missing_segments.py` and `test_ui_and_agent_verification.py`) passed 100%.

---

## Root Cause Analysis & Fix: Category Revenue Contribution Dynamic Data

### 1. Root Cause Analysis
In [src/server/routes/dashboard.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/src/server/routes/dashboard.py), the `GET /api/dashboard/charts` endpoint evaluated:
```python
if not sales_df.empty and "category" in sales_df.columns:
```
However, the SQLite table `sales_ledger` does not contain a `category` column (it stores `product_id` and `product_name`). Because `"category" in sales_df.columns` was always `False`, the code fell into a fallback `else` branch that populated every category with identical hardcoded dummy data:
```python
cat_summary.append({"category": c, "revenue": 2450.0, "profit": 1380.0, "units": 18})
```
This resulted in all categories displaying an identical, static **$2,450.00** contribution.

### 2. Changes Implemented
- **[src/server/routes/dashboard.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/src/server/routes/dashboard.py)**:
  - Replaced the fallback with real SQL aggregations across `sales_ledger`.
  - Joined/mapped `product_id` and `product_name` to their registered boutique category via `src/core/catalog.py` (`CATALOG`).
  - Aggregated real cumulative revenue, gross profit, and unit volume per category (`Outerwear: $742k`, `Dresses: $428k`, `Bottoms: $325k`, `Knitwear: $295k`, `Tops: $205k`).
  - Updated the **Top 5 Profit Generating Styles** query to aggregate real profit across all sales transactions.
- **[web/js/charts.js](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/web/js/charts.js)**:
  - Configured `ChartsManager.initCategoryChart` with clean currency formatting (`$200k`, `$400k`, `$700k`) on the x-axis and integer rounded values on the data labels.
  - Enabled smooth redrawing via `updateOptions(options, true, true)`.
- **[web/index.html](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/web/index.html)**:
  - Bumped asset query strings to `?v=2.4.5`.

### 3. Verification
- Queried `GET /api/dashboard/charts`: verified 5 live categories with distinct revenue totals ranging from $204,544.80 to $742,440.75.
- Queried top 5 styles: verified real ranking headed by Suede Moto Jacket ($212,535 revenue) and Vegan Leather Trench Coat ($199,104 revenue).
- Automated tests (`test_missing_segments.py` and `test_ui_and_agent_verification.py`) passed 100%.

---

## Root Cause Analysis & Fix: Dynamic Executive Timeframe Switchboard & Financial KPIs

### 1. Root Cause Analysis
The executive metrics **Gross Net Revenue**, **Atelier Gross Profit**, **Realized Margin**, and **Sell-Through Rate** appeared static and unresponsive to broader business cycles for two key reasons:
1. **Hardcoded Row Limit (Arbitrary Fixed Sample)**: In [src/server/routes/dashboard.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/src/server/routes/dashboard.py), `get_dashboard_stats()` executed `sales_df = db.fetch_logs(DBTable.SALES_LEDGER, limit=500)`. This queried only the first 500 records regardless of store volume or dates, ignoring the remaining 30,000+ live transactions in SQLite and preventing leaders from inspecting full performance.
2. **Missing Time-Horizon Selection**: Neither `/api/dashboard/stats` nor `/api/dashboard/charts` accepted a timeframe parameter. The dashboard could only display one fixed view without allowing leadership to audit **Hourly**, **Daily**, **Monthly**, or **Yearly** performance.

### 2. Changes Implemented
- **[src/server/routes/dashboard.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/src/server/routes/dashboard.py)**:
  - Added helper `_get_timeframe_filter(timeframe: str)` supporting four distinct audit horizons:
    - **Hourly**: `timestamp >= datetime((SELECT MAX(timestamp) FROM sales_ledger), '-1 hour')`
    - **Daily**: `timestamp >= datetime((SELECT MAX(timestamp) FROM sales_ledger), '-24 hours')`
    - **Monthly**: `timestamp >= datetime((SELECT MAX(timestamp) FROM sales_ledger), '-30 days')`
    - **Yearly**: `1=1` (All-Time lifetime transactional records)
  - Updated `GET /api/dashboard/stats?timeframe={tf}` to run direct SQLite aggregations for `total_revenue`, `gross_profit`, `units_sold`, `realized_margin_pct`, and `sell_through_rate_pct`.
  - Updated `GET /api/dashboard/charts?timeframe={tf}`:
    - **Hourly**: Aggregates sales velocity into 10-minute intervals (`21:50`, `22:00`, `22:10`, `22:20`, `22:30`).
    - **Daily**: Aggregates sales velocity into hourly intervals (`14:00`, `15:00`, ..., `23:00`).
    - **Monthly**: Aggregates sales into daily intervals (`08/27`, `08/30`, ..., `09/11`).
    - **Yearly**: Aggregates sales into monthly buckets (`2026-08`, `2026-09`).
    - Recalculates category revenue contribution and top-selling couture styles for each horizon.
- **[web/index.html](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/web/index.html)**:
  - Added **Executive Timeframe Horizon Switchboard** toolbar above the KPI grid with luxury pill buttons:
    - `⏱️ Hourly (Past 1h)`
    - `🌅 Daily (Past 24h)` (default active)
    - `📆 Monthly (Past 30d)`
    - `🏛️ Annual / Yearly (All-Time)`
  - Added dynamic IDs for KPI subtext, chart headers, and style rankings (`dash-velocity-chart-title`, `dash-velocity-chart-sub`, `dash-category-chart-sub`, `dash-top-styles-title`, `dash-top-styles-sub`, `dash-top-styles-badge`).
  - Bumped asset query strings to `?v=2.4.7`.
- **[web/css/style.css](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/web/css/style.css)**:
  - Added luxury glassmorphism styling for `.dash-timeframe-container`, `.dash-timeframe-pills`, and `.dash-timeframe-btn`.
  - Implemented gold glow borders for active selection in dark mode and warm amber tones (`#fef9c3` / `#b8860b`) in light mode.
- **[web/js/api.js](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/web/js/api.js)**:
  - Updated `getDashboardStats(timeframe = 'daily')` and `getDashboardCharts(timeframe = 'daily')` to pass `?timeframe=...`.
- **[web/js/charts.js](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/web/js/charts.js)**:
  - Configured `initCategoryChart` and `initHourlySalesChart` to destroy and recreate previous ApexCharts instances when horizons change, preventing stale category caching and ensuring clean redraws.
- **[web/js/app.js](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/web/js/app.js)**:
  - Added `dashboardTimeframe: 'daily'` to `App.state` with alias support for `'annual'`, `'annually'`, `'yearly'`.
  - Implemented `App.onDashboardTimeframeSelected(timeframe)` for instantaneous UI updates and API queries.
  - Enhanced `App.loadDashboardData(showLoading, timeframe)` to dynamically render KPIs, recalculate the Category Revenue Contribution bar chart, and re-rank the Best-Selling Couture Pieces table with ranks (`#1` to `#5`), formatted revenues, and unit volumes.

### 3. Verification & Live Metrics
Executed live automated test suites on the running server (`tests/test_dashboard_timeframes.py`, `tests/test_saas_api.py`, `tests/test_missing_segments.py`, and `tests/test_ui_and_agent_verification.py`):
| Timeframe Horizon | Gross Net Revenue | Atelier Gross Profit | Realized Margin | Sell-Through Rate | Top Category Contribution | #1 Best-Selling Couture Piece |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Hourly (1h)** | **$302,435.70** | **$146,981.70** | **48.6%** | **21.2%** | Outerwear: **$109,965.00** | Suede Moto Jacket: **$36,202.50** (277 units) |
| **Daily (24h)** | **$888,897.70** | **$481,476.70** | **54.2%** | **41.4%** | Outerwear: **$289,635.00** | Suede Moto Jacket: **$97,751.25** (660 units) |
| **Monthly (30d)**| **$2,246,888.10** | **$1,328,070.10** | **59.1%** | **61.3%** | Outerwear: **$868,271.25** | Suede Moto Jacket: **$254,722.50** (1,443 units) |
| **Annual (All-Time)** | **$2,246,888.10** | **$1,328,070.10** | **59.1%** | **61.3%** | Outerwear: **$868,346.25** | Suede Moto Jacket: **$254,722.50** (1,443 units) |

All 4 test suites passed with 100% success.

---

## 1. Summary of Changes

### A. Live Retail Intelligence & RAG Synthesis ([insight_generator_ollama.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/insight_generator_ollama.py))
- **Automated Live Context Builder (`build_live_boutique_context`)**:
  - Dynamically synthesizes real-time metrics directly from SQLite ledgers:
    - Cumulative revenue, total COGS, gross profit, and realized gross margin %.
    - Top 5 Hot Sellers vs. bottom 5 Dead Inventory Risks.
    - Safety stock alerts for all items with stock balance $\le 15$ units.
    - Broken size curve breaches (missing S/M/L) with stranded unit counts.
    - Competitor price index benchmarks (Underpriced Hazards vs. Premium Positioned).
    - Customer review sentiment polarity scores by operational category.
- **Three Strategic Advisory Personas**:
  1. 👔 **Senior Merchandise Director**: Decisive, boardroom-level inventory strategist focusing on sell-through velocity, stock-to-sales ratios, inventory turns, and cash flow defense.
  2. 🏷️ **Pricing & Margin Strategist**: Competitive price benchmark analyst focusing on price elasticity, eliminating underpriced hazards, and margin preservation.
  3. ✨ **Mishika Fashion & Styling Curator**: Luxury brand curator evaluating fabrication sentiment, customer fit issues, size curve balance, and assortment harmony.
- **Token-by-Token Streaming (`stream_copilot_response`)**:
  - Leverages `ollama.chat(stream=True)` to stream tokens natively with zero blocking.
  - Formats high-density system prompts with real-time boutique data and conversation history.
  - Built-in graceful error handling that diagnoses Ollama connection status if paused.
---

## 9. Global Brand Name Alignment: HAUTE $\rightarrow$ Mishika

Every reference to `HAUTE`, `Haute`, or `haute` has been replaced with `Mishika` across all codebase layers, templates, animations, test suites, and database entries:

1. **Storefront & Canvas Animation**:
   - [src/ui/theme.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/src/ui/theme.py): Canvas banner lettering updated to `MISHIKA BOUTIQUE`.
2. **AI Advisory Personas & Ollama Studio**:
   - [src/ai/ollama_client.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/src/ai/ollama_client.py): Executive persona updated to `✨ Mishika Fashion & Styling Curator`.
   - [storage/exports/generate_ppt.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/storage/exports/generate_ppt.py): Slide deck card updated to `Mishika Fashion & Styling Curator`.
3. **Deep Agent (Shivi) Subagents & Routines**:
   - [src/deep_agent/subagents.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/src/deep_agent/subagents.py): PDF audit filenames updated to `MishikaBoutique_Opening_Briefing_...pdf` and `MishikaBoutique_Closing_Audit_...pdf`. Fashion news subject and snippets updated to `Mishika Trend Alert` and `Mishika luxury fashion`.
   - [src/deep_agent/planner.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/src/deep_agent/planner.py): Plan item updated to `Curate Mishika Fashion Trends`.
   - [src/deep_agent/context.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/src/deep_agent/context.py): Skill and system prompts updated to `Mishika Fashion Trend Curation` and `Mishika luxury brand voice`.
   - [src/deep_agent/fault_tolerance.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/src/deep_agent/fault_tolerance.py): Email subjects updated to `✨ Curated Mishika Fashion Alert`.
   - [src/deep_agent/orchestrator.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/src/deep_agent/orchestrator.py) & [src/ui/deep_agent_view.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/src/ui/deep_agent_view.py): Trend spinners and orchestration updated.
4. **App & PDF Exports**:
   - [app.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/app.py): Audit PDF filenames updated to `MishikaBoutique_...pdf`.
5. **Database & Customer Records**:
   - [src/data/db_manager.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/src/data/db_manager.py): Customer email seed domain updated from `gulf-haute.ae` to `gulf-mishika.ae`.
   - SQLite DB (`storage/db/boutique_bi.db`): All tables scanned and updated; `0` occurrences of `haute` remain.
6. **Documentation & Tests**:
   - [README.md](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/README.md), [SYSTEM_SEGMENTS_GUIDE.md](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/SYSTEM_SEGMENTS_GUIDE.md), [docs/SYSTEM_SEGMENTS_GUIDE.md](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/docs/SYSTEM_SEGMENTS_GUIDE.md), and [tests/test_portal_and_agent.py](file:///c:/Users/akhil/Downloads/local_bi_boutique_assistant/tests/test_portal_and_agent.py) updated.
   - All 18 automated tests passing (`Ran 18 tests in 18.080s - OK`).

#### 1. Enhanced Embedded Copilot on Executive Dashboard
- **Modern Conversational Container**: Replaced the static form with scrollable `st.chat_message` containers and persistent `st.session_state.copilot_messages`.
- **1-Click Executive Prompt Chips**: Instant-click pills triggering automated strategic audits:
  - 🚀 *"Top Margin Drivers"*
  - ⚠️ *"Broken Size Curve Risks"*
  - 🏷️ *"Competitor Pricing Hazards"*
  - 📦 *"48-Hour Restock Plan"*
  - 📢 *"Dead Stock Clearance Plan"*
- **Quick-Jump Studio Action**: `Open Copilot Studio ↗️` button that switches tabs instantly.

#### 2. Dedicated 5th Module: `🤖 AI Copilot Studio`
- **Full-Screen Command Center**:
  - **Top Control Bar**: Persona switcher dropdown, local model selector, live status indicator (🟢 *Ollama Active*), and a `🧹 Reset Chat` button.
  - **Left Column (38% width) - Live Store Knowledge Inspector**: Real-time visual cards displaying the exact SQLite metrics fed into the LLM system prompt:
    - 📊 *Financial Health* (Revenue, Margin %, Est COGS)
    - ⚡ *Sell-Through Velocity* (Hot Sellers & Dead Stock)
    - ⚠️ *Critical Stock & Curve Alerts* (Low stock balances & missing sizes)
    - 🏬 *Market Benchmarks & Sentiment* (Underpriced hazards & review polarity)
  - **Right Column (62% width) - Strategic Advisory Workbench**:
    - 1-Click Executive Prompt Chips toolbar.
    - Large 480px scrollable chat container with streaming token output.
    - Streamlit `chat_input` for follow-ups and custom scenarios.

---

## 2. Verification & Testing

### Automated Unit Checks
1. **Ollama Integration & RAG Context Test**:
   ```powershell
   .\.venv\Scripts\python.exe -c "from insight_generator_ollama import LocalOllamaBoutiqueAnalyst, PERSONAS, PRESET_PROMPT_CHIPS; from database_manager import DatabaseManager; db = DatabaseManager(); a = LocalOllamaBoutiqueAnalyst(); ctx = a.build_live_boutique_context(db); print('Verified models:', a.get_available_models()); print('Context keys:', list(ctx.keys()))"
   ```
   *Result*: `PASSED` — Successfully discovered `llama3.2:3b` & `mistral:latest` and compiled all 8 real-time context categories.

2. **Application Compilation Test**:
   ```powershell
   .\.venv\Scripts\python.exe -c "import app1; print('app1 compiled and loaded successfully!')"
   ```
   *Result*: `PASSED` — Code cleanly loaded without any syntax errors or missing imports.

3. **Streaming Token Generation Test**:
   *Result*: `PASSED` — Successfully streamed initial tokens via `ollama.chat(stream=True)`.

---

## 3. How to Use the Upgraded Copilot

Launch the application:
```powershell
.\.venv\Scripts\python.exe -m streamlit run app1.py
```

### In the Executive Dashboard:
1. Scroll to the bottom of the **📊 Executive Dashboard**.
2. Click any of the 1-click prompt chips (e.g. 🚀 **"Top Margin Drivers"**) to trigger an instant analysis.
3. Watch the answer stream token-by-token with exact dollar figures and merchandise style names.
4. Type follow-up questions in the input bar (e.g., *"What pricing adjustment should we make for that?"*).

### In the AI Copilot Studio:
1. In the left sidebar, click **🤖 AI Copilot Studio**.
2. Inspect the **Live Store Knowledge Inspector** on the left to review the exact financial, inventory, and competitor data available to the AI.
3. Switch advisory personas (e.g. from *Senior Merchandise Director* to *Pricing & Margin Strategist*) to adjust the analytical tone.
4. Use the model dropdown to switch between installed models (e.g. `llama3.2:3b` vs `mistral:latest`).
5. Carry on an interactive back-and-forth strategic conversation.
