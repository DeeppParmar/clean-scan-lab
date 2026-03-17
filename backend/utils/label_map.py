"""
EcoLens — Hierarchical Label Map (Waste-Trained Model)
Maps class indices from kendrickfff/waste-classification-yolov8-ken
→ (WasteCategory, human-readable label)

Model classes (12):
  0: battery   1: biological   2: brown-glass   3: cardboard
  4: clothes   5: green-glass   6: metal   7: paper
  8: plastic   9: shoes   10: trash   11: white-glass
"""

# Waste-trained model class index → (category, label)
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

# Recyclable categories (sorted correctly = in one of these)
RECYCLABLE_CATEGORIES: frozenset[str] = frozenset({
    "plastic", "metal", "glass", "paper",
})
