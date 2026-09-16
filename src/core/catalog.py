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

# Detailed Haute Atelier Specifications (Colorways Palette, Textile Fabrics, Silhouettes, and Care)
ATELIER_SPECS = {
    "P001": {
        "colorways": [
            {"name": "Verdant Sage", "hex": "#2ecc71", "tone": "Earthy & Crisp"},
            {"name": "Terracotta Rust", "hex": "#d35400", "tone": "Warm Mediterranean"},
            {"name": "Raw Pearl Ivory", "hex": "#f5f5f0", "tone": "Classic Neutral"},
            {"name": "Riviera Navy", "hex": "#1b3a4b", "tone": "Deep Marine"},
            {"name": "Dusty Peony", "hex": "#e8b4b8", "tone": "Soft Floral Blush"}
        ],
        "fabric": {
            "composition": "100% Normandy Flax Linen",
            "weight_gsm": "170 GSM",
            "weave": "Airy Breathable Slub Weave",
            "handfeel": "Crisp yet supple with natural enzyme softness",
            "care": "Hand wash cold or gentle cycle • Line dry in shade • Warm steam iron",
            "origin": "Normandy, France • Handcrafted in Milan Atelier",
            "sustainability": "100% Biodegradable & OEKO-TEX® Certified"
        },
        "silhouette": "Surplice V-neckline with side sash tie and graceful tulip hemline",
        "styling_notes": "Pairs effortlessly with Suede Moto Jacket (P018) and woven espadrilles.",
        "pairing_sku": "P018"
    },
    "P002": {
        "colorways": [
            {"name": "Riviera Azure", "hex": "#3498db", "tone": "Vibrant Silk Cobalt"},
            {"name": "Atelier Gold", "hex": "#d4af37", "tone": "Warm Liquid Champagne"},
            {"name": "Midnight Noir", "hex": "#0f172a", "tone": "Glossy Deep Black"},
            {"name": "Dusty Petal", "hex": "#f472b6", "tone": "Pastel Rosé"},
            {"name": "Imperial Jade", "hex": "#065f46", "tone": "Lustrous Emerald"}
        ],
        "fabric": {
            "composition": "100% Pure Mulberry Silk (22 Momme Grade 6A)",
            "weight_gsm": "95 GSM",
            "weave": "Fluid Charmeuse Satin Weave",
            "handfeel": "Ultra-glossy pearl luster with fluid liquid drape",
            "care": "Dry clean recommended or hand wash with silk shampoo",
            "origin": "Como, Italy",
            "sustainability": "Cruelty-Free Mulberry Silk Production"
        },
        "silhouette": "High-waisted bias-cut midi with hidden interior elastic waistband",
        "styling_notes": "Stunning with Cashmere Crewneck (P005) tucked in or Ribbed Tank (P003).",
        "pairing_sku": "P005"
    },
    "P003": {
        "colorways": [
            {"name": "Royal Amethyst", "hex": "#9b59b6", "tone": "Rich Violet"},
            {"name": "Pure Alabaster", "hex": "#f8fafc", "tone": "Clean Optical White"},
            {"name": "Jet Noir", "hex": "#0f172a", "tone": "Midnight Saturated"},
            {"name": "Sunlight Butter", "hex": "#fde047", "tone": "Warm Pastel Gold"},
            {"name": "Soft Espresso", "hex": "#78716c", "tone": "Neutral Mocha Taupe"}
        ],
        "fabric": {
            "composition": "92% Organic Supima Cotton, 8% Spandex",
            "weight_gsm": "220 GSM",
            "weave": "2x2 Fine Rib Elastic Knit",
            "handfeel": "Skin-caressing stretch with shape-retaining memory",
            "care": "Machine wash cold gentle • Tumble dry low or air dry",
            "origin": "Guimarães, Portugal",
            "sustainability": "GOTS Certified Organic Supima"
        },
        "silhouette": "Fitted scoop neckline with bra-concealing tailored shoulder straps",
        "styling_notes": "Ideal foundation piece layered under Tailored Double-Breasted Blazer (P010).",
        "pairing_sku": "P010"
    },
    "P004": {
        "colorways": [
            {"name": "Vintage Mustard", "hex": "#f1c40f", "tone": "70s Sun-Drenched Tint"},
            {"name": "Heritage Indigo", "hex": "#2563eb", "tone": "Classic Mid-Wash Blue"},
            {"name": "Unbleached Ecru", "hex": "#fef3c7", "tone": "Natural Cotton Canvas"},
            {"name": "Faded Basalt", "hex": "#374151", "tone": "Mineral Washed Black"},
            {"name": "Olive Safari", "hex": "#4d7c0f", "tone": "Military Khaki Green"}
        ],
        "fabric": {
            "composition": "100% Rigid Organic Cotton",
            "weight_gsm": "460 GSM (13.5 oz)",
            "weave": "Right-Hand 3x1 Heavyweight Twill",
            "handfeel": "Sturdy architectural structure that softens with wear",
            "care": "Wash sparingly inside out in cold water • Hang dry",
            "origin": "Okayama, Japan",
            "sustainability": "Waterless Ozone Washing Process"
        },
        "silhouette": "Boxy drop-shoulder trucker silhouette with embossed brass shank buttons",
        "styling_notes": "Drapes effortlessly over Linen Wrap Dress (P001) for effortless chic.",
        "pairing_sku": "P001"
    },
    "P005": {
        "colorways": [
            {"name": "Autumn Caramel", "hex": "#e67e22", "tone": "Warm Spiced Amber"},
            {"name": "Alpine Heather", "hex": "#94a3b8", "tone": "Cool Silver Grey"},
            {"name": "Cashmere Cream", "hex": "#f5f5f4", "tone": "Unbleached Cloud Ivory"},
            {"name": "Highland Pine", "hex": "#14532d", "tone": "Deep Forest Green"},
            {"name": "Sovereign Navy", "hex": "#0f172a", "tone": "Classic Oxford Navy"}
        ],
        "fabric": {
            "composition": "100% Grade-A Mongolian Cashmere",
            "weight_gsm": "260 GSM (2-Ply 12-Gauge)",
            "weave": "Jersey Knit with 15.5 Micron Diameter Fibers",
            "handfeel": "Peerless cloud-soft thermal warmth with zero itch",
            "care": "Specialized dry clean or hand wash with cashmere shampoo • Dry flat",
            "origin": "Ulaanbaatar, Mongolia • Spun in Biella, Italy",
            "sustainability": "Sustainable Fibre Alliance (SFA) Certified"
        },
        "silhouette": "Timeless crewneck with ribbed tubular collar, micro-cuffs, and hem",
        "styling_notes": "Tuck the front hem into Wide Leg Trousers (P006) with gold jewelry.",
        "pairing_sku": "P006"
    },
    "P006": {
        "colorways": [
            {"name": "Empress Crimson", "hex": "#e74c3c", "tone": "Vibrant Statement Red"},
            {"name": "Savile Camel", "hex": "#d97706", "tone": "Classic Tailored Tan"},
            {"name": "Tuxedo Black", "hex": "#0f172a", "tone": "Deep Matte Noir"},
            {"name": "Tuscan Olive", "hex": "#3f6212", "tone": "Sophisticated Earthy Moss"},
            {"name": "Oatmeal Melange", "hex": "#e2e8f0", "tone": "Subtle Flecked Stone"}
        ],
        "fabric": {
            "composition": "68% Poly-Viscose, 28% Virgin Wool, 4% Lycra",
            "weight_gsm": "280 GSM",
            "weave": "High-Twist Gabardine Weave",
            "handfeel": "Smooth structured drape with anti-crease recovery",
            "care": "Dry clean only • Cool iron with pressing cloth",
            "origin": "Prato, Italy",
            "sustainability": "Recycled Wool Blend Fibers"
        },
        "silhouette": "High-rise contoured waistline, sharp front double pleats, wide puddle hem",
        "styling_notes": "Coordinates cleanly with Classic White Poplin Buttondown (P007).",
        "pairing_sku": "P007"
    },
    "P007": {
        "colorways": [
            {"name": "Teal-Tint Alabaster", "hex": "#1abc9c", "tone": "Crisp Sea-Breeze Tint"},
            {"name": "Optical Chalk", "hex": "#ffffff", "tone": "Pure Brilliant White"},
            {"name": "French Sky", "hex": "#60a5fa", "tone": "Light Corporate Blue"},
            {"name": "Morning Lilac", "hex": "#c084fc", "tone": "Ethereal Pastel Violet"},
            {"name": "Soft Peach", "hex": "#f472b6", "tone": "Warm Sorbet"}
        ],
        "fabric": {
            "composition": "100% Long-Staple Egyptian Giza 87 Cotton",
            "weight_gsm": "125 GSM (120/2 Two-Ply Yarn)",
            "weave": "Silky Compact Poplin Weave",
            "handfeel": "Crisp, silky, breathable with luminous clean surface",
            "care": "Machine wash warm • Line dry • High steam iron",
            "origin": "Nile Delta, Egypt • Tailored in Milan",
            "sustainability": "Better Cotton Initiative (BCI) Certified"
        },
        "silhouette": "Tailored boyfriend cut with structured point collar and mother-of-pearl buttons",
        "styling_notes": "Layer under Cropped Cable Knit Vest (P011) for equestrian sophistication.",
        "pairing_sku": "P011"
    },
    "P008": {
        "colorways": [
            {"name": "Carbon Slate", "hex": "#34495e", "tone": "Cool Storm Charcoal"},
            {"name": "Bourbon Cognac", "hex": "#9a3412", "tone": "Rich Saddle Tan"},
            {"name": "Forest Moss", "hex": "#365314", "tone": "Deep British Racing Green"},
            {"name": "Bordeaux Wine", "hex": "#881337", "tone": "Deep Black-Cherry Gloss"},
            {"name": "Piano Noir", "hex": "#09090b", "tone": "Glossy Midnight Patent"}
        ],
        "fabric": {
            "composition": "100% Waterborne Bio-Based Polyurethane on Recycled Viscose",
            "weight_gsm": "360 GSM",
            "weave": "Supple Micro-Porous Faux Nappa Leather",
            "handfeel": "Buttery soft handfeel indistinguishable from calfskin, waterproof",
            "care": "Wipe clean with microfiber damp cloth • Never machine wash or iron",
            "origin": "Seoul, South Korea",
            "sustainability": "100% Solvent-Free & PETA-Approved Vegan"
        },
        "silhouette": "Dramatic double-breasted maxi silhouette, storm gun flap, horn waist buckle",
        "styling_notes": "Cinch over the Satin Pleated Midi Skirt (P012) for street style elegance.",
        "pairing_sku": "P012"
    },
    "P009": {
        "colorways": [
            {"name": "Marigold Ochre", "hex": "#d35400", "tone": "Sun-Baked Terracotta"},
            {"name": "Bohemian Magenta", "hex": "#be185d", "tone": "Vibrant Fuchsia Bloom"},
            {"name": "Midnight Paisley", "hex": "#1e3a8a", "tone": "Deep Sapphire Floral"},
            {"name": "Forest Botanical", "hex": "#15803d", "tone": "Lush Emerald Canopy"},
            {"name": "Vintage Ivory", "hex": "#fef08a", "tone": "Champagne Butter Floral"}
        ],
        "fabric": {
            "composition": "100% EcoVero™ Lenzing Viscose Georgette",
            "weight_gsm": "115 GSM",
            "weave": "Airy Sheer Crepe with Detachable Cotton Slip",
            "handfeel": "Floating weightless texture with gentle crepe pebble touch",
            "care": "Hand wash cold inside out • Dry in shade • Low iron",
            "origin": "Jaipur, India",
            "sustainability": "50% Lower Emissions EcoVero™ Viscose"
        },
        "silhouette": "Floor-sweeping tiered maxi with smocked waistline and billowing raglan sleeves",
        "styling_notes": "Pairs effortlessly with Suede Moto Jacket (P018) for bohemian festival flair.",
        "pairing_sku": "P018"
    },
    "P010": {
        "colorways": [
            {"name": "Monochrome Flannel", "hex": "#7f8c8d", "tone": "Tailored Heather Slate"},
            {"name": "Tuxedo Jet", "hex": "#020617", "tone": "Formal Deep Noir"},
            {"name": "Viennese Camel", "hex": "#b45309", "tone": "Rich Aristocratic Camel"},
            {"name": "Prince of Wales", "hex": "#64748b", "tone": "Subtle Glen Plaid"},
            {"name": "Hunter Emerald", "hex": "#064e3b", "tone": "Regal Dark Malachite"}
        ],
        "fabric": {
            "composition": "100% Super 130s Virgin Italian Worsted Wool",
            "weight_gsm": "310 GSM",
            "weave": "Four-Season Hopsack Suiting Weave",
            "handfeel": "Crisp structured drape, natural wrinkle resistance, cupro lined",
            "care": "Specialized dry clean only • Hang on shaped cedar coat hanger",
            "origin": "Florence, Italy",
            "sustainability": "Mulesing-Free Responsible Wool Standard (RWS)"
        },
        "silhouette": "Double-breasted 6-button front, architectural peak lapels, jetted flap pockets",
        "styling_notes": "Coordinates with High-Waisted Wide Leg Trouser (P006) for a power suit.",
        "pairing_sku": "P006"
    },
    "P011": {
        "colorways": [
            {"name": "Nordic Seafoam", "hex": "#16a085", "tone": "Deep Oceanic Emerald"},
            {"name": "Traditional Aran", "hex": "#fef9c3", "tone": "Authentic Unbleached Wool"},
            {"name": "Dark Cocoa", "hex": "#451a03", "tone": "Rich Bittersweet Brown"},
            {"name": "Soft Thistle", "hex": "#c084fc", "tone": "Scottish Heather Lilac"},
            {"name": "Winter Holly", "hex": "#991b1b", "tone": "Deep Festive Berry"}
        ],
        "fabric": {
            "composition": "80% Pure Merino Wool, 20% Baby Alpaca",
            "weight_gsm": "380 GSM (3-Gauge Chunky Knit)",
            "weave": "Heritage Honeycomb & Trellis Cable Knit",
            "handfeel": "Plush, lofty, dimensional knit with insulating warmth",
            "care": "Hand wash cold with wool soap • Press in towel • Dry flat",
            "origin": "Galway, Ireland",
            "sustainability": "100% Untreated Natural Animal Fibers"
        },
        "silhouette": "Cropped V-neck vest silhouette with wide armholes and ribbed hem band",
        "styling_notes": "Layer directly over Classic White Poplin Buttondown (P007).",
        "pairing_sku": "P007"
    },
    "P012": {
        "colorways": [
            {"name": "Malachite Green", "hex": "#27ae60", "tone": "Rich Jewel Emerald"},
            {"name": "Champagne Rosé", "hex": "#fbcfe8", "tone": "Lustrous Blushing Bronze"},
            {"name": "Burnished Copper", "hex": "#b45309", "tone": "Metallic Molten Bronze"},
            {"name": "Deep Ocean", "hex": "#0c4a6e", "tone": "Dark Midnight Cobalt"},
            {"name": "Liquid Platinum", "hex": "#cbd5e1", "tone": "Futuristic Silver Sheen"}
        ],
        "fabric": {
            "composition": "100% Heavyweight Duchess Satin (Recycled Poly)",
            "weight_gsm": "190 GSM",
            "weave": "Permanent Knife Accordion Pleated Weave",
            "handfeel": "Silky crisp fluid motion with high-definition pleat retention",
            "care": "Gentle hand wash cold • Do not press pleats with iron • Vertical steam only",
            "origin": "Lyon, France",
            "sustainability": "GRS Certified Recycled Polyester"
        },
        "silhouette": "A-line midi with sunburst permanent accordion pleats and grosgrain waistband",
        "styling_notes": "Looks sublime paired with Cashmere Crewneck Sweater (P005).",
        "pairing_sku": "P005"
    },
    "P013": {
        "colorways": [
            {"name": "Bleach Stonewash", "hex": "#2980b9", "tone": "Sun-Bleached Mid-Blue"},
            {"name": "Midnight Indigo", "hex": "#1e3a8a", "tone": "Deep Raw Chambray"},
            {"name": "Summer Cloud", "hex": "#93c5fd", "tone": "Lightest Sky Blue"},
            {"name": "Desert Tan", "hex": "#d97706", "tone": "Warm Sand Khaki"},
            {"name": "Field Olive", "hex": "#3f6212", "tone": "Muted Workwear Green"}
        ],
        "fabric": {
            "composition": "100% Organic Selvedge Cotton Chambray",
            "weight_gsm": "160 GSM (5.5 oz)",
            "weave": "Plain Weave with White Weft and Indigo Warp",
            "handfeel": "Softened utility feel, breathable and exceptionally durable",
            "care": "Machine wash cold with like colors • Tumble dry low",
            "origin": "Greensboro, North Carolina",
            "sustainability": "Organic Cotton with Eco-Friendly Indigo Dye"
        },
        "silhouette": "Dual flap utility chest pockets, reinforced chain-stitched gussets, camp collar",
        "styling_notes": "Tuck into Distressed Straight Leg Denim (P016) for a chic Canadian tuxedo.",
        "pairing_sku": "P016"
    },
    "P014": {
        "colorways": [
            {"name": "Imperial Violet", "hex": "#8e44ad", "tone": "Deep Royal Plum"},
            {"name": "Warm Fawn", "hex": "#d97706", "tone": "Classic Biscuit Camel"},
            {"name": "Dark Basalt", "hex": "#1e293b", "tone": "Rich Charcoal Black"},
            {"name": "Unbleached Pearl", "hex": "#fafaf9", "tone": "Natural Bone Ecru"},
            {"name": "Scottish Moor", "hex": "#166534", "tone": "Deep Heathered Forest"}
        ],
        "fabric": {
            "composition": "100% Extra-Fine Australian Merino Wool",
            "weight_gsm": "240 GSM (14-Gauge Interlock Knit)",
            "weave": "Ultra-Fine 19.5 Micron Fully-Fashioned Knit",
            "handfeel": "Silky-smooth, naturally thermoregulating and odor-resistant",
            "care": "Hand wash cold with wool wash • Reshape and lay flat to dry",
            "origin": "Melbourne, Australia",
            "sustainability": "Woolmark Certified & Non-Mulesed"
        },
        "silhouette": "Relaxed V-neckline cardigan with genuine mottled tortoiseshell buttons",
        "styling_notes": "Drapes gently over Lace-Trim Cami Tank (P017) with tailored trousers.",
        "pairing_sku": "P017"
    },
    "P015": {
        "colorways": [
            {"name": "Opera Scarlet", "hex": "#c0392b", "tone": "Dramatic Venetian Red"},
            {"name": "Couture Noir", "hex": "#09090b", "tone": "Inky Midnight Black"},
            {"name": "Velvet Emerald", "hex": "#14532d", "tone": "Deep Lustrous Malachite"},
            {"name": "Tuscan Ochre", "hex": "#b45309", "tone": "Sun-Drenched Amber"},
            {"name": "Charcoal Heather", "hex": "#475569", "tone": "Refined Medium Slate"}
        ],
        "fabric": {
            "composition": "65% Lenzing Modal, 30% Polyamide, 5% Spandex",
            "weight_gsm": "270 GSM",
            "weave": "Heavyweight Sculptural Rib Knit",
            "handfeel": "Body-hugging contouring stretch with cool-to-touch silky drape",
            "care": "Hand wash cold inside out • Dry flat on towel • Steam low",
            "origin": "Vienna, Austria",
            "sustainability": "Zero Carbon Footprint Lenzing Modal"
        },
        "silhouette": "Striking one-shoulder neckline with diagonal thigh slit and gathered side ruche",
        "styling_notes": "Accessorize with metallic gold heels and Tailored Double-Breasted Blazer (P010).",
        "pairing_sku": "P010"
    },
    "P016": {
        "colorways": [
            {"name": "90s Stonewash", "hex": "#bdc3c7", "tone": "Faded Vintage Light Blue"},
            {"name": "Authentic Indigo", "hex": "#3b82f6", "tone": "Classic Heritage Denim"},
            {"name": "Washed Slate", "hex": "#1f2937", "tone": "Faded Charcoal Fade"},
            {"name": "Raw Natural", "hex": "#fef3c7", "tone": "Unbleached Cream Denim"},
            {"name": "Deep Clean Indigo", "hex": "#172554", "tone": "Rigid Dark Navy Rinse"}
        ],
        "fabric": {
            "composition": "99% Organic Cotton, 1% Eco-Spandex",
            "weight_gsm": "430 GSM (12.8 oz)",
            "weave": "Ring-Spun Authentic Selvedge Denim",
            "handfeel": "Authentic vintage rugged handfeel with micro-stretch for comfort",
            "care": "Cold wash inside out • Line dry • Avoid optical brighteners",
            "origin": "Milan, Italy (Candiani Mill)",
            "sustainability": "Kitotex® Natural Seaweed Sizing"
        },
        "silhouette": "Classic high-rise fit, straight leg from knee to ankle, subtle hand-abraded edges",
        "styling_notes": "Tuck in Classic White Poplin Buttondown (P007) and add leather belt.",
        "pairing_sku": "P007"
    },
    "P017": {
        "colorways": [
            {"name": "Silver Satin", "hex": "#95a5a6", "tone": "Cool Liquid Platinum"},
            {"name": "Vintage Ivory", "hex": "#fef08a", "tone": "Champagne Silk Pearl"},
            {"name": "Midnight Noir", "hex": "#020617", "tone": "Dramatic Black on Black"},
            {"name": "Bordeaux Plum", "hex": "#4a044e", "tone": "Deep Sensual Wine"},
            {"name": "Deep Malachite", "hex": "#064e3b", "tone": "Dark Forest Silk"}
        ],
        "fabric": {
            "composition": "95% Pure Silk Georgette, 5% Elastane with 100% Chantilly Lace",
            "weight_gsm": "85 GSM",
            "weave": "Delicate Double Georgette with Scalloped Eyelash Border",
            "handfeel": "Featherweight, translucent, whisper-soft against the skin",
            "care": "Hand wash cold in delicates bag • Lay flat • Steam reverse",
            "origin": "Calais, France",
            "sustainability": "Handcrafted Lace Trims from Historic French Looms"
        },
        "silhouette": "Bias-cut V-neckline with delicate eyelash lace insert and adjustable micro straps",
        "styling_notes": "Wear under Vegan Leather Trench Coat (P008) for an alluring evening contrast.",
        "pairing_sku": "P008"
    },
    "P018": {
        "colorways": [
            {"name": "Mustard Suede", "hex": "#f39c12", "tone": "70s Golden Tan Suede"},
            {"name": "Cigar Brown", "hex": "#78350f", "tone": "Deep Rich Espresso"},
            {"name": "Matte Jet", "hex": "#0f172a", "tone": "Saturated Charcoal Black"},
            {"name": "Earthy Moss", "hex": "#365314", "tone": "Tuscan Olive Velour"},
            {"name": "Desert Rosé", "hex": "#f472b6", "tone": "Subtle Dusty Terracotta"}
        ],
        "fabric": {
            "composition": "100% Genuine Goat Split Suede Leather",
            "weight_gsm": "480 GSM (0.7mm Nap)",
            "weave": "Velvety Brushed Nap with Silky Poly-Twill Lining",
            "handfeel": "Sumptuously soft, velvety touch with substantial wind-blocking weight",
            "care": "Specialized leather dry cleaner only • Treat with water repellent spray",
            "origin": "León, Mexico",
            "sustainability": "LWG (Leather Working Group) Gold-Rated Tannery"
        },
        "silhouette": "Asymmetric antiqued brass zip front, snap-down peak lapels, belted waist hem",
        "styling_notes": "Stunning contrast over Boho Floral Maxi Dress (P009) with ankle boots.",
        "pairing_sku": "P009"
    },
    "P019": {
        "colorways": [
            {"name": "Capri Lemon", "hex": "#f1c40f", "tone": "Radiant Sunshine Yellow"},
            {"name": "Riviera Gingham", "hex": "#38bdf8", "tone": "Bright Mediterranean Sky"},
            {"name": "Mediterranean Coral", "hex": "#f87171", "tone": "Warm Vibrant Geranium"},
            {"name": "Santorini White", "hex": "#f8fafc", "tone": "Pure Dazzling White"},
            {"name": "Tuscan Garden", "hex": "#65a30d", "tone": "Sage Vine Floral"}
        ],
        "fabric": {
            "composition": "100% Organic Cotton Broderie Anglaise",
            "weight_gsm": "145 GSM",
            "weave": "Delicate Eyelet Geometric Cutwork Embroidery",
            "handfeel": "Airy, crisp, romantic cotton with gentle sculptural body",
            "care": "Machine wash delicate cold in laundry bag • Line dry • Warm steam iron",
            "origin": "Athens, Greece",
            "sustainability": "100% GOTS Certified Organic Cotton"
        },
        "silhouette": "Square neckline, ruffled elasticized puff sleeves, smocked waist, tiered hem",
        "styling_notes": "Complete with woven raffia tote and oversized sunglasses for resort days.",
        "pairing_sku": "P002"
    },
    "P020": {
        "colorways": [
            {"name": "Heritage Forest", "hex": "#16a085", "tone": "Vintage Racing Green"},
            {"name": "Athletic Heather", "hex": "#64748b", "tone": "Gymnasium Flecked Grey"},
            {"name": "Washed Chalk", "hex": "#f5f5f4", "tone": "Unbleached Natural Cream"},
            {"name": "Faded Carbon", "hex": "#18181b", "tone": "Pigment Dyed Vintage Black"},
            {"name": "Autumn Brick", "hex": "#b91c1c", "tone": "Rich Burnt Rust"}
        ],
        "fabric": {
            "composition": "100% Combed Organic French Terry Cotton",
            "weight_gsm": "450 GSM (Ultra-Heavyweight Fleece)",
            "weave": "Tight-Knit Jersey Face with Brushed Loopback Interior",
            "handfeel": "Dense, substantial, supremely plush and cozy",
            "care": "Machine wash cold with like colors • Tumble dry low",
            "origin": "Toronto, Canada",
            "sustainability": "Fair Trade Certified Organic Cotton"
        },
        "silhouette": "Double-layered sculptural hood, clean seamless neckline, boxy drop-shoulder cut",
        "styling_notes": "Pairs effortlessly with High-Waisted Wide Leg Trouser (P006) for high-low streetwear.",
        "pairing_sku": "P006"
    }
}

def get_lookbook_catalog() -> dict:
    """
    Returns the full product catalog enriched with high-fashion atelier specifications.
    Combines core pricing, categories, and inventory parameters with fabric,
    colorways, and styling metadata.
    """
    enriched = {}
    for pid, base in CATALOG.items():
        specs = ATELIER_SPECS.get(pid, {
            "colorways": [{"name": "Signature Tone", "hex": base.get("color", "#2c3e50"), "tone": "Signature"}],
            "fabric": {
                "composition": "Luxury Natural Fiber Blend",
                "weight_gsm": "200 GSM",
                "weave": "Fine Tailored Weave",
                "handfeel": "Soft and structured luxury handfeel",
                "care": "Dry clean or delicate cold wash",
                "origin": "Artisan Atelier",
                "sustainability": "Eco-Friendly Production"
            },
            "silhouette": f"Signature tailored cut for {base.get('name')}",
            "styling_notes": "Coordinates across the capsule collection.",
            "pairing_sku": "P001"
        })
        
        enriched[pid] = {
            **base,
            **specs,
            "product_id": pid
        }
    return enriched

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


