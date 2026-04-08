from scipy.stats import norm as scipy_norm
from app.norms.norms_loader import get_age_group, get_norm

def z_score_normalize(
    value: float,
    mean: float,
    sd: float,
    lower_is_better: bool = False,
    clip_sd: float = 3.0,
) -> float:
    """Normalize a regular metric to a 0-1 percentile score. 
       0.5 = Exactly average, 1.0 = highly optimized performance."""
    if sd == 0:
        sd = 1e-6
    z = (value - mean) / sd
    z = max(-clip_sd, min(z, clip_sd))
    
    # Invert so higher Z translates to a "better"/"healthier" CDF percentile length.
    if lower_is_better:
        z = -z
        
    return float(scipy_norm.cdf(z))

def deviation_normalize(
    value: float,
    mean: float,
    sd: float,
    clip_sd: float = 3.0,
) -> float:
    """Normalize a metric where deviation from the mean in either direction is bad."""
    if sd == 0:
        sd = 1e-6
    z = abs(value - mean) / sd
    z = max(0.0, min(z, clip_sd))
    return float(1.0 - (z / clip_sd))

def normalize_metric(
    metric_name: str,
    value: float,
    bio_age: int,
) -> float:
    """Dispatches a normalization based on the metric behavior structure and user age."""
    age_group = get_age_group(bio_age)
    norm = get_norm(metric_name, age_group)
    
    if norm.get("deviation_metric", False):
        return deviation_normalize(value, norm["mean"], norm["sd"])
    else:
        return z_score_normalize(
            value, 
            norm["mean"], 
            norm["sd"], 
            norm.get("lower_is_better", False)
        )
