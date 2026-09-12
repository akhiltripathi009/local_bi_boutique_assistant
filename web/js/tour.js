/**
 * Mishika Fashion Luxury Boutique - In-UI Interactive Guided Architecture Tour
 * 
 * Provides an interactive spotlight tour with:
 * - Floating icon-only launcher
 * - Dashboard-covering glassmorphic popup modal
 * - Cross icon on TOP-LEFT corner
 * - Arrow navigation buttons (← / →)
 * - Concise, icon-driven summary cards
 * - Collapsible "ℹ️ Details & Code" info drawer
 * - Self-contained CSS injection (immune to browser stylesheet caching)
 */

const BoutiqueTour = {
  currentStepIndex: 0,
  isActive: false,
  detailsOpen: false,

  steps: [
    {
      id: 'welcome',
      tabId: 'tab-dashboard',
      targetSelector: '.brand-section',
      icon: '🏛️',
      title: 'System Architecture & 3 Pillars',
      badge: '1 / 7',
      pillar: 'Platform Core',
      summary: [
        { icon: '🔒', title: '100% On-Premises', text: 'Zero cloud data leaks: local SQLite database and local Ollama AI weights.' },
        { icon: '⚡', title: '3 Pillars', text: 'Discrete POS Simulation + Statistical BI Analytics + Shivi Autonomous Deep Agent.' },
        { icon: '🚀', title: 'Modern Stack', text: 'FastAPI backend with real-time SSE streaming and a high-performance Vanilla JS SPA.' }
      ],
      details: {
        concept: 'An autonomous, boardroom-grade retail intelligence platform built specifically for luxury boutiques.',
        flow: 'SQLite persistence (ACID) ➔ FastAPI REST & SSE streaming ➔ Vanilla JS Atelier SPA ➔ Local Ollama LLM.',
        code: 'src/core/constants.py • src/server/app.py • src/core/config.py'
      }
    },
    {
      id: 'dashboard',
      tabId: 'tab-dashboard',
      targetSelector: '#tab-dashboard .kpi-grid',
      icon: '📈',
      title: 'Executive KPIs & Retail Math',
      badge: '2 / 7',
      pillar: 'Analytics & BI',
      summary: [
        { icon: '💰', title: 'Gross Revenue & Margin', text: 'Tracks realtime register revenue, gross margins, and COGS calculations.' },
        { icon: '⚡', title: 'Sell-Through Rate (STR)', text: 'Measures inventory sales velocity (>80% = stockout risk; <35% = dead stock).' },
        { icon: '🎯', title: 'What-If Repricing', text: 'Simulates price elasticity against Zara, Mango, and Massimo Dutti benchmarks.' }
      ],
      details: {
        concept: 'Commercial health monitoring using mathematical retail formulas (STR %, Gross Margin %, Safety Stock).',
        flow: 'GET /api/dashboard/kpis aggregates sales_ledger and compares against stock receipts.',
        code: 'src/server/routes/dashboard.py • src/analytics/inventory.py • src/analytics/competitor.py'
      }
    },
    {
      id: 'live_ops',
      tabId: 'tab-live-ops',
      targetSelector: '#tab-live-ops .controls-card',
      icon: '⚡',
      title: 'Live Shop Operations & Simulation',
      badge: '3 / 7',
      pillar: 'POS Simulation',
      summary: [
        { icon: '🚶‍♀️', title: 'Virtual Shoppers', text: 'Simulates walk-in customer footfall, style browsing, and checkout decisions.' },
        { icon: '🚚', title: 'Supplier Restocks', text: 'Delivery trucks periodically arrive and deposit replenishment units into the warehouse.' },
        { icon: '📡', title: 'SSE Live Stream', text: 'Real-time event fan-out pushes transaction tickers and stock decrements to the canvas.' }
      ],
      details: {
        concept: 'Discrete event simulation of luxury boutique dynamics without requiring live physical POS hardware.',
        flow: 'SimulationEngine ticks ➔ decrements size_matrix_stock ➔ emits payload via GET /api/live-ops/stream.',
        code: 'src/simulation/engine.py • src/server/routes/live_operations.py • web/js/app.js'
      }
    },
    {
      id: 'inventory',
      tabId: 'tab-inventory',
      targetSelector: '#tab-inventory .data-table-container',
      icon: '📦',
      title: 'Dual-Location Inventory Isolation',
      badge: '4 / 7',
      pillar: 'Stock Portal',
      summary: [
        { icon: '🏬', title: 'Shop Floor Display', text: 'Visible on display racks. Customer checkouts deduct strictly from this location.' },
        { icon: '🏭', title: 'Warehouse Reserve', text: 'Isolated in backroom boxes. Supplier shipments land here and stay invisible to shoppers.' },
        { icon: '🔄', title: 'ACID Transfers', text: 'Move units between Shop Floor and Warehouse with an immutable audit ledger.' }
      ],
      details: {
        concept: 'Luxury apparel enforces strict isolation: display stock vs backroom reserve.',
        flow: 'POST /api/inventory/transfer applies atomic SQLite transaction across size_matrix_stock and warehouse_stock.',
        code: 'src/data/db_manager.py (transfer_stock) • src/server/routes/inventory.py'
      }
    },
    {
      id: 'crm',
      tabId: 'tab-crm',
      targetSelector: '#tab-crm .data-table-container',
      icon: '👑',
      title: 'VIP Client CRM & Attribution',
      badge: '5 / 7',
      pillar: 'Clienteling',
      summary: [
        { icon: '👥', title: '20 VIP Patron Dossiers', text: 'Comprehensive profiles tracking lifetime spend, preferred sizes, and visit frequency.' },
        { icon: '💎', title: 'Loyalty Tiers', text: 'Automated categorization into Bronze, Silver, Gold, and Platinum status.' },
        { icon: '🎂', title: 'Anniversary & Birthday Perks', text: '14-day proactive alerts for concierge gifts and targeted invitations.' }
      ],
      details: {
        concept: 'High-touch luxury clienteling and retention with automated purchase attribution.',
        flow: 'GET /api/crm/customers joins customers table with recent sales_ledger records for RFM scoring.',
        code: 'src/server/routes/crm.py • src/simulation/customer_profiles.py • src/data/db_manager.py'
      }
    },
    {
      id: 'agent',
      tabId: 'tab-agent',
      targetSelector: '#tab-agent .glass-card',
      icon: '🧠',
      title: 'Shivi Deep Agent & Safety Guardrails',
      badge: '6 / 7',
      pillar: 'Autonomous AI',
      summary: [
        { icon: '📋', title: 'Autonomous Routines', text: 'Prepares Morning Opening Briefings, Evening Closing Audits, and VIP Campaigns.' },
        { icon: '🛡️', title: 'Active Guardrails', text: 'Regex PII redaction (emails/phones) and enterprise 50.0% max discount safety cap.' },
        { icon: '✍️', title: 'HITL Steering', text: 'High-risk actions queue for human manager approval before live dispatch.' }
      ],
      details: {
        concept: 'Autonomous executive retail assistant capable of multi-step planning and guarded actions.',
        flow: 'POST /api/agent/run-action ➔ checks guardrails ➔ queues HITL or dispatches via SMTP/wa.me.',
        code: 'src/deep_agent/orchestrator.py • src/deep_agent/guardrails.py • src/deep_agent/steering.py'
      }
    },
    {
      id: 'reports_copilot',
      tabId: 'tab-dashboard',
      targetSelector: '#btn-open-copilot',
      icon: '📄',
      title: 'Boardroom Decks & AI Copilot',
      badge: '7 / 7',
      pillar: 'Executive AI',
      summary: [
        { icon: '📑', title: 'ReportLab PDFs', text: 'Download official boardroom-ready Morning and Evening PDF audit documents.' },
        { icon: '📊', title: '16:9 Presentation Deck', text: 'Instantly exports an executive PowerPoint (.pptx) pitch presentation.' },
        { icon: '🦙', title: 'Offline Copilot Studio', text: 'Chat with local Ollama models (Llama 3.2 / Mistral) using live boutique RAG.' }
      ],
      details: {
        concept: 'Boardroom-grade reporting coupled with an on-premises contextual RAG copilot.',
        flow: 'PDFs generated on-the-fly via ReportLab Platypus; Copilot streams via POST /api/copilot/chat SSE.',
        code: 'src/server/routes/reports.py • src/ai/ollama_client.py • src/server/routes/copilot.py'
      }
    }
  ],

  /**
   * Injects self-contained CSS styles directly into document head.
   * This completely eliminates browser stylesheet caching issues.
   */
  injectStyles() {
    let style = document.getElementById('boutique-tour-injected-styles');
    if (!style) {
      style = document.createElement('style');
      style.id = 'boutique-tour-injected-styles';
      document.head.appendChild(style);
    }
    style.textContent = `
      /* 1. Floating Tour Launcher */
      .fab-tour-launcher {
        position: fixed !important;
        bottom: 26px !important;
        right: 26px !important;
        width: 56px !important;
        height: 56px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #fde047 0%, #d4af37 50%, #aa820a 100%) !important;
        border: 2px solid rgba(255, 255, 255, 0.5) !important;
        box-shadow: 0 8px 28px rgba(212, 175, 55, 0.5), 0 0 16px rgba(212, 175, 55, 0.3) !important;
        cursor: pointer !important;
        z-index: 9999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        outline: none !important;
      }
      .fab-tour-launcher:hover {
        transform: scale(1.12) translateY(-3px) !important;
        box-shadow: 0 14px 34px rgba(212, 175, 55, 0.65), 0 0 24px rgba(212, 175, 55, 0.45) !important;
      }
      .fab-tour-icon {
        font-size: 26px !important;
        line-height: 1 !important;
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3)) !important;
      }
      .fab-tour-ring {
        position: absolute !important;
        inset: -6px !important;
        border-radius: 50% !important;
        border: 2px solid rgba(212, 175, 55, 0.6) !important;
        animation: fabPulseRing 2.4s cubic-bezier(0.25, 0, 0.2, 1) infinite !important;
        pointer-events: none !important;
      }
      @keyframes fabPulseRing {
        0% { transform: scale(0.9); opacity: 0.9; }
        70% { transform: scale(1.45); opacity: 0; }
        100% { transform: scale(1.5); opacity: 0; }
      }

      /* 2. Full Dashboard Coverage Backdrop */
      .tour-backdrop {
        position: fixed !important;
        inset: 0 !important;
        background: rgba(5, 8, 16, 0.85) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        z-index: 99990 !important;
        animation: tourBackdropFade 0.25s ease !important;
      }
      @keyframes tourBackdropFade {
        from { opacity: 0; }
        to { opacity: 1; }
      }

      /* 3. Compact Popup Window */
      .tour-card-compact {
        position: fixed !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        width: 92% !important;
        max-width: 550px !important;
        background: #0f172a !important;
        border: 1px solid rgba(212, 175, 55, 0.45) !important;
        box-shadow: 0 28px 72px rgba(0, 0, 0, 0.8), 0 0 36px rgba(212, 175, 55, 0.25) !important;
        border-radius: 20px !important;
        z-index: 100000 !important;
        overflow: hidden !important;
        display: flex !important;
        flex-direction: column !important;
        animation: tourPopupScaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        font-family: 'Inter', -apple-system, sans-serif !important;
        color: #f8fafc !important;
      }
      @keyframes tourPopupScaleIn {
        from { opacity: 0; transform: translate(-50%, -46%) scale(0.94); }
        to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
      }

      /* Top Progress Bar */
      .tour-progress-bar-container {
        width: 100% !important;
        height: 4px !important;
        background: rgba(255, 255, 255, 0.08) !important;
      }
      .tour-progress-bar {
        height: 100% !important;
        background: linear-gradient(90deg, #d4af37, #fde047) !important;
        width: 14% !important;
        transition: width 0.35s ease !important;
      }

      /* Header with Cross on TOP LEFT */
      .tour-compact-header {
        position: relative !important;
        display: flex !important;
        align-items: center !important;
        padding: 16px 20px 10px 62px !important;
      }
      .tour-close-top-left {
        position: absolute !important;
        top: 14px !important;
        left: 16px !important;
        width: 32px !important;
        height: 32px !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        background: rgba(255, 255, 255, 0.06) !important;
        color: #94a3b8 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
      }
      .tour-close-top-left:hover {
        color: #fb7185 !important;
        background: rgba(244, 63, 94, 0.15) !important;
        border-color: rgba(244, 63, 94, 0.4) !important;
        transform: scale(1.1) !important;
      }
      .tour-header-center {
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
      }
      .tour-hero-icon {
        font-size: 32px !important;
        animation: tourFloatIcon 3s ease-in-out infinite !important;
      }
      @keyframes tourFloatIcon {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-4px); }
      }
      .tour-title-compact {
        font-family: 'Playfair Display', Georgia, serif !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        color: #f3e5ab !important;
        margin: 0 0 3px 0 !important;
      }
      .tour-sub-badges {
        display: flex !important;
        gap: 6px !important;
        align-items: center !important;
      }
      .tour-badge-pill {
        font-size: 10px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        padding: 2px 8px !important;
        border-radius: 999px !important;
        background: rgba(56, 189, 248, 0.15) !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
      }
      .tour-badge-step {
        font-size: 10px !important;
        font-weight: 700 !important;
        padding: 2px 8px !important;
        border-radius: 999px !important;
        background: rgba(212, 175, 55, 0.15) !important;
        color: #f3e5ab !important;
        border: 1px solid rgba(212, 175, 55, 0.3) !important;
      }

      /* Summary Cards */
      .tour-cards-container {
        padding: 8px 20px 12px 20px !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
      }
      .tour-summary-card {
        display: flex !important;
        align-items: flex-start !important;
        gap: 12px !important;
        background: rgba(255, 255, 255, 0.035) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        transition: all 0.2s ease !important;
        animation: tourCardEnter 0.3s ease forwards !important;
      }
      @keyframes tourCardEnter {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .tour-summary-card:hover {
        background: rgba(212, 175, 55, 0.07) !important;
        border-color: rgba(212, 175, 55, 0.3) !important;
        transform: translateX(3px) !important;
      }
      .tour-summary-icon {
        font-size: 20px !important;
        line-height: 1.2 !important;
      }
      .tour-summary-body {
        flex: 1 !important;
      }
      .tour-summary-title {
        font-size: 12.5px !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        margin-bottom: 2px !important;
      }
      .tour-summary-text {
        font-size: 12px !important;
        line-height: 1.45 !important;
        color: #94a3b8 !important;
      }

      /* Collapsible Info Drawer */
      .tour-info-drawer {
        padding: 0 20px 12px 20px !important;
      }
      .tour-info-toggle-btn {
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        background: rgba(212, 175, 55, 0.06) !important;
        border: 1px dashed rgba(212, 175, 55, 0.35) !important;
        border-radius: 10px !important;
        padding: 8px 12px !important;
        font-size: 11.5px !important;
        color: #f3e5ab !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
      }
      .tour-info-toggle-btn:hover {
        background: rgba(212, 175, 55, 0.12) !important;
        border-color: #d4af37 !important;
      }
      .tour-details-content {
        margin-top: 8px !important;
        background: rgba(0, 0, 0, 0.45) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        padding: 10px 12px !important;
        font-size: 11.5px !important;
      }
      .tour-detail-row {
        margin-bottom: 6px !important;
        line-height: 1.45 !important;
      }
      .tour-detail-label {
        font-weight: 700 !important;
        color: #f3e5ab !important;
        margin-right: 4px !important;
      }
      .tour-detail-val {
        color: #94a3b8 !important;
      }
      .tour-detail-code {
        display: block !important;
        margin-top: 4px !important;
        padding: 6px 10px !important;
        background: rgba(15, 23, 42, 0.8) !important;
        border-radius: 6px !important;
        border-left: 3px solid #d4af37 !important;
        color: #7dd3fc !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 11px !important;
      }

      /* Arrow Navigation Footer */
      .tour-compact-footer {
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        padding: 12px 20px 16px 20px !important;
        border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
        background: rgba(0, 0, 0, 0.25) !important;
      }
      .tour-nav-arrow-btn {
        width: 46px !important;
        height: 46px !important;
        border-radius: 50% !important;
        border: 1.5px solid rgba(212, 175, 55, 0.5) !important;
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.2), rgba(212, 175, 55, 0.06)) !important;
        color: #f3e5ab !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        outline: none !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
      }
      .tour-nav-arrow-btn:hover:not(:disabled) {
        background: linear-gradient(135deg, #fde047, #d4af37) !important;
        color: #0f172a !important;
        box-shadow: 0 4px 18px rgba(212, 175, 55, 0.55) !important;
        transform: scale(1.1) !important;
      }
      .tour-nav-arrow-btn:active:not(:disabled) {
        transform: scale(0.95) !important;
      }
      .tour-nav-arrow-btn:disabled {
        opacity: 0.25 !important;
        cursor: not-allowed !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
      }
      .tour-dots {
        display: flex !important;
        gap: 6px !important;
        align-items: center !important;
      }
      .tour-dot {
        width: 7px !important;
        height: 7px !important;
        border-radius: 50% !important;
        background: rgba(255, 255, 255, 0.2) !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
      }
      .tour-dot.active {
        width: 22px !important;
        border-radius: 10px !important;
        background: #d4af37 !important;
      }
      .tour-dot:hover {
        background: #f3e5ab !important;
      }
      .tour-highlighted-element {
        position: relative !important;
        z-index: 99992 !important;
        box-shadow: 0 0 0 3px #d4af37, 0 0 32px rgba(212, 175, 55, 0.7) !important;
        transition: all 0.3s ease !important;
      }

      /* =======================================================
         LIGHT LUXURY THEME OVERRIDES (ANCESTOR & DIRECT CLASSES)
         ======================================================= */
      [data-theme="light"] .tour-backdrop,
      .tour-backdrop.light-theme,
      .tour-backdrop[data-theme="light"],
      html[data-theme="light"] .tour-backdrop,
      body[data-theme="light"] .tour-backdrop {
        background: rgba(15, 23, 42, 0.55) !important;
        backdrop-filter: blur(6px) !important;
        -webkit-backdrop-filter: blur(6px) !important;
      }

      [data-theme="light"] .tour-card-compact,
      .tour-card-compact.light-theme,
      .tour-card-compact[data-theme="light"],
      html[data-theme="light"] .tour-card-compact,
      body[data-theme="light"] .tour-card-compact {
        background: #ffffff !important;
        border: 1px solid rgba(184, 134, 11, 0.45) !important;
        box-shadow: 0 28px 72px rgba(15, 23, 42, 0.22), 0 0 36px rgba(184, 134, 11, 0.2) !important;
        color: #0f172a !important;
      }

      [data-theme="light"] .tour-progress-bar-container,
      .light-theme .tour-progress-bar-container,
      .tour-card-compact.light-theme .tour-progress-bar-container,
      .tour-card-compact[data-theme="light"] .tour-progress-bar-container {
        background: #e2e8f0 !important;
      }

      [data-theme="light"] .tour-progress-bar,
      .light-theme .tour-progress-bar,
      .tour-card-compact.light-theme .tour-progress-bar,
      .tour-card-compact[data-theme="light"] .tour-progress-bar {
        background: linear-gradient(90deg, #b8860b, #d97706) !important;
      }

      [data-theme="light"] .tour-close-top-left,
      .light-theme .tour-close-top-left,
      .tour-card-compact.light-theme .tour-close-top-left,
      .tour-card-compact[data-theme="light"] .tour-close-top-left {
        background: #f1f5f9 !important;
        border-color: #cbd5e1 !important;
        color: #475569 !important;
      }

      [data-theme="light"] .tour-close-top-left:hover,
      .light-theme .tour-close-top-left:hover,
      .tour-card-compact.light-theme .tour-close-top-left:hover,
      .tour-card-compact[data-theme="light"] .tour-close-top-left:hover {
        color: #e11d48 !important;
        background: rgba(225, 29, 72, 0.12) !important;
        border-color: rgba(225, 29, 72, 0.35) !important;
      }

      [data-theme="light"] .tour-title-compact,
      .light-theme .tour-title-compact,
      .tour-card-compact.light-theme .tour-title-compact,
      .tour-card-compact[data-theme="light"] .tour-title-compact {
        color: #7c4a03 !important;
      }

      [data-theme="light"] .tour-badge-pill,
      .light-theme .tour-badge-pill,
      .tour-card-compact.light-theme .tour-badge-pill,
      .tour-card-compact[data-theme="light"] .tour-badge-pill {
        background: rgba(2, 132, 199, 0.12) !important;
        color: #0369a1 !important;
        border-color: rgba(2, 132, 199, 0.3) !important;
      }

      [data-theme="light"] .tour-badge-step,
      .light-theme .tour-badge-step,
      .tour-card-compact.light-theme .tour-badge-step,
      .tour-card-compact[data-theme="light"] .tour-badge-step {
        background: rgba(184, 134, 11, 0.14) !important;
        color: #7c4a03 !important;
        border-color: rgba(184, 134, 11, 0.35) !important;
      }

      [data-theme="light"] .tour-summary-card,
      .light-theme .tour-summary-card,
      .tour-card-compact.light-theme .tour-summary-card,
      .tour-card-compact[data-theme="light"] .tour-summary-card {
        background: #f8fafc !important;
        border-color: #e2e8f0 !important;
      }

      [data-theme="light"] .tour-summary-card:hover,
      .light-theme .tour-summary-card:hover,
      .tour-card-compact.light-theme .tour-summary-card:hover,
      .tour-card-compact[data-theme="light"] .tour-summary-card:hover {
        background: #ffffff !important;
        border-color: rgba(184, 134, 11, 0.38) !important;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06) !important;
      }

      [data-theme="light"] .tour-summary-title,
      .light-theme .tour-summary-title,
      .tour-card-compact.light-theme .tour-summary-title,
      .tour-card-compact[data-theme="light"] .tour-summary-title {
        color: #0f172a !important;
      }

      [data-theme="light"] .tour-summary-text,
      .light-theme .tour-summary-text,
      .tour-card-compact.light-theme .tour-summary-text,
      .tour-card-compact[data-theme="light"] .tour-summary-text {
        color: #475569 !important;
      }

      [data-theme="light"] .tour-info-toggle-btn,
      .light-theme .tour-info-toggle-btn,
      .tour-card-compact.light-theme .tour-info-toggle-btn,
      .tour-card-compact[data-theme="light"] .tour-info-toggle-btn {
        background: rgba(184, 134, 11, 0.08) !important;
        border: 1px dashed rgba(184, 134, 11, 0.4) !important;
        color: #7c4a03 !important;
      }

      [data-theme="light"] .tour-info-toggle-btn:hover,
      .light-theme .tour-info-toggle-btn:hover,
      .tour-card-compact.light-theme .tour-info-toggle-btn:hover,
      .tour-card-compact[data-theme="light"] .tour-info-toggle-btn:hover {
        background: rgba(184, 134, 11, 0.16) !important;
        border-color: #b8860b !important;
      }

      [data-theme="light"] .tour-details-content,
      .light-theme .tour-details-content,
      .tour-card-compact.light-theme .tour-details-content,
      .tour-card-compact[data-theme="light"] .tour-details-content {
        background: #f1f5f9 !important;
        border-color: #e2e8f0 !important;
      }

      [data-theme="light"] .tour-detail-label,
      .light-theme .tour-detail-label,
      .tour-card-compact.light-theme .tour-detail-label,
      .tour-card-compact[data-theme="light"] .tour-detail-label {
        color: #7c4a03 !important;
      }

      [data-theme="light"] .tour-detail-val,
      .light-theme .tour-detail-val,
      .tour-card-compact.light-theme .tour-detail-val,
      .tour-card-compact[data-theme="light"] .tour-detail-val {
        color: #334155 !important;
      }

      [data-theme="light"] .tour-detail-code,
      .light-theme .tour-detail-code,
      .tour-card-compact.light-theme .tour-detail-code,
      .tour-card-compact[data-theme="light"] .tour-detail-code {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-left: 3px solid #b8860b !important;
        color: #0369a1 !important;
      }

      [data-theme="light"] .tour-compact-footer,
      .light-theme .tour-compact-footer,
      .tour-card-compact.light-theme .tour-compact-footer,
      .tour-card-compact[data-theme="light"] .tour-compact-footer {
        background: #f8fafc !important;
        border-top: 1px solid #e2e8f0 !important;
      }

      [data-theme="light"] .tour-nav-arrow-btn,
      .light-theme .tour-nav-arrow-btn,
      .tour-card-compact.light-theme .tour-nav-arrow-btn,
      .tour-card-compact[data-theme="light"] .tour-nav-arrow-btn {
        background: linear-gradient(135deg, rgba(184, 134, 11, 0.12), rgba(184, 134, 11, 0.04)) !important;
        border: 1.5px solid rgba(184, 134, 11, 0.45) !important;
        color: #7c4a03 !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08) !important;
      }

      [data-theme="light"] .tour-nav-arrow-btn:hover:not(:disabled),
      .light-theme .tour-nav-arrow-btn:hover:not(:disabled),
      .tour-card-compact.light-theme .tour-nav-arrow-btn:hover:not(:disabled),
      .tour-card-compact[data-theme="light"] .tour-nav-arrow-btn:hover:not(:disabled) {
        background: linear-gradient(135deg, #d4af37, #b8860b) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 16px rgba(184, 134, 11, 0.35) !important;
      }

      [data-theme="light"] .tour-nav-arrow-btn:disabled,
      .light-theme .tour-nav-arrow-btn:disabled,
      .tour-card-compact.light-theme .tour-nav-arrow-btn:disabled,
      .tour-card-compact[data-theme="light"] .tour-nav-arrow-btn:disabled {
        opacity: 0.25 !important;
        border-color: #e2e8f0 !important;
        color: #94a3b8 !important;
      }

      [data-theme="light"] .tour-dot,
      .light-theme .tour-dot,
      .tour-card-compact.light-theme .tour-dot,
      .tour-card-compact[data-theme="light"] .tour-dot {
        background: rgba(15, 23, 42, 0.2) !important;
      }

      [data-theme="light"] .tour-dot.active,
      .light-theme .tour-dot.active,
      .tour-card-compact.light-theme .tour-dot.active,
      .tour-card-compact[data-theme="light"] .tour-dot.active {
        background: #b8860b !important;
      }

      [data-theme="light"] .tour-dot:hover,
      .light-theme .tour-dot:hover,
      .tour-card-compact.light-theme .tour-dot:hover,
      .tour-card-compact[data-theme="light"] .tour-dot:hover {
        background: #7c4a03 !important;
      }

      [data-theme="light"] .tour-highlighted-element {
        box-shadow: 0 0 0 3px #b8860b, 0 0 32px rgba(184, 134, 11, 0.45) !important;
      }

      [data-theme="light"] .fab-tour-launcher,
      .fab-tour-launcher.light-theme,
      .fab-tour-launcher[data-theme="light"],
      html[data-theme="light"] .fab-tour-launcher,
      body[data-theme="light"] .fab-tour-launcher {
        background: linear-gradient(135deg, #fde047 0%, #d4af37 50%, #b8860b 100%) !important;
        border: 2px solid #ffffff !important;
        box-shadow: 0 8px 26px rgba(184, 134, 11, 0.4), 0 0 16px rgba(184, 134, 11, 0.25) !important;
      }

      [data-theme="light"] .fab-tour-launcher:hover,
      .fab-tour-launcher.light-theme:hover,
      .fab-tour-launcher[data-theme="light"]:hover,
      html[data-theme="light"] .fab-tour-launcher:hover,
      body[data-theme="light"] .fab-tour-launcher:hover {
        box-shadow: 0 14px 34px rgba(184, 134, 11, 0.55), 0 0 24px rgba(184, 134, 11, 0.35) !important;
      }
    `;
  },

  /**
   * Returns current active theme ('light' or 'dark').
   */
  getCurrentTheme() {
    return document.documentElement.getAttribute('data-theme') || 
           (document.body && document.body.getAttribute('data-theme')) || 
           localStorage.getItem('mishika_theme') || 
           'dark';
  },

  /**
   * Synchronizes theme classes and data attributes on all tour elements.
   */
  updateTheme() {
    const theme = this.getCurrentTheme();
    const isLight = theme === 'light';

    const card = document.getElementById('boutique-tour-card');
    const backdrop = document.getElementById('boutique-tour-backdrop');
    const fab = document.getElementById('fab-tour-launcher');

    if (card) {
      card.setAttribute('data-theme', theme);
      card.classList.toggle('light-theme', isLight);
      card.classList.toggle('dark-theme', !isLight);
    }
    if (backdrop) {
      backdrop.setAttribute('data-theme', theme);
      backdrop.classList.toggle('light-theme', isLight);
      backdrop.classList.toggle('dark-theme', !isLight);
    }
    if (fab) {
      fab.setAttribute('data-theme', theme);
      fab.classList.toggle('light-theme', isLight);
      fab.classList.toggle('dark-theme', !isLight);
    }
  },

  /**
   * Automatically observes DOM data-theme changes to keep tour popup in sync.
   */
  initThemeObserver() {
    if (this._themeObserver) return;
    if (typeof MutationObserver === 'undefined') return;

    this._themeObserver = new MutationObserver(() => {
      this.updateTheme();
    });

    if (document.documentElement) {
      this._themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    }
    if (document.body) {
      this._themeObserver.observe(document.body, { attributes: true, attributeFilter: ['data-theme'] });
    }
  },

  /**
   * Starts the interactive tour from the beginning (or specified index).
   */
  start(stepIndex = 0) {
    this.injectStyles();
    this.isActive = true;
    this.detailsOpen = false;
    this.currentStepIndex = Math.max(0, Math.min(stepIndex, this.steps.length - 1));
    this.injectTourDOM();
    this.renderStep();
  },

  /**
   * Injects the backdrop modal and card layout into the DOM.
   * Features:
   * - Cross icon on TOP LEFT corner
   * - Arrow buttons (← and →) for navigation
   * - Collapsible info drawer for deep dive details
   */
  injectTourDOM() {
    this.injectStyles();
    this.initThemeObserver();
    if (document.getElementById('boutique-tour-backdrop')) {
      this.updateTheme();
      return;
    }

    const theme = this.getCurrentTheme();
    const isLight = theme === 'light';

    const backdrop = document.createElement('div');
    backdrop.id = 'boutique-tour-backdrop';
    backdrop.className = `tour-backdrop ${isLight ? 'light-theme' : 'dark-theme'}`;
    backdrop.setAttribute('data-theme', theme);
    backdrop.onclick = (e) => {
      if (e.target === backdrop) BoutiqueTour.end();
    };

    const card = document.createElement('div');
    card.id = 'boutique-tour-card';
    card.className = `tour-card-compact ${isLight ? 'light-theme' : 'dark-theme'}`;
    card.setAttribute('data-theme', theme);

    card.innerHTML = `
      <!-- Top Progress Bar -->
      <div class="tour-progress-bar-container">
        <div class="tour-progress-bar" id="tour-progress-bar"></div>
      </div>

      <!-- Header with Cross on TOP LEFT -->
      <div class="tour-compact-header">
        <button class="tour-close-top-left" onclick="BoutiqueTour.end()" aria-label="Close" title="Exit Tour">✕</button>
        <div class="tour-header-center">
          <span class="tour-hero-icon" id="tour-hero-icon">🏛️</span>
          <div>
            <h3 class="tour-title-compact" id="tour-title">Tour Title</h3>
            <div class="tour-sub-badges">
              <span class="tour-badge-pill" id="tour-pillar-badge">Pillar</span>
              <span class="tour-badge-step" id="tour-step-badge">1 / 7</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Concise Visual Summary Cards -->
      <div class="tour-cards-container" id="tour-summary-cards"></div>

      <!-- Expandable Info & Code Drawer -->
      <div class="tour-info-drawer">
        <button class="tour-info-toggle-btn" id="tour-info-toggle-btn" onclick="BoutiqueTour.toggleDetails()">
          <span class="tour-info-icon-badge">ℹ️</span>
          <span id="tour-info-btn-text">Technical Details & Code</span>
          <span class="tour-chevron" id="tour-chevron">▼</span>
        </button>

        <div class="tour-details-content" id="tour-details-content" style="display:none;">
          <div class="tour-detail-row">
            <span class="tour-detail-label">Concept:</span>
            <span class="tour-detail-val" id="tour-detail-concept"></span>
          </div>
          <div class="tour-detail-row">
            <span class="tour-detail-label">Data Flow:</span>
            <span class="tour-detail-val" id="tour-detail-flow"></span>
          </div>
          <div class="tour-detail-row">
            <span class="tour-detail-label">Source Code:</span>
            <code class="tour-detail-code" id="tour-detail-code"></code>
          </div>
        </div>
      </div>

      <!-- Arrow Navigation Footer -->
      <div class="tour-compact-footer">
        <button class="tour-nav-arrow-btn" id="tour-btn-prev" onclick="BoutiqueTour.prev()" title="Previous Step (Left Arrow)" aria-label="Previous Step">
          ←
        </button>

        <div class="tour-dots" id="tour-dots"></div>

        <button class="tour-nav-arrow-btn" id="tour-btn-next" onclick="BoutiqueTour.next()" title="Next Step (Right Arrow)" aria-label="Next Step">
          →
        </button>
      </div>
    `;

    document.body.appendChild(backdrop);
    document.body.appendChild(card);

    // Keyboard navigation: Left/Right arrows and Escape key
    document.addEventListener('keydown', (e) => {
      if (!this.isActive) return;
      if (e.key === 'Escape') this.end();
      else if (e.key === 'ArrowRight') this.next();
      else if (e.key === 'ArrowLeft') this.prev();
    });
  },

  /**
   * Toggles the collapsible deep dive info drawer.
   */
  toggleDetails() {
    this.detailsOpen = !this.detailsOpen;
    const content = document.getElementById('tour-details-content');
    const chevron = document.getElementById('tour-chevron');
    const btnText = document.getElementById('tour-info-btn-text');

    if (content) {
      content.style.display = this.detailsOpen ? 'block' : 'none';
    }
    if (chevron) {
      chevron.style.transform = this.detailsOpen ? 'rotate(180deg)' : 'rotate(0deg)';
    }
    if (btnText) {
      btnText.innerText = this.detailsOpen ? 'Hide Technical Details' : 'Technical Details & Code';
    }
  },

  /**
   * Renders the active step.
   */
  renderStep() {
    const step = this.steps[this.currentStepIndex];
    if (!step) return;

    this.updateTheme();

    // 1. Auto-switch active tab
    if (step.tabId && typeof App !== 'undefined' && App.switchTab) {
      App.switchTab(step.tabId);
    }

    // 2. Update progress bar
    const progress = ((this.currentStepIndex + 1) / this.steps.length) * 100;
    const pBar = document.getElementById('tour-progress-bar');
    if (pBar) pBar.style.width = `${progress}%`;

    // 3. Header Info
    const heroIcon = document.getElementById('tour-hero-icon');
    const title = document.getElementById('tour-title');
    const stepBadge = document.getElementById('tour-step-badge');
    const pillarBadge = document.getElementById('tour-pillar-badge');

    if (heroIcon) heroIcon.innerText = step.icon;
    if (title) title.innerText = step.title;
    if (stepBadge) stepBadge.innerText = step.badge;
    if (pillarBadge) pillarBadge.innerText = step.pillar;

    // 4. Concise Summary Cards (With animations)
    const cardsContainer = document.getElementById('tour-summary-cards');
    if (cardsContainer && step.summary) {
      cardsContainer.innerHTML = step.summary.map((item, idx) => `
        <div class="tour-summary-card" style="animation-delay: ${idx * 0.08}s">
          <div class="tour-summary-icon">${item.icon}</div>
          <div class="tour-summary-body">
            <div class="tour-summary-title">${item.title}</div>
            <div class="tour-summary-text">${item.text}</div>
          </div>
        </div>
      `).join('');
    }

    // 5. Populate Info Details
    const dConcept = document.getElementById('tour-detail-concept');
    const dFlow = document.getElementById('tour-detail-flow');
    const dCode = document.getElementById('tour-detail-code');

    if (dConcept) dConcept.innerText = step.details.concept;
    if (dFlow) dFlow.innerText = step.details.flow;
    if (dCode) dCode.innerText = step.details.code;

    // 6. Navigation Buttons (Arrows)
    const prevBtn = document.getElementById('tour-btn-prev');
    const nextBtn = document.getElementById('tour-btn-next');
    if (prevBtn) prevBtn.disabled = this.currentStepIndex === 0;
    if (nextBtn) {
      nextBtn.title = this.currentStepIndex === this.steps.length - 1 ? 'Finish Tour' : 'Next Step (Right Arrow)';
      nextBtn.innerHTML = this.currentStepIndex === this.steps.length - 1 ? '✓' : '→';
    }

    // 7. Render Navigation Dots
    const dots = document.getElementById('tour-dots');
    if (dots) {
      dots.innerHTML = this.steps.map((_, i) => `
        <span class="tour-dot ${i === this.currentStepIndex ? 'active' : ''}" onclick="BoutiqueTour.goToStep(${i})" title="Jump to step ${i + 1}"></span>
      `).join('');
    }

    // 8. Element Spotlight
    this.removeHighlight();
    if (step.targetSelector) {
      setTimeout(() => {
        const rawEl = document.querySelector(step.targetSelector);
        if (rawEl) {
          // Never highlight an entire section/tab container as it would cover the view
          const el = (rawEl.tagName.toLowerCase() === 'section' || rawEl.classList.contains('tab-content'))
            ? (rawEl.querySelector('.data-table-container, .glass-card, .table-container') || rawEl)
            : rawEl;
          el.classList.add('tour-highlighted-element');
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 150);
    }
  },

  /**
   * Advances to next step.
   */
  next() {
    if (this.currentStepIndex < this.steps.length - 1) {
      this.currentStepIndex++;
      this.renderStep();
    } else {
      this.end();
      if (typeof App !== 'undefined' && App.showToast) {
        App.showToast('🎉 Tour Complete! You now understand the full architecture of Mishika Boutique.');
      }
    }
  },

  /**
   * Moves to previous step.
   */
  prev() {
    if (this.currentStepIndex > 0) {
      this.currentStepIndex--;
      this.renderStep();
    }
  },

  /**
   * Jumps to specific step.
   */
  goToStep(index) {
    this.currentStepIndex = index;
    this.renderStep();
  },

  /**
   * Clears spotlight halos.
   */
  removeHighlight() {
    document.querySelectorAll('.tour-highlighted-element').forEach(el => {
      el.classList.remove('tour-highlighted-element');
    });
  },

  /**
   * Exits and destroys the tour popup.
   */
  end() {
    this.isActive = false;
    this.removeHighlight();
    const backdrop = document.getElementById('boutique-tour-backdrop');
    const card = document.getElementById('boutique-tour-card');
    if (backdrop) backdrop.remove();
    if (card) card.remove();
  }
};

// Automatically inject styles and setup theme observer as soon as the script loads
if (typeof document !== 'undefined') {
  const initTour = () => {
    BoutiqueTour.injectStyles();
    BoutiqueTour.initThemeObserver();
    BoutiqueTour.updateTheme();
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTour);
  } else {
    initTour();
  }
}

// Expose globally
window.BoutiqueTour = BoutiqueTour;
