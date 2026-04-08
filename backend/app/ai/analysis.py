from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.routers.schemas import ReportCreate
from ai.brain import Brain
from ai.diff_calc import matrix_calc
from app.config import get_settings
from app.data.tables import Users, Profiles, Injury, Report 
from datetime import datetime, timezone

settings = get_settings()

class Analysis:
    def __init__(self, db: Session):
        self.db = db
        self.brain = Brain()
    
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
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
        
        return report_summaries
        return report_data

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
    
    def generate_report(self, report_data: ReportCreate) -> Report:
        user = self.db.query(Users).filter(Users.id == report_data.user_id).first()
        if not user:
            raise ValueError(f"User {report_data.user_id} not found")

        profile = self.db.query(Profiles).filter(Profiles.id == user.id).first()
        injury = self.db.query(Injury).filter(Injury.user_id == user.id).first()

        previous_reports = self.get_user_previous_reports(
            user.id, limit=settings.CONTEXT_WINDOW_SIZE
        )

        days_post_op = None
        if injury and injury.diagnosis_date:
            days_post_op = (datetime.now(timezone.utc) - injury.diagnosis_date.replace(tzinfo=timezone.utc)).days

        user_payload = {
            "personal_info": {
                "age": profile.age if profile else None,
                "gender": profile.gender.value if profile else None,
                "weight": profile.weight if profile else None,
                "height": profile.height if profile else None,
                "leg_length": profile.leg_length if profile else None,
                "shoe_size": profile.shoe_size if profile else None,
            },
            "injury_context": {
                "has_injury": profile.have_injury if profile else False,
                "body_part": [bp.value for bp in injury.body_part] if injury else [],
                "injury_type": [it.value for it in injury.injury_type] if injury else [],
                "side": injury.side.value if injury else None,
                "placed_leg": injury.placed_leg.value if injury else profile.dominant_leg.value,
                "pain_level": injury.pain_level if injury else 0,
                "days_since_diagnosis": days_post_op
            }
        }

        session_metrics = report_data.session_metrics.model_dump()
    
        ai_narrative = self.brain.analyze_gait(
            user_profile=user_payload,
            session_metrics=session_metrics,
            previous_reports=previous_reports
        )

        personal_targets = self.brain.extract_targets(ai_narrative)
        flat_user_data = self._flatten_metrics(session_metrics)
    
        final_targets = {k: personal_targets.get(k, self.CLINICAL_NORMS.get(k, 0)) for k in flat_user_data.keys()}
    
        analysis_matrix = matrix_calc(
            user_data=flat_user_data,
            clinical_norm=self.CLINICAL_NORMS,
            personal_target=final_targets
        )

        current_pain = injury.pain_level if injury else 0
        clinical_pattern = self._detect_clinical_pattern(analysis_matrix, current_pain)
        overall_score = self._calculate_smart_score(analysis_matrix, clinical_pattern["status"])

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
        self.db.refresh(new_report)
        return new_report
    
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

    def generate_report(self, report_data: ReportCreate) -> Report:
        user = self.db.query(Users).filter(Users.id == report_data.user_id).first()
        if not user:
            raise ValueError(f"User {report_data.user_id} not found")

        profile = self.db.query(Profiles).filter(Profiles.id == user.id).first()
        injury = self.db.query(Injury).filter(Injury.user_id == user.id).first()

        # История
        previous_reports = self.get_user_previous_reports(user.id, limit=settings.CONTEXT_WINDOW_SIZE)

        # Дни после операции
        days_post_op = None
        if injury and injury.diagnosis_date:
            days_post_op = (datetime.now(timezone.utc) - injury.diagnosis_date.replace(tzinfo=timezone.utc)).days

        # Сборка Payload для AI
        user_payload = {
            "personal_info": {
                "age": profile.age if profile else None,
                "gender": profile.gender.value if profile else None,
                # ... остальные поля ...
            },
            "injury_context": {
                "pain_level": injury.pain_level if injury else 0,
                "days_since_diagnosis": days_post_op,
                # ... остальные поля ...
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
        analysis_matrix = matrix_calc(
            user_data=flat_user_data,
            clinical_norm=self.CLINICAL_NORMS,
            personal_target=final_targets,
            baseline_data=flat_baseline  # <--- ВОТ ЗДЕСЬ ПРОИСХОДИТ МАГИЯ
        )

        # 6. Паттерны и Скоринг
        current_pain = injury.pain_level if injury else 0
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
        update_daily_snapshot(user.id, self.db)

        self.db.refresh(new_report)
        return new_report