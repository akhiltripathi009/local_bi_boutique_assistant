/**
 * Mishika Fashion Luxury Boutique - Commercial SaaS Web Controller
 * Reactive single-page application engine
 */

const App = {
  state: {
    activeTab: 'tab-dashboard',
    models: [],
    activeModel: 'llama3.2:3b',
    personas: [],
    activePersona: '👔 Senior Merchandise Director',
    copilotMessages: [
      {
        role: 'assistant',
        content: '👋 **Welcome to Mishika Fashion Boutique Executive Studio.** Live real-time transactions, warehouse stock, and VIP customer CRM are loaded. How may I assist your retail strategy today?'
      }
    ],
    isStreaming: false,
    sandboxPresets: {},
    activePresetKey: '',
    liveOpsRunning: false,
    liveOpsEventSource: null,
    liveOpsPollTimer: null,
    arenaState: null,
    agentPreviewMessages: [],
    agentActiveRecipientIndex: 0,
    agentEmailConfig: null,
    theme: 'dark'
  },

  async init() {
    console.log('Initializing Mishika Luxury Boutique SaaS SPA...');
    this.initTheme();
    this.bindNavigation();
    this.bindModals();
    this.bindCopilotDrawer();
    this.bindSandbox();
    this.bindLiveOps();
    this.initLiveArena();

    // Check system health
    await this.checkHealth();

    // Load initial data
    await this.loadDashboardData();
    await this.loadCopilotMetadata();

    // Periodic auto-refresh every 30 seconds for live store updates
    setInterval(() => {
      if (!this.state.isStreaming && document.visibilityState === 'visible') {
        if (this.state.activeTab === 'tab-dashboard') this.loadDashboardData(false);
      }
    }, 30000);

    // Prompt interactive architecture tour on first visit
    if (!localStorage.getItem('mishika_tour_seen')) {
      setTimeout(() => {
        if (typeof BoutiqueTour !== 'undefined') {
          localStorage.setItem('mishika_tour_seen', 'true');
          BoutiqueTour.start();
        }
      }, 1500);
    }
  },

  startInteractiveTour() {
    if (typeof BoutiqueTour !== 'undefined') {
      BoutiqueTour.start();
    }
  },

  // ----------------------------------------------------
  // THEME MANAGEMENT (Dark / Light Luxury Mode)
  // ----------------------------------------------------
  initTheme() {
    const saved = localStorage.getItem('mishika_theme') || 'dark';
    this.setTheme(saved, false);
  },

  setTheme(theme, notify = true) {
    const targetTheme = (theme === 'light') ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', targetTheme);
    localStorage.setItem('mishika_theme', targetTheme);
    this.state.theme = targetTheme;

    const icon = document.getElementById('theme-toggle-icon');
    const text = document.getElementById('theme-toggle-text');
    if (icon && text) {
      if (targetTheme === 'light') {
        icon.innerText = '🌙';
        text.innerText = 'Dark Mode';
      } else {
        icon.innerText = '☀️';
        text.innerText = 'Light Mode';
      }
    }

    if (typeof ChartsManager !== 'undefined' && ChartsManager.updateTheme) {
      ChartsManager.updateTheme(targetTheme);
    }

    if (notify) {
      showToast(targetTheme === 'light' ? 'Switched to Champagne & Ivory Light Mode' : 'Switched to Atelier Noir Dark Mode');
    }
  },

  toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || this.state.theme || 'dark';
    const next = current === 'light' ? 'dark' : 'light';
    this.setTheme(next, true);
  },

  async checkHealth() {
    try {
      const h = await API.getHealth();
      const dot = document.getElementById('header-status-dot');
      const text = document.getElementById('header-status-text');
      if (h.database_connected) {
        text.innerText = h.ollama_active ? 'Store & AI Live' : 'Store Live (Ollama Offline)';
        dot.style.background = h.ollama_active ? '#10b981' : '#f59e0b';
      } else {
        text.innerText = 'Database Offline';
        dot.style.background = '#f43f5e';
      }
    } catch (e) {
      console.warn('Health check warning:', e);
    }
  },

  // ----------------------------------------------------
  // NAVIGATION & TABS
  // ----------------------------------------------------
  bindNavigation() {
    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const targetTab = btn.dataset.tab;
        this.switchTab(targetTab);
      });
    });
  },

  switchTab(tabId) {
    this.state.activeTab = tabId;
    document.querySelectorAll('.nav-tab-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.tab === tabId);
    });
    document.querySelectorAll('.tab-content').forEach(c => {
      c.classList.toggle('active', c.id === tabId);
    });

    // Lazy load data for selected tab
    if (tabId === 'tab-dashboard') this.loadDashboardData();
    else if (tabId === 'tab-live-ops') {
      this.loadLiveOpsData();
      setTimeout(() => this.resizeLiveArena(), 50);
    }
    else if (tabId === 'tab-inventory') this.loadInventoryData();
    else if (tabId === 'tab-crm') this.loadCRMData();
    else if (tabId === 'tab-campaigns') this.loadCampaignsData();
    else if (tabId === 'tab-agent') this.loadAgentData();
    else if (tabId === 'tab-sandbox') this.loadSandboxData();
  },

  // ----------------------------------------------------
  // 1. DASHBOARD VIEW
  // ----------------------------------------------------
  async loadDashboardData(showLoading = true) {
    try {
      const [statsRes, chartsRes, alertsRes] = await Promise.allSettled([
        API.getDashboardStats(),
        API.getDashboardCharts(),
        API.getDashboardAlerts()
      ]);

      // 1. Populate KPIs
      if (statsRes.status === 'fulfilled') {
        const stats = statsRes.value;
        const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
        setEl('kpi-revenue', `$${Number(stats.total_revenue || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}`);
        setEl('kpi-profit', `$${Number(stats.gross_profit || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}`);
        setEl('kpi-margin', `${stats.realized_margin_pct}%`);
        setEl('kpi-str', `${stats.sell_through_rate_pct}%`);
        setEl('kpi-shop-stock', `${Number(stats.shop_floor_units || 0).toLocaleString()} pcs`);
        setEl('kpi-wh-stock', `${Number(stats.warehouse_reserve_units || 0).toLocaleString()} pcs`);
      } else {
        console.warn('Failed to fetch dashboard stats:', statsRes.reason);
      }

      // 2. Render Charts & Top Styles Table
      if (chartsRes.status === 'fulfilled') {
        const charts = chartsRes.value;
        if (charts.hourly_sales) ChartsManager.initHourlySalesChart('chart-hourly-sales', charts.hourly_sales);
        if (charts.category_summary) ChartsManager.initCategoryChart('chart-category-performance', charts.category_summary);

        const topTbody = document.getElementById('top-styles-tbody');
        if (topTbody && charts.top_styles && charts.top_styles.length > 0) {
          topTbody.innerHTML = charts.top_styles.map(s => `
            <tr>
              <td style="font-weight:600;">${s.name}</td>
              <td>$${Number(s.revenue || 0).toLocaleString()}</td>
              <td style="color:#10b981; font-weight:700;">$${Number(s.profit || 0).toLocaleString()}</td>
              <td>${s.units} units</td>
            </tr>
          `).join('');
        }
      } else {
        console.warn('Failed to fetch dashboard charts:', chartsRes.reason);
      }

      // 3. Populate Alerts Count Banner
      if (alertsRes.status === 'fulfilled') {
        const alerts = alertsRes.value;
        const alertBanner = document.getElementById('dashboard-alert-banner');
        if (alertBanner) {
          if (alerts.total_alerts > 0) {
            alertBanner.style.display = 'block';
            document.getElementById('alert-count-label').innerText = `${alerts.total_alerts} Critical Safety Alert(s)`;
          } else {
            alertBanner.style.display = 'none';
          }
        }
      }
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    }
  },

  // ----------------------------------------------------
  // 2. INVENTORY & WAREHOUSE VIEW
  // ----------------------------------------------------
  async loadInventoryData() {
    try {
      const inv = await API.getInventoryOverview();
      const tbody = document.getElementById('inventory-table-tbody');
      if (!tbody) return;

      tbody.innerHTML = inv.products.map(p => `
        <tr>
          <td><span style="font-family:var(--font-mono); font-size:11.5px; color:var(--gold-light);">${p.product_id}</span></td>
          <td style="font-weight:600;">${p.product_name}</td>
          <td><span class="badge-gold">${p.category}</span></td>
          <td>$${p.retail_price.toFixed(2)}</td>
          <td style="font-weight:700; color:${p.shop_stock <= 15 ? 'var(--rose)' : 'var(--emerald)'};">
            ${p.shop_stock} units
          </td>
          <td style="font-weight:700; color:var(--text-secondary);">${p.warehouse_stock} units</td>
          <td>
            <button class="btn btn-secondary" style="padding:4px 10px; font-size:11.5px;" onclick="App.openTransferModal('${p.product_id}', '${p.product_name}', ${p.shop_stock}, ${p.warehouse_stock})">
              🔄 Move Stock
            </button>
          </td>
        </tr>
      `).join('');

      document.getElementById('inv-summary-shop').innerText = `${inv.total_shop_units.toLocaleString()} units`;
      document.getElementById('inv-summary-wh').innerText = `${inv.total_warehouse_units.toLocaleString()} units`;
    } catch (err) {
      console.error('Failed to load inventory:', err);
      showToast('Could not load inventory: ' + err.message, 'error');
    }
  },

  openTransferModal(productId, productName, shopQty, whQty) {
    document.getElementById('transfer-product-id').value = productId;
    document.getElementById('transfer-product-name').innerText = productName;
    document.getElementById('transfer-shop-avail').innerText = shopQty;
    document.getElementById('transfer-wh-avail').innerText = whQty;
    document.getElementById('modal-transfer-stock').classList.add('active');
  },

  // ----------------------------------------------------
  // 3. VIP CLIENT CRM VIEW
  // ----------------------------------------------------
  async loadCRMData() {
    const tier = document.getElementById('crm-tier-filter')?.value || 'All';
    const search = document.getElementById('crm-search-input')?.value || '';
    try {
      const res = await API.getCustomers(tier, search);
      const tbody = document.getElementById('crm-customers-tbody');
      if (!tbody) return;

      tbody.innerHTML = res.customers.map(c => `
        <tr>
          <td><span style="font-family:var(--font-mono); font-size:11px; color:var(--gold-light);">${c.customer_code}</span></td>
          <td style="font-weight:600;">${c.name}</td>
          <td>${c.phone}</td>
          <td style="color:var(--text-secondary);">${c.email}</td>
          <td><span class="badge-gold">${c.loyalty_tier}</span></td>
          <td style="font-weight:700; color:var(--emerald);">$${c.total_spend.toLocaleString()}</td>
          <td>${c.preferred_size}</td>
          <td>
            <button class="btn btn-secondary" style="padding:4px 10px; font-size:11.5px;" onclick="App.openCustomerEditModal(${c.id})">
              ✏️ Edit
            </button>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      console.error('Failed to load CRM:', err);
    }
  },

  async openCustomerEditModal(customerId) {
    try {
      const res = await API.getCustomerProfile(customerId);
      const c = res.profile;
      document.getElementById('edit-cust-id').value = c.id;
      document.getElementById('edit-cust-name').value = c.name;
      document.getElementById('edit-cust-phone').value = c.phone;
      document.getElementById('edit-cust-email').value = c.email;
      document.getElementById('edit-cust-size').value = c.preferred_size;
      document.getElementById('edit-cust-style').value = c.style_preference;
      document.getElementById('edit-cust-tier').value = c.loyalty_tier;
      document.getElementById('edit-cust-opt-wa').checked = !!c.opt_in_whatsapp;
      document.getElementById('edit-cust-opt-email').checked = !!c.opt_in_email;
      document.getElementById('modal-edit-customer').classList.add('active');
    } catch (err) {
      showToast('Failed to load customer profile: ' + err.message, 'error');
    }
  },

  // ----------------------------------------------------
  // 4. CAMPAIGNS VIEW
  // ----------------------------------------------------
  async loadCampaignsData() {
    try {
      const res = await API.getCampaigns();
      const container = document.getElementById('campaigns-card-grid');
      if (!container) return;

      container.innerHTML = res.campaigns.map(c => `
        <div class="glass-card" style="border-left:4px solid ${c.status === 'Active' ? 'var(--emerald)' : 'var(--text-muted)'};">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
            <h4 style="font-size:16px; font-weight:700; color:var(--gold-light); margin:0;">${c.name}</h4>
            <span class="${c.status === 'Active' ? 'badge-emerald' : 'badge-gold'}">${c.status.toUpperCase()}</span>
          </div>
          <p style="font-size:13px; color:var(--text-secondary); margin-bottom:12px;">${c.description}</p>
          <div style="display:flex; justify-content:space-between; align-items:center; font-size:12px; color:var(--text-muted);">
            <span>🏷️ Discount: <b style="color:var(--text-primary); font-size:14px;">${c.discount_pct}% OFF</b></span>
            <span>Category: <b style="color:var(--text-primary);">${c.target_category}</b></span>
          </div>
          <div style="margin-top:14px; display:flex; gap:8px;">
            ${c.status === 'Active' ? `
              <button class="btn btn-secondary" style="padding:4px 12px; font-size:11.5px;" onclick="App.toggleCampaignStatus(${c.id}, 'Paused')">⏸️ Pause</button>
            ` : `
              <button class="btn btn-secondary" style="padding:4px 12px; font-size:11.5px;" onclick="App.toggleCampaignStatus(${c.id}, 'Active')">▶️ Activate</button>
            `}
            <button class="btn btn-secondary" style="padding:4px 12px; font-size:11.5px; color:var(--rose);" onclick="App.toggleCampaignStatus(${c.id}, 'Ended')">⏹️ End</button>
          </div>
        </div>
      `).join('');
    } catch (err) {
      console.error('Failed to load campaigns:', err);
    }
  },

  async toggleCampaignStatus(id, status) {
    try {
      await API.updateCampaignStatus(id, status);
      showToast(`Campaign status updated to ${status}`);
      await this.loadCampaignsData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  },

  // ----------------------------------------------------
  // 5. SHIVI DEEP AGENT VIEW
  // ----------------------------------------------------
  // Helper to clean phone numbers for wa.me
  cleanPhoneDigits(phone) {
    if (!phone) return '';
    return phone.replace(/\D/g, '');
  },

  switchAgentSubTab(subTabName) {
    document.querySelectorAll('.agent-subtab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.agent-subtab-content').forEach(pane => pane.classList.remove('active'));

    const activeBtn = document.querySelector(`.agent-subtab-btn[onclick*="${subTabName}"]`);
    if (activeBtn) activeBtn.classList.add('active');

    const activePane = document.getElementById(`subtab-${subTabName}`);
    if (activePane) activePane.classList.add('active');

    if (subTabName === 'client-previews') {
      if (!this.state.agentPreviewMessages || this.state.agentPreviewMessages.length === 0) {
        this.loadAgentNewsPreview();
      }
      this.loadAgentCommunications();
    } else if (subTabName === 'email-gateway') {
      this.loadAgentEmailConfig();
    } else if (subTabName === 'guardrails-inspector') {
      this.runPIIRedaction();
      this.runDiscountValidation();
    }
  },

  async loadAgentData() {
    const planBox = document.getElementById('agent-plan-container');
    const appContainer = document.getElementById('agent-approvals-list');
    const metricMemories = document.getElementById('agent-metric-memories');
    const metricApprovals = document.getElementById('agent-metric-approvals');

    try {
      const [statusRes, approvalsRes] = await Promise.allSettled([
        API.getAgentStatus(),
        API.getAgentApprovals()
      ]);

      const status = statusRes.status === 'fulfilled' ? statusRes.value : null;
      const approvals = approvalsRes.status === 'fulfilled' ? approvalsRes.value : { approvals: [] };

      // Update Top Status Strip
      if (metricMemories && status) {
        metricMemories.innerText = `🧠 ${status.recent_memories_count || 0} Memories`;
      }
      if (metricApprovals && approvals) {
        const count = Array.isArray(approvals.approvals) ? approvals.approvals.length : 0;
        metricApprovals.innerText = `🚦 ${count} Approvals`;
      }

      // Render Plan & Checklist
      if (planBox) {
        if (status && status.current_plan && Array.isArray(status.current_plan.items) && status.current_plan.items.length > 0) {
          const p = status.current_plan;
          const statusColor = p.status === 'Completed' ? 'var(--emerald)' : (p.status === 'In Progress' ? 'var(--gold-light)' : 'var(--indigo-light)');
          planBox.innerHTML = `
            <div style="margin-bottom:14px; padding-bottom:10px; border-bottom:1px solid var(--border-subtle);">
              <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <h4 style="font-size:15px; font-weight:700; color:var(--gold-light); margin:0;">${p.goal}</h4>
                <span class="badge-gold" style="color:${statusColor}; border-color:${statusColor}; font-weight:700;">${p.status}</span>
              </div>
              <div style="display:flex; justify-content:space-between; font-size:11.5px; color:var(--text-muted); margin-top:6px;">
                <span>Plan ID: <b style="font-family:var(--font-mono); color:var(--text-secondary);">${p.plan_id}</b></span>
                <span>Created: ${p.created_at || 'Active Operational Session'}</span>
              </div>
            </div>
            <div style="display:flex; flex-direction:column; gap:8px;">
              ${p.items.map(item => `
                <div style="display:flex; align-items:center; gap:10px; background:rgba(255,255,255,0.02); padding:10px 12px; border-radius:var(--radius-sm); border:1px solid var(--border-subtle);">
                  <span style="font-size:16px;">${item.status === 'Completed' ? '✅' : (item.status === 'In Progress' ? '⏳' : '⚪')}</span>
                  <div style="flex:1; min-width:0;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                      <span style="font-size:13px; font-weight:600; color:var(--text-primary);">${item.title}</span>
                      <span style="font-size:10px; padding:1px 6px; border-radius:4px; background:rgba(255,255,255,0.05); color:${item.status === 'Completed' ? 'var(--emerald)' : (item.status === 'In Progress' ? 'var(--gold-light)' : 'var(--text-muted)')}; font-weight:600;">${item.status}</span>
                    </div>
                    <div style="font-size:11.5px; color:var(--text-secondary); margin-top:2px; line-height:1.4;">${item.result || item.description}</div>
                  </div>
                  <span style="font-size:10px; font-family:var(--font-mono); color:var(--text-muted); background:rgba(0,0,0,0.3); padding:3px 7px; border-radius:4px; white-space:nowrap;">${item.subagent}</span>
                </div>
              `).join('')}
            </div>
          `;
        } else {
          planBox.innerHTML = `
            <div style="text-align:center; padding:28px 16px; color:var(--text-muted);">
              <div style="font-size:26px; margin-bottom:8px;">🤖</div>
              <div style="font-size:14px; font-weight:600; color:var(--text-primary); margin-bottom:4px;">No Active Plan</div>
              <p style="font-size:12px; color:var(--text-secondary); max-width:320px; margin:0 auto 12px auto;">
                Select an operational directive above to activate Shivi's hierarchical task sequence.
              </p>
            </div>
          `;
        }
      }

      // Render HITL Approvals Queue
      if (appContainer) {
        const queue = (approvals && Array.isArray(approvals.approvals)) ? approvals.approvals : [];
        if (queue.length > 0) {
          appContainer.innerHTML = queue.map(a => `
            <div class="glass-card" style="border-left:4px solid var(--amber); margin-bottom:12px;">
              <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <h5 style="margin:0; font-size:14px; font-weight:700;">#${a.id} • ${a.title}</h5>
                <span class="badge-gold">PENDING APPROVAL</span>
              </div>
              <p style="font-size:12.5px; color:var(--text-secondary); margin:6px 0;">${a.description}</p>
              <div style="display:flex; gap:8px; margin-top:10px;">
                <button class="btn btn-primary" style="padding:4px 12px; font-size:11px;" onclick="App.processApprovalDecision(${a.id}, 'Approve')">✅ Authorize Action</button>
                <button class="btn btn-danger" style="padding:4px 12px; font-size:11px;" onclick="App.processApprovalDecision(${a.id}, 'Reject')">❌ Reject</button>
              </div>
            </div>
          `).join('');
        } else {
          appContainer.innerHTML = `<div style="text-align:center; padding:24px; color:var(--text-muted); font-size:12.5px;">No pending steering authorizations in queue. All systems operating within autonomous guardrails.</div>`;
        }
      }

      // Auto-load sub-tab data
      if (!this.state.agentPreviewMessages || this.state.agentPreviewMessages.length === 0) {
        await this.loadAgentNewsPreview();
      }
      await this.loadAgentEmailConfig();
      await this.loadAgentCommunications();
      this.runPIIRedaction();
      this.runDiscountValidation();
    } catch (err) {
      console.error('Failed to load agent view:', err);
      if (planBox) {
        planBox.innerHTML = `
          <div style="text-align:center; padding:20px; color:var(--rose); font-size:12.5px;">
            ⚠️ Unable to load agent plan: ${err.message || 'Connection error'}.
            <br><button class="btn btn-secondary" style="margin-top:10px; font-size:11px; padding:4px 12px;" onclick="App.loadAgentData()">🔄 Retry</button>
          </div>
        `;
      }
    }
  },

  async triggerAgentAction(actionName) {
    const statusMsg = document.getElementById('agent-trigger-status');
    const pdfBanner = document.getElementById('agent-pdf-banner');
    const pdfTitle = document.getElementById('agent-pdf-title');
    const pdfDesc = document.getElementById('agent-pdf-desc');
    const pdfDownloadBtn = document.getElementById('agent-pdf-download-btn');

    const actionLabels = {
      morning_opening: '🌅 Morning Opening Briefing',
      evening_closing: '🌆 Evening Closing Audit',
      fashion_news: '📰 Trending Fashion News Dispatch',
      campaign_launch: '📢 VIP Campaign Launch Broadcast',
      restock: '🔔 Back-in-Stock VIP Reservation Alert',
      birthday: '🎂 VIP Birthday Perks & Privilege Vouchers'
    };

    const label = actionLabels[actionName] || actionName;

    if (statusMsg) {
      statusMsg.innerText = `Shivi is autonomously executing ${label}...`;
      statusMsg.style.display = 'block';
    }

    try {
      const res = await API.runAgentAction(actionName);
      showToast(`Shivi successfully executed ${label}!`);
      await this.loadAgentData();

      // Show PDF banner if opening or closing
      if (actionName.includes('opening')) {
        if (pdfBanner) {
          pdfTitle.innerText = 'Morning Store Opening Briefing PDF Ready';
          pdfDesc.innerText = 'Pre-opening stock balance, outages, and birthday briefings compiled autonomously.';
          pdfDownloadBtn.href = '/api/reports/opening-pdf';
          pdfBanner.style.display = 'flex';
        }
        await this.loadDashboardData();
      } else if (actionName.includes('closing')) {
        if (pdfBanner) {
          pdfTitle.innerText = 'Evening Financial Closing Audit PDF Ready';
          pdfDesc.innerText = 'Daily revenue reconciliation, margins, and transfer audits compiled autonomously.';
          pdfDownloadBtn.href = '/api/reports/closing-pdf';
          pdfBanner.style.display = 'flex';
        }
        await this.loadDashboardData();
      } else if (actionName === 'fashion_news') {
        await this.loadAgentNewsPreview('', true);
      }

      await this.loadAgentCommunications();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      if (statusMsg) statusMsg.style.display = 'none';
    }
  },

  async processApprovalDecision(approvalId, decision) {
    try {
      await API.processApproval(approvalId, decision);
      showToast(`Action #${approvalId} was ${decision}d.`);
      await this.loadAgentData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  },

  async loadAgentNewsPreview(topicQuery = '', randomize = false) {
    try {
      const res = await API.getAgentNewsPreview(topicQuery, randomize);
      if (res && res.messages) {
        this.state.agentPreviewMessages = res.messages;
        this.state.agentActiveRecipientIndex = 0;

        // Render Source Status Banner
        const banner = document.getElementById('agent-news-status-banner');
        const title = document.getElementById('agent-news-source-title');
        const subtitle = document.getElementById('agent-news-source-subtitle');

        if (banner && title && subtitle) {
          if (res.is_live_internet) {
            banner.style.background = 'rgba(16, 185, 129, 0.15)';
            banner.style.border = '1px solid rgba(16, 185, 129, 0.4)';
            banner.style.borderLeft = '4px solid #10b981';
            title.style.color = '#34d399';
            title.innerText = `${res.news_source || 'Live RSS News'}`;
            subtitle.innerText = '• Connected to Live RSS Runway Wire. Real-time runway headlines are actively synthesized into customer communications.';
          } else {
            banner.style.background = 'rgba(245, 158, 11, 0.12)';
            banner.style.border = '1px solid rgba(245, 158, 11, 0.35)';
            banner.style.borderLeft = '4px solid var(--amber)';
            title.style.color = 'var(--gold-light)';
            title.innerText = 'Default Curated News Active (Offline Safe Mode)';
            subtitle.innerText = '• Fault-Tolerant Atelier Fallback. Shivi seamlessly synthesizes high-fidelity default luxury themes with zero disruption.';
          }
        }

        // Render Headlines Explorer List
        const headlinesBox = document.getElementById('agent-news-headlines-list');
        if (headlinesBox) {
          headlinesBox.innerHTML = res.messages.map(m => {
            const t = m.article_title || m.email_subject || 'Fashion Trend';
            const src = m.article_source || 'Fashion Wire';
            const lnk = m.article_link || '#';
            return `<div style="margin-bottom:6px;">
              • <a href="${lnk}" target="_blank" style="color:var(--gold-light); font-weight:600; text-decoration:none;">${t}</a> — 
              <span style="color:var(--text-muted); font-style:italic;">${src}</span> 
              <span style="font-size:11px; color:var(--text-secondary);">(Assigned to ${m.customer_name})</span>
            </div>`;
          }).join('');
        }

        // Populate Recipient Select dropdown
        const select = document.getElementById('agent-preview-recipient-select');
        if (select) {
          select.innerHTML = res.messages.map((m, idx) => {
            return `<option value="${idx}">${m.customer_name} (${m.masked_email || m.customer_email} | ${m.masked_phone || m.customer_phone})</option>`;
          }).join('');
          select.value = '0';
        }

        this.renderAgentRecipientPreview(0);
      }
    } catch (err) {
      console.error('Failed to load news preview:', err);
    }
  },

  onAgentTopicChanged() {
    const sel = document.getElementById('agent-news-topic-select');
    const topic = sel ? sel.value : '';
    this.loadAgentNewsPreview(topic, false);
  },

  async refreshAgentNews(randomize = true) {
    const sel = document.getElementById('agent-news-topic-select');
    const topic = sel ? sel.value : '';
    showToast('Refreshing live runway wire stories...');
    await this.loadAgentNewsPreview(topic, randomize);
    showToast('Runway news refreshed successfully!');
  },

  onAgentRecipientChanged() {
    const select = document.getElementById('agent-preview-recipient-select');
    const idx = select ? parseInt(select.value, 10) : 0;
    this.state.agentActiveRecipientIndex = idx;
    this.renderAgentRecipientPreview(idx);
  },

  renderAgentRecipientPreview(index) {
    const msgs = this.state.agentPreviewMessages || [];
    if (msgs.length === 0 || index < 0 || index >= msgs.length) return;
    const msg = msgs[index];

    // Left: Email Preview
    const emailSubject = document.getElementById('agent-preview-email-subject');
    const emailTo = document.getElementById('agent-email-preview-to');
    const emailBody = document.getElementById('agent-email-preview-body');
    const mailtoBtn = document.getElementById('btn-agent-mailto');
    const sendSingleBtn = document.getElementById('btn-agent-send-smtp');

    if (emailSubject) emailSubject.innerText = msg.email_subject || 'Mishika Fashion Boutique Alert';
    if (emailTo) emailTo.innerHTML = `<b>To:</b> ${msg.customer_name} &lt;${msg.customer_email}&gt;`;
    if (emailBody) emailBody.innerHTML = msg.email_html || '<p>No preview</p>';
    if (sendSingleBtn) sendSingleBtn.innerText = `🚀 Send Real Email via Gmail SMTP to ${msg.customer_name}`;

    const plainBody = `Dear ${msg.customer_name},\n\nCheck out our latest boutique updates and new arrivals.\n\nWarm regards,\nMishika Fashion Boutique Concierge`;
    if (mailtoBtn) {
      mailtoBtn.href = `mailto:${msg.customer_email}?subject=${encodeURIComponent(msg.email_subject || 'Boutique Alert')}&body=${encodeURIComponent(plainBody)}`;
    }

    // Right: WhatsApp Preview
    const waPhone = document.getElementById('agent-preview-wa-phone');
    const waBubble = document.getElementById('agent-wa-bubble-text');
    const waTime = document.getElementById('agent-wa-bubble-time');
    const waMeBtn = document.getElementById('btn-agent-wa-me');

    if (waPhone) waPhone.innerText = msg.customer_phone || '';
    if (waBubble) waBubble.innerText = msg.whatsapp_text || '';
    if (waTime) {
      const now = new Date();
      waTime.innerText = `${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ✓✓`;
    }

    const cleanDigits = this.cleanPhoneDigits(msg.customer_phone);
    if (waMeBtn) {
      waMeBtn.href = `https://wa.me/${cleanDigits}?text=${encodeURIComponent(msg.whatsapp_text || '')}`;
      waMeBtn.innerText = `📲 Send Real WhatsApp via wa.me (${msg.customer_phone})`;
    }

    // Draft link for test personal email
    const testDraftLink = document.getElementById('btn-test-my-email-draft');
    if (testDraftLink) {
      testDraftLink.href = `mailto:?subject=${encodeURIComponent(msg.email_subject || 'Boutique Alert')}&body=${encodeURIComponent(plainBody)}`;
    }
  },

  async sendCurrentRecipientEmail() {
    const msgs = this.state.agentPreviewMessages || [];
    const idx = this.state.agentActiveRecipientIndex || 0;
    if (msgs.length === 0 || !msgs[idx]) {
      showToast('No recipient loaded for email send.', 'error');
      return;
    }
    const msg = msgs[idx];
    try {
      showToast(`Sending real email via Gmail SMTP to ${msg.customer_email}...`);
      const res = await API.sendAgentEmail({
        to_email: msg.customer_email,
        subject: msg.email_subject,
        html_body: msg.email_html,
        customer_id: msg.customer_id,
        customer_name: msg.customer_name
      });
      showToast(res.message || `Email sent successfully to ${msg.customer_email}!`);
      await this.loadAgentCommunications();
    } catch (err) {
      showToast(err.message, 'error');
    }
  },

  async sendBatchEmails() {
    const msgs = this.state.agentPreviewMessages || [];
    if (msgs.length === 0) {
      showToast('No messages available for batch dispatch.', 'error');
      return;
    }
    if (!confirm(`Are you sure you want to broadcast real emails to ALL ${msgs.length} VIP clients via Gmail SMTP?`)) {
      return;
    }
    try {
      showToast(`Dispatching batch emails to ${msgs.length} clients via Gmail SMTP...`);
      const res = await API.sendAgentEmail({
        batch: true,
        messages: msgs
      });
      showToast(`🎉 Delivered ${res.dispatched_count || 0} real emails via Gmail SMTP!`);
      await this.loadAgentCommunications();
    } catch (err) {
      showToast(err.message, 'error');
    }
  },

  launchTestMyWhatsApp() {
    const phoneInput = document.getElementById('agent-test-my-phone');
    const phone = phoneInput ? phoneInput.value.trim() : '';
    if (!phone) {
      showToast('Please enter your WhatsApp phone number.', 'error');
      return;
    }
    const msgs = this.state.agentPreviewMessages || [];
    const idx = this.state.agentActiveRecipientIndex || 0;
    const msg = msgs[idx] || {};
    const text = msg.whatsapp_text || 'Hello from Mishika Fashion Boutique!';
    const cleanDigits = this.cleanPhoneDigits(phone);
    window.open(`https://wa.me/${cleanDigits}?text=${encodeURIComponent(text)}`, '_blank');
  },

  async sendTestMyEmail() {
    const emailInput = document.getElementById('agent-test-my-email');
    const email = emailInput ? emailInput.value.trim() : '';
    if (!email) {
      showToast('Please enter your test email address.', 'error');
      return;
    }
    const msgs = this.state.agentPreviewMessages || [];
    const idx = this.state.agentActiveRecipientIndex || 0;
    const msg = msgs[idx] || {};
    try {
      showToast(`Sending test email to ${email}...`);
      const res = await API.sendAgentEmail({
        to_email: email,
        subject: msg.email_subject || '✨ Shivi Deep Agent Test Email',
        html_body: msg.email_html || '<p>Test verification email from Shivi Deep Agent.</p>'
      });
      showToast(`✅ Real test email delivered to ${email}!`);
      await this.loadAgentCommunications();
    } catch (err) {
      showToast(err.message, 'error');
    }
  },

  async loadAgentCommunications() {
    const tbody = document.getElementById('agent-comms-table-tbody');
    if (!tbody) return;
    try {
      const res = await API.getAgentCommunications();
      const comms = (res && Array.isArray(res.communications)) ? res.communications : [];
      if (comms.length > 0) {
        tbody.innerHTML = comms.map(c => `
          <tr>
            <td style="font-family:var(--font-mono); font-size:11.5px; color:var(--text-muted);">${c.timestamp || ''}</td>
            <td style="font-weight:600; color:var(--text-primary);">${c.customer_name || 'VIP Patron'}</td>
            <td><span class="badge-gold">${c.channel || 'Email'}</span></td>
            <td><span style="font-size:11px; color:var(--text-secondary);">${c.message_type || 'Marketing'}</span></td>
            <td style="font-size:12px; color:var(--text-secondary); max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${c.subject || 'Direct Dispatch'}</td>
            <td><span style="font-size:11px; font-weight:600; color:var(--emerald);">${c.status || 'Dispatched'}</span></td>
          </tr>
        `).join('');
      } else {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:16px;">No communications recorded yet.</td></tr>`;
      }
    } catch (err) {
      console.error('Failed to load communications:', err);
    }
  },

  async loadAgentEmailConfig() {
    try {
      const res = await API.getAgentEmailConfig();
      if (!res || !res.config) return;
      const cfg = res.config;
      this.state.agentEmailConfig = cfg;

      // Populate Inputs
      const userIn = document.getElementById('email-cfg-user');
      const passIn = document.getElementById('email-cfg-pass');
      const adminIn = document.getElementById('email-cfg-admin');
      const nameIn = document.getElementById('email-cfg-from-name');
      const hostIn = document.getElementById('email-cfg-host');
      const portIn = document.getElementById('email-cfg-port');
      const autoAdminIn = document.getElementById('email-cfg-auto-admin');
      const autoCustIn = document.getElementById('email-cfg-auto-cust');
      const testTarget = document.getElementById('email-test-target');

      if (userIn) userIn.value = cfg.smtp_user || '';
      if (passIn) passIn.value = cfg.smtp_pass || '';
      if (adminIn) adminIn.value = cfg.admin_email || '';
      if (nameIn) nameIn.value = cfg.from_name || 'Mishika Fashion Boutique Concierge';
      if (hostIn) hostIn.value = cfg.smtp_host || 'smtp.gmail.com';
      if (portIn) portIn.value = cfg.smtp_port || 587;
      if (autoAdminIn) autoAdminIn.checked = !!cfg.auto_send_admin_audits;
      if (autoCustIn) autoCustIn.checked = !!cfg.auto_send_customer_emails;
      if (testTarget && !testTarget.value) {
        testTarget.value = cfg.admin_email || cfg.smtp_user || '';
      }

      // Update Gateway Status Banner
      const banner = document.getElementById('agent-email-gateway-banner');
      const statusBadge = document.getElementById('agent-smtp-status-badge');
      const statusCallout = document.getElementById('agent-smtp-status-callout');

      if (cfg.is_configured) {
        if (banner) {
          banner.style.background = 'rgba(16, 185, 129, 0.15)';
          banner.style.border = '1px solid rgba(16, 185, 129, 0.4)';
          banner.style.color = '#34d399';
          banner.innerHTML = `🟢 Automated Email Gateway Active: Authenticated as <b>${cfg.smtp_user}</b> via ${cfg.smtp_host}:${cfg.smtp_port}.`;
        }
        if (statusBadge) {
          statusBadge.className = 'badge-emerald';
          statusBadge.innerText = '🟢 SMTP Active';
        }
        if (statusCallout) {
          statusCallout.style.background = 'rgba(16, 185, 129, 0.12)';
          statusCallout.style.border = '1px solid rgba(16, 185, 129, 0.3)';
          statusCallout.style.color = '#34d399';
          statusCallout.innerHTML = `🟢 <b>Gmail SMTP Active:</b> Sending directly from <code>${cfg.smtp_user}</code> (TLS:587).`;
        }
      } else {
        if (banner) {
          banner.style.background = 'rgba(245, 158, 11, 0.15)';
          banner.style.border = '1px solid rgba(245, 158, 11, 0.4)';
          banner.style.color = 'var(--gold-light)';
          banner.innerHTML = `⚠️ Automated Email Pending: Please enter your Gmail address and 16-character App Password below.`;
        }
        if (statusBadge) {
          statusBadge.className = 'badge-gold';
          statusBadge.innerText = '⚠️ App Password Pending';
        }
        if (statusCallout) {
          statusCallout.style.background = 'rgba(245, 158, 11, 0.12)';
          statusCallout.style.border = '1px solid rgba(245, 158, 11, 0.3)';
          statusCallout.style.color = 'var(--gold-light)';
          statusCallout.innerHTML = `⚠️ <b>Gmail App Password Pending:</b> Activate your Gmail App Password in Tab 2 to send directly to inboxes.`;
        }
      }
    } catch (err) {
      console.error('Failed to load email config:', err);
    }
  },

  async saveEmailConfiguration() {
    const userIn = document.getElementById('email-cfg-user');
    const passIn = document.getElementById('email-cfg-pass');
    const adminIn = document.getElementById('email-cfg-admin');
    const nameIn = document.getElementById('email-cfg-from-name');
    const hostIn = document.getElementById('email-cfg-host');
    const portIn = document.getElementById('email-cfg-port');
    const autoAdminIn = document.getElementById('email-cfg-auto-admin');
    const autoCustIn = document.getElementById('email-cfg-auto-cust');

    const payload = {
      smtp_host: hostIn ? hostIn.value.trim() : 'smtp.gmail.com',
      smtp_port: portIn ? parseInt(portIn.value, 10) : 587,
      smtp_user: userIn ? userIn.value.trim() : '',
      smtp_pass: passIn ? passIn.value.trim() : '',
      smtp_from: userIn ? userIn.value.trim() : '',
      from_name: nameIn ? nameIn.value.trim() : 'Mishika Fashion Boutique Concierge',
      admin_email: adminIn ? adminIn.value.trim() : '',
      auto_send_admin_audits: autoAdminIn ? autoAdminIn.checked : true,
      auto_send_customer_emails: autoCustIn ? autoCustIn.checked : true
    };

    try {
      showToast('Saving and activating email configuration...');
      const res = await API.saveAgentEmailConfig(payload);
      showToast(res.message || 'Email settings saved successfully!');
      await this.loadAgentEmailConfig();
    } catch (err) {
      showToast(err.message, 'error');
    }
  },

  async runEmailConnectionTest() {
    const testTarget = document.getElementById('email-test-target');
    const targetEmail = testTarget ? testTarget.value.trim() : '';
    const feedback = document.getElementById('agent-email-test-feedback');

    if (!targetEmail) {
      showToast('Please specify a target test email recipient.', 'error');
      return;
    }

    if (feedback) {
      feedback.style.display = 'block';
      feedback.style.background = 'rgba(212, 175, 55, 0.12)';
      feedback.style.border = '1px solid rgba(212, 175, 55, 0.3)';
      feedback.style.color = 'var(--gold-light)';
      feedback.innerText = 'Connecting to SMTP server and transmitting verification email...';
    }

    try {
      const res = await API.testAgentEmail(targetEmail);
      if (feedback) {
        feedback.style.background = 'rgba(16, 185, 129, 0.15)';
        feedback.style.border = '1px solid rgba(16, 185, 129, 0.4)';
        feedback.style.color = '#34d399';
        feedback.innerText = res.message || 'Verification email delivered successfully!';
      }
      showToast('Verification email delivered successfully!');
    } catch (err) {
      if (feedback) {
        feedback.style.background = 'rgba(244, 63, 94, 0.15)';
        feedback.style.border = '1px solid rgba(244, 63, 94, 0.4)';
        feedback.style.color = '#fb7185';
        feedback.innerText = err.message || 'Connection test failed.';
      }
      showToast(err.message, 'error');
    }
  },

  // Guardrails Handlers
  onPIIInputChanged() {
    clearTimeout(this._piiTimer);
    this._piiTimer = setTimeout(() => this.runPIIRedaction(), 300);
  },

  async runPIIRedaction() {
    const input = document.getElementById('agent-pii-input');
    const output = document.getElementById('agent-pii-output');
    const text = input ? input.value : '';
    if (!text) {
      if (output) output.innerText = '';
      return;
    }
    try {
      const res = await API.testPIIRedaction(text);
      if (output) output.innerText = res.sanitized_text || '';
    } catch (err) {
      console.error('PII redaction failed:', err);
    }
  },

  onDiscountInputChanged() {
    clearTimeout(this._discTimer);
    this._discTimer = setTimeout(() => this.runDiscountValidation(), 200);
  },

  async runDiscountValidation() {
    const input = document.getElementById('agent-discount-input');
    const slider = document.getElementById('agent-discount-slider');
    const feedback = document.getElementById('agent-discount-feedback');
    const pct = input ? parseFloat(input.value) || 0 : 0;
    if (slider) slider.value = pct;

    try {
      const res = await API.testDiscountGuardrail(pct);
      if (feedback) {
        if (res.is_safe) {
          feedback.style.background = 'rgba(16, 185, 129, 0.15)';
          feedback.style.border = '1px solid rgba(16, 185, 129, 0.4)';
          feedback.style.color = '#34d399';
          feedback.innerHTML = `<b>✅ Approved:</b> ${res.effective_discount.toFixed(1)}% discount is within safe boundaries.<br><span style="font-size:11px; opacity:0.85;">${res.message}</span>`;
        } else {
          feedback.style.background = 'rgba(245, 158, 11, 0.15)';
          feedback.style.border = '1px solid rgba(245, 158, 11, 0.4)';
          feedback.style.color = 'var(--gold-light)';
          feedback.innerHTML = `<b>⚠️ Guardrail Interception:</b> Requested ${res.requested_discount.toFixed(1)}% clamped to <b>${res.effective_discount.toFixed(1)}%</b> (Cap: 50.0%).<br><span style="font-size:11px; opacity:0.85;">${res.message}</span>`;
        }
      }
    } catch (err) {
      console.error('Discount validation failed:', err);
    }
  },

  // ----------------------------------------------------
  // 6. DATA SCIENCE SANDBOX VIEW
  // ----------------------------------------------------
  async loadSandboxData() {
    try {
      const res = await API.getSandboxPresets();
      this.state.sandboxPresets = res.presets;
      const sel = document.getElementById('sandbox-preset-select');
      if (sel && sel.options.length <= 1) {
        sel.innerHTML = Object.keys(res.presets).map(k => `
          <option value="${k}">${k}</option>
        `).join('');
        this.selectSandboxPreset(Object.keys(res.presets)[0]);
      }
    } catch (err) {
      console.error('Failed to load sandbox presets:', err);
    }
  },

  selectSandboxPreset(presetName) {
    this.state.activePresetKey = presetName;
    const code = this.state.sandboxPresets[presetName] || '';
    const editor = document.getElementById('sandbox-editor');
    if (editor) editor.value = code;
  },

  async executeSandboxCode() {
    const editor = document.getElementById('sandbox-editor');
    const outPre = document.getElementById('sandbox-output-pre');
    const outBox = document.getElementById('sandbox-output-container');
    if (!editor || !outPre) return;

    outPre.innerText = 'Executing script in secure Python Sandbox...';
    outBox.style.display = 'block';

    try {
      const res = await API.executeSandboxCode(editor.value);
      if (res.success) {
        outPre.innerText = `[Completed in ${res.duration_sec}s]\n\n${res.output || '(No stdout produced)'}`;
        outPre.style.color = '#10b981';
      } else {
        outPre.innerText = `[Execution Error]\n\n${res.error}\n\n${res.output || ''}`;
        outPre.style.color = '#f43f5e';
      }
    } catch (err) {
      outPre.innerText = `[Network Error]: ${err.message}`;
      outPre.style.color = '#f43f5e';
    }
  },

  bindSandbox() {
    const sel = document.getElementById('sandbox-preset-select');
    if (sel) {
      sel.addEventListener('change', (e) => this.selectSandboxPreset(e.target.value));
    }
    const reloadBtn = document.getElementById('btn-sandbox-reload');
    if (reloadBtn) {
      reloadBtn.addEventListener('click', () => {
        if (this.state.activePresetKey) {
          this.selectSandboxPreset(this.state.activePresetKey);
          showToast('Preset reloaded cleanly.');
        }
      });
    }
    const execBtn = document.getElementById('btn-sandbox-execute');
    if (execBtn) {
      execBtn.addEventListener('click', () => this.executeSandboxCode());
    }
  },

  // ----------------------------------------------------
  // 7. COPILOT STUDIO DRAWER (STREAMING)
  // ----------------------------------------------------
  async loadCopilotMetadata() {
    try {
      const [mRes, pRes] = await Promise.all([
        API.getCopilotModels(),
        API.getCopilotPersonas()
      ]);
      this.state.models = mRes.models;
      this.state.activeModel = mRes.active_default;
      this.state.personas = pRes.personas;

      // Populate Model Selector in Drawer
      const mSel = document.getElementById('copilot-model-select');
      if (mSel) {
        mSel.innerHTML = mRes.models.map(m => `
          <option value="${m}" ${m === this.state.activeModel ? 'selected' : ''}>🦙 ${m}</option>
        `).join('');
        mSel.addEventListener('change', (e) => {
          this.state.activeModel = e.target.value;
        });
      }

      // Populate Persona Selector
      const pSel = document.getElementById('copilot-persona-select');
      if (pSel) {
        pSel.innerHTML = pRes.personas.map(p => `
          <option value="${p.key}">${p.key}</option>
        `).join('');
        pSel.addEventListener('change', (e) => {
          this.state.activePersona = e.target.value;
        });
      }
    } catch (err) {
      console.warn('Copilot metadata warning:', err);
    }
  },

  bindCopilotDrawer() {
    const trigger = document.getElementById('btn-open-copilot');
    const drawer = document.getElementById('copilot-drawer');
    const closeBtn = document.getElementById('btn-close-copilot');

    if (trigger && drawer) {
      trigger.addEventListener('click', () => drawer.classList.add('open'));
    }
    if (closeBtn && drawer) {
      closeBtn.addEventListener('click', () => drawer.classList.remove('open'));
    }

    const sendBtn = document.getElementById('btn-copilot-send');
    const input = document.getElementById('copilot-chat-input');
    if (sendBtn && input) {
      sendBtn.addEventListener('click', () => this.sendCopilotMessage());
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendCopilotMessage();
        }
      });
    }
  },

  async sendCopilotMessage() {
    const input = document.getElementById('copilot-chat-input');
    if (!input || !input.value.trim() || this.state.isStreaming) return;

    const userText = input.value.trim();
    input.value = '';

    // Append user message
    this.state.copilotMessages.push({ role: 'user', content: userText });
    this.renderChatMessages();

    // Prepare assistant placeholder
    const assistantIndex = this.state.copilotMessages.length;
    this.state.copilotMessages.push({ role: 'assistant', content: '' });
    this.state.isStreaming = true;

    // Create assistant message element in DOM
    const chatBody = document.getElementById('copilot-chat-body');
    const assistantMsgEl = document.createElement('div');
    assistantMsgEl.className = 'chat-message assistant';
    assistantMsgEl.innerHTML = `<div class="chat-bubble" id="streaming-token-bubble">⏳ Thinking...</div>`;
    chatBody.appendChild(assistantMsgEl);
    chatBody.scrollTop = chatBody.scrollHeight;

    let fullResponse = '';
    const bubbleEl = document.getElementById('streaming-token-bubble');

    await API.streamCopilotChat(
      this.state.copilotMessages.slice(0, -1),
      this.state.activeModel,
      this.state.activePersona,
      (token) => {
        if (fullResponse === '') bubbleEl.innerText = '';
        fullResponse += token;
        bubbleEl.innerText = fullResponse;
        chatBody.scrollTop = chatBody.scrollHeight;
      },
      () => {
        this.state.isStreaming = false;
        this.state.copilotMessages[assistantIndex].content = fullResponse;
        bubbleEl.removeAttribute('id');
      },
      (err) => {
        this.state.isStreaming = false;
        bubbleEl.innerText = `\n\n❌ Connection notice: ${err.message}`;
        bubbleEl.style.color = '#f43f5e';
      }
    );
  },

  renderChatMessages() {
    const chatBody = document.getElementById('copilot-chat-body');
    if (!chatBody) return;
    chatBody.innerHTML = this.state.copilotMessages.map(m => `
      <div class="chat-message ${m.role}">
        <div class="chat-bubble">${m.content}</div>
      </div>
    `).join('');
    chatBody.scrollTop = chatBody.scrollHeight;
  },

  // ----------------------------------------------------
  // 8. MODAL CONTROLS & FORMS
  // ----------------------------------------------------
  bindModals() {
    // Close modal on clicking overlay or close button
    document.querySelectorAll('.modal-overlay').forEach(modal => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.remove('active');
      });
      const cBtn = modal.querySelector('.modal-close');
      if (cBtn) cBtn.addEventListener('click', () => modal.classList.remove('active'));
    });

    // Stock Transfer Form
    const transferForm = document.getElementById('form-transfer-stock');
    if (transferForm) {
      transferForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const pid = document.getElementById('transfer-product-id').value;
        const size = document.getElementById('transfer-size').value;
        const qty = parseInt(document.getElementById('transfer-qty').value, 10);
        const direction = document.getElementById('transfer-direction').value;

        const source = direction === 'shop_to_wh' ? 'Shop Floor' : 'Warehouse Reserve';
        const dest = direction === 'shop_to_wh' ? 'Warehouse Reserve' : 'Shop Floor';

        try {
          await API.transferStock({
            product_id: pid,
            size_variant: size,
            quantity: qty,
            source_location: source,
            dest_location: dest
          });
          showToast(`Transferred ${qty}x (${size}) of ${pid} to ${dest}!`);
          document.getElementById('modal-transfer-stock').classList.remove('active');
          await this.loadInventoryData();
          await this.loadDashboardData();
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    }

    // Customer Contact Edit Form
    const custForm = document.getElementById('form-edit-customer');
    if (custForm) {
      custForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const cid = parseInt(document.getElementById('edit-cust-id').value, 10);
        const payload = {
          name: document.getElementById('edit-cust-name').value,
          phone: document.getElementById('edit-cust-phone').value,
          email: document.getElementById('edit-cust-email').value,
          preferred_size: document.getElementById('edit-cust-size').value,
          style_preference: document.getElementById('edit-cust-style').value,
          loyalty_tier: document.getElementById('edit-cust-tier').value,
          opt_in_whatsapp: document.getElementById('edit-cust-opt-wa').checked ? 1 : 0,
          opt_in_email: document.getElementById('edit-cust-opt-email').checked ? 1 : 0
        };
        try {
          await API.updateCustomerContact(cid, payload);
          showToast(`Updated contact information for ${payload.name}!`);
          document.getElementById('modal-edit-customer').classList.remove('active');
          await this.loadCRMData();
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    }

    // Launch Campaign Modal & Form
    const openCampBtn = document.getElementById('btn-open-create-campaign');
    if (openCampBtn) {
      openCampBtn.addEventListener('click', () => {
        document.getElementById('modal-create-campaign').classList.add('active');
      });
    }

    const campForm = document.getElementById('form-create-campaign');
    if (campForm) {
      campForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
          name: document.getElementById('new-camp-name').value,
          description: document.getElementById('new-camp-desc').value,
          discount_pct: parseFloat(document.getElementById('new-camp-discount').value),
          target_category: document.getElementById('new-camp-cat').value
        };
        try {
          const res = await API.createCampaign(payload);
          if (res.guardrail_warning) {
            showToast(res.guardrail_warning, 'error');
          } else {
            showToast(`Campaign '${payload.name}' launched successfully!`);
          }
          document.getElementById('modal-create-campaign').classList.remove('active');
          await this.loadCampaignsData();
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    }
  },

  // ----------------------------------------------------
  // LIVE SHOP OPERATIONS (SEGMENT 2)
  // ----------------------------------------------------
  bindLiveOps() {
    const toggleBtn = document.getElementById('btn-toggle-live-ops');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', async () => {
        if (this.state.liveOpsRunning) {
          await this.stopLiveOpsLoop();
        } else {
          await this.startLiveOpsLoop();
        }
      });
    }

    const stepBtn = document.getElementById('btn-step-live-ops');
    if (stepBtn) {
      stepBtn.addEventListener('click', async () => {
        try {
          const res = await API.stepLiveOpsTick();
          if (res.success) {
            await this.loadLiveOpsData(false);
          }
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    }

    const resetBtn = document.getElementById('btn-reset-live-ops');
    if (resetBtn) {
      resetBtn.addEventListener('click', async () => {
        try {
          await API.resetLiveOpsInventory();
          showToast('Live inventory synchronized with database.');
          await this.loadLiveOpsData();
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    }

    const discRange = document.getElementById('live-ops-discount-range');
    const discLabel = document.getElementById('live-ops-discount-label');
    if (discRange && discLabel) {
      discRange.addEventListener('input', async (e) => {
        const val = parseInt(e.target.value, 10);
        discLabel.innerText = `${val}%`;
        try {
          await API.updateLiveOpsSettings({ promo_discount: val });
        } catch (_) {}
      });
    }

    const spdRange = document.getElementById('live-ops-speed-range');
    const spdLabel = document.getElementById('live-ops-speed-label');
    if (spdRange && spdLabel) {
      spdRange.addEventListener('input', async (e) => {
        const val = parseFloat(e.target.value);
        spdLabel.innerText = `${val.toFixed(2)}s`;
        try {
          await API.updateLiveOpsSettings({ tick_speed: val });
        } catch (_) {}
      });
    }
  },

  async startLiveOpsLoop() {
    try {
      await API.startLiveOps();
      this.state.liveOpsRunning = true;
      const toggleBtn = document.getElementById('btn-toggle-live-ops');
      if (toggleBtn) {
        toggleBtn.innerText = '⏸️ Pause Simulation';
        toggleBtn.className = 'btn btn-danger';
        toggleBtn.style.minWidth = '165px';
      }
      this.startLiveTelemetryStream();
      showToast('Live Operations simulation loop activated!');
    } catch (err) {
      showToast(err.message, 'error');
    }
  },

  async stopLiveOpsLoop() {
    try {
      await API.pauseLiveOps();
      this.state.liveOpsRunning = false;
      const toggleBtn = document.getElementById('btn-toggle-live-ops');
      if (toggleBtn) {
        toggleBtn.innerText = '▶️ Start Live Loop';
        toggleBtn.className = 'btn btn-primary';
        toggleBtn.style.minWidth = '165px';
      }
      this.stopLiveTelemetryStream();
      await this.loadLiveOpsData(false);
      showToast('Live Operations simulation paused.');
    } catch (err) {
      showToast(err.message, 'error');
    }
  },

  startLiveTelemetryStream() {
    this.stopLiveTelemetryStream();
    try {
      if (window.EventSource) {
        const es = new EventSource('/api/live-ops/stream');
        es.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data && data.status) {
              this.applyLiveOpsSnapshot(data.status, data.chart, data.ledgers);
            }
          } catch (e) {
            console.warn('SSE parse error:', e);
          }
        };
        es.onerror = () => {
          es.close();
          this.state.liveOpsEventSource = null;
          if (!this.state.liveOpsPollTimer && this.state.liveOpsRunning) {
            this.state.liveOpsPollTimer = setInterval(() => {
              if (this.state.liveOpsRunning && this.state.activeTab === 'tab-live-ops') {
                this.loadLiveOpsData(false);
              }
            }, 600);
          }
        };
        this.state.liveOpsEventSource = es;
      } else {
        throw new Error('SSE not supported');
      }
    } catch (_) {
      this.state.liveOpsPollTimer = setInterval(() => {
        if (this.state.liveOpsRunning && this.state.activeTab === 'tab-live-ops') {
          this.loadLiveOpsData(false);
        }
      }, 500);
    }
  },

  stopLiveTelemetryStream() {
    if (this.state.liveOpsEventSource) {
      this.state.liveOpsEventSource.close();
      this.state.liveOpsEventSource = null;
    }
    if (this.state.liveOpsPollTimer) {
      clearInterval(this.state.liveOpsPollTimer);
      this.state.liveOpsPollTimer = null;
    }
  },

  async loadLiveOpsData(showToastAlert = false) {
    try {
      const [statusRes, chartRes, logsRes] = await Promise.allSettled([
        API.getLiveOpsStatus(),
        API.getLiveOpsStockChart(),
        API.getLiveOpsLogs(8)
      ]);

      const status = statusRes.status === 'fulfilled' ? statusRes.value : null;
      const chart = chartRes.status === 'fulfilled' ? chartRes.value.items : [];
      const ledgers = logsRes.status === 'fulfilled' ? logsRes.value : { sales_log: [], restocks_log: [] };

      if (status) {
        this.applyLiveOpsSnapshot(status, chart, ledgers);
      }
    } catch (err) {
      console.warn('Failed to load Live Ops data:', err);
    }
  },

  applyLiveOpsSnapshot(status, chartItems, ledgers) {
    // 1. Sync running button state
    this.state.liveOpsRunning = !!status.running;
    const toggleBtn = document.getElementById('btn-toggle-live-ops');
    if (toggleBtn) {
      if (status.running) {
        toggleBtn.innerText = '⏸️ Pause Simulation';
        toggleBtn.className = 'btn btn-danger';
        toggleBtn.style.minWidth = '165px';
      } else {
        toggleBtn.innerText = '▶️ Start Live Loop';
        toggleBtn.className = 'btn btn-primary';
        toggleBtn.style.minWidth = '165px';
      }
    }

    // 2. Sliders & Clock
    const discRange = document.getElementById('live-ops-discount-range');
    const discLabel = document.getElementById('live-ops-discount-label');
    if (discRange && discLabel && document.activeElement !== discRange) {
      discRange.value = status.promo_discount || 0;
      discLabel.innerText = `${status.promo_discount || 0}%`;
    }
    const spdRange = document.getElementById('live-ops-speed-range');
    const spdLabel = document.getElementById('live-ops-speed-label');
    if (spdRange && spdLabel && document.activeElement !== spdRange) {
      spdRange.value = status.tick_speed || 0.35;
      spdLabel.innerText = `${(status.tick_speed || 0.35).toFixed(2)}s`;
    }

    const clockEl = document.getElementById('live-ops-clock');
    if (clockEl) {
      clockEl.innerText = status.latest_event?.timestamp?.split(' ')[1] || new Date().toLocaleTimeString();
    }

    // 3. Status Strip Cards
    const revEl = document.getElementById('live-ops-revenue');
    if (revEl) revEl.innerText = `$${(status.total_revenue || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

    const lowStockVal = document.getElementById('live-ops-low-stock-val');
    const lowStockBadge = document.getElementById('live-ops-stock-badge');
    const cardLowStock = document.getElementById('card-low-stock');
    const lCount = status.low_stock_count || 0;
    if (lowStockVal) lowStockVal.innerText = `${lCount} Styles`;
    if (lowStockBadge && cardLowStock) {
      if (lCount > 0) {
        lowStockBadge.className = 'badge-gold';
        lowStockBadge.innerText = '≤ 15 UNITS';
        cardLowStock.style.borderLeftColor = 'var(--gold-primary)';
      } else {
        lowStockBadge.className = 'badge-emerald';
        lowStockBadge.innerText = 'HEALTHY';
        cardLowStock.style.borderLeftColor = 'var(--emerald)';
      }
    }

    const badgeEl = document.getElementById('live-ops-status-badge');
    const textEl = document.getElementById('live-ops-status-text');
    const event = status.latest_event || {};
    if (badgeEl) {
      if (status.running) {
        badgeEl.className = 'badge-status-live';
        badgeEl.innerHTML = '<span class="pulse-dot" style="width:5px; height:5px; background:#ef4444; border-radius:50%; box-shadow:0 0 4px #ef4444;"></span> LIVE';
      } else {
        badgeEl.className = 'badge-status-standby';
        badgeEl.innerText = 'STANDBY';
      }
    }
    if (textEl) {
      textEl.innerText = event.event_text || 'Monitoring transaction channel...';
      textEl.title = event.event_text || 'Simulation Standby';
    }

    // 4. Update HUD Pill in Arena
    const hudPill = document.getElementById('arena-hud-pill');
    const hudIcon = document.getElementById('arena-hud-icon');
    const hudLabel = document.getElementById('arena-hud-label');
    if (hudPill && hudIcon && hudLabel) {
      const eType = (event.event_type || 'Idle').toLowerCase();
      hudPill.className = `arena-hud-pill pill-${eType}`;
      if (eType === 'sale') {
        hudIcon.innerText = '🛍️';
        hudLabel.innerText = event.product_name ? `SALE: ${event.product_name} (+$${(event.unit_price || 0).toFixed(2)})` : 'SALE CONFIRMED';
      } else if (eType === 'purchase') {
        hudIcon.innerText = '🚚';
        hudLabel.innerText = event.product_name ? `RESTOCK: ${event.product_name} INBOUND` : 'RESTOCK INBOUND';
      } else if (eType === 'blocked') {
        hudIcon.innerText = '⚠️';
        hudLabel.innerText = 'CIRCUIT BLOCKED';
      } else {
        hudIcon.innerText = '⚡';
        hudLabel.innerText = status.running ? 'STREAM INGESTION ONLINE' : 'SIMULATION STANDBY';
      }
    }

    // 5. Update Arena Animation Target
    const ctxProd = status.active_product_context || {};
    this.triggerArenaEvent(
      event.event_type || 'Idle',
      ctxProd.current_stock || 0,
      ctxProd.max_stock || 100,
      ctxProd.product_name || '',
      ctxProd.unit_price || 0
    );

    // 6. Update Stock Chart
    if (chartItems && chartItems.length > 0) {
      ChartsManager.initLiveOpsStockChart('chart-live-ops-stock', chartItems);
      const sub = document.getElementById('live-ops-chart-subtitle');
      if (sub && event.product_name && (event.event_type === 'Sale' || event.event_type === 'Purchase')) {
        sub.innerHTML = `Dynamic event color highlighting • Latest Change: <b style="color:#f8fafc;">${event.product_name}</b> (${event.event_type})`;
      }
    }

    // 7. Render Ledgers
    this.renderLiveLedgers(ledgers);
  },

  renderLiveLedgers(ledgers) {
    const salesContainer = document.getElementById('live-sales-log-container');
    const restocksContainer = document.getElementById('live-restocks-log-container');

    if (salesContainer) {
      const sales = ledgers?.sales_log || [];
      if (sales.length === 0) {
        salesContainer.innerHTML = '<div style="text-align:center; padding:16px; color:var(--text-muted); font-size:12px;">Awaiting customer checkout events...</div>';
      } else {
        salesContainer.innerHTML = sales.map(s => {
          const timeStr = s.timestamp?.split(' ')[1] || s.timestamp;
          const promoBadge = s.is_promotional ? '<span class="badge-gold" style="font-size:9px; padding:1px 5px;">PROMO</span>' : '';
          return `
            <div class="live-log-item" style="border-left: 3px solid var(--emerald);">
              <div style="min-width:0;">
                <div style="font-weight:600; color:#f8fafc; display:flex; align-items:center; gap:6px;">
                  <span>${s.customer_name}</span>
                  <span style="font-size:10px; color:var(--text-muted);">(${s.size_purchased})</span>
                  ${promoBadge}
                </div>
                <div style="font-size:11px; color:var(--text-muted);">${s.product_name}</div>
              </div>
              <div style="text-align:right;">
                <div style="font-weight:700; color:var(--emerald);">+$${s.revenue.toFixed(2)}</div>
                <div style="font-size:10px; color:var(--text-muted);">${timeStr}</div>
              </div>
            </div>
          `;
        }).join('');
      }
    }

    if (restocksContainer) {
      const restocks = ledgers?.restocks_log || [];
      if (restocks.length === 0) {
        restocksContainer.innerHTML = '<div style="text-align:center; padding:16px; color:var(--text-muted); font-size:12px;">Awaiting supplier deliveries...</div>';
      } else {
        restocksContainer.innerHTML = restocks.map(r => {
          const timeStr = r.timestamp?.split(' ')[1] || r.timestamp;
          return `
            <div class="live-log-item" style="border-left: 3px solid var(--indigo);">
              <div style="min-width:0;">
                <div style="font-weight:600; color:#f8fafc;">Received +${r.quantity}x units</div>
                <div style="font-size:11px; color:var(--text-muted);">${r.product_name}</div>
              </div>
              <div style="text-align:right;">
                <div style="font-weight:700; color:var(--gold-light);">-$${r.cost.toFixed(2)}</div>
                <div style="font-size:10px; color:var(--text-muted);">${timeStr}</div>
              </div>
            </div>
          `;
        }).join('');
      }
    }
  },

  // ----------------------------------------------------
  // 60 FPS HTML5 CANVAS ARENA ENGINE
  // ----------------------------------------------------
  initLiveArena() {
    const canvas = document.getElementById('liveArenaCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let W = 0, H = 0, DPR = window.devicePixelRatio || 1;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      W = rect.width || 800;
      H = rect.height || 220;
      canvas.width = Math.round(W * DPR);
      canvas.height = Math.round(H * DPR);
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    };

    window.addEventListener('resize', resize);
    resize();

    // Stars / luxury ambient particles
    const stars = [];
    for (let i = 0; i < 30; i++) {
      stars.push({
        x: Math.random(),
        y: Math.random() * 0.7,
        radius: Math.random() * 1.2 + 0.4,
        alpha: Math.random() * 0.6 + 0.2,
        speed: Math.random() * 0.0008 + 0.0003
      });
    }

    const state = {
      W, H, ctx, resize,
      stockFill: 50,
      targetStockFill: 50,
      curStock: 50,
      maxStock: 100,
      wavePhase: 0,
      waveSplash: 0,
      particles: [],
      truck: { x: -160, targetX: -160, speed: 0, state: 'idle', cargoCount: 3, wheelAngle: 0 },
      shopper: { x: 900, targetX: 900, speed: 0, state: 'idle', walkCycle: 0, hasBag: false, cheerTimer: 0 },
      lastEventId: '',
      lastTime: performance.now()
    };

    this.state.arenaState = state;

    // 60 FPS Animation Loop
    const frame = (now) => {
      const dt = Math.min((now - state.lastTime) / 1000, 0.1);
      state.lastTime = now;

      const curW = canvas.getBoundingClientRect().width || 800;
      const curH = canvas.getBoundingClientRect().height || 220;

      // 1. Clear frame
      ctx.clearRect(0, 0, curW, curH);

      const groundY = curH - 52;
      const boutiqueX = Math.max(curW - 165, 520);

      // 2. Stars
      stars.forEach(s => {
        s.x = (s.x + s.speed) % 1;
        ctx.beginPath();
        ctx.arc(s.x * curW, s.y * curH, s.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${s.alpha})`;
        ctx.fill();
      });

      // Ground runway
      ctx.beginPath();
      ctx.moveTo(10, groundY);
      ctx.lineTo(curW - 10, groundY);
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#334155';
      ctx.stroke();

      // Glowing road dashes
      ctx.setLineDash([12, 16]);
      ctx.beginPath();
      ctx.moveTo(140, groundY + 12);
      ctx.lineTo(curW - 40, groundY + 12);
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = 'rgba(51, 65, 85, 0.6)';
      ctx.stroke();
      ctx.setLineDash([]);

      // 3. Liquid Tank (Left Depot)
      const tankX = 70;
      const tankY = groundY - 56;
      const tankR = 42;

      state.stockFill += (state.targetStockFill - state.stockFill) * 0.08;
      state.wavePhase += dt * 3.2;
      state.waveSplash = Math.max(0, state.waveSplash - dt * 0.6);

      ctx.save();
      ctx.beginPath();
      ctx.arc(tankX, tankY, tankR, 0, Math.PI * 2);
      ctx.clip();

      ctx.fillStyle = '#090d16';
      ctx.fill();

      // Sine Waves
      const waterY = tankY + tankR - (state.stockFill / 100) * (2 * tankR);

      // Back wave
      ctx.beginPath();
      ctx.moveTo(tankX - tankR, tankY + tankR);
      for (let x = tankX - tankR; x <= tankX + tankR; x += 2) {
        const wy = waterY + Math.sin((x - tankX) * 0.07 + state.wavePhase) * (3.5 + state.waveSplash * 6);
        ctx.lineTo(x, wy);
      }
      ctx.lineTo(tankX + tankR, tankY + tankR);
      ctx.closePath();
      ctx.fillStyle = 'rgba(30, 58, 138, 0.45)';
      ctx.fill();

      // Front wave
      ctx.beginPath();
      ctx.moveTo(tankX - tankR, tankY + tankR);
      for (let x = tankX - tankR; x <= tankX + tankR; x += 2) {
        const wy = waterY + Math.sin((x - tankX) * 0.08 + state.wavePhase * 1.35 + 1.2) * (2.8 + state.waveSplash * 5);
        ctx.lineTo(x, wy);
      }
      ctx.lineTo(tankX + tankR, tankY + tankR);
      ctx.closePath();
      const liquidGrad = ctx.createLinearGradient(tankX, waterY - 10, tankX, tankY + tankR);
      liquidGrad.addColorStop(0, '#06b6d4');
      liquidGrad.addColorStop(0.45, '#2563eb');
      liquidGrad.addColorStop(1, '#1e1b4b');
      ctx.fillStyle = liquidGrad;
      ctx.fill();
      ctx.restore();

      // Tank Bezel
      ctx.beginPath();
      ctx.arc(tankX, tankY, tankR, 0, Math.PI * 2);
      ctx.lineWidth = 4;
      ctx.strokeStyle = '#334155';
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(tankX, tankY, tankR - 1, 0, Math.PI * 2);
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = state.stockFill <= 15 ? '#ef4444' : (state.stockFill <= 35 ? '#f59e0b' : '#38bdf8');
      ctx.stroke();

      // Tank Label
      ctx.font = 'bold 11.5px Inter, sans-serif';
      ctx.fillStyle = '#f8fafc';
      ctx.textAlign = 'center';
      ctx.fillText(`${state.curStock} / ${state.maxStock} Qty`, tankX, groundY + 18);

      ctx.font = '9px monospace';
      ctx.fillStyle = '#64748b';
      ctx.fillText(`STOCK ${Math.round(state.stockFill)}%`, tankX, groundY + 31);

      // 4. Boutique Architecture (Right Storefront)
      const bW = 120, bH = 96;
      const bY = groundY - bH;

      ctx.fillStyle = '#0f172a';
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 2;
      ctx.fillRect(boutiqueX, bY, bW, bH);
      ctx.strokeRect(boutiqueX, bY, bW, bH);

      // Gold Roof Cornice
      ctx.fillStyle = '#d4af37';
      ctx.fillRect(boutiqueX - 4, bY - 4, bW + 8, 6);

      // Store Title Sign
      ctx.fillStyle = '#020617';
      ctx.fillRect(boutiqueX + 8, bY + 8, bW - 16, 20);
      ctx.strokeStyle = '#b45309';
      ctx.strokeRect(boutiqueX + 8, bY + 8, bW - 16, 20);

      ctx.font = 'bold 9px "Playfair Display", serif';
      ctx.fillStyle = '#fef08a';
      ctx.textAlign = 'center';
      ctx.fillText('MISHIKA ATELIER', boutiqueX + bW / 2, bY + 21);

      // Showroom Window with Warm Glow
      ctx.fillStyle = '#1e293b';
      ctx.fillRect(boutiqueX + 10, bY + 36, bW - 20, 54);

      const glowGrad = ctx.createLinearGradient(boutiqueX + 10, bY + 36, boutiqueX + 10, bY + 90);
      glowGrad.addColorStop(0, 'rgba(253, 224, 71, 0.35)');
      glowGrad.addColorStop(1, 'rgba(15, 23, 42, 0.85)');
      ctx.fillStyle = glowGrad;
      ctx.fillRect(boutiqueX + 12, bY + 38, bW - 24, 50);

      // Boutique Glass Doors
      ctx.strokeStyle = 'rgba(212, 175, 55, 0.45)';
      ctx.lineWidth = 1;
      ctx.strokeRect(boutiqueX + 38, bY + 45, 44, 43);
      ctx.beginPath();
      ctx.moveTo(boutiqueX + 60, bY + 45);
      ctx.lineTo(boutiqueX + 60, bY + 88);
      ctx.stroke();

      // 5. Depot Platform (Left)
      ctx.fillStyle = '#1e293b';
      ctx.fillRect(115, groundY - 18, 38, 18);
      ctx.strokeStyle = '#334155';
      ctx.strokeRect(115, groundY - 18, 38, 18);

      // Overhead Depot Lamp
      ctx.beginPath();
      ctx.moveTo(134, groundY - 18);
      ctx.lineTo(134, groundY - 48);
      ctx.lineTo(146, groundY - 48);
      ctx.strokeStyle = '#475569';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(146, groundY - 46, 3, 0, Math.PI * 2);
      ctx.fillStyle = '#38bdf8';
      ctx.fill();

      // 6. Delivery Truck Simulation
      const t = state.truck;
      if (t.state === 'inbound') {
        const dx = t.targetX - t.x;
        t.speed = Math.max(25, Math.min(180, dx * 1.8));
        t.x += t.speed * dt;
        t.wheelAngle += dt * 10;
        if (t.x >= t.targetX - 2) {
          t.x = t.targetX;
          t.state = 'docked';
          t.unloadTimer = 1.4;
        }
      } else if (t.state === 'docked') {
        t.unloadTimer -= dt;
        if (t.unloadTimer <= 0) {
          t.state = 'outbound';
          t.targetX = curW + 80;
        }
      } else if (t.state === 'outbound') {
        t.speed = Math.min(220, (t.speed || 40) + 90 * dt);
        t.x += t.speed * dt;
        t.wheelAngle += dt * 12;
        if (t.x > curW + 60) {
          t.state = 'idle';
        }
      }

      // Draw Truck
      if (t.x > -140 && t.x < curW + 60) {
        const trY = groundY - 42;
        // Cargo Bay
        ctx.fillStyle = '#1e293b';
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 1.5;
        ctx.fillRect(t.x - 70, trY, 52, 34);
        ctx.strokeRect(t.x - 70, trY, 52, 34);

        // Crates inside bay
        if (t.state !== 'outbound' && t.cargoCount > 0) {
          ctx.fillStyle = '#b45309';
          ctx.fillRect(t.x - 64, trY + 12, 16, 16);
          ctx.fillRect(t.x - 44, trY + 12, 16, 16);
        }

        // Cab
        ctx.fillStyle = '#2563eb';
        ctx.fillRect(t.x - 18, trY + 8, 26, 26);
        // Windshield
        ctx.fillStyle = '#93c5fd';
        ctx.fillRect(t.x - 6, trY + 11, 12, 10);
        // Headlight
        ctx.fillStyle = '#fef08a';
        ctx.fillRect(t.x + 8, trY + 24, 3, 5);

        // Wheels
        [t.x - 56, t.x - 30, t.x - 4].forEach(wx => {
          ctx.beginPath();
          ctx.arc(wx, groundY - 4, 7, 0, Math.PI * 2);
          ctx.fillStyle = '#0f172a';
          ctx.fill();
          ctx.lineWidth = 1.5;
          ctx.strokeStyle = '#64748b';
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(wx, groundY - 4, 3, 0, Math.PI * 2);
          ctx.fillStyle = '#cbd5e1';
          ctx.fill();
        });
      }

      // 7. Luxury Shopper Simulation
      const sh = state.shopper;
      if (sh.state === 'entering') {
        const dx = sh.targetX - sh.x;
        sh.speed = -Math.max(30, Math.min(110, Math.abs(dx) * 1.5));
        sh.x += sh.speed * dt;
        sh.walkCycle += dt * 7;
        if (sh.x <= sh.targetX + 3) {
          sh.x = sh.targetX;
          sh.state = 'shopping';
          sh.shopTimer = 1.2;
          for (let p = 0; p < 14; p++) {
            state.particles.push({
              x: boutiqueX + 45 + Math.random() * 20,
              y: groundY - 45 + Math.random() * 20,
              vx: (Math.random() - 0.5) * 60,
              vy: -Math.random() * 50 - 20,
              color: Math.random() > 0.4 ? '#f59e0b' : '#34d399',
              life: 1.0,
              size: Math.random() * 3 + 1.5
            });
          }
        }
      } else if (sh.state === 'shopping') {
        sh.shopTimer -= dt;
        if (sh.shopTimer <= 0) {
          sh.state = 'exiting';
          sh.hasBag = true;
          sh.targetX = -60;
        }
      } else if (sh.state === 'exiting') {
        sh.speed = -85;
        sh.x += sh.speed * dt;
        sh.walkCycle += dt * 8;
        if (sh.x < -40) {
          sh.state = 'idle';
        }
      }

      // Draw Shopper
      if (sh.x > -30 && sh.x < curW + 40 && sh.state !== 'shopping') {
        const shY = groundY - 48;
        const legOffset = Math.sin(sh.walkCycle) * 5;

        // Legs
        ctx.strokeStyle = '#f8fafc';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(sh.x - 2, shY + 32);
        ctx.lineTo(sh.x - 2 - legOffset, groundY);
        ctx.moveTo(sh.x + 2, shY + 32);
        ctx.lineTo(sh.x + 2 + legOffset, groundY);
        ctx.stroke();

        // Elegant Dress Silhouette
        ctx.fillStyle = '#e11d48';
        ctx.beginPath();
        ctx.moveTo(sh.x, shY + 12);
        ctx.lineTo(sh.x - 7, shY + 34);
        ctx.lineTo(sh.x + 7, shY + 34);
        ctx.closePath();
        ctx.fill();

        // Torso / Coat
        ctx.fillStyle = '#be123c';
        ctx.fillRect(sh.x - 4, shY + 12, 8, 14);

        // Head
        ctx.beginPath();
        ctx.arc(sh.x, shY + 6, 5, 0, Math.PI * 2);
        ctx.fillStyle = '#fed7aa';
        ctx.fill();

        // Couture Hat
        ctx.fillStyle = '#0f172a';
        ctx.beginPath();
        ctx.ellipse(sh.x, shY + 3, 7, 2.5, 0, 0, Math.PI * 2);
        ctx.fill();

        // Luxury Boutique Shopping Bag
        if (sh.hasBag) {
          const bagX = sh.x - 10;
          const bagY = shY + 22;
          ctx.fillStyle = '#d4af37';
          ctx.fillRect(bagX, bagY, 9, 12);
          ctx.strokeStyle = '#92400e';
          ctx.strokeRect(bagX, bagY, 9, 12);

          // Handle
          ctx.beginPath();
          ctx.arc(bagX + 4.5, bagY - 2, 3, Math.PI, 0);
          ctx.strokeStyle = '#fef08a';
          ctx.stroke();
        }
      }

      // 8. Particle Sparkles
      for (let i = state.particles.length - 1; i >= 0; i--) {
        const p = state.particles[i];
        p.life -= dt * 1.2;
        p.x += p.vx * dt;
        p.y += p.vy * dt;
        if (p.life <= 0) {
          state.particles.splice(i, 1);
        } else {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
          ctx.fillStyle = p.color;
          ctx.globalAlpha = Math.max(0, p.life);
          ctx.fill();
          ctx.globalAlpha = 1.0;
        }
      }

      requestAnimationFrame(frame);
    };

    requestAnimationFrame(frame);
  },

  resizeLiveArena() {
    if (this.state.arenaState?.resize) {
      this.state.arenaState.resize();
    }
  },

  triggerArenaEvent(eventType, currentStock, maxStock, productName, unitPrice) {
    const state = this.state.arenaState;
    if (!state) return;

    state.curStock = currentStock;
    state.maxStock = maxStock || 100;
    state.targetStockFill = Math.min(100, Math.max(0, Math.round((currentStock / state.maxStock) * 100)));

    const eventKey = `${eventType}_${currentStock}_${productName}`;
    if (state.lastEventId === eventKey) return;
    state.lastEventId = eventKey;

    if (eventType === 'Purchase') {
      state.truck.x = -140;
      state.truck.targetX = 145;
      state.truck.state = 'inbound';
      state.truck.cargoCount = 3;
      state.waveSplash = 0.8;
    } else if (eventType === 'Sale') {
      const curW = state.ctx?.canvas?.getBoundingClientRect()?.width || 800;
      state.shopper.x = Math.max(curW - 20, 680);
      state.shopper.targetX = Math.max(curW - 130, 540);
      state.shopper.state = 'entering';
      state.shopper.hasBag = false;
    }
  }
};

// Start application when DOM is ready
document.addEventListener('DOMContentLoaded', () => App.init());
