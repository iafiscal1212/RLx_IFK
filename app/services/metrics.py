import math
import re
from typing import List, Tuple

_EXCL = re.compile(r"!+")
_REPEAT = re.compile(r"(.)\1{2,}")  # letras repetidas 3+
_ALPHA = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]")


def _caps_ratio(text: str) -> float:
    letters = _ALPHA.findall(text)
    if not letters:
        return 0.0
    upp = sum(1 for ch in letters if ch.isupper())
    return min(1.0, upp / max(1, len(letters)))


def _excl_score(text: str) -> float:
    m = _EXCL.findall(text)
    if not m:
        return 0.0
    total = sum(len(s) for s in m)
    return min(1.0, total / 5.0)


def _elong_score(text: str) -> float:
    elong = 0
    for m in _REPEAT.finditer(text):
        run = len(m.group(0))
        elong += max(0, run - 2)
    return min(1.0, elong / 10.0)


def message_score(text: str) -> float:
    caps = _caps_ratio(text)
    exc = _excl_score(text)
    elo = _elong_score(text)
    # Ponderación determinista, sin ML
    return 0.5 * caps + 0.3 * exc + 0.2 * elo


def zscore(latest: float, history: List[float], window: int = 50) -> Tuple[float, int]:
    xs = (history + [latest])[-window:]
    n = len(xs)
    if n <= 1:
        return 0.0, n
    mu = sum(xs) / n
    var = sum((x - mu) ** 2 for x in xs) / (n - 1)
    sd = math.sqrt(var)
    if sd < 1e-6:
        return 0.0, n
    return (latest - mu) / sd, n