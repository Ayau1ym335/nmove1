# backend/app/services/movement_age_service.py
from app.models.gait_session import GaitSession

def compute_movement_age(metrics: dict, session: GaitSession) -> dict:
    # Note: bio_age on User model may not exist yet, defaulting to None if missing
    bio_age = getattr(session.user, "bio_age", None)
    
    # Real formula: regression model trained on age-labeled gait data
    # For now: penalize low symmetry and stability vs age norms
    base_age = bio_age or 35
    symmetry_penalty = (1.0 - metrics["symmetry_score"]) * 10
    stability_penalty = (1.0 - metrics["stability_score"]) * 8
    movement_age = round(base_age + symmetry_penalty + stability_penalty, 1)
    delta = round(movement_age - base_age, 1) if bio_age is not None else None

    return {
        "movement_age": movement_age,
        "bio_age": bio_age,
        "delta": delta,
    }
