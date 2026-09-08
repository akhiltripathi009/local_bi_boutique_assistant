"""
src/core/config.py
==================
Centralized system configuration, filesystem paths, and environment settings.
Provides deterministic resolution of local storage, logs, and database paths.
"""

from pathlib import Path
import os

# Root base directory (local_bi_boutique_assistant/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Storage directories
STORAGE_DIR = BASE_DIR / "storage"
DB_DIR = STORAGE_DIR / "db"
EXPORTS_DIR = STORAGE_DIR / "exports"
LOGS_DIR = BASE_DIR / "logs"

# Ensure runtime directories exist
for directory in [STORAGE_DIR, DB_DIR, EXPORTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database path resolution: favors storage/db/boutique_bi.db, falls back to root if present
_primary_db = DB_DIR / "boutique_bi.db"
_root_db = BASE_DIR / "boutique_bi.db"

if _primary_db.exists():
    DB_PATH = str(_primary_db)
elif _root_db.exists():
    DB_PATH = str(_root_db)
else:
    DB_PATH = str(_primary_db)

# Log file path
LOG_FILE = str(LOGS_DIR / "app.log")

# Application domain constants
APP_TITLE = "Local BI Boutique Assistant"
APP_VERSION = "2.5.0"
DEFAULT_CURRENCY = "$"
CRITICAL_STOCK_THRESHOLD = 15

# Ollama Local LLM defaults
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
FALLBACK_OLLAMA_MODEL = "mistral:latest"
