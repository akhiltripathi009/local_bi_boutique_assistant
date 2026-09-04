"""
animation_assets.py
Manages Lottie animation assets and network fetching logic.
"""
import streamlit as st
import requests
import logging
from logger_config import setup_logging

logger = setup_logging("animation_assets")

def load_lottie_url(url: str):
    """
    Fetches Lottie JSON animation files from a remote URL.
    
    Args:
        url (str): The secure CDN URL for the Lottie file.
        
    Returns:
        dict: The loaded JSON animation data, or None if the request fails.
    """
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        logger.warning(f"Failed to fetch Lottie asset from {url}: HTTP {response.status_code}")
        return None
    except Exception as e:
        logger.error(f"Error loading Lottie URL {url}: {e}")
        return None

@st.cache_resource
def get_local_animation_pack():
    """
    Retrieves and caches a collection of retail-specific animations.
    Uses memory-based caching to prevent redundant network requests.
    
    Returns:
        dict: A dictionary of animation data mapped by event type.
    """
    try:
        logger.info("Loading Lottie animation pack...")
        pack = {
            "truck": load_lottie_url("https://lottie.host"),    # Logistics Restock Truck placeholder
            "shopper": load_lottie_url("https://lottie.host"),  # Retail Customer Buyer placeholder
            "idle": load_lottie_url("https://lottie.host")     # Ambient System Radar Pulse placeholder
        }
        logger.info("Lottie animation pack loaded.")
        return pack
    except Exception as e:
        logger.error(f"Error initializing animation pack: {e}")
        return {"truck": None, "shopper": None, "idle": None}
