"""
theme_manager.py
Handles the visual styling and luxury branding of the Streamlit application.
Includes custom CSS injections, KPI layouts, and animated operational arenas.
"""
import streamlit as st
import streamlit.components.v1 as components
import logging
import time
from logger_config import setup_logging

logger = setup_logging("theme_manager")


def _clean_html(raw_html: str) -> str:
    """
    Normalizes a multi-line HTML/CSS string into a single continuous block.

    Kept as a defensive helper for any legacy ``st.markdown`` call sites, but
    the primary rendering path now uses ``st.html`` (Streamlit >= 1.33), which
    renders raw HTML directly and does NOT run it through the Markdown parser.
    That means indented lines or blank lines can no longer be misinterpreted as
    literal code blocks (the root cause of raw HTML showing up on the UI).

    Args:
        raw_html (str): The indented multi-line HTML/CSS string.

    Returns:
        str: A normalized, single-block HTML string safe for st.markdown.
    """
    return " ".join(line.strip() for line in raw_html.splitlines() if line.strip())


def inject_luxury_branding():
    """
    Injects premium CSS styles and micro-animations into the Streamlit app.
    Sets the typography, card layouts, and keyframe animations for sprites.
    """
    try:
        st.html("""
        <link href="https://jsdelivr.net" rel="stylesheet">
        <link href="https://googleapis.com" rel="stylesheet">

        <style>
        html, body, [class*="st-text"], .stMarkdown { font-family: 'Inter', sans-serif; color: #1e293b; }
        h1, h2, h3, .luxury-title { font-family: 'Playfair Display', serif !important; color: #0f172a !important; }

        .premium-card {
            background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03); position: relative; overflow: hidden;
        }

        .metric-card {
            background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 5px solid #2c3e50; margin-bottom: 15px;
        }
        .badge-dead { background-color: #fdebd0; color: #b03a2e; padding: 4px 8px; border-radius: 4px; font-weight: bold; }

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
    """)
    except Exception as e:
        logger.error(f"Error injecting luxury branding: {e}")


def render_luxury_kpi_strip(revenue: float, low_stock: int, status_text: str, is_active: bool):
    """
    Renders a row of three premium KPI cards at the top of the dashboard.
    
    Args:
        revenue (float): Total session revenue.
        low_stock (int): Count of products with low stock levels.
        status_text (str): Current status message from the simulation engine.
        is_active (bool): Whether the real-time simulation is currently running.
    """
    try:
        badge_html = '<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-red-500 text-white animate-pulse">● LIVE STREAM</span>' if is_active else '<span class="bg-gray-200 text-gray-700 px-3 py-1 rounded-full text-xs font-bold">OFFLINE</span>'
        st.html(f"""
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
        """)
    except Exception as e:
        logger.error(f"Error rendering luxury KPI strip: {e}")


def render_animated_arena(event_type: str, current_stock: int, max_stock: int):
    """
    Renders an animated stage showing customer activity or truck deliveries.
    
    Args:
        event_type (str): Type of event to animate ('Sale', 'Purchase', or 'Idle').
        current_stock (int): Current total stock level of the highlighted product.
        max_stock (int): Maximum capacity limit for the product.
    """
    try:
        fill_percentage = min(100, int((current_stock / max_stock) * 100)) if max_stock > 0 else 0
        wave_top_position = 100 - fill_percentage

        # ROOT-CAUSE FIX: st.html() injects HTML into the main app DOM and runs it
        # through Streamlit's sanitizer, which strips <style>/@keyframes -> the
        # sprites never moved (they looked static). components.html() instead
        # loads a REAL sandboxed <iframe> document that fully executes CSS
        # animations and reloads on every rerun, so motion is guaranteed.
        #
        # Both sprites now animate on an INFINITE loop so the stage is always
        # visibly alive; the sprite matching the current event is fully opaque
        # and highlighted, while the other is dimmed to indicate the active flow.
        truck_active = event_type == "Purchase"
        shopper_active = event_type == "Sale"
        truck_opacity = "1" if truck_active else "0.28"
        shopper_opacity = "1" if shopper_active else "0.28"

        # SMOOTHNESS FIX: components.html() reloads a fresh iframe on every
        # simulation tick, which would restart the CSS animation from 0% and
        # make the sprites appear to "jump" back and move in fast bursts. By
        # anchoring each animation to a NEGATIVE animation-delay derived from the
        # continuous wall-clock time, every fresh iframe resumes the animation at
        # the exact phase it should already be in, producing one seamless, slow,
        # continuous glide across reruns instead of stuttering restarts.
        anim_period = 7.0
        phase_offset = time.time() % anim_period
        anim_delay = f"-{phase_offset:.3f}s"

        arena_html = f"""
        <style>
            @keyframes arena-truck {{
                0%   {{ transform: translateX(-160px) translateY(0);   opacity: 0; }}
                12%  {{ transform: translateX(-40px)  translateY(0);   opacity: 1; }}
                40%  {{ transform: translateX(150px)  translateY(-2px); opacity: 1; }}
                60%  {{ transform: translateX(150px)  translateY(0);   opacity: 1; }}
                88%  {{ transform: translateX(430px)  translateY(-2px); opacity: 1; }}
                100% {{ transform: translateX(540px)  translateY(0);   opacity: 0; }}
            }}
            @keyframes arena-shopper {{
                0%   {{ transform: translateX(500px)  translateY(0);   opacity: 0; }}
                12%  {{ transform: translateX(380px)  translateY(0);   opacity: 1; }}
                40%  {{ transform: translateX(200px)  translateY(-2px); opacity: 1; }}
                60%  {{ transform: translateX(200px)  translateY(0);   opacity: 1; }}
                88%  {{ transform: translateX(-30px)  translateY(-2px); opacity: 1; }}
                100% {{ transform: translateX(-150px) translateY(0);   opacity: 0; }}
            }}
            @keyframes arena-wave {{
                0%   {{ transform: translateX(0) rotate(0deg); }}
                100% {{ transform: translateX(-25%) rotate(360deg); }}
            }}
            @keyframes arena-bob {{
                0%, 100% {{ transform: translateY(0); }}
                50%      {{ transform: translateY(-6px); }}
            }}
            .arena-stage {{
                position: relative; width: 100%; height: 240px; overflow: hidden;
                background-color: #0f172a; border: 1px solid #1e293b; border-radius: 16px;
                margin: 16px 0; font-family: monospace;
            }}
            .arena-label {{
                position: absolute; top: 16px; left: 20px; color: #64748b;
                font-size: 11px; letter-spacing: 2px; text-transform: uppercase;
            }}
            .arena-tank-wrap {{
                position: absolute; top: 50%; left: 40px; transform: translateY(-50%);
                display: flex; flex-direction: column; align-items: center; z-index: 10;
            }}
            .arena-tank {{
                position: relative; width: 90px; height: 90px; background: #e2e8f0;
                border-radius: 50%; overflow: hidden; border: 3px solid #1e293b;
            }}
            .arena-wave {{
                position: absolute; width: 200%; height: 200%; background: #2c3e50;
                left: -50%; border-radius: 38%;
                animation: arena-wave 6s infinite linear;
            }}
            .arena-qty {{ color: #fff; font-weight: bold; margin-top: 8px; font-size: 13px; }}
            .arena-ground {{
                position: absolute; bottom: 60px; left: 190px; right: 40px;
                height: 3px; background: #334155; border-radius: 3px;
            }}
            .arena-store {{
                position: absolute; bottom: 66px; left: 300px; font-size: 42px;
                animation: arena-bob 3s ease-in-out infinite; z-index: 5;
            }}
            .arena-sprite {{
                position: absolute; bottom: 66px; left: 190px; font-size: 42px; z-index: 6;
            }}
            .arena-tag {{
                position: absolute; top: -22px; left: 8px; font-size: 10px; color: #fff;
                font-weight: bold; padding: 2px 5px; border-radius: 4px;
                white-space: nowrap; font-family: sans-serif;
            }}
        </style>
        <div class="arena-stage">
            <div class="arena-label">Visual Arena Pipeline</div>

            <div class="arena-tank-wrap">
                <div class="arena-tank">
                    <div class="arena-wave" style="top: {wave_top_position}%;"></div>
                </div>
                <span class="arena-qty">{current_stock} / {max_stock} Qty</span>
            </div>

            <div class="arena-ground"></div>
            <div class="arena-store">🏪</div>

            <div class="arena-sprite" style="opacity: {truck_opacity}; animation: arena-truck 7s linear {anim_delay} infinite; will-change: transform, opacity;">
                🚚<span class="arena-tag" style="background:#2563eb;">RESTOCK INBOUND</span>
            </div>

            <div class="arena-sprite" style="opacity: {shopper_opacity}; animation: arena-shopper 7s linear {anim_delay} infinite; will-change: transform, opacity;">
                🚶<span class="arena-tag" style="background:#059669;">BUYER</span>
            </div>
        </div>
        """

        # Render inside a real sandboxed iframe so the CSS keyframes execute.
        components.html(arena_html, height=260)
    except Exception as e:
        logger.error(f"Error rendering animated arena: {e}")
