"""
EcoLens — Eco-Scorer v3
Score 0–100 with confidence weighting, heavier category penalties,
and diversity penalty for mixed waste.
"""
from __future__ import annotations

from collections import Counter

from models.schemas import Detection
from utils.label_map import RECYCLABILITY_WEIGHTS


def calculate_eco_score(detections: list[Detection]) -> float:
    """
    Score 0–100. Four factors:
    1. Base: confidence-weighted recyclability average
    2. Category penalty: ewaste -20pts, general -10pts each
    3. Diversity penalty: >2 unique categories reduces by 3% each additional
    4. Volume penalty: >5 items reduces by 1% each additional
    """
    if not detections:
        return 0.0

    # Factor 1: confidence-weighted recyclability base
    total_conf = sum(d.confidence for d in detections)
    base = sum(
        d.confidence * RECYCLABILITY_WEIGHTS.get(d.category, 0.10)
        for d in detections
    ) / total_conf  # normalised 0–1

    # Factor 2: heavier per-item penalties
    penalty = 0.0
    for d in detections:
        if d.category == "ewaste":
            penalty += 0.20 * d.confidence
        elif d.category == "general":
            penalty += 0.10 * d.confidence
        elif d.category == "unknown":
            penalty += 0.05 * d.confidence

    # Factor 3: diversity penalty — harder to sort when many categories mixed
    unique_categories = len({d.category for d in detections})
    diversity_penalty = max(0.0, (unique_categories - 2) * 0.03)

    # Factor 4: volume penalty — more waste = lower score
    volume_penalty = max(0.0, (len(detections) - 5) * 0.01)

    raw = base - penalty - diversity_penalty - volume_penalty
    raw = max(0.0, min(1.0, raw))
    return round(raw * 100, 1)
