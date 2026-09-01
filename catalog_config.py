# catalog_config.py
import random

# Complete 20-item production catalog map
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

def generate_initial_inventory():
    """
    Initializes 20 products: 15 items fully stocked and available (35-60 units),
    and 5 specific items completely unavailable (0 units).
    """
    inventory_state = {}
    for pid in CATALOG:
        # Check if the product matches the designated out-of-stock range
        if int(pid[1:]) >= 16:
            inventory_state[pid] = 0 # Completely unavailable / Out-of-Stock
        else:
            inventory_state[pid] = random.randint(35, 60) # Fully Stocked
    return inventory_state
