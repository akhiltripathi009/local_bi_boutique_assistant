"""
catalog_config.py
Centralized product catalog and initial inventory generation logic for the boutique.
"""
import random
import logging
try:
    from src.core.logger import setup_logging
except ImportError:
    from logger_config import setup_logging

logger = setup_logging("catalog_config")

# Complete 20-item production catalog map
# Defines core attributes: name, cost, retail price, theme color, and product category.
CATALOG = {
    "P001": {"name": "Linen Wrap Dress", "cost": 35.0, "price": 95.0, "color": "#2ecc71", "category": "Dresses"},
    "P002": {"name": "Silk Slip Skirt", "cost": 25.0, "price": 75.0, "color": "#3498db", "category": "Bottoms"},
    "P003": {"name": "Ribbed Knit Tank", "cost": 8.0, "price": 28.0, "color": "#9b59b6", "category": "Tops"},
    "P004": {"name": "Oversized Denim Jacket", "cost": 40.0, "price": 120.0, "color": "#f1c40f", "category": "Outerwear"},
    "P005": {"name": "Cashmere Crewneck Sweater", "cost": 45.0, "price": 140.0, "color": "#e67e22", "category": "Knitwear"},
    "P006": {"name": "High-Waisted Wide Leg Trouser", "cost": 22.0, "price": 68.0, "color": "#e74c3c", "category": "Bottoms"},
    "P007": {"name": "Classic White Poplin Buttondown", "cost": 15.0, "price": 48.0, "color": "#1abc9c", "category": "Tops"},
    "P008": {"name": "Vegan Leather Trench Coat", "cost": 65.0, "price": 195.0, "color": "#34495e", "category": "Outerwear"},
    "P009": {"name": "Boho Floral Maxi Dress", "cost": 38.0, "price": 110.0, "color": "#d35400", "category": "Dresses"},
    "P010": {"name": "Tailored Double-Breasted Blazer", "cost": 50.0, "price": 150.0, "color": "#7f8c8d", "category": "Outerwear"},
    "P011": {"name": "Cropped Cable Knit Vest", "cost": 12.0, "price": 38.0, "color": "#16a085", "category": "Knitwear"},
    "P012": {"name": "Satin Pleated Midi Skirt", "cost": 20.0, "price": 62.0, "color": "#27ae60", "category": "Bottoms"},
    "P013": {"name": "Chambray Utility Shirt", "cost": 14.0, "price": 45.0, "color": "#2980b9", "category": "Tops"},
    "P014": {"name": "Merino Wool Cardigan", "cost": 30.0, "price": 98.0, "color": "#8e44ad", "category": "Knitwear"},
    "P015": {"name": "Asymmetrical Knit Midi Dress", "cost": 32.0, "price": 88.0, "color": "#c0392b", "category": "Dresses"},
    # 🚨 OUT OF STOCK ITEMS (Simulated Availability Outages)
    "P016": {"name": "Distressed Straight Leg Denim", "cost": 24.0, "price": 78.0, "color": "#bdc3c7", "category": "Bottoms"},
    "P017": {"name": "Lace-Trim Cami Cami Tank", "cost": 6.0, "price": 22.0, "color": "#95a5a6", "category": "Tops"},
    "P018": {"name": "Suede Moto Jacket", "cost": 75.0, "price": 225.0, "color": "#f39c12", "category": "Outerwear"},
    "P019": {"name": "Smocked Waist Tiered Sun Dress", "cost": 28.0, "price": 85.0, "color": "#f1c40f", "category": "Dresses"},
    "P020": {"name": "Heavyweight Cotton Hoodie", "cost": 18.0, "price": 55.0, "color": "#16a085", "category": "Tops"}
}

def generate_initial_inventory() -> dict:
    """
    Initializes realistic initial inventory distribution across the 20 boutique styles.
    
    Working:
    - Seeds 15 core styles with healthy, randomized inventory buffers (35-60 units).
    - Deliberately seeds 5 designated styles (P016-P020) at 0 stock.
    
    Why Required:
    - Provides immediate real-world operational realism for the executive BI dashboard,
      simulating urgent procurement reorder scenarios, stockout alerts, and back-in-stock
      customer notification workflows out-of-the-box.
    
    Returns:
        dict: Mapping of product ID (e.g., 'P001') to integer stock on hand.
    """
    try:
        inventory_state = {}
        for pid in CATALOG:
            if pid.startswith("P") and pid[1:].isdigit() and int(pid[1:]) >= 16:
                inventory_state[pid] = 0
            else:
                inventory_state[pid] = random.randint(35, 60)
        logger.info("Initial inventory state generated successfully.")
        return inventory_state
    except Exception as e:
        logger.error(f"Error generating initial inventory: {e}")
        return {pid: 0 for pid in CATALOG}


def register_product(
    pid: str,
    name: str,
    cost: float,
    price: float,
    color: str = "#2c3e50",
    category: str = "Apparel"
) -> dict:
    """
    Dynamically registers a newly created style into the in-memory product catalog.
    
    Working:
    - Validates numeric pricing and builds the canonical dictionary representation.
    - Updates the global CATALOG map so new styles are immediately recognized by
      the simulation engine, copilot context, and analytical models without server restarts.
    
    Why Required:
    - Allows boutique merchants to launch custom capsule collections and seasonal styles
      directly through the web portal or Shivi Deep Agent procurement routines.
    
    Args:
        pid (str): Unique alphanumeric SKU / identifier (e.g. 'P021').
        name (str): Luxury product title.
        cost (float): Wholesale procurement acquisition cost basis.
        price (float): Recommended retail price (RRP).
        color (str): Hex color code for UI visualization chips.
        category (str): Merchandise classification (e.g. 'Dresses', 'Knitwear').
        
    Returns:
        dict: The newly created product specification record.
    """
    product_entry = {
        "name": name,
        "cost": float(cost),
        "price": float(price),
        "color": color,
        "category": category
    }
    CATALOG[pid] = product_entry
    logger.info(f"Registered dynamic product {pid}: {name}")
    return product_entry


CATEGORIES = ["Dresses", "Bottoms", "Tops", "Outerwear", "Knitwear"]


