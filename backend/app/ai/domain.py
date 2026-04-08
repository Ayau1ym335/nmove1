from typing import Any, Dict, List, cast
from app.data.constants import METRIC_DOMAINS_MAP, ALL_METRICS_LIST
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, date
from app.legacy.data_tables import Report, ProgressSnapshot
import numpy as np

def daily_snapshot(db: Session, user_id: int):
    today = datetime.now(timezone.utc).date()
    reports = db.query(Report).filter(
        Report.user_id == user_id, 
        func.date(Report.created_at) == today
    ).all()
    
    if not reports: return

    metrics_collection = {m: [] for m in ALL_METRICS_LIST}
    
    for r in reports:
        data = r.session_metrics_data
        for m in ALL_METRICS_LIST:
            if data.get(m) is not None:
                metrics_collection[m].append(data[m])

    daily_stats: Dict[str, Dict[str, float]] = {}
    pathology_log: List[Dict[str, Any]] = []
    
    for metric, values in metrics_collection.items():
        if not values: continue
        
        median_val = float(np.median(values))
        min_val = float(np.min(values))
        max_val = float(np.max(values))
        
        daily_stats[metric] = {
            "median": round(median_val, 2),
            "mean": round(float(np.mean(values)), 2),
            "min": round(min_val, 2),
            "max": round(max_val, 2)
        }
        
        # 3. ДЕТЕКЦИЯ ПАТОЛОГИЙ (Anomalies)
        # Правило 1: Резкое падение амплитуды (Судорога/Боль)
        if metric == "knee_amplitude":
            # Если минимум на 40% меньше медианы - это аномалия
            if min_val < (median_val * 0.6):
                pathology_log.append({
                    "type": "Severe ROM Drop",
                    "metric": "knee_amplitude",
                    "value": min_val,
                    "typical": median_val,
                    "insight": "Possible muscle spasm or locking"
                })
        
        # Правило 2: Всплеск нестабильности (GVI)
        if metric == "gvi":
            if max_val > 140: # Абсолютный порог
                pathology_log.append({
                    "type": "Critical Instability",
                    "metric": "gvi",
                    "value": max_val,
                    "insight": "High fall risk detected"
                })

    # 4. Расчет Радар-чарта (на основе Медианных значений)
    # Нам нужно посчитать доменный балл не для каждой сессии, а для "Типичной" (Медианной) сессии дня
    
    # Сначала соберем "Медианный профиль" юзера за сегодня
    median_profile = {m: stats["median"] for m, stats in daily_stats.items()}
    
    # ...Здесь вызываем функцию calculate_domain_scores(median_profile)...
    # (Функция из Дня 1, которая возвращает 0-100 для 4 доменов)
    # Для примера:
    radar_domains: Dict[str, float] = {
        "rhythm": 85.0, "mechanics": 70.0, "stability": 60.0, "symmetry": 90.0
    }

    # 5. Сохранение
    snapshot = db.query(ProgressSnapshot).filter_by(user_id=user_id, date=today).first()
    if not snapshot:
        snapshot = ProgressSnapshot(user_id=user_id, date=today)
        db.add(snapshot)
    
    overall_scores = [cast(float, r.overall_score) for r in reports if r.overall_score is not None]
    avg_overall = round(float(np.mean(overall_scores)), 1) if overall_scores else 0.0
    gvi_median = float(daily_stats.get("gvi", {}).get("median", 0.0))

    setattr(snapshot, "daily_stats", daily_stats)
    setattr(snapshot, "radar_domains", radar_domains)
    setattr(snapshot, "pathology_log", pathology_log)
    setattr(snapshot, "avg_overall_score", avg_overall)
    setattr(snapshot, "avg_gvi_score", gvi_median) # Лучше брать медиану GVI
    
    db.commit()

def calculate_domain(analysis_matrix: Dict[str, Dict]) -> Dict[str, float]:
    domain_scores = {
        "rhythm": 0.0,
        "mechanics": 0.0,
        "variability": 0.0,
        "symmetry": 0.0
    }
    
    for domain, metrics_list in METRIC_DOMAINS_MAP.items():
        total_score = 0
        count = 0
        
        for metric in metrics_list:
            metric_data = analysis_matrix.get(metric)
            if not metric_data:
                continue
            
            diff = metric_data["vs_clinical"]["diff_percent"]
            
            if diff is None:
                continue

            score = max(40, 100 - abs(diff))
            
            total_score += score
            count += 1

        if count > 0:
            domain_scores[domain] = round(total_score / count, 1)
        else:
            domain_scores[domain] = 0.0 
            
    return domain_scores