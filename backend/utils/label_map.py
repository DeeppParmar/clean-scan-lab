"""
EcoLens — Hierarchical Label Map
Maps YOLO COCO class indices → (WasteCategory, human-readable label)
"""

# COCO class index → (category, label)
LABEL_MAP: dict[int, tuple[str, str]] = {
    # Plastic
    39: ("plastic", "Plastic Bottle"),
    41: ("plastic", "Plastic Cup"),
    46: ("plastic", "Plastic Bag"),
    # Organic
    47: ("organic", "Apple"),
    48: ("organic", "Banana"),
    49: ("organic", "Orange"),
    50: ("organic", "Broccoli"),
    51: ("organic", "Carrot"),
    52: ("organic", "Food Waste"),
    # E-Waste
    67: ("ewaste", "Mobile Phone"),
    63: ("ewaste", "Laptop"),
    66: ("ewaste", "Keyboard"),
    65: ("ewaste", "Remote Control"),
    # Metal
    43: ("metal", "Fork"),
    44: ("metal", "Knife"),
    45: ("metal", "Spoon"),
    # Paper
    73: ("paper", "Book"),
    # Glass
    40: ("glass", "Wine Glass"),
}

# Category slug → representative COCO class idx (for Grad-CAM targeting)
CATEGORY_TO_CLASS_IDX: dict[str, int] = {
    "plastic": 39,
    "organic": 47,
    "ewaste": 67,
    "metal": 43,
    "paper": 73,
    "glass": 40,
}

# Recyclability weights used by eco-scorer
RECYCLABILITY_WEIGHTS: dict[str, float] = {
    "plastic": 0.60,
    "metal": 0.90,
    "glass": 0.85,
    "paper": 0.80,
    "organic": 0.70,
    "ewaste": 0.30,
    "unknown": 0.10,
}

# Recyclable categories (sorted correctly = in one of these)
RECYCLABLE_CATEGORIES: frozenset[str] = frozenset({"plastic", "metal", "glass", "paper"})
