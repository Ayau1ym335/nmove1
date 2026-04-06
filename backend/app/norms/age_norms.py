from dataclasses import dataclass
from typing import Optional

@dataclass
class NormValue:
    """Represents a specific metric norm for a given age bracket."""
    mean: float
    sd: float
    min_healthy: Optional[float] = None
    max_healthy: Optional[float] = None

@dataclass
class MetricConfig:
    """Specifies metric evaluation polarity and age group mappings."""
    lower_is_better: bool
    deviation_metric: bool
    groups: dict[str, NormValue]
