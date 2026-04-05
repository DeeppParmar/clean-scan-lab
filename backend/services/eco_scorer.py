"""EcoLens — Eco Score Calculation"""

from models.schemas import Detection
from utils.label_map import RECYCLABILITY_WEIGHTS


def calculate_eco_score(detections: list[Detection]) -> float:
    """Score 0–100 based on recyclability, penalties, diversity, and volume."""
    if not detections:
        return 0.0

    total_conf = sum(d.confidence for d in detections)
    base = sum(
        d.confidence * RECYCLABILITY_WEIGHTS.get(d.category, 0.10)
        for d in detections
    ) / total_conf

    penalty = 0.0
    for d in detections:
        if d.category == "ewaste":
            penalty += 0.20 * d.confidence
        elif d.category == "general":
            penalty += 0.10 * d.confidence
        elif d.category == "unknown":
            penalty += 0.05 * d.confidence

    unique_categories = len({d.category for d in detections})
    diversity_penalty = max(0.0, (unique_categories - 2) * 0.03)
    volume_penalty = max(0.0, (len(detections) - 5) * 0.01)

    raw = base - penalty - diversity_penalty - volume_penalty
    raw = max(0.0, min(1.0, raw))
    return round(raw * 100, 1)
