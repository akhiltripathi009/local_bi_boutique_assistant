# Walkthrough: Advanced Boutique AI Copilot Engine & Studio

This walkthrough documents the comprehensive elevation of the **Boutique AI Copilot** into an enterprise-grade retail intelligence workstation with dual deployment across both the **Executive Dashboard** and a dedicated full-screen **AI Copilot Studio**.

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
