import logging
from typing import Optional

from app.norms.norms_loader import (
    METRIC_DOMAIN_MAP, 
    DOMAIN_WEIGHTS, 
    list_all_metrics, 
    get_age_group
)
from app.services.normalization_service import normalize_metric

logger = logging.getLogger("nmove.services")

def compute_movement_age(
    metrics: dict,
    bio_age: Optional[int],
) -> dict:
    """Calculate the comprehensive movement age utilizing parameterized and validated normal curves."""
    # Step 1 — resolve bio_age
    effective_bio_age = bio_age if bio_age and 10 <= bio_age <= 100 else 35

    # Step 2 — normalize each metric
    normalized = {}
    valid_metrics = list_all_metrics()
    
    for metric_name, value in metrics.items():
        if metric_name not in valid_metrics:
            continue
        try:
            normalized[metric_name] = normalize_metric(
                metric_name, value, effective_bio_age
            )
        except Exception as e:
            logger.warning(f"Could not normalize {metric_name}: {e}")
            normalized[metric_name] = 0.5

    # Step 3 — compute domain scores
    domain_scores = {}
    for domain, metric_weights in METRIC_DOMAIN_MAP.items():
        domain_total = 0.0
        weight_sum = 0.0
        
        for metric_name, weight in metric_weights.items():
            if metric_name in normalized:
                domain_total += normalized[metric_name] * weight
                weight_sum += weight
                
        if weight_sum > 0:
            domain_scores[domain] = domain_total / weight_sum
        else:
            domain_scores[domain] = 0.5

    # Step 4 — compute composite score
    composite = sum(
        domain_scores[domain] * DOMAIN_WEIGHTS[domain]
        for domain in DOMAIN_WEIGHTS
    )

    # Step 5 — compute movement_age
    if composite >= 0.5:
        improvement_factor = (composite - 0.5) * 2   # maps 0.5 -> 0.0, 1.0 -> 1.0
        movement_age = effective_bio_age - (improvement_factor * effective_bio_age * 0.4)
    else:
        decline_factor = (0.5 - composite) * 2       # maps 0.5 -> 0.0, 0.0 -> 1.0
        movement_age = effective_bio_age + (decline_factor * effective_bio_age * 0.5)

    movement_age = int(round(movement_age))
    movement_age = max(10, min(movement_age, 100))  # hard clamp
    delta = movement_age - effective_bio_age

    # Step 6 — return payload
    return {
        "movement_age":       movement_age,
        "bio_age":            bio_age,
        "effective_bio_age":  effective_bio_age,
        "delta":              delta,
        "composite_score":    round(composite, 4),
        "domain_scores":      {k: round(v, 4) for k, v in domain_scores.items()},
        "normalized_metrics": {k: round(v, 4) for k, v in normalized.items()},
        "age_group_used":     get_age_group(effective_bio_age),
    }
