"""
src/core/logger.py
==================
Unicode-safe logging infrastructure supporting Windows console environments (cp1252/utf-8)
and rotated/permanent log writing to logs/app.log.
"""

import logging
import sys
from pathlib import Path
from src.core.config import LOG_FILE

def setup_logging(name: str = "boutique_assistant") -> logging.Logger:
    """
    Sets up a consistent, unicode-safe logging configuration across the application.
    Handles Windows console cp1252 charmap encoding safely.
    
    Args:
        name (str): Identifier for the logger instance.
        
    Returns:
        logging.Logger: Configured logger with console and file handlers.
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Configure stdout for utf-8 if supported on Windows
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Stream handler for console output
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        # File handler for permanent log storage
        try:
            file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            # Fallback to local app.log if directory permission issue
            fallback_handler = logging.FileHandler("app.log", encoding="utf-8")
            fallback_handler.setFormatter(formatter)
            logger.addHandler(fallback_handler)
        
    return logger
