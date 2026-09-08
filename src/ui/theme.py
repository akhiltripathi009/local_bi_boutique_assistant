"""
theme_manager.py
Handles the visual styling and luxury branding of the Streamlit application.
Includes custom CSS injections, KPI layouts, and animated operational arenas.
"""
import streamlit as st
import logging
try:
    from src.core.logger import setup_logging
except ImportError:
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

        .animate-truck { animation: driveIn 4.5s cubic-bezier(0.25, 1, 0.5, 1) forwards; }
        .animate-shopper { animation: walkAndShop 4.5s cubic-bezier(0.25, 1, 0.5, 1) forwards; }

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
    Renders an ultra-compact, high-density row of three luxury KPI status cards
    (Total Sales Revenue, Low Stock Warnings, Pipeline Activity) visible at a glance.
    
    Args:
        revenue (float): Total session revenue.
        low_stock (int): Count of products with low stock levels.
        status_text (str): Current status message from the simulation engine.
        is_active (bool): Whether the real-time simulation is currently running.
    """
    try:
        safe_status = (status_text or "Monitoring transaction channel...").replace('"', '&quot;').replace("'", "&#39;")

        # Pipeline Activity Live Badge
        if is_active:
            badge_html = (
                '<span style="display:inline-flex; align-items:center; gap:4px; font-size:9.5px; font-weight:700; '
                'color:#ef4444; background:#fef2f2; border:1px solid #fecaca; padding:1px 7px; border-radius:9999px; white-space:nowrap;">'
                '<span style="width:5px; height:5px; background:#ef4444; border-radius:50%; box-shadow:0 0 4px #ef4444;"></span>'
                'LIVE</span>'
            )
        else:
            badge_html = (
                '<span style="font-size:9.5px; font-weight:700; color:#64748b; background:#f1f5f9; '
                'border:1px solid #cbd5e1; padding:1px 7px; border-radius:9999px; white-space:nowrap;">STANDBY</span>'
            )

        # Low Stock Warnings Badge
        if low_stock > 0:
            stock_color = "#d97706"
            stock_badge = (
                '<span style="font-size:9.5px; font-weight:700; color:#b45309; background:#fffbeb; '
                'border:1px solid #fde68a; padding:1px 7px; border-radius:9999px; white-space:nowrap;">≤ 15 UNITS</span>'
            )
            stock_border = "#f59e0b"
        else:
            stock_color = "#059669"
            stock_badge = (
                '<span style="font-size:9.5px; font-weight:700; color:#047857; background:#ecfdf5; '
                'border:1px solid #a7f3d0; padding:1px 7px; border-radius:9999px; white-space:nowrap;">HEALTHY</span>'
            )
            stock_border = "#10b981"

        st.html(f"""
        <div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 4px 0 8px 0;">
            <!-- Card 1: Total Sales Revenue -->
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #10b981; border-radius: 8px; padding: 7px 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); display: flex; align-items: center; justify-content: space-between; min-height: 52px;">
                <div style="min-width: 0;">
                    <div style="font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; line-height: 1.2;">Total Sales Revenue</div>
                    <div style="font-size: 17px; font-weight: 800; color: #0f172a; line-height: 1.2; margin-top: 2px;">${revenue:,.2f}</div>
                </div>
                <span style="font-size: 9.5px; font-weight: 700; color: #059669; background: #ecfdf5; border: 1px solid #a7f3d0; padding: 1px 7px; border-radius: 9999px; white-space: nowrap;">
                    LIVE GROSS
                </span>
            </div>

            <!-- Card 2: Low Stock Warnings -->
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid {stock_border}; border-radius: 8px; padding: 7px 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); display: flex; align-items: center; justify-content: space-between; min-height: 52px;">
                <div style="min-width: 0;">
                    <div style="font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; line-height: 1.2;">Low Stock Warnings</div>
                    <div style="font-size: 17px; font-weight: 800; color: {stock_color}; line-height: 1.2; margin-top: 2px;">{low_stock} Styles</div>
                </div>
                {stock_badge}
            </div>

            <!-- Card 3: Pipeline Activity -->
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 7px 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); display: flex; flex-direction: column; justify-content: center; min-height: 52px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 2px;">
                    <div style="font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; line-height: 1.2;">Pipeline Activity</div>
                    {badge_html}
                </div>
                <div style="font-size: 11.5px; font-weight: 600; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.2;" title="{safe_status}">
                    {safe_status}
                </div>
            </div>
        </div>
        """)
    except Exception as e:
        logger.error(f"Error rendering luxury KPI strip: {e}")


def render_animated_arena(
    event_type: str,
    current_stock: int,
    max_stock: int,
    product_name: str = "",
    unit_price: float = 0.0,
    event_text: str = ""
):
    """
    Renders a hardware-accelerated 60 FPS interactive luxury boutique arena.
    Features smooth vehicle deceleration, customer walk cycles, floating particle effects,
    and fluid mathematical dual sine-wave liquid physics for inventory levels.

    Args:
        event_type (str): Active simulation event ('Sale', 'Purchase', 'Blocked', 'Idle').
        current_stock (int): Current inventory on hand for the active product.
        max_stock (int): Maximum storage capacity limit for the product.
        product_name (str, optional): Name of the active product involved in the event.
        unit_price (float, optional): Price or transaction value of the event.
        event_text (str, optional): Summary narrative of the transaction.
    """
    try:
        fill_pct = min(100, max(0, int((current_stock / max_stock) * 100))) if max_stock > 0 else 0
        safe_product = (product_name or "Luxury Item").replace('"', '\\"').replace("'", "\\'")
        safe_text = (event_text or "Operations Pipeline Active").replace('"', '\\"').replace("'", "\\'")
        safe_type = event_type.capitalize() if event_type else "Idle"

        # Determine HUD Pill branding
        if safe_type == "Sale":
            pill_class = "pill-sale"
            pill_icon = "🛍️"
            pill_label = f"SALE: {product_name} (+${unit_price:.2f})" if product_name and unit_price > 0 else "SALE CONFIRMED"
        elif safe_type == "Purchase":
            pill_class = "pill-restock"
            pill_icon = "🚚"
            pill_label = f"RESTOCK: {product_name} INBOUND" if product_name else "RESTOCK INBOUND"
        elif safe_type == "Blocked":
            pill_class = "pill-blocked"
            pill_icon = "⚠️"
            pill_label = "CIRCUIT BLOCKED"
        else:
            pill_class = "pill-idle"
            pill_icon = "⚡"
            pill_label = "STREAM INGESTION ONLINE"

        arena_html = f"""<!DOCTYPE html>
<html lang="en" style="background:#0f172a; margin:0; padding:0; overflow:hidden;">
<head>
  <meta charset="utf-8">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{
      width: 100%;
      height: 100%;
      background: #0f172a;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      user-select: none;
    }}
    .arena-box {{
      position: relative;
      width: 100%;
      height: 220px;
      background: radial-gradient(circle at 50% 25%, #1e293b 0%, #0f172a 70%, #020617 100%);
      border: 1px solid #1e293b;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.06), 0 6px 20px -4px rgba(0, 0, 0, 0.35);
    }}
    canvas {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      display: block;
    }}
    .hud-bar {{
      position: absolute;
      top: 12px;
      left: 18px;
      right: 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      pointer-events: none;
      z-index: 10;
    }}
    .hud-left {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      color: #94a3b8;
    }}
    .live-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 8px #10b981;
      animation: pulse-dot 1.8s infinite ease-in-out;
    }}
    @keyframes pulse-dot {{
      0%, 100% {{ opacity: 1; transform: scale(1); }}
      50% {{ opacity: 0.35; transform: scale(0.85); }}
    }}
    .hud-pill {{
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      padding: 5px 14px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }}
    .pill-sale {{ border-color: rgba(16, 185, 129, 0.45); color: #34d399; }}
    .pill-restock {{ border-color: rgba(59, 130, 246, 0.45); color: #60a5fa; }}
    .pill-blocked {{ border-color: rgba(245, 158, 11, 0.45); color: #fbbf24; }}
    .pill-idle {{ border-color: rgba(148, 163, 184, 0.25); color: #94a3b8; }}
  </style>
</head>
<body>
  <div class="arena-box">
    <div class="hud-bar">
      <div class="hud-left">
        <span class="live-dot"></span>
        <span>Visual Operations Pipeline</span>
      </div>
      <div class="hud-pill {pill_class}">
        <span>{pill_icon}</span>
        <span>{pill_label}</span>
      </div>
    </div>
    <canvas id="arenaCanvas"></canvas>
  </div>

  <script>
    (function() {{
      const canvas = document.getElementById('arenaCanvas');
      const ctx = canvas.getContext('2d');
      let W = 0, H = 0, DPR = window.devicePixelRatio || 1;

      function resize() {{
        const rect = canvas.getBoundingClientRect();
        W = rect.width;
        H = rect.height;
        canvas.width = Math.round(W * DPR);
        canvas.height = Math.round(H * DPR);
        ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
      }}
      window.addEventListener('resize', resize);
      resize();

      // State restoration across iframe re-renders to prevent visual jump/flash
      const STORAGE_KEY = 'luxury_arena_state_v2';
      let saved = {{}};
      try {{
        saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '{{}}');
      }} catch(e) {{}}

      const targetStockFill = {fill_pct};
      const curStock = {current_stock};
      const maxStock = {max_stock};
      const eventType = "{safe_type}";
      const unitPrice = {unit_price};
      const productName = "{safe_product}";

      let stockFill = (typeof saved.stockFill === 'number') ? saved.stockFill : targetStockFill;
      let wavePhase = (typeof saved.wavePhase === 'number') ? saved.wavePhase : 0;
      let waveSplash = (typeof saved.waveSplash === 'number') ? saved.waveSplash : 0;
      let particles = Array.isArray(saved.particles) ? saved.particles : [];

      // Truck animation state
      let truck = saved.truck || {{ x: -160, targetX: -160, speed: 0, state: 'idle', cargoCount: 3, wheelAngle: 0 }};
      // Shopper animation state
      let shopper = saved.shopper || {{ x: 900, targetX: 900, speed: 0, state: 'idle', walkCycle: 0, hasBag: false, cheerTimer: 0 }};

      // Handle new incoming event trigger
      const lastEventId = saved.lastEventId || "";
      const currentEventId = eventType + "_" + curStock + "_" + Date.now().toString().slice(-4);

      if (eventType === "Purchase") {{
        // Reset truck for delivery run
        truck.x = -160;
        truck.targetX = 145; // dock at depot
        truck.state = 'inbound';
        truck.cargoCount = 3;
        waveSplash = 0.8;
      }} else if (eventType === "Sale") {{
        // Reset shopper to enter boutique
        shopper.x = Math.max(W - 20, 680);
        shopper.targetX = Math.max(W - 130, 560); // walk to boutique entrance
        shopper.state = 'entering';
        shopper.hasBag = false;
        shopper.cheerTimer = 0;
      }}

      // Background stars / luxury dust motes
      const stars = [];
      for (let i = 0; i < 28; i++) {{
        stars.push({{
          x: Math.random(),
          y: Math.random() * 0.7,
          radius: Math.random() * 1.2 + 0.4,
          alpha: Math.random() * 0.6 + 0.2,
          speed: Math.random() * 0.0008 + 0.0003
        }});
      }}

      let lastTime = performance.now();

      function frame(now) {{
        const dt = Math.min((now - lastTime) / 1000, 0.1);
        lastTime = now;

        // 1. Clear Frame
        ctx.clearRect(0, 0, W, H);

        const groundY = H - 55;
        const depotX = 150;
        const boutiqueX = Math.max(W - 165, 540);

        // 2. Render Ambient Atmosphere & Grid
        stars.forEach(s => {{
          s.x = (s.x + s.speed) % 1;
          ctx.beginPath();
          ctx.arc(s.x * W, s.y * H, s.radius, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(255, 255, 255, ${{s.alpha}})`;
          ctx.fill();
        }});

        // Runway line with ground depth
        ctx.beginPath();
        ctx.moveTo(10, groundY);
        ctx.lineTo(W - 10, groundY);
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#334155';
        ctx.stroke();

        // Subtle glowing road dashes
        ctx.setLineDash([12, 16]);
        ctx.beginPath();
        ctx.moveTo(140, groundY + 14);
        ctx.lineTo(W - 40, groundY + 14);
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = 'rgba(51, 65, 85, 0.6)';
        ctx.stroke();
        ctx.setLineDash([]);

        // 3. Render Stock Liquid Vat (Left Depot)
        const tankX = 72;
        const tankY = groundY - 58;
        const tankR = 44;

        // Smoothly interpolate stock fill
        stockFill += (targetStockFill - stockFill) * 0.08;
        wavePhase += dt * 3.2;
        waveSplash = Math.max(0, waveSplash - dt * 0.6);

        // Liquid clipping region
        ctx.save();
        ctx.beginPath();
        ctx.arc(tankX, tankY, tankR, 0, Math.PI * 2);
        ctx.clip();

        // Dark tank background
        ctx.fillStyle = '#090d16';
        ctx.fill();

        // Dual Sine-Wave Liquid Simulation
        const waterY = tankY + tankR - (stockFill / 100) * (2 * tankR);

        // Back wave
        ctx.beginPath();
        ctx.moveTo(tankX - tankR, tankY + tankR);
        for (let x = tankX - tankR; x <= tankX + tankR; x += 2) {{
          const wy = waterY + Math.sin((x - tankX) * 0.07 + wavePhase) * (3.5 + waveSplash * 6);
          ctx.lineTo(x, wy);
        }}
        ctx.lineTo(tankX + tankR, tankY + tankR);
        ctx.closePath();
        ctx.fillStyle = 'rgba(30, 58, 138, 0.45)';
        ctx.fill();

        // Front wave with rich gradient
        ctx.beginPath();
        ctx.moveTo(tankX - tankR, tankY + tankR);
        for (let x = tankX - tankR; x <= tankX + tankR; x += 2) {{
          const wy = waterY + Math.sin((x - tankX) * 0.08 + wavePhase * 1.35 + 1.2) * (2.8 + waveSplash * 5);
          ctx.lineTo(x, wy);
        }}
        ctx.lineTo(tankX + tankR, tankY + tankR);
        ctx.closePath();
        const liquidGrad = ctx.createLinearGradient(tankX, waterY - 10, tankX, tankY + tankR);
        liquidGrad.addColorStop(0, '#06b6d4');
        liquidGrad.addColorStop(0.45, '#2563eb');
        liquidGrad.addColorStop(1, '#1e1b4b');
        ctx.fillStyle = liquidGrad;
        ctx.fill();

        ctx.restore();

        // Outer Metallic Ring Bezel
        ctx.beginPath();
        ctx.arc(tankX, tankY, tankR, 0, Math.PI * 2);
        ctx.lineWidth = 4;
        ctx.strokeStyle = '#334155';
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(tankX, tankY, tankR - 1, 0, Math.PI * 2);
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = stockFill <= 15 ? '#ef4444' : (stockFill <= 35 ? '#f59e0b' : '#38bdf8');
        ctx.stroke();

        // Tank Status Label
        ctx.font = 'bold 12px -apple-system, BlinkMacSystemFont, sans-serif';
        ctx.fillStyle = '#f8fafc';
        ctx.textAlign = 'center';
        ctx.fillText(curStock + ' / ' + maxStock + ' Qty', tankX, groundY + 22);

        ctx.font = '9px monospace';
        ctx.fillStyle = '#64748b';
        ctx.fillText('STOCK LEVEL ' + Math.round(stockFill) + '%', tankX, groundY + 36);

        // 4. Render Boutique Architecture (Right Storefront)
        const bW = 125, bH = 100;
        const bY = groundY - bH;

        // Boutique main structure
        ctx.fillStyle = '#0f172a';
        ctx.strokeStyle = '#1e293b';
        ctx.lineWidth = 2;
        ctx.fillRect(boutiqueX, bY, bW, bH);
        ctx.strokeRect(boutiqueX, bY, bW, bH);

        // Warm glowing boutique display window
        const winX = boutiqueX + 14, winY = bY + 32, winW = 46, winH = 48;
        const winGrad = ctx.createLinearGradient(winX, winY, winX, winY + winH);
        winGrad.addColorStop(0, 'rgba(251, 191, 36, 0.45)');
        winGrad.addColorStop(1, 'rgba(217, 119, 6, 0.15)');
        ctx.fillStyle = winGrad;
        ctx.fillRect(winX, winY, winW, winH);
        ctx.strokeStyle = '#d97706';
        ctx.lineWidth = 1.5;
        ctx.strokeRect(winX, winY, winW, winH);

        // Window silhouette mannequin
        ctx.fillStyle = '#1e293b';
        ctx.beginPath();
        ctx.arc(winX + winW / 2, winY + 14, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.moveTo(winX + winW / 2 - 8, winY + winH - 4);
        ctx.lineTo(winX + winW / 2 + 8, winY + winH - 4);
        ctx.lineTo(winX + winW / 2 + 4, winY + 20);
        ctx.lineTo(winX + winW / 2 - 4, winY + 20);
        ctx.closePath();
        ctx.fill();

        // Boutique Entrance Doorway
        const doorX = boutiqueX + 72, doorY = bY + 38, doorW = 38, doorH = 62;
        ctx.fillStyle = '#020617';
        ctx.fillRect(doorX, doorY, doorW, doorH);
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 1;
        ctx.strokeRect(doorX, doorY, doorW, doorH);

        // Door ambient light pool
        const doorGlow = ctx.createRadialGradient(doorX + doorW/2, doorY + doorH - 4, 2, doorX + doorW/2, doorY + doorH - 4, 26);
        doorGlow.addColorStop(0, 'rgba(245, 158, 11, 0.4)');
        doorGlow.addColorStop(1, 'rgba(245, 158, 11, 0)');
        ctx.fillStyle = doorGlow;
        ctx.fillRect(doorX - 10, doorY + doorH - 12, doorW + 20, 16);

        // Striped luxury awning
        const awnY = bY + 12;
        ctx.fillStyle = '#1e1b4b';
        ctx.fillRect(boutiqueX - 4, awnY, bW + 8, 16);
        for (let i = 0; i < 7; i++) {{
          if (i % 2 === 0) {{
            ctx.fillStyle = '#d97706';
            ctx.fillRect(boutiqueX - 4 + i * ((bW + 8) / 7), awnY, (bW + 8) / 7, 16);
          }}
        }}

        // Boutique Signboard
        ctx.fillStyle = '#0b0f19';
        ctx.fillRect(boutiqueX + 10, bY - 4, bW - 20, 14);
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 1;
        ctx.strokeRect(boutiqueX + 10, bY - 4, bW - 20, 14);
        ctx.font = 'bold 8px -apple-system, BlinkMacSystemFont, sans-serif';
        ctx.fillStyle = '#fde68a';
        ctx.textAlign = 'center';
        ctx.fillText('HAUTE BOUTIQUE', boutiqueX + bW / 2, bY + 6);

        // 5. TRUCK DYNAMICS (Restock Logistics - Smooth & Steady Screen Pacing)
        if (truck.state === 'inbound') {{
          truck.x += (truck.targetX - truck.x) * 0.024;
          truck.wheelAngle += 0.12;
          if (Math.abs(truck.targetX - truck.x) < 4) {{
            truck.state = 'docked';
            truck.dockTimer = 0;
          }}
        }} else if (truck.state === 'docked') {{
          truck.dockTimer = (truck.dockTimer || 0) + dt;
          // Levitate cargo crates into reservoir with deliberate pacing
          if (truck.cargoCount > 0 && truck.dockTimer > 0.65) {{
            truck.cargoCount--;
            truck.dockTimer = 0;
            particles.push({{
              type: 'crate',
              x: truck.x + 35,
              y: groundY - 24,
              startX: truck.x + 35,
              startY: groundY - 24,
              targetX: tankX + (Math.random() - 0.5) * 20,
              targetY: tankY + 10,
              progress: 0,
              speed: 0.85
            }});
          }}
          if (truck.cargoCount === 0 && truck.dockTimer > 1.3) {{
            truck.state = 'outbound';
            truck.targetX = W + 160;
          }}
        }} else if (truck.state === 'outbound') {{
          truck.x += (truck.targetX - truck.x) * 0.02 + 1.1;
          truck.wheelAngle += 0.16;
          if (truck.x > W + 120) {{
            truck.state = 'idle';
          }}
        }}

        // Draw Truck if in view
        if (truck.x > -180 && truck.x < W + 160) {{
          const tx = truck.x, ty = groundY - 36;
          // Soft headlight beam
          const beamGrad = ctx.createRadialGradient(tx + 58, ty + 18, 2, tx + 140, ty + 18, 90);
          beamGrad.addColorStop(0, 'rgba(56, 189, 248, 0.45)');
          beamGrad.addColorStop(1, 'rgba(56, 189, 248, 0)');
          ctx.fillStyle = beamGrad;
          ctx.beginPath();
          ctx.moveTo(tx + 56, ty + 12);
          ctx.lineTo(tx + 140, ty - 8);
          ctx.lineTo(tx + 140, ty + 36);
          ctx.lineTo(tx + 56, ty + 24);
          ctx.closePath();
          ctx.fill();

          // Truck Cargo Container
          ctx.fillStyle = '#1d4ed8';
          ctx.fillRect(tx, ty, 42, 26);
          ctx.strokeStyle = '#60a5fa';
          ctx.lineWidth = 1;
          ctx.strokeRect(tx, ty, 42, 26);

          // Logistics text on container
          ctx.font = 'bold 8px monospace';
          ctx.fillStyle = '#ffffff';
          ctx.textAlign = 'center';
          ctx.fillText('CARGO', tx + 21, ty + 16);

          // Truck Cabin
          ctx.fillStyle = '#2563eb';
          ctx.beginPath();
          ctx.moveTo(tx + 42, ty + 26);
          ctx.lineTo(tx + 42, ty + 6);
          ctx.lineTo(tx + 52, ty + 6);
          ctx.lineTo(tx + 58, ty + 16);
          ctx.lineTo(tx + 58, ty + 26);
          ctx.closePath();
          ctx.fill();

          // Cabin Windshield
          ctx.fillStyle = '#38bdf8';
          ctx.beginPath();
          ctx.moveTo(tx + 45, ty + 8);
          ctx.lineTo(tx + 51, ty + 8);
          ctx.lineTo(tx + 55, ty + 15);
          ctx.lineTo(tx + 45, ty + 15);
          ctx.closePath();
          ctx.fill();

          // Rotating Wheels
          [tx + 12, tx + 48].forEach(wx => {{
            ctx.beginPath();
            ctx.arc(wx, groundY - 4, 6, 0, Math.PI * 2);
            ctx.fillStyle = '#0f172a';
            ctx.fill();
            ctx.strokeStyle = '#94a3b8';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Wheel spoke rotation
            ctx.beginPath();
            ctx.moveTo(wx - Math.cos(truck.wheelAngle) * 4, groundY - 4 - Math.sin(truck.wheelAngle) * 4);
            ctx.lineTo(wx + Math.cos(truck.wheelAngle) * 4, groundY - 4 + Math.sin(truck.wheelAngle) * 4);
            ctx.lineWidth = 1.5;
            ctx.strokeStyle = '#cbd5e1';
            ctx.stroke();
          }});
        }}

        // 6. SHOPPER DYNAMICS (Customer Purchase - Elegant Luxury Walk)
        if (shopper.state === 'entering') {{
          shopper.x += (shopper.targetX - shopper.x) * 0.025;
          shopper.walkCycle += 0.12;
          if (Math.abs(shopper.targetX - shopper.x) < 4) {{
            shopper.state = 'transacting';
            shopper.cheerTimer = 0;
          }}
        }} else if (shopper.state === 'transacting') {{
          shopper.cheerTimer = (shopper.cheerTimer || 0) + dt;
          // Spawn golden sparkles and revenue badge with longer visibility
          if (shopper.cheerTimer < 0.1) {{
            for (let i = 0; i < 16; i++) {{
              particles.push({{
                type: 'gold',
                x: boutiqueX + 88,
                y: groundY - 50,
                vx: (Math.random() - 0.5) * 2.6,
                vy: -Math.random() * 3.5 - 2.0,
                life: 1.5,
                decay: 0.012 + Math.random() * 0.012,
                char: Math.random() > 0.5 ? '✨' : '🪙'
              }});
            }}
            particles.push({{
              type: 'text',
              x: boutiqueX + 88,
              y: groundY - 60,
              text: unitPrice > 0 ? '+$' + unitPrice.toFixed(2) : '+REVENUE',
              life: 1.8,
              vy: -0.6
            }});
          }}
          if (shopper.cheerTimer > 1.5) {{
            shopper.hasBag = true;
            shopper.state = 'leaving';
            shopper.targetX = -60;
          }}
        }} else if (shopper.state === 'leaving') {{
          shopper.x += (shopper.targetX - shopper.x) * 0.02 - 0.85;
          shopper.walkCycle += 0.13;
          if (shopper.x < -40) {{
            shopper.state = 'idle';
          }}
        }}

        // Draw Shopper if active
        if (shopper.x > -40 && shopper.x < W + 40) {{
          const sx = shopper.x;
          const bobY = Math.abs(Math.sin(shopper.walkCycle)) * 4;
          const sy = groundY - 42 - bobY;

          // Head
          ctx.beginPath();
          ctx.arc(sx, sy, 5, 0, Math.PI * 2);
          ctx.fillStyle = '#f8fafc';
          ctx.fill();

          // Chic coat / outfit
          ctx.fillStyle = '#059669';
          ctx.beginPath();
          ctx.moveTo(sx - 5, sy + 7);
          ctx.lineTo(sx + 5, sy + 7);
          ctx.lineTo(sx + 7, sy + 24);
          ctx.lineTo(sx - 7, sy + 24);
          ctx.closePath();
          ctx.fill();

          // Animated legs swing
          const legSwing = Math.sin(shopper.walkCycle) * 6;
          ctx.lineWidth = 2;
          ctx.strokeStyle = '#0f172a';
          ctx.beginPath();
          ctx.moveTo(sx - 2, sy + 24);
          ctx.lineTo(sx - 2 + legSwing, groundY);
          ctx.stroke();

          ctx.beginPath();
          ctx.moveTo(sx + 2, sy + 24);
          ctx.lineTo(sx + 2 - legSwing, groundY);
          ctx.stroke();

          // Shopping Bag if completed transaction
          if (shopper.hasBag) {{
            ctx.font = '14px sans-serif';
            ctx.fillText('🛍️', sx - 16, sy + 18);
          }}
        }}

        // 7. PARTICLES ENGINE
        for (let i = particles.length - 1; i >= 0; i--) {{
          const p = particles[i];
          if (p.type === 'crate') {{
            p.progress += dt * p.speed;
            const t = Math.min(p.progress, 1);
            // Parabolic arc into the liquid tank
            const curX = p.startX + (p.targetX - p.startX) * t;
            const curY = p.startY + (p.targetY - p.startY) * t - Math.sin(t * Math.PI) * 45;
            ctx.font = '16px sans-serif';
            ctx.fillText('📦', curX, curY);

            if (t >= 1) {{
              waveSplash = 1.0;
              particles.splice(i, 1);
            }}
          }} else if (p.type === 'gold') {{
            p.x += p.vx;
            p.y += p.vy;
            p.vy += 0.12; // gravity
            p.life -= p.decay;
            ctx.font = '12px sans-serif';
            ctx.fillStyle = `rgba(251, 191, 36, ${{Math.max(0, p.life)}})`;
            ctx.fillText(p.char, p.x, p.y);
            if (p.life <= 0) particles.splice(i, 1);
          }} else if (p.type === 'text') {{
            p.y += p.vy;
            p.life -= dt * 0.9;
            ctx.font = 'bold 12px -apple-system, BlinkMacSystemFont, sans-serif';
            ctx.fillStyle = `rgba(52, 211, 153, ${{Math.max(0, p.life)}})`;
            ctx.textAlign = 'center';
            ctx.fillText(p.text, p.x, p.y);
            if (p.life <= 0) particles.splice(i, 1);
          }}
        }}

        // 8. Save state continuously to sessionStorage
        try {{
          sessionStorage.setItem(STORAGE_KEY, JSON.stringify({{
            stockFill: stockFill,
            wavePhase: wavePhase,
            waveSplash: waveSplash,
            truck: truck,
            shopper: shopper,
            lastEventId: currentEventId
          }}));
        }} catch(e) {{}}

        requestAnimationFrame(frame);
      }}

      requestAnimationFrame(frame);
    }})();
  </script>
</body>
</html>
"""
        # Render clean HTML iframe with compact 228px container height
        if hasattr(st, "iframe"):
            st.iframe(arena_html, height=228)
        else:
            components.html(arena_html, height=228)
    except Exception as e:
        logger.error(f"Error rendering animated arena: {e}")

