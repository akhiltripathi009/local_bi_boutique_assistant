import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse

from src.server.routes import (
    dashboard,
    inventory,
    crm,
    campaigns,
    agent,
    copilot,
    sandbox,
    reports,
    live_operations
)

# Initialize FastAPI Application
app = FastAPI(
    title="Mishika Fashion Luxury Boutique - Enterprise BI & Deep Agent SaaS",
    description="Commercial-grade autonomous retail intelligence and store operations API.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for cross-origin web clients & mobile frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Modular API Routers
app.include_router(dashboard.router)
app.include_router(live_operations.router)
app.include_router(inventory.router)
app.include_router(crm.router)
app.include_router(campaigns.router)
app.include_router(agent.router)
app.include_router(copilot.router)
app.include_router(sandbox.router)
app.include_router(reports.router)

@app.get("/api/health")
def health_check():
    """System status check verifying database and local Ollama connectivity."""
    db_ok = False
    ollama_ok = False
    ollama_models = []

    # Verify SQLite DB
    try:
        from src.data.db_manager import DatabaseManager
        db = DatabaseManager()
        db.get_current_stock_on_hand()
        db_ok = True
    except Exception:
        db_ok = False

    # Verify Local Ollama
    try:
        from src.ai.ollama_client import LocalOllamaBoutiqueAnalyst
        analyst = LocalOllamaBoutiqueAnalyst()
        ollama_models = analyst.get_available_models()
        ollama_ok = len(ollama_models) > 0
    except Exception:
        ollama_ok = False

    return {
        "status": "healthy" if (db_ok and ollama_ok) else "degraded",
        "service": "Mishika Fashion Boutique Enterprise SaaS",
        "version": "2.0.0",
        "database_connected": db_ok,
        "ollama_active": ollama_ok,
        "discovered_models": ollama_models
    }

# Resolve absolute paths to web frontend directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
web_dir = BASE_DIR / "web"
css_dir = web_dir / "css"
js_dir = web_dir / "js"

if not web_dir.exists():
    web_dir.mkdir(parents=True, exist_ok=True)

# Mount /css, /js, and /static routes directly for full browser compatibility
if css_dir.exists():
    app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
if js_dir.exists():
    app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

@app.get("/")
def serve_spa():
    """Serves the main commercial luxury web application."""
    index_file = web_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Mishika Fashion Boutique API running. Frontend web/index.html is initializing."}
