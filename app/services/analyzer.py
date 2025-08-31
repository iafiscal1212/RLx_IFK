import re
import math

# Mini-léxicos para análisis de valencia e incertidumbre (100% local)
VALENCE_POSITIVE_WORDS = {"bien", "gracias", "genial", "perfecto", "acuerdo", "claro", "sí", "ok", "vale", "buena"}
VALENCE_NEGATIVE_WORDS = {"mal", "no", "problema", "pero", "difícil", "nunca", "atasco", "bloqueo", "duda"}
UNCERTAINTY_WORDS = {"quizás", "tal vez", "posiblemente", "supongo", "creo", "podría", "parece"}

# Expresiones regulares pre-compiladas para eficiencia
UPPERCASE_RE = re.compile(r'\b[A-Z]{3,}\b')
ELONGATION_RE = re.compile(r'([a-zA-Z])\1{2,}')

def calculate_raw_signals(text: str) -> dict:
    """
    Calcula las señales afectivas brutas de un texto.
    Cumple con ZTL: solo usa regex y conteo de palabras.
    """
    text_lower = text.lower()
    words = set(re.findall(r'\b\w+\b', text_lower))

    # --- Arousal (Excitación) ---
    # Señales: mayúsculas, exclamaciones, interrogaciones, elongaciones.
    arousal = 0
    arousal += len(UPPERCASE_RE.findall(text))
    arousal += text.count('!')
    arousal += text.count('?')
    arousal += len(ELONGATION_RE.findall(text_lower))

    # --- Valence (Positividad/Negatividad) ---
    # Señales: palabras de léxicos positivo/negativo.
    valence = 0
    valence += len(words.intersection(VALENCE_POSITIVE_WORDS))
    valence -= len(words.intersection(VALENCE_NEGATIVE_WORDS))

    # --- Uncertainty (Incertidumbre) ---
    # Señales: palabras modales o de duda.
    uncertainty = len(words.intersection(UNCERTAINTY_WORDS))

    return {
        "raw_arousal": float(arousal),
        "raw_valence": float(valence),
        "raw_uncertainty": float(uncertainty)
    }

def sigmoid(x: float) -> float:
    """Función sigmoide para normalizar la carga emocional entre 0 y 1."""
    # Se usa un clip para evitar overflow con valores grandes
    return 1 / (1 + math.exp(-max(-700, min(x, 700))))

def calculate_emotional_load(arousal_z: float, valence_z: float, uncertainty_z: float) -> float:
    """
    Calcula la carga emocional (E_user) según la fórmula del libro blanco.
    E_user = σ(0.5·Z_A − 0.3·Z_V + 0.2·Z_U)
    """
    combined_signal = (0.5 * arousal_z) - (0.3 * valence_z) + (0.2 * uncertainty_z)
    return sigmoid(combined_signal)
