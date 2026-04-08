from typing import Dict, List, Any, Optional, cast
from sqlalchemy.orm import Session
from sqlalchemy import func
from .brain import Brain
from .diff_calc import matrix_calc
from app.config import get_settings
from app.legacy.data_tables import Users, Profiles, Injury, Report, ProgressSnapshot
from datetime import datetime, timezone, date
import json
import uuid

settings = get_settings()

def update_daily_snapshot(user_id: int, db: Session) -> None:
    """Create or update today's progress snapshot for a user."""
    user_id = int(user_id)
    today = date.today()

    todays_reports = (
        db.query(Report)
        .filter(Report.user_id == user_id, func.date(Report.created_at) == today)
        .all()
    )

    session_count = len(todays_reports)
    if session_count == 0:
        return

    overall_scores = [r.overall_score for r in todays_reports if r.overall_score is not None]
    gvi_scores = [r.gvi_score for r in todays_reports if r.gvi_score is not None]

    avg_overall_score = (
        sum(overall_scores) / len(overall_scores) if overall_scores else None
    )
    avg_gvi_score = sum(gvi_scores) / len(gvi_scores) if gvi_scores else None

    snapshot = (
        db.query(ProgressSnapshot)
        .filter(ProgressSnapshot.user_id == user_id, ProgressSnapshot.date == today)
        .first()
    )

    daily_stats = {
        "reports_processed": session_count,
        "report_ids": [r.id for r in todays_reports],
    }

    if snapshot:
        setattr(snapshot, "avg_overall_score", avg_overall_score)
        setattr(snapshot, "avg_gvi_score", avg_gvi_score)
        setattr(snapshot, "session_count", session_count)
        setattr(snapshot, "daily_stats", daily_stats)
    else:
        snapshot = ProgressSnapshot(
            user_id=user_id,
            date=today,
            avg_overall_score=avg_overall_score,
            avg_gvi_score=avg_gvi_score,
            session_count=session_count,
            daily_stats=daily_stats,
        )
        db.add(snapshot)

    db.commit()

class Analysis:
    def __init__(self, db: Session):
        self.db = db
        self.brain = Brain()
        self.CLINICAL_NORMS: Dict[str, float] = {
            "gvi": 100.0,
            "cadence": 110.0,
            "avg_speed": 1.3,
            "knee_rom": 120.0,
            "stance_swing_ratio": 1.5,
        }
        # region agent log
        self._debug_log(
            "H0",
            "analysis.py:__init__",
            "Analysis class initialized",
            {"db_class": type(db).__name__},
        )
        # endregion

    def _debug_log(self, hypothesis_id: str, location: str, message: str, data: Dict[str, Any]) -> None:
        try:
            payload = {
                "sessionId": "b8f56c",
                "id": f"log_{uuid.uuid4().hex}",
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                "runId": "pre-fix",
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data,
            }
            line = json.dumps(payload, ensure_ascii=True) + "\n"
            wrote = False
            for path in ("C:/Users/user/Desktop/nmove/debug-b8f56c.log", "debug-b8f56c.log"):
                try:
                    with open(path, "a", encoding="utf-8") as f:
                        f.write(line)
                    wrote = True
                except Exception:
                    continue
            if not wrote:
                return
        except Exception:
            pass
    
    def get_previous_reports(self, user_id: int, limit: int = 3) -> List[Dict]:
        reports = (
            self.db.query(Report)
            .filter(Report.user_id == user_id)
            .order_by(Report.created_at.desc())
            .limit(limit)
            .all()
        )
        
        report_summaries = []
        report_data = []
        for r in reports:
            report_summaries.append({
                "date": r.created_at.isoformat(),
                "gvi_score": r.gvi_score,
                "overall_score": r.overall_score,
            })
            report_data.append({
                "id": r.id,
                "user_id": r.user_id,
                "activity_type": r.activity_type,
                "notes": r.notes,
                "protocol_reference": r.protocol_reference,
                "personalized_target": r.personalized_target,
                "analysis_matrix": r.analysis_matrix,
                "clinical_narrative": r.clinical_narrative,
                "status": r.status,
                "key_metrics": {
                    "rhythm_pace": r.rhythm_pace,
                    "joint_mechanics": r.joint_mechanics,
                    "variability": r.variability,
                    "symmetry_phases": r.symmetry_phases,
                },
                "recommendations": r.recommendations,
                "overall_score": r.overall_score,
                "gvi_score": r.gvi_score,
                "created_at": r.created_at.isoformat() if r.created_at is not None else None,
            })
        
        return report_summaries

    def get_user_previous_reports(self, user_id: int, limit: int = 3) -> List[Dict]:
        return self.get_previous_reports(user_id, limit)

    def _flatten_metrics(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        rhythm = metrics.get("rhythm_pace", {})
        mechanics = metrics.get("joint_mechanics", {})
        knee = mechanics.get("knee_angle", {})
        variability = metrics.get("variability", {})
        phases = metrics.get("symmetry_phases", {})

        return {
            "gvi": float(variability.get("gvi", 0.0)),
            "cadence": float(rhythm.get("cadence", 0.0)),
            "avg_speed": float(rhythm.get("avg_speed", 0.0)),
            "knee_rom": float(knee.get("amplitude", 0.0)),
            "stance_swing_ratio": float(phases.get("stance_swing_ratio", 0.0)),
        }

    def _detect_clinical_pattern(self, matrix: Dict[str, Dict[str, Any]], current_pain: int) -> Dict[str, str]:
        statuses = [
            str(metric.get("vs_clinical", {}).get("status", "Unknown"))
            for metric in matrix.values()
        ]
        critical_count = sum(1 for s in statuses if s == "Critical")
        warning_count = sum(1 for s in statuses if s == "Warning")

        if critical_count > 0 or current_pain >= 8:
            return {
                "status": "Critical",
                "description": "Gait analysis indicates high-risk deviations that require caution.",
                "recommendation": "Reduce load and contact your clinician for guided recovery adjustments.",
            }
        if warning_count > 1 or current_pain >= 4:
            return {
                "status": "Warning",
                "description": "Gait analysis shows moderate deviations from expected recovery targets.",
                "recommendation": "Continue rehab with focus on form and monitor pain/symmetry trends daily.",
            }
        return {
            "status": "Normal",
            "description": "Gait metrics are within acceptable range for the current stage.",
            "recommendation": "Maintain current progression and keep consistency in rehabilitation sessions.",
        }

    def _calculate_smart_score(self, matrix: Dict[str, Dict[str, Any]], status: str) -> float:
        return self._calculate_score(matrix, status)

    def _flatten_data(self, data: Dict) -> Dict[str, Any]:
        try:
            profile = data.get("user_profile", {})
            injury = profile.get("injury_info", {})
            metrics = data.get("session_metrics", {})
        
            rhythm = metrics.get("rhythm_pace", {})
            mechanics = metrics.get("joint_mechanics", {})
            knee = mechanics.get("knee_angle", {})
            variability = metrics.get("variability", {})
            phases = metrics.get("symmetry_phases", {})
        
            verdict = data.get("clinical_verdict", {})

            return {
                "category": data.get("clinical_category"),
                "description": data.get("description"),
                "user_age": profile.get("age"),
                "user_gender": profile.get("gender"),
                "pain_level": injury.get("pain_level", 0),
                "gvi": variability.get("gvi", 0),
                "cadence": rhythm.get("cadence", 0),
                "avg_speed": rhythm.get("avg_speed", 0),
                "angular_velocity": rhythm.get("avg_peak_angular_velocity", 0),
                "knee_rom": knee.get("amplitude", 0),
                "knee_mean": knee.get("mean", 0),
                "step_var": variability.get("step_time_variability", 0),
                "knee_var": variability.get("knee_angle_variability", 0),
                "stance_swing_ratio": phases.get("stance_swing_ratio", 0),
                "impact_force": phases.get("avg_impact_force", 0),
                "verdict_status": verdict.get("status"),
                "key_anomaly": verdict.get("key_anomaly"),
                "comparison_note": verdict.get("comparison_note")
            }
        except Exception as e:
            print(f"Ошибка при обработке полных данных: {e}")
            return {}
    
    def _calculate_score(self, matrix: Dict, status: str) -> float:
        weights = {
            "gvi": 0.35,        
            "symmetry": 0.25,   
            "rom": 0.20,        
            "rhythm": 0.20      
        }

        score_gvi = min(matrix["gvi"]["current_value"] / 100.0, 1.0)
        
        sym_diff = abs(matrix.get("stance_swing_ratio", {}).get("vs_clinical", {}).get("diff_percent", 0))
        score_sym = max(0, 1.0 - (sym_diff / 50.0)) 
        rom_diff = abs(matrix.get("knee_rom", {}).get("vs_clinical", {}).get("diff_percent", 0))
        score_rom = max(0, 1.0 - (rom_diff / 100.0))

        cadence_diff = abs(matrix.get("cadence", {}).get("vs_clinical", {}).get("diff_percent", 0))
        score_rhythm = max(0, 1.0 - (cadence_diff / 100.0))

        raw_score = (
            (score_gvi * weights["gvi"]) +
            (score_sym * weights["symmetry"]) +
            (score_rom * weights["rom"]) +
            (score_rhythm * weights["rhythm"])
        ) * 100.0

        if status == "Critical":
            return min(raw_score, 60.0)
        elif status == "Warning":
            return min(raw_score, 85.0)
        
        return round(raw_score, 1)

    
    def get_full_analysis_text(self, report_id: int) -> str:
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        user = report.user
        
        user_profile = {
            "age": user.age,
            "gender": user.gender,
            "injury_info": user.injury_info
        }
        
        session_metrics = {
            "rhythm_pace": report.rhythm_pace,
            "joint_mechanics": report.joint_mechanics,
            "variability": report.variability,
            "symmetry_phases": report.symmetry_phases
        }
        
        return self.brain.analyze_gait(user_profile, session_metrics)

    def set_baseline(self, report_id: int, user_id: int) -> bool:
        profile = self.db.query(Profiles).filter(Profiles.id == user_id).first()
        if not profile:
            raise ValueError("Profile not found")
        report = self.db.query(Report).filter(Report.id == report_id, Report.user_id == user_id).first()
        if not report:
            raise ValueError("Report not found or does not belong to user")
        profile.baseline_report_id = report.id
        self.db.commit()
        self.db.refresh(profile)
        return True

    def generate_report(self, report_data: Any) -> Report:
        # region agent log
        self._debug_log(
            "H1A",
            "analysis.py:generate_report_v1:entry",
            "Entered first generate_report declaration",
            {"user_id": getattr(report_data, "user_id", None), "line_hint": 97},
        )
        # endregion
        user = self.db.query(Users).filter(Users.id == report_data.user_id).first()
        if not user:
            raise ValueError(f"User {report_data.user_id} not found")

        profile = self.db.query(Profiles).filter(Profiles.id == user.id).first()
        injury = self.db.query(Injury).filter(Injury.user_id == user.id).first()

        # История
        # region agent log
        self._debug_log(
            "H2",
            "analysis.py:generate_report_v2:before_previous_reports",
            "About to call previous reports accessor",
            {
                "has_get_user_previous_reports": hasattr(self, "get_user_previous_reports"),
                "has_get_previous_reports": hasattr(self, "get_previous_reports"),
            },
        )
        # endregion
        previous_reports = self.get_user_previous_reports(cast(int, user.id), limit=settings.CONTEXT_WINDOW_SIZE)

        # Дни после операции
        days_post_op = None
        if injury is not None and injury.diagnosis_date is not None:
            days_post_op = (datetime.now(timezone.utc) - injury.diagnosis_date.replace(tzinfo=timezone.utc)).days

        # Сборка Payload для AI
        user_payload = {
            "personal_info": {
                "user_id": user.id,
                "public_code": user.public_code,
                "name": user.name,
                "city": user.city,
                "email": user.email,
                "registered_at": user.created_at.isoformat() if user.created_at is not None else None,
                "age": profile.age if profile else None,
                "gender": profile.gender.value if profile else None,
                "weight": profile.weight if profile else None,
                "height": profile.height if profile else None,
                "nationality": profile.nationality if profile else None,
                "have_injury": profile.have_injury if profile else None,
                "have_banomaly": profile.have_banomaly if profile else None,
                "banomaly": profile.banomaly if profile else None,
                "shoe_size": profile.shoe_size if profile else None,
                "leg_length": profile.leg_length if profile else None,
                "dominant_leg": profile.dominant_leg.value if profile is not None and profile.dominant_leg is not None else None,
                "lifestyle": profile.lifestyle if profile else None,
                "smoke": profile.smoke if profile else None,
                "alcohol": profile.alcohol if profile else None,
                "notes": profile.notes if profile else None,
                "profile_created_at": profile.created_at.isoformat() if profile is not None and profile.created_at is not None else None,
                "baseline_report_id": profile.baseline_report_id if profile else None,
            },
            "injury_context": {
                "pain_level": injury.pain_level if injury else 0,
                "days_since_diagnosis": days_post_op,
                "injury_id": injury.id if injury else None,
                "user_id": injury.user_id if injury else None,
                "body_part": [bp.value for bp in injury.body_part] if injury is not None and injury.body_part is not None else [],
                "side": injury.side.value if injury is not None and injury.side is not None else None,
                "injury_type": [it.value for it in injury.injury_type] if injury is not None and injury.injury_type is not None else [],
                "diagnosis_date": injury.diagnosis_date.isoformat() if injury is not None and injury.diagnosis_date is not None else None,
                "is_active": injury.is_active if injury else None,
                "placed_leg": injury.placed_leg.value if injury is not None and injury.placed_leg is not None else None,
            }
        }

        session_metrics = report_data.session_metrics.model_dump()
        
        # 1. AI Анализ
        ai_narrative = self.brain.analyze_gait(
            user_profile=user_payload,
            session_metrics=session_metrics,
            previous_reports=previous_reports
        )

        # 2. Вытаскиваем цели из AI
        personal_targets = self.brain.extract_targets(ai_narrative)
        
        # 3. Подготовка данных для Матрицы
        # region agent log
        self._debug_log(
            "H3",
            "analysis.py:generate_report_v2:before_flatten",
            "About to flatten metrics and access clinical norms",
            {
                "has_flatten_metrics": hasattr(self, "_flatten_metrics"),
                "has_clinical_norms": hasattr(self, "CLINICAL_NORMS"),
                "metrics_keys": list(session_metrics.keys()) if isinstance(session_metrics, dict) else [],
            },
        )
        # endregion
        flat_user_data = self._flatten_metrics(session_metrics)
        final_targets = {k: personal_targets.get(k, self.CLINICAL_NORMS.get(k, 0)) for k in flat_user_data.keys()}

        # --- [NEW] 4. ПОДГОТОВКА BASELINE (ЭТАЛОНА) ---
        flat_baseline = None
        if profile and profile.baseline_report:
            # Восстанавливаем словарь метрик из объекта отчета, чтобы flatten его съел
            baseline_raw = {
                "rhythm_pace": profile.baseline_report.rhythm_pace,
                "joint_mechanics": profile.baseline_report.joint_mechanics,
                "variability": profile.baseline_report.variability,
                "symmetry_phases": profile.baseline_report.symmetry_phases
            }
            flat_baseline = self._flatten_metrics(baseline_raw)

        # --- [UPDATED] 5. РАСЧЕТ МАТРИЦЫ (С BASELINE) ---
        # region agent log
        self._debug_log(
            "H4",
            "analysis.py:generate_report_v2:before_matrix_calc",
            "About to call matrix_calc",
            {
                "kwargs": ["user_data", "clinical_norm", "personal_target", "baseline_data"],
                "has_baseline": flat_baseline is not None,
            },
        )
        # endregion
        analysis_matrix = matrix_calc(
            user_data=flat_user_data,
            clinical_norm=self.CLINICAL_NORMS,
            baseline_data=flat_baseline  
        )

        # 6. Паттерны и Скоринг
        current_pain = cast(int, injury.pain_level) if injury is not None else 0
        clinical_pattern = self._detect_clinical_pattern(analysis_matrix, current_pain)
        overall_score = self._calculate_smart_score(analysis_matrix, clinical_pattern["status"])

        # 7. Сохранение
        new_report = Report(
            user_id=user.id,
            activity_type=session_metrics.get("activity_type", ["walking"]),
            rhythm_pace=session_metrics["rhythm_pace"],
            joint_mechanics=session_metrics["joint_mechanics"],
            variability=session_metrics["variability"],
            symmetry_phases=session_metrics["symmetry_phases"],
            protocol_reference=ai_narrative,
            personalized_target=final_targets,
            analysis_matrix=analysis_matrix,
            clinical_narrative=clinical_pattern["description"],
            recommendations=clinical_pattern["recommendation"],
            status=clinical_pattern["status"],
            overall_score=overall_score,
            gvi_score=flat_user_data.get("gvi", 0)
        )

        self.db.add(new_report)
        self.db.commit()
        
        # --- [NEW] 8. ОБНОВЛЕНИЕ ГРАФИКОВ ПРОГРЕССА ---
        # region agent log
        self._debug_log(
            "H5",
            "analysis.py:generate_report_v2:before_snapshot_update",
            "About to call update_daily_snapshot",
            {"defined_in_globals": "update_daily_snapshot" in globals()},
        )
        # endregion
        update_daily_snapshot(cast(int, user.id), self.db)

        self.db.refresh(new_report)
        return new_report