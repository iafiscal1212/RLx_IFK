import re
from collections import Counter
from datetime import datetime, timedelta

# Stopwords simples por idioma. En un sistema real, esto podría ser más completo.
STOPWORDS = {
    "es": {
        "a", "ante", "bajo", "con", "contra", "de", "desde", "en", "entre", "hacia", "hasta", "para", "por", "según",
        "sin", "sobre", "tras", "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "pero", "si", "que",
        "no", "es", "del", "al", "se", "lo", "su", "me", "le", "les"
    },
    "en": {
        "and", "the", "is", "in", "it", "of", "to", "for", "with", "on", "at", "by", "an", "a", "that", "this",
        "we", "you", "he", "she", "they", "are", "was", "were", "be", "i", "as", "not", "if", "or", "but"
    }
}

DECISION_KEYWORDS = {
    "es": [
        "acuerdo:", "decisión:", "acordado:", "decidido:", "aprobado:"
    ],
    "en": [
        "decision:", "approved:", "agreement:", "decided:"
    ]
}

# Patrones para detectar acciones asignadas. {user_names_re} se reemplazará dinámicamente.
ACTION_PATTERNS = {
    "es": [
        r"(?P<assignee>{user_names_re})\s+(se encargará de|es responsable de|hará|revisará)\s+(?P<task>.+)",
        r"acción para (?P<assignee>{user_names_re}):\s+(?P<task>.+)",
        r"asignado a (?P<assignee>{user_names_re}):\s+(?P<task>.+)",
    ],
    "en": [
        r"(?P<assignee>{user_names_re})\s+(will handle|is responsible for|will review|will do)\s+(?P<task>.+)",
        r"action for (?P<assignee>{user_names_re}):\s+(?P<task>.+)",
        r"assigned to (?P<assignee>{user_names_re}):\s+(?P<task>.+)",
    ]
}

def _simple_stem_es(word: str) -> str:
    """
    Un stemmer muy básico para español, ZTL-compliant.
    Reduce plurales y algunas terminaciones verbales comunes.
    """
    if len(word) > 5 and word.endswith(('ando', 'iendo')):
        return word[:-4]
    if len(word) > 4 and (word.endswith('aron') or word.endswith('ieron')):
        return word[:-4]
    if len(word) > 3 and (word.endswith('ar') or word.endswith('er') or word.endswith('ir')):
        return word[:-2]
    if len(word) > 2 and word.endswith('es'):
        return word[:-2]
    if len(word) > 1 and word.endswith('s'):
        return word[:-1]
    return word

def _simple_stem_en(word: str) -> str:
    """Un stemmer muy básico para inglés, ZTL-compliant."""
    if len(word) > 4 and word.endswith('ing'):
        return word[:-3]
    if len(word) > 3 and word.endswith('ed'):
        return word[:-2]
    if len(word) > 2 and word.endswith('es'):
        return word[:-2]
    if len(word) > 1 and word.endswith('s'):
        return word[:-1]
    return word

STEMMERS = {"es": _simple_stem_es, "en": _simple_stem_en}

def _multilang_stem(word: str, lang: str) -> str:
    return STEMMERS.get(lang, lambda w: w)(word)

def _extract_topics(texts: list[str], lang: str, top_n: int = 5) -> list[str]:
    """Extrae los temas más comunes de una lista de textos usando un stemmer específico del idioma."""
    if not texts:
        return []

    stopwords_for_lang = STOPWORDS.get(lang, set())
    full_text = " ".join(texts).lower()
    words = re.findall(r'\b\w{3,}\b', full_text) # Palabras de 3 o más letras

    # Mapea cada raíz (stem) a las palabras originales que la generaron.
    stem_to_words = {}
    for word in words:
        if word in stopwords_for_lang:
            continue
        stem = _multilang_stem(word, lang)
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

def _extract_decisions(records: list[dict], lang: str) -> list[str]:
    """Extrae decisiones de una lista de registros de log."""
    decisions = []
    keywords_for_lang = DECISION_KEYWORDS.get(lang, [])

    for record in records:
        text = record.get("text", "").lower()
        for keyword in keywords_for_lang:
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

def _extract_actions(records: list[dict], lang: str, user_names: list[str]) -> list[dict]:
    """Extrae acciones asignadas de una lista de registros, usando los nombres de los usuarios."""
    if not user_names:
        return []

    actions = []
    patterns_for_lang = ACTION_PATTERNS.get(lang, [])

    # Crea una expresión regular que busca cualquiera de los nombres de usuario.
    user_names_re = '|'.join(re.escape(name) for name in user_names)

    compiled_patterns = [
        re.compile(pattern.format(user_names_re=user_names_re), re.IGNORECASE)
        for pattern in patterns_for_lang
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

def generate_daily_summary(log_records: list[dict], lang: str = "es", user_names: list[str] | None = None) -> dict:
    """Genera un resumen diario a partir de los registros de log."""
    messages = [r for r in log_records if r.get("type") == "message"]
    message_texts = [msg.get("text", "") for msg in messages]

    topics = _extract_topics(message_texts, lang=lang)
    decisions = _extract_decisions(messages, lang=lang)
    actions = _extract_actions(messages, lang=lang, user_names=user_names or [])

    return {"topics": topics, "decisions": decisions, "actions": actions, "message_count": len(messages)}
