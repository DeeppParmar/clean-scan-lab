"""EcoLens — Hierarchical Label Map"""

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
    "plastic": 7, "organic": 1, "ewaste": 0, "metal": 5,
    "paper": 6, "glass": 4, "textile": 3, "general": 9,
}

RECYCLABILITY_WEIGHTS: dict[str, float] = {
    "plastic": 0.60, "metal": 0.90, "glass": 0.85, "paper": 0.80,
    "organic": 0.70, "ewaste": 0.30, "textile": 0.40, "general": 0.15,
    "unknown": 0.10,
}

RECYCLABLE_CATEGORIES: frozenset[str] = frozenset({
    "plastic", "metal", "glass", "paper",
})
