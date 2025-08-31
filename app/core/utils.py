import re

# Una expresión regular estricta para nombres de archivo seguros.
# Permite letras (incluyendo Unicode), números, guiones bajos, guiones y puntos.
_filename_re = re.compile(r"[^a-zA-Z0-9._-]")

def sanitize_filename(filename: str) -> str:
    """
    Sanitiza un nombre de archivo para prevenir ataques de path traversal.
    Reemplaza caracteres no seguros por guiones bajos.
    """
    # Reemplaza cualquier caracter no permitido por un guion bajo.
    sanitized = _filename_re.sub("_", filename)
    # Colapsa múltiples puntos o guiones bajos para evitar ofuscación.
    sanitized = re.sub(r"_{2,}", "_", sanitized)
    sanitized = re.sub(r"\.{2,}", ".", sanitized)
    # Elimina caracteres peligrosos al inicio o final del nombre.
    return sanitized.strip("._")

def validate_group_id(group_id: str):
    """Valida un ID de grupo para asegurar que es un nombre de directorio seguro."""
    if not group_id.isalnum() or ".." in group_id or "/" in group_id:
        raise ValueError(f"ID de grupo no válido: '{group_id}'")
