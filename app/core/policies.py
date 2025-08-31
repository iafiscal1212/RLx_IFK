import yaml
from pathlib import Path

# Valor por defecto en caso de que el fichero de políticas no exista o esté mal formado.
DEFAULT_AROUSAL_THRESHOLD = 1.5

def load_arousal_threshold() -> float:
    """Carga el umbral de 'arousal spike' desde el fichero de políticas éticas."""
    policy_path = Path("ethics/policies.yaml")
    if not policy_path.is_file():
        return DEFAULT_AROUSAL_THRESHOLD
    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            policies = yaml.safe_load(f)
        # Navega la estructura del YAML de forma segura para obtener el valor.
        return float(policies['alerts']['arousal_spike_detected']['threshold_z'])
    except (IOError, yaml.YAMLError, KeyError, TypeError, ValueError):
        return DEFAULT_AROUSAL_THRESHOLD

# El umbral se carga una sola vez cuando se importa el módulo.
AROUSAL_SPIKE_THRESHOLD = load_arousal_threshold()
