from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import numpy as np # Нам понадобится numpy для корреляции
from app.data.constants import ALL_METRICS_LIST, METRIC_DOMAINS_MAP
from app.data.tables import Report, ProgressSnapshot

class PeriodAggregator:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def get_trends(self, days: int = 7) -> Dict[str, Dict]:
        today = datetime.now(timezone.utc).date()
        current_start = today - timedelta(days=days)
        previous_start = current_start - timedelta(days=days)
        
        current_data = self._get_snapshots(current_start, today)
        previous_data = self._get_snapshots(previous_start, current_start)
        
        if not current_data:
            return {} 

        curr_metrics = self._average_metrics(current_data)
        prev_metrics = self._average_metrics(previous_data) if previous_data else None
        
        trends = {}
        for metric, value in curr_metrics.items():
            prev_value = prev_metrics.get(metric) if prev_metrics else None
            
            trends[metric] = {
                "current_avg": value,
                "previous_avg": prev_value,
                "change_percent": self._calculate_percent_change(value, prev_value),
                "direction": self._get_trend_direction(metric, value, prev_value)
            }
            
        return trends

    def analyze_pain_correlation(self, days: int = 30) -> Dict:
        start_date = datetime.now(timezone.utc).date() - timedelta(days=days)
        snapshots = self._get_snapshots(start_date, datetime.now(timezone.utc).date())
        
        if len(snapshots) < 3:
            return {"correlation": None, "insight": "Недостаточно данных для анализа"}
            
        pain_values = []
        gvi_values = []
        dates = []
        
        for s in snapshots:
            pain = getattr(s, 'avg_pain_level', 0) 
            gvi = s.avg_gvi_score
            
            if pain is not None and gvi is not None:
                pain_values.append(pain)
                gvi_values.append(gvi)
                dates.append(s.date)

        if len(set(pain_values)) > 1 and len(set(gvi_values)) > 1:
            correlation = np.corrcoef(pain_values, gvi_values)[0, 1]
            correlation = round(correlation, 2)
        else:
            correlation = 0.0 
            
        return {
            "period_days": days,
            "correlation_coefficient": correlation,
            "insight": self._generate_correlation_insight(correlation),
            "graph_data": {
                "dates": [d.isoformat() for d in dates],
                "pain": pain_values,
                "gvi": gvi_values
            }
        }

    def _get_snapshots(self, start, end) -> List[ProgressSnapshot]:
        return self.db.query(ProgressSnapshot).filter(
            and_(
                ProgressSnapshot.user_id == self.user_id,
                ProgressSnapshot.date >= start,
                ProgressSnapshot.date < end
            )
        ).order_by(ProgressSnapshot.date.asc()).all()

    def _average_metrics(self, snapshots: List[ProgressSnapshot]) -> Dict[str, float]:
        if not snapshots: return {}
        count = len(snapshots)
        
        avg_score = sum(s.avg_overall_score for s in snapshots) / count
        avg_gvi = sum(s.avg_gvi_score for s in snapshots) / count
        avg_pain = sum(getattr(s, 'avg_pain_level', 0) for s in snapshots) / count
        
        avg_rom = 0 # Пример, если нужно вытаскивать из json
        # (Тут можно добавить логику распаковки avg_domain_scores, если нужно)
        
        return {
            "overall_score": round(avg_score, 1),
            "gvi": round(avg_gvi, 1),
            "pain": round(avg_pain, 1)
        }

    def _calculate_percent_change(self, current, previous) -> Optional[float]:
        if previous is None or previous == 0:
            return None
        change = ((current - previous) / previous) * 100
        return round(change, 1)

    def _get_trend_direction(self, metric: str, current, previous) -> str:
        if previous is None: return "New"
        diff = current - previous
        
        if metric in ["gvi", "pain"]:
            if diff > 1: return "Regressing"    
            elif diff < -1: return "Improving"  
            return "Stable"
            
        else:
            if diff > 1: return "Improving"     
            elif diff < -1: return "Regressing" 
            return "Stable"

    def _generate_correlation_insight(self, corr: float) -> str:
        if corr > 0.6:
            return "🔴 Высокая связь: При усилении боли походка становится нестабильной. Боль — ограничивающий фактор."
        elif corr < -0.6:
            return "🟡 Парадоксальная связь: При боли стабильность улучшается (возможно, пациент 'зажимается')."
        elif abs(corr) < 0.3:
            return "🟢 Нет явной связи: Нестабильность походки не зависит от текущего уровня боли (проблема в механике/мышцах)."
        else:
            return "⚪ Умеренная связь."



