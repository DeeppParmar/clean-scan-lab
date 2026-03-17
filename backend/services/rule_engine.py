"""
EcoLens — Rule Engine
Maps each waste category → disposal metadata.
"""
from __future__ import annotations

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
    "unknown": {
        "recyclable": False,
        "bin_color": "black",
        "disposal_instructions": "Unidentified item — check local council guidelines before disposal.",
        "hazardous": False,
    },
}


def apply_rules(category: str) -> dict:
    """Return disposal rule dict for a given category slug."""
    return RULES.get(category, RULES["unknown"])
