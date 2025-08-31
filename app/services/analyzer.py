import math
from datetime import datetime

ELONG_MIN = 3
TAU_GAP_S = 300.0

def _gap_factor(last_ts: datetime | None, ts: datetime) -> float:
    if not last_ts:
        return 0.0
    dt = (ts - last_ts).total_seconds()
    return math.exp(-dt / TAU_GAP_S)

def calculate_raw_signals(text: str) -> dict:
    letters = [c for c in text if c.isalpha()]
    n_letters = max(len(letters), 1)
    raw_arousal = (text.count("!") + text.count("?")) / max(len(text), 1)
    raw_caps = sum(1 for c in letters if c.isupper()) / n_letters
    raw_elong = sum(1 for w in text.split() if len(set(w)) < len(w) and any(w.count(ch) >= ELONG_MIN for ch in set(w))) / max(len(text.split()), 1)
    return {"raw_arousal": raw_arousal, "raw_caps": raw_caps, "raw_elong": raw_elong}

def calculate_emotional_load(a_z: float, v_z: float, u_z: float) -> float:
    x = 0.5 * a_z - 0.3 * v_z + 0.2 * u_z
    return 1.0 / (1.0 + math.exp(-x))
