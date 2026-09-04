import logging
import sys

def setup_logging(name: str = "boutique_assistant"):
    """
    Sets up a consistent logging configuration across the application.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Stream handler for console output
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        # File handler for permanent log storage
        file_handler = logging.FileHandler("app.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger
