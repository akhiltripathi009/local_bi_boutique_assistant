# theme_manager.py
import streamlit as st


def inject_luxury_branding():
    """Injects Google Fonts, TailwindCSS components, and interactive CSS hover frames."""
    st.markdown("""
        <link href="https://jsdelivr.net" rel="stylesheet">
        <link href="https://googleapis.com" rel="stylesheet">

        <style>
        /* Base typography overrides */
        html, body, [class*="st-text"], .stMarkdown {
            font-family: 'Inter', sans-serif;
            color: #1e293b;
        }
        h1, h2, h3, .luxury-header {
            font-family: 'Playfair Display', serif !important;
            color: #0f172a !important;
        }

        /* Glassmorphism Key KPI Styling Cards */
        .premium-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        .premium-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            border-color: #cbd5e1;
        }
        .premium-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; width: 4px; height: 100%;
        }
        .card-revenue::before { background: #10b981; }
        .card-stock::before { background: #f59e0b; }
        .card-status::before { background: #3b82f6; }

        /* Smooth CSS Pulse Animation for active loops */
        @keyframes subtle-pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.05); opacity: 0.85; }
        }
        .live-badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            background-color: #ef4444;
            color: white;
            animation: subtle-pulse 2s infinite ease-in-out;
        }

        /* Fade-in for real-time streaming logs */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .stream-tick {
            animation: fadeIn 0.4s ease-out forwards;
            border-left: 3px solid #64748b;
        }
        </style>
    """, unsafe_allow_html=True)


def render_luxury_kpi_strip(revenue: float, low_stock: int, status_text: str, is_active: bool):
    """Renders highly styled executive visual cards across column splits."""
    badge_html = '<span class="live-badge">● LIVE STREAM</span>' if is_active else '<span class="bg-gray-200 text-gray-700 px-3 py-1 rounded-full text-xs font-bold">OFFLINE</span>'

    st.markdown(f"""
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 my-6">
        <div class="premium-card card-revenue">
            <p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Database Session Revenue</p>
            <h3 class="text-3xl font-bold text-slate-800 mt-1">${revenue:,.2f}</h3>
            <p class="text-xs text-emerald-600 mt-2">↑ Cumulative Vault Metrics</p>
        </div>
        <div class="premium-card card-stock">
            <p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Critical Safety Breaches</p>
            <h3 class="text-3xl font-bold text-slate-800 mt-1">{low_stock} Styles</h3>
            <p class="text-xs text-amber-600 mt-2">Stock levels below 15 units</p>
        </div>
        <div class="premium-card card-status">
            <div class="flex justify-between items-center mb-1">
                <p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Engine Processing State</p>
                {badge_html}
            </div>
            <p class="text-sm font-medium text-slate-700 mt-2 truncate">{status_text if status_text else "Awaiting operation loop initialization..."}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
