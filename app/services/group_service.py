import os
import yaml
import logging
from pathlib import Path
import statistics
from datetime import datetime, timedelta
from filelock import FileLock, Timeout

from ..models import schemas
from . import analyzer
from ..core.utils import validate_group_id
from ..core.policies import AROUSAL_SPIKE_THRESHOLD

from functools import lru_cache
# Constantes para la política de sugerencia de pausa
SUSTAINED_AROUSAL_WINDOW_MIN = 60  # Analizar la última hora
SUSTAINED_AROUSAL_SUB_WINDOWS = 3  # Dividida en 3 sub-ventanas de 20 min
SUSTAINED_AROUSAL_THRESHOLD = 1.4  # Umbral para tensión sostenida (ligeramente inferior al de pico)
PAUSE_SUGGESTION_COOLDOWN_MIN = 30 # No sugerir una pausa más de una vez cada 30 minutos
DEFAULT_PAUSE_DURATION_MIN = 5     # Duración por defecto de la pausa sugerida

# Directorio donde se guardará la memoria persistente.
# Debe estar fuera del código fuente, como se especifica en la arquitectura.
MEMORY_DIR = Path("local_bundle/groups")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# Directorio de perfiles
PROFILES_DIR = Path("profiles")
PROFILES_DIR.mkdir(exist_ok=True)

@lru_cache(maxsize=16)
def _load_group_profile(group_id: str) -> dict:
    """Carga el perfil completo de un grupo desde profiles/groups.yaml."""
    profiles_path = PROFILES_DIR / "groups.yaml"
    if not profiles_path.exists():
        return {}
    try:
        with open(profiles_path, "r", encoding="utf-8") as f:
            all_groups = yaml.safe_load(f) or {}
        return all_groups.get(group_id, {})
    except (IOError, yaml.YAMLError):
        return {}

@lru_cache(maxsize=16)
def _load_group_settings(group_id: str) -> dict:
    """Carga la sección 'companion_settings' de un grupo."""
    profile = _load_group_profile(group_id)
    return profile.get("companion_settings", {})

def get_group_memory_path(group_id: str) -> Path:
    """Construye la ruta al fichero YAML de memoria para un grupo."""
    validate_group_id(group_id)
    return MEMORY_DIR / f"{group_id}.yaml"

def create_group(group_id: str) -> Path:
    """
    Crea un nuevo fichero de memoria para un grupo si no existe.
    Devuelve la ruta al fichero creado.
    """
    filepath = get_group_memory_path(group_id)
    if filepath.exists():
        raise FileExistsError(f"El proyecto '{group_id}' ya existe.")

    # Crear el fichero con un estado inicial mínimo
    initial_state = {
        "meta": {"group_id": group_id, "created": datetime.utcnow().isoformat()},
        "log": [],
        "user_stats": {}
    }
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(initial_state, f, default_flow_style=False, allow_unicode=True)
    except IOError as e:
        raise IOError(f"No se pudo crear el fichero del proyecto: {e}") from e

    return filepath

def persist_message(group_id: str, message: schemas.MessageIngest):
    """
    Añade un mensaje al log de un grupo en su fichero YAML.
    Utiliza un bloqueo de fichero para evitar condiciones de carrera.
    """
    filepath = get_group_memory_path(group_id)
    lock_path = filepath.with_suffix(".yaml.lock")

    try:
        with FileLock(lock_path, timeout=5):
            # Carga el estado actual, o crea uno nuevo si no existe
            state = {}
            if filepath.exists():
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        state = yaml.safe_load(f) or {}
                except yaml.YAMLError as e:
                    logging.error(f"Fichero YAML corrupto para group_id={group_id}: {e}. Se creará uno nuevo.")
                    # Opcional: mover el fichero corrupto a una carpeta de cuarentena

            if not state:
                state = { "meta": {"group_id": group_id, "created": datetime.utcnow().isoformat()}, "log": [], "user_stats": {} }

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
                # Usar .get() para evitar fallos si el analizador aún no provee todas las señales
                raw_val = raw_signals.get(f"raw_{key}", 0.0)
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
            if record.affective_proxy and record.affective_proxy.arousal_z > AROUSAL_SPIKE_THRESHOLD:
                alert_details = schemas.AlertDetails(
                    value=round(record.affective_proxy.arousal_z, 4),
                    threshold=AROUSAL_SPIKE_THRESHOLD,
                    rationale="El nivel de excitación (arousal) del mensaje supera el umbral normalizado para este usuario."
                )
                alert_record = schemas.AlertRecord(trigger_ref=record.msg_id, details=alert_details)
                state["log"].append(alert_record.model_dump(mode='json'))

            # --- 5. Comprobar Políticas Proactivas ---
            # Esta función modificará el 'state' si es necesario.
            check_and_suggest_pause(group_id, state)

            # Guarda el estado actualizado
            with open(filepath, "w", encoding="utf-8") as f:
                yaml.dump(state, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    except Timeout:
        logging.error(f"No se pudo adquirir el bloqueo para el grupo {group_id} en 5 segundos.")
        raise

def get_group_state(group_id: str):
    """Lee y devuelve el estado completo de un grupo desde su YAML."""
    filepath = get_group_memory_path(group_id)
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_group_affective_state(group_id: str, window_minutes: int = 10) -> dict:
    """
    Calcula el estado afectivo agregado de un grupo (temperatura emocional)
    basándose en los mensajes recientes.
    """
    state = get_group_state(group_id)
    if not state or "log" not in state:
        return {"group_arousal_z": 0.0, "active_users": 0}

    now_utc = datetime.utcnow()
    recent_arousal_scores = []

    # Iterar sobre el log en orden inverso para encontrar mensajes recientes
    for record in reversed(state.get("log", [])):
        if record.get("type") != "message" or "affective_proxy" not in record:
            continue

        ts_str = record.get("ts")
        if not ts_str:
            continue

        try:
            # El timestamp en YAML es un string ISO. Lo convertimos a datetime naive UTC.
            ts_utc = datetime.fromisoformat(ts_str).replace(tzinfo=None)

            if (now_utc - ts_utc).total_seconds() / 60 > window_minutes:
                break  # Salir si el mensaje es más antiguo que la ventana de tiempo

            recent_arousal_scores.append(record["affective_proxy"]["arousal_z"])
        except (ValueError, TypeError):
            continue  # Ignorar registros con timestamp mal formado o tipo incorrecto

    if not recent_arousal_scores:
        return {"group_arousal_z": 0.0, "active_users": 0}

    # Usar la mediana para ser robusto a outliers (valores extremos de un solo mensaje)
    median_arousal = statistics.median(recent_arousal_scores)

    return {"group_arousal_z": median_arousal}

def get_affective_history(group_id: str, since_hours: int = 24) -> dict:
    """
    Recupera el historial de 'arousal_z' de un grupo para un período determinado.
    """
    state = get_group_state(group_id)
    if not state or "log" not in state:
        return {"history": []}

    history_points = []
    since_ts = datetime.utcnow() - timedelta(hours=since_hours)

    for record in state.get("log", []):
        if record.get("type") != "message" or "affective_proxy" not in record:
            continue

        try:
            ts = datetime.fromisoformat(record["ts"]).replace(tzinfo=None)
            if ts >= since_ts:
                history_points.append({
                    "ts": ts,
                    "value": record["affective_proxy"]["arousal_z"]
                })
        except (ValueError, TypeError):
            continue

    return {"history": history_points}

def check_and_suggest_pause(group_id: str, state: dict):
    """
    Comprueba si el arousal ha sido alto durante un período sostenido y, si es así,
    añade una sugerencia de pausa al estado. Incluye un mecanismo de cooldown.
    Los umbrales pueden ser personalizados por grupo.
    """
    # Cargar configuración personalizada del grupo, con fallback a los valores globales.
    group_settings = _load_group_settings(group_id)
    threshold = group_settings.get("sustained_arousal_threshold", SUSTAINED_AROUSAL_THRESHOLD)
    cooldown_min = group_settings.get("pause_suggestion_cooldown_min", PAUSE_SUGGESTION_COOLDOWN_MIN)
    pause_duration = group_settings.get("suggested_pause_duration_min", DEFAULT_PAUSE_DURATION_MIN)

    now = datetime.utcnow()
    meta = state.setdefault("meta", {})
    last_suggestion_ts_str = meta.get("last_pause_suggestion_ts")

    # 1. Comprobar Cooldown: No sugerir si ya se hizo recientemente.
    if last_suggestion_ts_str:
        last_suggestion_ts = datetime.fromisoformat(last_suggestion_ts_str)
        if (now - last_suggestion_ts).total_seconds() / 60 < cooldown_min:
            return  # En período de enfriamiento

    log = state.get("log", [])
    if not log:
        return

    # 2. Analizar sub-ventanas de tiempo para detectar tensión sostenida.
    window_start_ts = now - timedelta(minutes=SUSTAINED_AROUSAL_WINDOW_MIN)
    arousal_scores_in_window = [
        (datetime.fromisoformat(r["ts"]).replace(tzinfo=None), r["affective_proxy"]["arousal_z"])
        for r in log if r.get("type") == "message" and "affective_proxy" in r and datetime.fromisoformat(r["ts"]).replace(tzinfo=None) > window_start_ts
    ]

    sub_window_duration_sec = (SUSTAINED_AROUSAL_WINDOW_MIN / SUSTAINED_AROUSAL_SUB_WINDOWS) * 60
    all_sub_windows_high = True
    for i in range(SUSTAINED_AROUSAL_SUB_WINDOWS):
        sub_window_end = now - timedelta(seconds=i * sub_window_duration_sec)
        sub_window_start = now - timedelta(seconds=(i + 1) * sub_window_duration_sec)
        scores_in_sub = [score for ts, score in arousal_scores_in_window if sub_window_start <= ts < sub_window_end]
        if not scores_in_sub or statistics.median(scores_in_sub) < threshold:
            all_sub_windows_high = False
            break

    # 3. Si la condición se cumple, generar la sugerencia.
    if all_sub_windows_high:
        details = schemas.SuggestionDetails(
            rationale=f"El nivel de energía del grupo se ha mantenido elevado de forma constante durante los últimos {SUSTAINED_AROUSAL_WINDOW_MIN} minutos.",
            suggestion_text=f"He notado que la energía del grupo ha sido alta durante un tiempo. ¿Consideraríais tomar una breve pausa de {pause_duration} minutos para recargar?"
        )
        suggestion_record = schemas.SuggestionRecord(details=details)
        state.setdefault("log", []).append(suggestion_record.model_dump(mode='json'))
        meta["last_pause_suggestion_ts"] = now.isoformat()
