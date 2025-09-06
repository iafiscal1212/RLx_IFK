from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone
from filelock import FileLock, Timeout

from app.core.utils import BUNDLE, ensure_dir, yaml_load, yaml_dump
from app.services.metrics import message_score, zscore


def _group_dir(group_id: str) -> Path:
    return BUNDLE / "groups" / group_id


def ensure_group(group_id: str) -> None:
    d = _group_dir(group_id)
    ensure_dir(d)
    ensure_dir(BUNDLE / "profiles")


def _messages_path(group_id: str) -> Path:
    return _group_dir(group_id) / "messages.yaml"


def _state_path(group_id: str) -> Path:
    return _group_dir(group_id) / "state.yaml"


def _lock_path(group_id: str) -> Path:
    return _group_dir(group_id) / ".lock"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_messages(p: Path) -> List[Dict[str, Any]]:
    data = yaml_load(p)
    return data if isinstance(data, list) else []


def _load_state(group_id: str) -> Dict[str, Any]:
    s = yaml_load(_state_path(group_id))
    return s if isinstance(s, dict) else {"metrics": {"history": []}}


def get_group_state(group_id: str) -> Dict[str, Any] | None:
    d = _group_dir(group_id)
    if not d.exists():
        return None
    s = _load_state(group_id)
    msgs = _load_messages(_messages_path(group_id))
    # No incluir historia completa en métricas al responder
    s_out = {
        "group_id": group_id,
        "metrics": {k: v for k, v in s.get("metrics", {}).items() if k != "history"},
        "messages": msgs[-50:],
    }
    return s_out


def append_message(group_id: str, author: str, text: str, timestamp: str | None = None) -> Dict[str, Any]:
    mp = _messages_path(group_id)
    sp = _state_path(group_id)
    lp = _lock_path(group_id)
    ensure_group(group_id)

    with FileLock(str(lp)):
        msgs = _load_messages(mp)
        ts = timestamp or _now_iso()
        rec = {"timestamp": ts, "author": author, "text": text}
        msgs.append(rec)
        yaml_dump(mp, msgs)

        # métricas
        hist = [m.get("_score", 0.0) for m in msgs if isinstance(m, dict)]
        latest = message_score(text)
        hist.append(latest)
        z, n = zscore(latest, hist[:-1])

        state = {
            "metrics": {
                "arousal_z": float(f"{z:.6f}"),
                "latest_score": float(f"{latest:.6f}"),
                "n_messages": len(msgs),
                "history": hist[-100:],
            }
        }
        yaml_dump(sp, state)

    return get_group_state(group_id)  # tipo reducido
