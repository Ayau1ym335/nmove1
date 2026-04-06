import json
import os

DOMAIN_WEIGHTS = {
    "variability":      0.25,
    "symmetry_phases":  0.30,
    "rhythm_pace":      0.25,
    "joint_mechanics":  0.20,
}

METRIC_DOMAIN_MAP = {
    "variability": {
        "stride_time_cv":      0.55,
        "trunk_sway_rms":      0.45,
    },
    "symmetry_phases": {
        "step_symmetry_ratio": 0.45,
        "stance_phase_pct":    0.30,
        "double_support_pct":  0.25,
    },
    "rhythm_pace": {
        "cadence":             0.40,
        "stride_length":       0.35,
        "stride_time_cv":      0.25,
    },
    "joint_mechanics": {
        "hip_rotation_rom":    0.35,
        "ankle_pushoff_proxy": 0.40,
        "vertical_oscillation":0.25,
    },
}

# Domain validation
assert abs(sum(DOMAIN_WEIGHTS.values()) - 1.0) < 1e-6, "DOMAIN_WEIGHTS must sum to 1.0"
for _domain, _metrics in METRIC_DOMAIN_MAP.items():
    assert abs(sum(_metrics.values()) - 1.0) < 1e-6, f"{_domain} metric weights must sum to 1.0"

_NORMS_DATA: dict[str, dict] = {}
_METRIC_CONFIGS: dict[str, dict] = {}

def _load_data() -> None:
    """Pre-load all norm parameters recursively at import time."""
    if _NORMS_DATA:
        return
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "norms_data")
    if not os.path.exists(data_dir):
        return
        
    for filename in os.listdir(data_dir):
        if filename.endswith(".json"):
            domain = filename[:-5]
            with open(os.path.join(data_dir, filename), "r") as f:
                data = json.load(f)
                _NORMS_DATA[domain] = data.get("metrics", {})
                for metric, config in _NORMS_DATA[domain].items():
                    _METRIC_CONFIGS[metric] = config

_load_data()

def get_age_group(bio_age: int) -> str:
    """Map bio_age to decade key: 20/30/40/50/60/70"""
    if bio_age < 30: return "20"
    if bio_age < 40: return "30"
    if bio_age < 50: return "40"
    if bio_age < 60: return "50"
    if bio_age < 70: return "60"
    return "70"


def get_norm(metric_name: str, age_group: str) -> dict:
    """Return {"mean": float, "sd": float, "min_healthy": float, "max_healthy": float}
       Raise ValueError if metric or age_group not found."""
    if metric_name not in _METRIC_CONFIGS:
        raise ValueError(f"Metric {metric_name} not found")
        
    metric_config = _METRIC_CONFIGS[metric_name]
    groups = metric_config.get("groups", {})
    
    if age_group not in groups:
        raise ValueError(f"Age group {age_group} not found for metric {metric_name}")
        
    norm_val = groups[age_group]
    return {
        "mean": norm_val.get("mean"),
        "sd": norm_val.get("sd"),
        "min_healthy": norm_val.get("min_healthy"),
        "max_healthy": norm_val.get("max_healthy"),
        "lower_is_better": metric_config.get("lower_is_better", False),
        "deviation_metric": metric_config.get("deviation_metric", False)
    }


def list_all_metrics() -> list[str]:
    """Return flat list of all metric names across all domains."""
    metrics = set()
    for domain_metrics in METRIC_DOMAIN_MAP.values():
        metrics.update(domain_metrics.keys())
    return list(metrics)

def get_domain_for_metric(metric_name: str) -> str:
    """Return domain name for a given metric. Raise if not found."""
    domains = [d for d, m in METRIC_DOMAIN_MAP.items() if metric_name in m]
    if not domains:
        raise ValueError(f"Metric {metric_name} not found in any domain")
    return domains[0]
