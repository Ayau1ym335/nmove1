# backend/app/services/interpretation_service.py
def compute_interpretation(metrics: dict, movement_age: dict) -> dict:
    symmetry = metrics["symmetry_score"]
    stability = metrics["stability_score"]
    delta = movement_age.get("delta")

    # Status rules
    if symmetry >= 0.90 and stability >= 0.85:
        status = "normal"
    elif symmetry >= 0.75 and stability >= 0.70:
        status = "improving"
    else:
        status = "needs_attention"

    # Exercise rules — at least one exercise always returned
    exercises = []
    if symmetry < 0.85:
        exercises.append({
            "title": "Single-leg balance",
            "description": "Stand on one leg for 30 seconds. Switch legs. Repeat 3 times each side.",
            "difficulty": "easy",
            "duration_minutes": 5,
        })
    if stability < 0.80:
        exercises.append({
            "title": "Heel-to-toe walk",
            "description": "Walk in a straight line placing heel directly in front of toes for 10 steps.",
            "difficulty": "easy",
            "duration_minutes": 5,
        })
    if delta and delta > 5:
        exercises.append({
            "title": "Hip flexor stretch",
            "description": "Lunge stretch, 30 seconds each side, 3 sets. Improves stride length.",
            "difficulty": "medium",
            "duration_minutes": 8,
        })
    if not exercises:
        exercises.append({
            "title": "Maintenance walk",
            "description": "15-minute brisk walk maintaining your current good form.",
            "difficulty": "easy",
            "duration_minutes": 15,
        })

    return {"status": status, "exercises": exercises}
