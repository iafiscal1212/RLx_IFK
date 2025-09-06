from pathlib import Path
from app.core.utils import BUNDLE, yaml_load

DEFAULT_THRESHOLD = 1.5


def get_threshold_z() -> float:
    p = BUNDLE / "ethics" / "policies.yaml"
    data = yaml_load(p) or {}
    try:
        return float(data.get("alerts", {}).get("arousal_spike_detected", {}).get("threshold_z", DEFAULT_THRESHOLD))
    except Exception:
        return DEFAULT_THRESHOLD
