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

    # 2. Check Ollama Local AI connection
    logger.info("Checking Ollama local AI server connectivity...")
    try:
        models = LocalOllamaBoutiqueAnalyst().get_available_models()
        if models:
            logger.info(f"Ollama AI Online! Available models: {', '.join(models)}")
        else:
            logger.warning("Ollama not currently detected. Boutique BI and rule-based systems will run in offline mode.")
    except Exception as e:
        logger.warning(f"Ollama check skipped: {e}")

    # 3. Schedule auto-opening browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    logger.info("Starting Mishika Atelier Commercial SaaS Server on http://localhost:8000 ...")
    print("\n   Access URL: http://localhost:8000")
    print("   API Docs:   http://localhost:8000/docs")
    print("   Press CTRL+C to safely terminate the server.\n")

    uvicorn.run(
        "src.server.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src", "web"],
        log_level="info"
    )

if __name__ == "__main__":
    main()
