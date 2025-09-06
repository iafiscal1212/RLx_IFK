import re
from pathlib import Path
from typing import Any, Dict
import yaml

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "local_bundle"


def validate_group_id(group_id: str) -> str:
    if not re.fullmatch(r"[a-z0-9\-]+", group_id):
        raise ValueError("invalid group id: use lowercase, digits, hyphen")
    return group_id


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def yaml_load(p: Path) -> Any:
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) if f.readable() else None


def yaml_dump(p: Path, data: Any) -> None:
    ensure_dir(p.parent)
    with p.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
