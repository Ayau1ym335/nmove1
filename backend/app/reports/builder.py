import os
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from uuid import UUID
from typing import Optional, Literal, cast
from sqlalchemy import text
from app.schemas.doctor import SessionRow, ExerciseAdherenceRow, MovementAgeSummaryDetail
from app.reports.medical_text import ClinicalText, generate_clinical_text
from app.services.doctor_service import _build_movement_age_summary, resolve_status_badge

@dataclass
class ReportData:
    patient:         dict
    doctor:          dict
    generated_at:    datetime
    report_period:   tuple[date, date]
    sessions:        list[SessionRow]
    snapshots:       list[dict]
    exercises:       list[ExerciseAdherenceRow]
    movement_age:    MovementAgeSummaryDetail
    domain_scores:   dict[str, float]
    norms:           dict[str, dict]
    clinical_text:   Optional[ClinicalText] = None
    charts_svg:      dict[str, str] = field(default_factory=dict)

def sync_query_user(db, user_id: UUID) -> dict | None:
    res = db.execute(text("SELECT * FROM users WHERE id = :idx"), {"idx": str(user_id)})
    row = res.mappings().first()
    return dict(row) if row else None

def sync_query_session_history(db, patient_id: UUID, doctor_id: UUID, days: int) -> list[dict]:
    # Since report handles entire period, we do unbounded pagination (or limited strictly to timeframe)
    q_data = text(f"""
        SELECT gs.id as session_id, gs.started_at, gs.ended_at, gs.duration_seconds, gs.status, gs.device_id,
               ms.movement_age, ms.interpretation_status, ms.symmetry_score, ms.stability_score, ms.cadence, ms.movement_age_delta
        FROM gait_sessions gs
        LEFT JOIN metrics_snapshots ms ON ms.gait_session_id = gs.id
        WHERE gs.user_id = :patient_id AND gs.doctor_id = :doctor_id
          AND gs.started_at >= NOW() - INTERVAL '{days} days'
        ORDER BY gs.started_at DESC
    """)
    res = db.execute(q_data, {"patient_id": str(patient_id), "doctor_id": str(doctor_id)})
    return [dict(r) for r in res.mappings().all()]

def sync_query_chart_data(db, patient_id: UUID, doctor_id: UUID, trend_days: int) -> list[dict]:
    q_safe = text(f"""
        SELECT
            time_bucket('1 day', gs.started_at) AS bucket,
            AVG(ms.movement_age)                AS movement_age,
            AVG(ms.symmetry_score)              AS symmetry_score,
            AVG(ms.stability_score)             AS stability_score,
            AVG(ms.cadence)                     AS cadence,
            COUNT(*)                            AS session_count
        FROM gait_sessions gs
        JOIN metrics_snapshots ms ON ms.gait_session_id = gs.id
        WHERE gs.user_id = :patient_id
          AND gs.doctor_id = :doctor_id
          AND gs.status = 'done'
          AND gs.started_at >= NOW() - INTERVAL '{trend_days} days'
        GROUP BY bucket
        ORDER BY bucket ASC
    """)
    res = db.execute(q_safe, {"patient_id": str(patient_id), "doctor_id": str(doctor_id)})
    return [dict(r) for r in res.mappings().all()]

def sync_query_exercise_adherence(db, patient_id: UUID, doctor_id: UUID) -> list[dict]:
    q = text("""
        SELECT
            e.title,
            e.difficulty,
            NULL as for_metric,
            COUNT(e.id) AS times_prescribed,
            MAX(gs.started_at) AS last_prescribed
        FROM exercises e
        JOIN metrics_snapshots ms ON ms.id = e.metrics_snapshot_id
        JOIN gait_sessions gs ON gs.id = ms.gait_session_id
        WHERE gs.user_id = :patient_id AND gs.doctor_id = :doctor_id
        GROUP BY e.title, e.difficulty
        ORDER BY times_prescribed DESC
        LIMIT 20
    """)
    res = db.execute(q, {"patient_id": str(patient_id), "doctor_id": str(doctor_id)})
    return [dict(r) for r in res.mappings().all()]

def assemble_report_data(db, patient_id: str, doctor_id: str, days: int) -> ReportData:
    patient = sync_query_user(db, UUID(patient_id))
    if not patient:
        raise ValueError("Patient not found")
        
    doctor = sync_query_user(db, UUID(doctor_id))
    if not doctor:
        raise ValueError("Doctor not found")

    session_rows = sync_query_session_history(db, UUID(patient_id), UUID(doctor_id), days)
    chart_rows = sync_query_chart_data(db, UUID(patient_id), UUID(doctor_id), days)
    exercise_rows = sync_query_exercise_adherence(db, UUID(patient_id), UUID(doctor_id))
    
    # Process structured outputs
    mapped_sessions = []
    for r in session_rows:
        mapped_sessions.append(SessionRow(
            session_id=r["session_id"],
            started_at=r["started_at"],
            ended_at=r["ended_at"],
            duration_seconds=r["duration_seconds"],
            status=r["status"],
            device_id=r["device_id"],
            movement_age=r["movement_age"],
            movement_age_delta=r["movement_age_delta"],
            interpretation_status=r["interpretation_status"],
            symmetry_score=r["symmetry_score"],
            stability_score=r["stability_score"],
            cadence=r["cadence"],
            status_badge=cast(
                Literal["normal", "attention", "concern", "no_data"],
                resolve_status_badge(r["interpretation_status"])
            )
        ))
        
    mapped_exercises = []
    for e in exercise_rows:
        mapped_exercises.append(ExerciseAdherenceRow(
            title=e["title"],
            difficulty=e["difficulty"],
            for_metric=e["for_metric"],
            times_prescribed=e["times_prescribed"],
            last_prescribed=e["last_prescribed"]
        ))
        
    ma_summary = _build_movement_age_summary(session_rows, patient.get("bio_age"))
    
    from_date = date.today() - timedelta(days=days - 1)
    to_date = date.today()
    
    return ReportData(
        patient=patient,
        doctor=doctor,
        generated_at=datetime.utcnow(),
        report_period=(from_date, to_date),
        sessions=mapped_sessions,
        snapshots=chart_rows,
        exercises=mapped_exercises,
        movement_age=ma_summary,
        domain_scores={}, # Optional extra mapping depending on DB logic
        norms={}, # Would be mapped directly natively if extracting norms dynamically per schema requirement
        clinical_text=None,
        charts_svg={}
    )
