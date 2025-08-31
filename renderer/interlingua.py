import re

# Umbral de arousal a partir del cual se reduce el número de opciones.
# Un valor de 1.5 es coherente con AROUSAL_SPIKE_THRESHOLD.
AROUSAL_THRESHOLD_FOR_FEWER_OPTIONS = 1.5

def build_structure(text: str, affective_context: dict | None = None) -> dict:
    """
    Convierte un texto plano en una estructura de datos neutral (Interlingua)
    con 'bullets' y 'options', ajustando el número de opciones según el
    contexto afectivo (Affective Proxy).

    Reglas deterministas:
    - El número máximo de opciones por defecto es 3 (Ley de Hick).
    - Si el 'arousal_z' en el contexto afectivo supera un umbral, el máximo
      de opciones se reduce a 2 para disminuir la carga cognitiva.
    - Las listas con un número de ítems inferior o igual al máximo permitido
      se clasifican como 'options'. El resto, como 'bullets'.
    """
    list_items = []
    paragraphs = []
    bullets = []
    options = []

    # Determinar el número máximo de opciones según el contexto afectivo.
    max_options = 3
    if affective_context and affective_context.get('group_arousal_z', 0.0) > AROUSAL_THRESHOLD_FOR_FEWER_OPTIONS:
        max_options = 2  # Reducir la carga cognitiva en momentos de alta tensión.

    option_pattern = re.compile(r"^\s*([*-]|\d+\.|\w\))\s+.*", re.UNICODE)
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]

    for line in lines:
        if option_pattern.match(line):
            list_items.append(line)
        else:
            paragraphs.append(line)

    # Aplicar la Ley de Hick adaptativa.
    if 0 < len(list_items) <= max_options:
        options = list_items
        bullets = paragraphs
    else:
        # Si hay más ítems que el máximo permitido, o no hay ninguno, todo es parte del resumen.
        bullets = paragraphs + list_items

    return {
        "bullets": bullets,
        "options": options,
        "alerts": [],
    }
