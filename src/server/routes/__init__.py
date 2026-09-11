"""
src/server/routes/__init__.py
=============================
FastAPI Route Controllers Package for Local BI Boutique Assistant.

Why Required:
- Consolidates and exports all API route controllers powering the Atelier Web SPA,
  AI Copilot Studio, and Shivi Deep Agent.
"""

from src.server.routes.dashboard import router as dashboard_router
from src.server.routes.live_operations import router as live_ops_router
from src.server.routes.inventory import router as inventory_router
from src.server.routes.campaigns import router as campaigns_router
from src.server.routes.crm import router as crm_router
from src.server.routes.copilot import router as copilot_router
from src.server.routes.sandbox import router as sandbox_router
from src.server.routes.reports import router as reports_router
from src.server.routes.agent import router as agent_router

__all__ = [
    "dashboard_router",
    "live_ops_router",
    "inventory_router",
    "campaigns_router",
    "crm_router",
    "copilot_router",
    "sandbox_router",
    "reports_router",
    "agent_router",
]
