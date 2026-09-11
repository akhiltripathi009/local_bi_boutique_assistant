/**
 * Mishika Fashion Luxury Boutique - API Client Layer
 * Clean async REST client with Server-Sent Events (SSE) streaming support
 */

const API = {
  // Base fetch helper
  async request(endpoint, options = {}) {
    try {
      const response = await fetch(endpoint, {
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {})
        },
        ...options
      });

      if (!response.ok) {
        let errDetail = 'Request failed';
        try {
          const errData = await response.json();
          errDetail = errData.detail || errData.message || JSON.stringify(errData);
        } catch (_) {
          errDetail = await response.text();
        }
        throw new Error(errDetail);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error on ${endpoint}:`, error);
      throw error;
    }
  },

  // Health
  getHealth: () => API.request('/api/health'),

  // Dashboard
  getDashboardStats: () => API.request('/api/dashboard/stats'),
  getDashboardCharts: () => API.request('/api/dashboard/charts'),
  getDashboardAlerts: () => API.request('/api/dashboard/alerts'),

  // Inventory & Warehouse
  getInventoryOverview: () => API.request('/api/inventory/overview'),
  transferStock: (payload) => API.request('/api/inventory/transfer', {
    method: 'POST',
    body: JSON.stringify(payload)
  }),
  addNewProduct: (payload) => API.request('/api/inventory/add-product', {
    method: 'POST',
    body: JSON.stringify(payload)
  }),
  placeProcurementOrder: (payload) => API.request('/api/inventory/procurement-order', {
    method: 'POST',
    body: JSON.stringify(payload)
  }),
  getTransferHistory: () => API.request('/api/inventory/transfers'),

  // CRM
  getCustomers: (tier = '', search = '') => {
    const params = new URLSearchParams();
    if (tier && tier !== 'All') params.append('tier', tier);
    if (search) params.append('search', search);
    return API.request(`/api/crm/customers?${params.toString()}`);
  },
  getCustomerProfile: (id) => API.request(`/api/crm/customer/${id}`),
  updateCustomerContact: (id, payload) => API.request(`/api/crm/customer/${id}/update`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }),
  getUpcomingBirthdays: (daysAhead = 14) => API.request(`/api/crm/birthdays?days_ahead=${daysAhead}`),

  // Campaigns
  getCampaigns: () => API.request('/api/campaigns'),
  createCampaign: (payload) => API.request('/api/campaigns/create', {
    method: 'POST',
    body: JSON.stringify(payload)
  }),
  updateCampaignStatus: (id, status) => API.request(`/api/campaigns/${id}/status`, {
    method: 'POST',
    body: JSON.stringify({ status })
  }),

  // Agent (Shivi)
  getAgentStatus: () => API.request('/api/agent/status'),
  runAgentAction: (action, options = {}) => API.request('/api/agent/run-action', {
    method: 'POST',
    body: JSON.stringify({ action, ...options })
  }),
  getAgentApprovals: () => API.request('/api/agent/approvals'),
  processApproval: (id, decision) => API.request(`/api/agent/approvals/${id}/action`, {
    method: 'POST',
    body: JSON.stringify({ decision })
  }),
  getAgentCommunications: () => API.request('/api/agent/communications'),
  getAgentNewsPreview: (topicQuery = '', randomize = false, customerId = null) => {
    const params = new URLSearchParams();
    if (topicQuery) params.append('topic_query', topicQuery);
    if (randomize) params.append('randomize', 'true');
    if (customerId) params.append('customer_id', customerId);
    const qs = params.toString();
    return API.request(`/api/agent/news-preview${qs ? '?' + qs : ''}`);
  },
  sendAgentEmail: (payload) => API.request('/api/agent/send-email', {
    method: 'POST',
    body: JSON.stringify(payload)
  }),
  getAgentEmailConfig: () => API.request('/api/agent/email-config'),
  saveAgentEmailConfig: (config) => API.request('/api/agent/email-config', {
    method: 'POST',
    body: JSON.stringify(config)
  }),
  testAgentEmail: (toEmail, config = null) => API.request('/api/agent/test-email', {
    method: 'POST',
    body: JSON.stringify({ to_email: toEmail, config })
  }),
  testPIIRedaction: (text) => API.request('/api/agent/guardrails/redact-pii', {
    method: 'POST',
    body: JSON.stringify({ text })
  }),
  testDiscountGuardrail: (discountPct, isSuperadmin = false) => API.request('/api/agent/guardrails/validate-discount', {
    method: 'POST',
    body: JSON.stringify({ discount_pct: discountPct, is_superadmin: isSuperadmin })
  }),

  // Copilot (Ollama)
  getCopilotModels: () => API.request('/api/copilot/models'),
  getCopilotPersonas: () => API.request('/api/copilot/personas'),
  getCopilotFAQs: () => API.request('/api/copilot/faqs'),
  getCopilotKnowledge: () => API.request('/api/copilot/knowledge'),

  /**
   * Stream copilot chat via Server-Sent Events (SSE)
   */
  async streamCopilotChat(messages, model, personaKey, onToken, onComplete, onError) {
    try {
      const response = await fetch('/api/copilot/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages,
          model,
          persona_key: personaKey
        })
      });

      if (!response.ok) {
        throw new Error(`SSE request failed: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop(); // Keep partial chunk in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.replace('data: ', '').trim();
            if (jsonStr) {
              try {
                const data = JSON.parse(jsonStr);
                if (data.token) {
                  onToken(data.token);
                }
                if (data.done) {
                  onComplete();
                  return;
                }
                if (data.error) {
                  onError(new Error(data.error));
                  return;
                }
              } catch (e) {
                console.warn('Failed to parse SSE payload:', jsonStr);
              }
            }
          }
        }
      }
      onComplete();
    } catch (err) {
      if (onError) onError(err);
    }
  },

  // Sandbox
  getSandboxPresets: () => API.request('/api/sandbox/presets'),
  executeSandboxCode: (code) => API.request('/api/sandbox/execute', {
    method: 'POST',
    body: JSON.stringify({ code })
  }),

  // Live Shop Operations (Segment 2)
  getLiveOpsStatus: () => API.request('/api/live-ops/status'),
  startLiveOps: () => API.request('/api/live-ops/start', { method: 'POST' }),
  pauseLiveOps: () => API.request('/api/live-ops/pause', { method: 'POST' }),
  stepLiveOpsTick: () => API.request('/api/live-ops/tick', { method: 'POST' }),
  updateLiveOpsSettings: (payload) => API.request('/api/live-ops/settings', {
    method: 'POST',
    body: JSON.stringify(payload)
  }),
  resetLiveOpsInventory: () => API.request('/api/live-ops/reset', { method: 'POST' }),
  getLiveOpsStockChart: () => API.request('/api/live-ops/stock-chart'),
  getLiveOpsLogs: (limit = 8) => API.request(`/api/live-ops/logs?limit=${limit}`)
};

// UI Notification Toast Helper
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✅' : '⚠️'}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
