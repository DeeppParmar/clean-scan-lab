"""
EcoLens — Hierarchical Label Map (Waste-Trained Model)
Maps class indices from kendrickfff/waste-classification-yolov8-ken
→ (WasteCategory, human-readable label)

Model classes (12):
  0: battery   1: biological   2: brown-glass   3: cardboard
  4: clothes   5: green-glass   6: metal   7: paper
  8: plastic   9: shoes   10: trash   11: white-glass

Normalized to 8 clean categories:
  plastic | paper | metal | glass | organic | ewaste | textile | general
"""

# Waste-trained model class index → (normalized_category, human_label)
LABEL_MAP: dict[int, tuple[str, str]] = {
    0:  ("ewaste",  "Battery"),
    1:  ("organic", "Biological Waste"),
    2:  ("glass",   "Brown Glass"),
    3:  ("paper",   "Cardboard"),
    4:  ("textile", "Clothes"),
    5:  ("glass",   "Green Glass"),
    6:  ("metal",   "Metal"),
    7:  ("paper",   "Paper"),
    8:  ("plastic", "Plastic"),
    9:  ("textile", "Shoes"),
    10: ("general", "General Trash"),
    11: ("glass",   "White Glass"),
}

def normalize_category(raw_category: str) -> tuple[str, str]:
    """Map string labels from MobileNetV2 to internal standardized categories."""
    raw = raw_category.lower()
    
    # Map common dataset categories to our internal schema
    if raw in ["plastic"]:
        return ("plastic", "Plastic")
    elif raw in ["metal"]:
        return ("metal", "Metal Component")
    elif raw in ["glass", "brown-glass", "green-glass", "white-glass"]:
        return ("glass", "Glass")
    elif raw in ["paper", "cardboard"]:
        return ("paper", "Paper / Cardboard")
    elif raw in ["battery"]:
        return ("ewaste", "E-Waste / Hazardous")
    elif raw in ["biological", "organic", "food"]:
        return ("organic", "Organic Waste")
    elif raw in ["clothes", "shoes", "textile"]:
        return ("textile", "Textile")
    else:
        return ("general", "General Waste")

# Category slug → representative class idx (for Grad-CAM targeting)
CATEGORY_TO_CLASS_IDX: dict[str, int] = {
    "plastic": 8,
    "organic": 1,
    "ewaste":  0,
    "metal":   6,
    "paper":   7,
    "glass":   2,
    "textile": 4,
    "general": 10,
}

# Recyclability weights used by eco-scorer
RECYCLABILITY_WEIGHTS: dict[str, float] = {
    "plastic":  0.60,
    "metal":    0.90,
    "glass":    0.85,
    "paper":    0.80,
    "organic":  0.70,
    "ewaste":   0.30,
    "textile":  0.40,
    "general":  0.15,
    "unknown":  0.10,
}

# Recyclable categories
RECYCLABLE_CATEGORIES: frozenset[str] = frozenset({
    "plastic", "metal", "glass", "paper",
})
