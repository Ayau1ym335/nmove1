from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import and_, func

from app.legacy.data_tables import Injury, ProgressSnapshot, WalkingSessions


class ReportAggregator:
    def __init__(self, db_session, user_id: int, injury_id: int):
        self.db = db_session
        self.user_id = user_id
        self.injury_id = injury_id

    def get_executive_summary(self, start_date: datetime, end_date: datetime) -> Dict:
        sessions = self.db.query(WalkingSessions).filter(
            and_(
                WalkingSessions.user_id == self.user_id,
                WalkingSessions.start_time >= start_date,
                WalkingSessions.start_time <= end_date,
                WalkingSessions.is_processed == True,
            )
        ).all()

        injury = self.db.query(Injury).get(self.injury_id)

        latest_snapshot = self.db.query(ProgressSnapshot).filter(
            ProgressSnapshot.injury_id == self.injury_id
        ).order_by(ProgressSnapshot.created_at.desc()).first()

        prev_week_start = start_date - timedelta(days=7)
        prev_snapshot = self.db.query(ProgressSnapshot).filter(
            and_(
                ProgressSnapshot.injury_id == self.injury_id,
                ProgressSnapshot.created_at >= prev_week_start,
                ProgressSnapshot.created_at < start_date,
            )
        ).order_by(ProgressSnapshot.created_at.desc()).first()

        score_change = None
        if latest_snapshot and prev_snapshot:
            latest_score = self._to_float(getattr(latest_snapshot, "overall_score", None))
            prev_score = self._to_float(getattr(prev_snapshot, "overall_score", None))
            if latest_score is not None and prev_score is not None:
                score_change = latest_score - prev_score

        critical_alerts = self._detect_critical_alerts(sessions)

        return {
            "patient": {
                "name": f"{injury.user.first_name} {injury.user.last_name}",
                "age": self._calculate_age(injury.user.date_of_birth),
                "injury_type": injury.injury_type,
                "affected_side": injury.affected_side,
            },
            "timeline": {
                "post_op_day": (datetime.now() - injury.surgery_date).days if injury.surgery_date else None,
                "recovery_phase": injury.recovery_phase,
                "report_period": f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
            },
            "overall_score": self._to_float(getattr(latest_snapshot, "overall_score", None))
            if latest_snapshot
            else None,
            "score_trend": score_change,
            "critical_alerts": critical_alerts,
            "total_sessions": len(sessions),
        }

    def _detect_critical_alerts(self, sessions: List[WalkingSessions]) -> List[Dict]:
        alerts: List[Dict[str, Any]] = []

        for session in sessions:
            gvi = self._to_float(getattr(session, "gvi", None))
            knee_amplitude = self._to_float(getattr(session, "knee_amplitude", None))
            step_time_variability = self._to_float(getattr(session, "step_time_variability", None))

            if gvi is not None and gvi > 150:
                alerts.append(
                    {
                        "severity": "CRITICAL",
                        "type": "high_gvi",
                        "timestamp": session.start_time,
                        "value": gvi,
                        "message": f"GVI превысил 150 ({gvi:.1f})",
                    }
                )

            if knee_amplitude is not None and knee_amplitude < 70:
                alerts.append(
                    {
                        "severity": "WARNING",
                        "type": "low_rom",
                        "timestamp": session.start_time,
                        "value": knee_amplitude,
                        "message": f"ROM ниже критического уровня ({knee_amplitude:.1f}°)",
                    }
                )

            if step_time_variability is not None and step_time_variability > 15:
                alerts.append(
                    {
                        "severity": "WARNING",
                        "type": "unstable_gait",
                        "timestamp": session.start_time,
                        "value": step_time_variability,
                        "message": "Нестабильность походки",
                    }
                )

        return alerts

    def get_primary_gait_parameters(self, sessions: List[WalkingSessions]) -> Dict:
        _ = [s for s in sessions if self._is_injured_side_session(s)]
        _ = [s for s in sessions if not self._is_injured_side_session(s)]

        gvi_mean = self._mean_metric(sessions, "gvi")
        metrics = {
            "knee_rom": self._calculate_metric_comparison(sessions, "knee_amplitude", clinical_norm=120),
            "cadence": self._calculate_metric_comparison(sessions, "cadence", clinical_norm=110),
            "stride_length": self._calculate_metric_comparison(sessions, "avg_speed", clinical_norm=1.3),
            "gvi": {
                "injured": gvi_mean,
                "healthy": 98,
                "asymmetry": None,
                "clinical_norm": 110,
                "status": self._get_status_color(gvi_mean or 0.0, 110),
            },
        }

        return metrics

    def _calculate_metric_comparison(
        self, sessions: List[WalkingSessions], field_name: str, clinical_norm: float
    ) -> Optional[Dict[str, Any]]:
        values = [
            value
            for s in sessions
            if (value := self._to_float(getattr(s, field_name, None))) is not None
        ]
        if not values:
            return None

        avg_value = float(np.mean(values))
        asymmetry = abs(avg_value - clinical_norm) / clinical_norm * 100
        return {
            "injured": avg_value,
            "healthy": clinical_norm * 0.95,
            "asymmetry": asymmetry,
            "clinical_norm": clinical_norm,
            "status": self._get_status_color(asymmetry, threshold=10),
        }

    def _get_status_color(self, value: float, threshold: float, inverse: bool = False) -> str:
        if inverse:
            if value < threshold:
                return "green"
            if value < threshold * 1.5:
                return "yellow"
            return "red"

        if value > threshold:
            return "red"
        if value > threshold * 0.7:
            return "yellow"
        return "green"

    def get_three_matrix_data(self, sessions: List[WalkingSessions], metric: str = "knee_amplitude") -> Dict:
        clinical_norm = self._get_clinical_norm(metric)
        baseline_sessions = self.db.query(WalkingSessions).filter(
            and_(WalkingSessions.user_id == self.user_id, WalkingSessions.is_baseline == True)
        ).all()

        personal_baseline = None
        if baseline_sessions:
            baseline_values = [
                value
                for s in baseline_sessions
                if (value := self._to_float(getattr(s, metric, None))) is not None
            ]
            personal_baseline = float(np.mean(baseline_values)) if baseline_values else None

        current_values = [
            value
            for s in sessions
            if (value := self._to_float(getattr(s, metric, None))) is not None
        ]
        daily_data = self._group_by_days(sessions, metric)

        return {
            "clinical_norm": clinical_norm,
            "personal_baseline": personal_baseline,
            "current_performance": {
                "daily_values": daily_data,
                "average": float(np.mean(current_values)) if current_values else None,
            },
            "metric_name": metric,
            "unit": self._get_metric_unit(metric),
        }

    def _get_clinical_norm(self, metric: str) -> float:
        clinical_norms = {
            "knee_amplitude": 120.0,
            "cadence": 110.0,
            "avg_speed": 1.3,
            "gvi": 100.0,
            "step_time_variability": 5.0,
        }
        return float(clinical_norms.get(metric, 0.0))

    def _group_by_days(self, sessions: List[WalkingSessions], metric: str) -> List[Dict]:
        from collections import defaultdict

        daily = defaultdict(list)
        for session in sessions:
            day = session.start_time.date()
            value = self._to_float(getattr(session, metric, None))
            if value is not None:
                daily[day].append(value)

        return [
            {
                "date": str(day),
                "value": float(np.mean(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
            }
            for day, values in sorted(daily.items())
        ]

    def get_weekly_trends(self, weeks: int = 4) -> Dict:
        end_date = datetime.now()
        trends = []

        for week_offset in range(weeks, 0, -1):
            week_end = end_date - timedelta(days=7 * (week_offset - 1))
            week_start = week_end - timedelta(days=7)

            sessions = self.db.query(WalkingSessions).filter(
                and_(
                    WalkingSessions.user_id == self.user_id,
                    WalkingSessions.start_time >= week_start,
                    WalkingSessions.start_time < week_end,
                    WalkingSessions.is_processed == True,
                )
            ).all()
            if not sessions:
                continue

            trends.append(
                {
                    "week_number": weeks - week_offset + 1,
                    "date_range": f"{week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m')}",
                    "rom": self._mean_metric(sessions, "knee_amplitude"),
                    "symmetry": self._calculate_symmetry_index(sessions),
                    "gvi": self._mean_metric(sessions, "gvi"),
                    "overall_score": self._get_snapshot_for_week(week_start, week_end),
                }
            )

        return {"weeks": trends, "improvement_rate": self._calculate_improvement_rate(trends)}

    def _calculate_symmetry_index(self, sessions: List[WalkingSessions]) -> Optional[float]:
        ratios = [
            value
            for s in sessions
            if (value := self._to_float(getattr(s, "stance_swing_ratio", None))) is not None
        ]
        if not ratios:
            return None

        ideal_ratio = 1.5
        avg_ratio = float(np.mean(ratios))
        symmetry_index = (1 - abs(avg_ratio - ideal_ratio) / ideal_ratio) * 100
        return float(max(0.0, min(100.0, symmetry_index)))

    def _calculate_improvement_rate(self, trends: List[Dict]) -> float:
        if len(trends) < 2:
            return 0.0
        first_score = trends[0]["overall_score"]
        last_score = trends[-1]["overall_score"]
        if not first_score or not last_score:
            return 0.0
        return float(((last_score - first_score) / first_score) * 100)

    def get_pain_correlation_data(self, sessions: List[WalkingSessions]) -> Dict:
        daily_data = []
        for session in sessions:
            notes = self._to_str(getattr(session, "notes", None))
            pain_level = self._extract_pain_from_notes(notes)
            daily_data.append(
                {
                    "date": session.start_time.strftime("%d.%m"),
                    "pain": pain_level,
                    "gvi": self._to_float(getattr(session, "gvi", None)),
                    "rom": self._to_float(getattr(session, "knee_amplitude", None)),
                }
            )

        correlation = None
        if len(daily_data) > 3:
            pain_values = [d["pain"] for d in daily_data if d["pain"] is not None]
            gvi_values = [d["gvi"] for d in daily_data if d["gvi"] is not None]
            if len(pain_values) == len(gvi_values) and pain_values:
                correlation = float(np.corrcoef(pain_values, gvi_values)[0, 1])

        return {
            "daily_data": daily_data,
            "correlation_coefficient": correlation,
            "insight": self._generate_pain_insight(correlation),
        }

    def _extract_pain_from_notes(self, notes: Optional[str]) -> Optional[int]:
        if not notes:
            return None
        import re

        match = re.search(r"(\d+)/10", notes)
        if match:
            return int(match.group(1))
        return None

    def _generate_pain_insight(self, correlation: Optional[float]) -> str:
        if correlation is None:
            return "Недостаточно данных для анализа"
        if correlation > 0.5:
            return "Сильная положительная корреляция: высокая боль совпадает с нестабильностью походки"
        if correlation < -0.5:
            return "Обратная корреляция: боль снижается при улучшении стабильности"
        return "Слабая корреляция: боль и походка могут быть независимыми факторами"

    def get_session_breakdown(self, sessions: List[WalkingSessions]) -> List[Dict]:
        breakdown = []
        for session in sessions:
            notes = self._to_str(getattr(session, "notes", None))
            pain_pre = self._extract_pain_from_notes(notes)
            duration = self._to_float(getattr(session, "duration", None))
            breakdown.append(
                {
                    "date": session.start_time.strftime("%d.%m"),
                    "time": session.start_time.strftime("%H:%M"),
                    "duration_min": round(duration / 60, 1) if duration is not None else None,
                    "rom": self._to_float(getattr(session, "knee_amplitude", None)),
                    "gvi": self._to_float(getattr(session, "gvi", None)),
                    "cadence": self._to_float(getattr(session, "cadence", None)),
                    "pain_pre": pain_pre,
                    "pain_post": None,
                    "activity_type": session.activity_type,
                }
            )
        return breakdown

    def _to_float(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _to_str(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        try:
            return str(value)
        except Exception:
            return None

    def _mean_metric(self, sessions: List[WalkingSessions], field_name: str) -> Optional[float]:
        values = [
            value
            for s in sessions
            if (value := self._to_float(getattr(s, field_name, None))) is not None
        ]
        if not values:
            return None
        return float(np.mean(values))

    def _calculate_age(self, date_of_birth: Optional[datetime]) -> Optional[int]:
        if date_of_birth is None:
            return None
        today = datetime.now().date()
        dob = date_of_birth.date()
        years = today.year - dob.year
        if (today.month, today.day) < (dob.month, dob.day):
            years -= 1
        return years

    def _is_injured_side_session(self, session: WalkingSessions) -> bool:
        session_side = self._to_str(getattr(session, "affected_side", None))
        injury_side = self._to_str(getattr(session, "injury_side", None))
        if session_side and injury_side:
            return session_side.lower() == injury_side.lower()
        return False

    def _get_metric_unit(self, metric: str) -> str:
        units = {
            "knee_amplitude": "deg",
            "cadence": "steps/min",
            "avg_speed": "m/s",
            "gvi": "%",
            "step_time_variability": "cv%",
        }
        return units.get(metric, "")

    def _get_snapshot_for_week(self, week_start: datetime, week_end: datetime) -> Optional[float]:
        snapshot = self.db.query(ProgressSnapshot).filter(
            and_(
                ProgressSnapshot.injury_id == self.injury_id,
                ProgressSnapshot.created_at >= week_start,
                ProgressSnapshot.created_at < week_end,
            )
        ).order_by(ProgressSnapshot.created_at.desc()).first()
        if snapshot is None:
            return None
        return self._to_float(getattr(snapshot, "overall_score", None))