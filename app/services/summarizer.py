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

# Patrones para detectar acciones asignadas. {user_names_re} se reemplazará dinámicamente.
ACTION_PATTERNS = [
    r"(?P<assignee>{user_names_re})\s+(se encargará de|es responsable de|hará|revisará|will handle|is responsible for)\s+(?P<task>.+)",
    r"acción para (?P<assignee>{user_names_re}):\s+(?P<task>.+)",
    r"asignado a (?P<assignee>{user_names_re}):\s+(?P<task>.+)",
]

def _simple_stem(word: str) -> str:
    """
    Un stemmer muy básico para español, ZTL-compliant.
    Reduce plurales y algunas terminaciones verbales comunes.
    """
    # Es más eficiente comprobar las terminaciones más largas primero.
    if len(word) > 5 and word.endswith(('ando', 'iendo')):
        return word[:-4]
    if len(word) > 4 and (word.endswith('aron') or word.endswith('ieron')):
        return word[:-4]
    if len(word) > 3 and (word.endswith('ar') or word.endswith('er') or word.endswith('ir')):
        return word[:-2]
    if len(word) > 3 and word.endswith('es'):
        return word[:-2]
    if len(word) > 2 and word.endswith('s'):
        return word[:-1]
    return word

def _extract_topics(texts: list[str], top_n: int = 5) -> list[str]:
    """Extrae los temas más comunes de una lista de textos usando stemming simple."""
    if not texts:
        return []

    full_text = " ".join(texts).lower()
    words = re.findall(r'\b\w{3,}\b', full_text) # Palabras de 3 o más letras

    # Mapea cada raíz (stem) a las palabras originales que la generaron.
    stem_to_words = {}
    for word in words:
        if word in STOPWORDS:
            continue
        stem = _simple_stem(word)
        if stem not in stem_to_words:
            stem_to_words[stem] = Counter()
        stem_to_words[stem][word] += 1

    # Calcula el recuento total para cada raíz.
    stem_counts = {stem: sum(counts.values()) for stem, counts in stem_to_words.items()}

    # Ordena las raíces por su frecuencia total.
    sorted_stems = sorted(stem_counts, key=stem_counts.get, reverse=True)

    # Para los temas principales, elige la palabra original más común para esa raíz.
    top_topics = [stem_to_words[stem].most_common(1)[0][0] for stem in sorted_stems[:top_n]]

    return top_topics

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

def _extract_actions(records: list[dict], user_names: list[str]) -> list[dict]:
    """Extrae acciones asignadas de una lista de registros, usando los nombres de los usuarios."""
    if not user_names:
        return []

    actions = []
    # Crea una expresión regular que busca cualquiera de los nombres de usuario.
    user_names_re = '|'.join(re.escape(name) for name in user_names)

    compiled_patterns = [
        re.compile(pattern.format(user_names_re=user_names_re), re.IGNORECASE)
        for pattern in ACTION_PATTERNS
    ]

    for record in records:
        text = record.get("text", "")
        for line in text.split('\n'):
            for pat in compiled_patterns:
                match = pat.search(line)
                if match:
                    assignee = match.group('assignee').strip()
                    task = match.group('task').strip()
                    # Verificación final para asegurar que el asignado es un usuario válido
                    if assignee.lower() in [name.lower() for name in user_names]:
                         actions.append({"assignee": assignee, "task": task})
                         break  # Ir a la siguiente línea
            else:
                continue
            break # Ir al siguiente mensaje si se encontró una acción en la línea
    return actions

def generate_daily_summary(log_records: list[dict], user_names: list[str] | None = None) -> dict:
    """Genera un resumen diario a partir de los registros de log."""
    messages = [r for r in log_records if r.get("type") == "message"]
    message_texts = [msg.get("text", "") for msg in messages]

    topics = _extract_topics(message_texts)
    decisions = _extract_decisions(messages)
    actions = _extract_actions(messages, user_names or [])

    return {"topics": topics, "decisions": decisions, "actions": actions, "message_count": len(messages)}
