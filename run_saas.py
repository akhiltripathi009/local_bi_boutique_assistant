#!/usr/bin/env python3
"""
Mishika Fashion Luxury Boutique - Commercial SaaS Web Launcher
Launches the FastAPI backend and Atelier single page application on http://localhost:8000.
"""

import os
import sys
import time
import threading
import webbrowser
import logging
import uvicorn

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import DB_PATH
from src.data.seed_db import initialize_database
from src.ai.ollama_client import LocalOllamaBoutiqueAnalyst

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mishika_saas_launcher")

BANNER = r"""
================================================================================
    __  ___ _      __     _  __            ______           __    _             
   /  |/  /(_)____/ /_   (_)/ /______ _   / ____/___ ______/ /_  (_)____  ____  
  / /|_/ // // ___/ __ \ / // //_/ __ `/  / /_  / __ `/ ___/ __ \/ // __ \/ __ \ 
 / /  / // /(__  ) / / // // ,< / /_/ /  / __/ / /_/ (__  ) / / / // /_/ / / / / 
/_/  /_//_//____/_/ /_//_//_/|_|\__,_/  /_/    \__,_/____/_/ /_/_/ \____/_/ /_/  
                                                                                 
              ★ LUXURY BOUTIQUE BI & SHIVI DEEP AGENT SUITE ★                   
                     Commercial Single-Tenant Edition                            
================================================================================
"""

def open_browser():
    time.sleep(1.8)
    url = "http://localhost:8000"
    logger.info(f"Opening Atelier Commercial Web Application: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        logger.warning(f"Could not auto-open browser: {e}")

def main():
    print(BANNER)
    
    # 1. Verify / initialize Database
    if not os.path.exists(DB_PATH):
        logger.info(f"Database not found at '{DB_PATH}'. Initializing fresh schema...")
        initialize_database()
        logger.info("Database initialized successfully.")
    else:
        logger.info(f"Database verified at: {DB_PATH}")

    # 2. Check AI Engine connectivity (Google AI Studio Gemini & Local Ollama)
    logger.info("Initializing Boutique Intelligence AI engine...")
    try:
        from src.ai import GoogleGeminiBoutiqueAnalyst, LocalOllamaBoutiqueAnalyst
        gemini_analyst = GoogleGeminiBoutiqueAnalyst()
        if gemini_analyst.is_configured():
            logger.info("✨ Google AI Studio (Gemini) Online! Primary Cloud Intelligence active.")
        else:
            logger.info("Checking Local Ollama daemon connectivity...")
            models = LocalOllamaBoutiqueAnalyst().get_available_models()
            if models:
                logger.info(f"🦙 Local Ollama Online! Available models: {', '.join(models)}")
            else:
                logger.info("Local Ollama not detected. Set GEMINI_API_KEY to activate Google AI Studio.")
    except Exception as e:
        logger.debug(f"AI engine check skipped: {e}")

    # 3. Dynamic cloud port resolution (Google Cloud Run / Render inject $PORT)
    port = int(os.getenv("PORT", 8000))
    is_cloud = os.getenv("PORT") is not None

    if not is_cloud:
        threading.Thread(target=open_browser, daemon=True).start()

    logger.info(f"Starting Mishika Atelier Commercial SaaS Server on port {port}...")
    print(f"\n   Access URL: http://localhost:{port}")
    print(f"   API Docs:   http://localhost:{port}/docs\n")

    uvicorn.run(
        "src.server.app:app",
        host="0.0.0.0",
        port=port,
        reload=not is_cloud,
        reload_dirs=["src", "web"] if not is_cloud else None,
        log_level="info"
    )

if __name__ == "__main__":
    main()
