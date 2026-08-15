"""
Phase 13: deterministic sustainability score.

Formula
-------
The score is a linear inverse mapping of predicted carbon footprint onto a
0-100 scale, anchored to the real training-data distribution of
`carbon_footprint_kg_co2e_per_ha` (see ml/datasets/train.csv, post Phase 4
cleaning) rather than an arbitrary made-up range:

    MIN_REFERENCE = 557.00    # [DATA-DERIVED] min of train.csv target (post Phase 4 winsorizing)
    MAX_REFERENCE = 3020.03   # [DATA-DERIVED] max of train.csv target (post Phase 4 winsorizing)

    score = 100 - ((footprint - MIN_REFERENCE) / (MAX_REFERENCE - MIN_REFERENCE)) * 100

Clamped to [0, 100] and rounded to the nearest integer. Lower footprint ->
higher score. This is a monotonic, fully deterministic function of a single
input — no randomness, no hidden state. A prediction below the training
min or above the training max simply clamps to 100 or 0 rather than
producing an out-of-range score.

Categories (fixed thresholds, spec-mandated):
    90-100  Excellent
    75-89   Good
    50-74   Moderate
    0-49    Needs Improvement
"""

MIN_REFERENCE = 557.00
MAX_REFERENCE = 3020.03


def compute_sustainability_score(carbon_footprint_kg_co2e_per_ha: float) -> int:
    raw = 100 - ((carbon_footprint_kg_co2e_per_ha - MIN_REFERENCE) / (MAX_REFERENCE - MIN_REFERENCE)) * 100
    clamped = max(0.0, min(100.0, raw))
    return round(clamped)


def categorize_score(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 50:
        return "Moderate"
    return "Needs Improvement"
