"""EcoLens — Rules & Suggestions Engine"""

RULES: dict[str, dict] = {
    "plastic": {
        "recyclable": True,
        "bin_color": "yellow",
        "disposal_instructions": "Empty, rinse, and flatten before placing in yellow recycling bin.",
        "hazardous": False,
    },
    "organic": {
        "recyclable": False,
        "bin_color": "green",
        "disposal_instructions": "Compost in a green organics bin or home compost heap.",
        "hazardous": False,
    },
    "ewaste": {
        "recyclable": False,
        "bin_color": "red",
        "disposal_instructions": "Do NOT bin. Take to an authorised e-waste drop-off or retailer take-back scheme.",
        "hazardous": True,
    },
    "metal": {
        "recyclable": True,
        "bin_color": "yellow",
        "disposal_instructions": "Rinse cans/cutlery and place in yellow recycling bin.",
        "hazardous": False,
    },
    "paper": {
        "recyclable": True,
        "bin_color": "blue",
        "disposal_instructions": "Keep dry. Flatten boxes and place in blue recycling bin.",
        "hazardous": False,
    },
    "glass": {
        "recyclable": True,
        "bin_color": "white",
        "disposal_instructions": "Rinse and place in glass/white recycling bin. Remove lids.",
        "hazardous": False,
    },
    "textile": {
        "recyclable": False,
        "bin_color": "purple",
        "disposal_instructions": "Donate usable items. Worn-out textiles go to textile recycling drop-off.",
        "hazardous": False,
    },
    "general": {
        "recyclable": False,
        "bin_color": "black",
        "disposal_instructions": "Place in general waste (black bin). Not recyclable.",
        "hazardous": False,
    },
    "unknown": {
        "recyclable": False,
        "bin_color": "black",
        "disposal_instructions": "Unidentified item — check local council guidelines before disposal.",
        "hazardous": False,
    },
}

BULK_SUGGESTIONS: dict[str, str] = {
    "plastic": " Consider bulk recycling at a deposit centre.",
    "metal": " Large metal items may qualify for scrap metal pickup.",
    "glass": " Group by colour for better recycling outcomes.",
    "paper": " Bundle cardboard flat for efficient collection.",
    "ewaste": " Schedule a free e-waste collection with your council.",
    "textile": " Consider donating to charity or textile recycling banks.",
    "organic": " Start a home compost for consistent organic waste.",
    "general": " Minimise general waste — check if items can be separated.",
}


def apply_rules(category: str, count: int = 1) -> dict:
    base = RULES.get(category, RULES["unknown"]).copy()
    suggestion = base["disposal_instructions"]
    if count > 3 and category in BULK_SUGGESTIONS:
        suggestion += BULK_SUGGESTIONS[category]
    base["suggestion"] = suggestion
    base["action"] = "Recycle" if base["recyclable"] else "Dispose"
    return base
