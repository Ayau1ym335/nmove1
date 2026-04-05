# backend/app/services/metrics_service.py
def compute_gait_metrics(readings: list) -> dict:
    duration_seconds = (readings[-1].time - readings[0].time).total_seconds()
    
    if duration_seconds < 1:
        # Default metrics for too short an interval
        return {
            "cadence": 0.0,
            "symmetry_score": 1.0,
            "stability_score": 1.0,
            "duration_seconds": duration_seconds,
            "reading_count": len(readings),
        }
        
    cadence = round((len(readings) / max(duration_seconds, 1)) * 60, 2)
    
    # Real formula: compare left vs right step timing variance
    # symmetry = 1 - (abs(left_mean - right_mean) / (left_mean + right_mean))
    
    # Real formula: RMS of acceleration magnitude variance
    # stability = 1 - std(sqrt(ax²+ay²+az²)) / mean(sqrt(ax²+ay²+az²))

    return {
        "cadence": cadence,
        "symmetry_score": 0.85, # placeholder 0.85 
        "stability_score": 0.80, # placeholder 0.80
        "duration_seconds": duration_seconds,
        "reading_count": len(readings),
    }
