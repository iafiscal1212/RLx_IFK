import os
import yaml
from pathlib import Path
from datetime import datetime

from ..models import schemas
from . import analyzer

# Directorio donde se guardará la memoria persistente.
# Debe estar fuera del código fuente, como se especifica en la arquitectura.
MEMORY_DIR = Path("local_bundle/groups")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# Umbral definido en la política de ética (ethics/policies.yaml)
AROUSAL_SPIKE_THRESHOLD = 1.5

def get_group_memory_path(group_id: str) -> Path:
    """Construye la ruta al fichero YAML de memoria para un grupo."""
    # Validar group_id para evitar path traversal
    if not group_id.isalnum() or ".." in group_id or "/" in group_id:
        raise ValueError("ID de grupo no válido.")
    return MEMORY_DIR / f"{group_id}.yaml"

def persist_message(group_id: str, message: schemas.MessageIngest):
    """
    Añade un mensaje al log de un grupo en su fichero YAML.
    """
    filepath = get_group_memory_path(group_id)

    # Carga el estado actual, o crea uno nuevo si no existe
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {
            "meta": {"group_id": group_id, "created": datetime.utcnow().isoformat()},
            "log": [],
            "user_stats": {}
        }

    # --- 1. Análisis Afectivo (Affective Proxy) ---
    raw_signals = analyzer.calculate_raw_signals(message.text)

    # --- 2. Normalización y actualización de estadísticas del usuario (EWMA) ---
    user_id = message.author
    state.setdefault("user_stats", {}).setdefault(user_id, {
        "ewma_arousal": 0.0, "ewma_valence": 0.0, "ewma_uncertainty": 0.0,
        "ewma_arousal_sq": 0.0, "ewma_valence_sq": 0.0, "ewma_uncertainty_sq": 0.0,
        "count": 0
    })
    stats = state["user_stats"][user_id]
    alpha = 0.1  # Factor de suavizado, como en el libro blanco

    # Actualizar medias y varianzas con EWMA
    z_scores = {}
    for key in ["arousal", "valence", "uncertainty"]:
        raw_val = raw_signals[f"raw_{key}"]
        # Actualizar media
        stats[f"ewma_{key}"] = alpha * raw_val + (1 - alpha) * stats[f"ewma_{key}"]
        # Actualizar varianza (usando la media de los cuadrados)
        stats[f"ewma_{key}_sq"] = alpha * (raw_val ** 2) + (1 - alpha) * stats[f"ewma_{key}_sq"]

        # Calcular Z-score
        std_dev = (stats[f"ewma_{key}_sq"] - stats[f"ewma_{key}"] ** 2) ** 0.5
        z_scores[f"{key}_z"] = (raw_val - stats[f"ewma_{key}"]) / (std_dev + 1e-6) # Evitar división por cero

    stats["count"] += 1

    # --- 3. Calcular Carga Emocional y preparar el registro ---
    e_user = analyzer.calculate_emotional_load(z_scores["arousal_z"], z_scores["valence_z"], z_scores["uncertainty_z"])
    affective_proxy_data = schemas.AffectiveProxy(**raw_signals, **z_scores, e_user=e_user)
    record = schemas.MessageRecord(**message.model_dump(), actor=message.author, affective_proxy=affective_proxy_data)

    state.setdefault("log", []).append(record.model_dump(mode='json'))

    # --- 4. Comprobar Políticas Éticas ---
    # Si el arousal normalizado supera el umbral, se registra una alerta.
    if record.affective_proxy and record.affective_proxy.arousal_z > AROUSAL_SPIKE_THRESHOLD:
        alert_details = schemas.AlertDetails(
            value=round(record.affective_proxy.arousal_z, 4),
            threshold=AROUSAL_SPIKE_THRESHOLD,
            rationale="El nivel de excitación (arousal) del mensaje supera el umbral normalizado para este usuario."
        )
        alert_record = schemas.AlertRecord(
            trigger_ref=record.msg_id,
            details=alert_details
        )
        state["log"].append(alert_record.model_dump(mode='json'))

    # Guarda el estado actualizado
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

def get_group_state(group_id: str):
    """Lee y devuelve el estado completo de un grupo desde su YAML."""
    filepath = get_group_memory_path(group_id)
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
