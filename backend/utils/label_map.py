"""EcoLens — Hierarchical Label Map"""

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
    raw = raw_category.lower()
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


CATEGORY_TO_CLASS_IDX: dict[str, int] = {
    "plastic": 8, "organic": 1, "ewaste": 0, "metal": 6,
    "paper": 7, "glass": 2, "textile": 4, "general": 10,
}

RECYCLABILITY_WEIGHTS: dict[str, float] = {
    "plastic": 0.60, "metal": 0.90, "glass": 0.85, "paper": 0.80,
    "organic": 0.70, "ewaste": 0.30, "textile": 0.40, "general": 0.15,
    "unknown": 0.10,
}

RECYCLABLE_CATEGORIES: frozenset[str] = frozenset({
    "plastic", "metal", "glass", "paper",
})
