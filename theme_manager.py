# theme_manager.py
import streamlit as st


def inject_luxury_branding():
    """Injects premium styles, layout rules, and micro-animations safely without f-string corruption."""
    st.markdown("""
        <link href="https://jsdelivr.net" rel="stylesheet">
        <link href="https://googleapis.com" rel="stylesheet">

        <style>
        html, body, [class*="st-text"], .stMarkdown { font-family: 'Inter', sans-serif; color: #1e293b; }
        h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #0f172a !important; }

        .premium-card {
            background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03); position: relative; overflow: hidden;
        }

        /* Fixed keyframe parsing structures using clean native string containers */
        @keyframes driveIn {
            0% { transform: translateX(-150px); opacity: 0; }
            45% { transform: translateX(180px); opacity: 1; }
            75% { transform: translateX(180px); opacity: 1; }
            100% { transform: translateX(600px); opacity: 0; }
        }
        @keyframes walkAndShop {
            0% { transform: translateX(500px); opacity: 0; }
            45% { transform: translateX(250px); opacity: 1; }
            75% { transform: translateX(250px); opacity: 1; }
            100% { transform: translateX(-100px); opacity: 0; }
        }
        @keyframes fillWave {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .animate-truck { animation: driveIn 2.5s cubic-bezier(0.25, 1, 0.5, 1) forwards; }
        .animate-shopper { animation: walkAndShop 2.5s cubic-bezier(0.25, 1, 0.5, 1) forwards; }

        .liquid-tank {
            position: relative; width: 100px; height: 100px; background: #e2e8f0;
            border-radius: 50%; overflow: hidden; border: 3px solid #1e293b;
        }
        .liquid-wave {
            position: absolute; width: 200%; height: 200%; background: #2c3e50;
            left: -50%; border-radius: 38%;
            animation: fillWave 6s infinite linear; transition: top 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
        </style>
    """, unsafe_allow_html=True)


def render_luxury_kpi_strip(revenue: float, low_stock: int, status_text: str, is_active: bool):
    badge_html = '<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-red-500 text-white animate-pulse">● LIVE STREAM</span>' if is_active else '<span class="bg-gray-200 text-gray-700 px-3 py-1 rounded-full text-xs font-bold">OFFLINE</span>'
    st.markdown(f"""
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 my-4">
        <div class="premium-card">
            <p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Database Session Revenue</p>
            <h3 class="text-3xl font-bold mt-1">${revenue:,.2f}</h3>
        </div>
        <div class="premium-card">
            <p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Critical Safety Breaches</p>
            <h3 class="text-3xl font-bold mt-1 text-amber-600">{low_stock} Styles</h3>
        </div>
        <div class="premium-card">
            <div class="flex justify-between items-center mb-1">
                <p class="text-xs uppercase font-semibold text-gray-400 tracking-wider">Engine Processing State</p>
                {badge_html}
            </div>
            <p class="text-sm font-medium text-slate-700 mt-2 truncate">{status_text if status_text else "Awaiting operation loop initialize..."}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_animated_arena(event_type: str, current_stock: int, max_stock: int):
    """Generates the graphical animation stage container overlaying active sprite channels."""
    fill_percentage = min(100, int((current_stock / max_stock) * 100)) if max_stock > 0 else 0
    wave_top_position = 100 - fill_percentage

    truck_class = "animate-truck" if event_type == "Purchase" else "opacity-0 hidden"
    shopper_class = "animate-shopper" if event_type == "Sale" else "opacity-0 hidden"

    st.markdown(f"""
    <div class="w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 relative overflow-hidden my-4" style="height: 240px; background-color: #0f172a;">
        <div class="absolute top-4 left-6 z-10">
            <span class="text-xs font-mono text-slate-500 uppercase tracking-widest">Visual Arena Pipeline</span>
        </div>

        <div class="absolute top-1/2 left-12 transform -translate-y-1/2 flex flex-col items-center z-10">
            <div class="liquid-tank">
                <div class="liquid-wave" style="top: {wave_top_position}%;"></div>
            </div>
            <span class="text-white font-mono font-bold mt-2 text-sm">{current_stock} / {max_stock} Qty</span>
        </div>

        <div class="absolute inset-0 w-full h-full flex items-end pb-8 pl-48 pr-12">
            <div class="absolute bottom-8 left-48 right-12 h-1 bg-slate-700 rounded-full"></div>

            <div class="absolute bottom-9 text-5xl {truck_class}" style="left: 0px;">
                🚚 <span class="text-xs bg-blue-600 text-white font-bold p-1 rounded shadow-md absolute -top-6 left-2 font-sans" style="font-size: 10px; white-space: nowrap;">RESTOCK INBOUND</span>
            </div>

            <div class="absolute bottom-9 text-5xl" style="left: 280px; z-index: 5;">
                🏪
            </div>

            <div class="absolute bottom-9 text-5xl {shopper_class}" style="left: 0px;">
                🚶‍♂️ <span class="text-xs bg-emerald-600 text-white font-bold p-1 rounded shadow-md absolute -top-6 left-2 font-sans" style="font-size: 10px; white-space: nowrap;">BUYER</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
