import re
from collections import Counter
from datetime import datetime, timedelta

# Stopwords simples para español e inglés. En un sistema real, esto podría ser más completo.
STOPWORDS = {
    "a", "ante", "bajo", "con", "contra", "de", "desde", "en", "entre", "hacia", "hasta", "para", "por", "según",
    "sin", "sobre", "tras", "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "pero", "si", "que",
    "no", "es", "del", "al", "se", "lo", "su", "me", "le", "les", "and", "the", "is", "in", "it", "of", "to",
    "for", "with", "on", "at", "by", "an", "a", "that", "this", "we", "you", "he", "she", "they", "are", "was",
    "were", "be", "i", "as", "not", "if", "or", "but"
}

DECISION_KEYWORDS = [
    "acuerdo:", "decisión:", "acordado:", "decidido:", "aprobado:",
    "decision:", "approved:", "agreement:"
]

def _extract_topics(texts: list[str], top_n: int = 5) -> list[str]:
    """Extrae los temas más comunes de una lista de textos."""
    if not texts:
        return []

    full_text = " ".join(texts).lower()
    words = re.findall(r'\b\w{3,}\b', full_text) # Palabras de 3 o más letras

    word_counts = Counter(word for word in words if word not in STOPWORDS)

    return [word for word, count in word_counts.most_common(top_n)]

def _extract_decisions(records: list[dict]) -> list[str]:
    """Extrae decisiones de una lista de registros de log."""
    decisions = []
    for record in records:
        text = record.get("text", "").lower()
        for keyword in DECISION_KEYWORDS:
            if keyword in text:
                # Extrae la línea o frase que contiene la palabra clave
                for line in record.get("text", "").split('\n'):
                    if keyword in line.lower():
                        decision_text = line.strip()
                        # Limpiar la palabra clave para una mejor legibilidad
                        clean_decision = re.sub(f'(?i){keyword}', '', decision_text, 1).strip()
                        if clean_decision:
                            decisions.append(clean_decision)
                break # Pasar al siguiente mensaje una vez encontrada una decisión
    return decisions

def generate_daily_summary(log_records: list[dict]) -> dict:
    """Genera un resumen diario a partir de los registros de log."""
    messages = [r for r in log_records if r.get("type") == "message"]
    message_texts = [msg.get("text", "") for msg in messages]

    topics = _extract_topics(message_texts)
    decisions = _extract_decisions(messages)

    return {"topics": topics, "decisions": decisions, "message_count": len(messages)}
