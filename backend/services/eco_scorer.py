"""
EcoLens — Eco-Scorer v2
Score 0–100 with confidence weighting, category penalties, and diversity penalty.
"""
from __future__ import annotations

from models.schemas import Detection
from utils.label_map import RECYCLABILITY_WEIGHTS


def calculate_eco_score(detections: list[Detection]) -> float:
    """
    Score 0–100. Three factors:
    1. Base: confidence-weighted recyclability average
    2. Penalty: e-waste and unknown items subtract from score
    3. Diversity penalty: >2 unique categories reduces by 2% each additional
    """
    if not detections:
        return 0.0

    # Factor 1: confidence-weighted recyclability base
    total_conf = sum(d.confidence for d in detections)
    base = sum(
        d.confidence * RECYCLABILITY_WEIGHTS.get(d.category, 0.10)
        for d in detections
    ) / total_conf  # normalised 0–1

    # Factor 2: per-item penalties for hard-to-dispose categories
    penalty = 0.0
    for d in detections:
        if d.category == "ewaste":
            penalty += 0.04 * d.confidence
        elif d.category == "unknown":
            penalty += 0.02 * d.confidence

    # Factor 3: diversity penalty — harder to sort when many categories mixed
    unique_categories = len({d.category for d in detections})
    diversity_penalty = max(0.0, (unique_categories - 2) * 0.02)

    raw = base - penalty - diversity_penalty
    raw = max(0.0, min(1.0, raw))
    return round(raw * 100, 1)
