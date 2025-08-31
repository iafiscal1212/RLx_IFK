from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status

from ..core.config import MAX_UPLOAD_SIZE_BYTES
from ..core.utils import sanitize_filename, validate_group_id

router = APIRouter(
    prefix="/files",
    tags=["files"],
)

UPLOADS_DIR = Path("local_bundle/uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/{group_id}/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(group_id: str, file: UploadFile = File(...)):
    """
    Sube un archivo a un directorio seguro asociado a un grupo.
    - Valida el ID del grupo para evitar path traversal.
    - Sanitiza el nombre del archivo.
    - Limita el tamaño máximo del archivo.
    - Evita sobrescribir archivos existentes.
    """
    try:
        validate_group_id(group_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    target_dir = UPLOADS_DIR / group_id
    target_dir.mkdir(exist_ok=True)

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se proporcionó un nombre de archivo.")

    safe_filename = sanitize_filename(file.filename)
    if not safe_filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre del archivo no es válido.")

    filepath = target_dir / safe_filename
    if filepath.exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"El archivo '{safe_filename}' ya existe.")

    bytes_written = 0
    try:
        with open(filepath, "wb") as buffer:
            # Lee el archivo en trozos para no consumir toda la RAM con archivos grandes.
            while chunk := await file.read(8192):
                if bytes_written + len(chunk) > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"El archivo supera el tamaño máximo de {MAX_UPLOAD_SIZE_BYTES // 1024 // 1024} MB.")
                buffer.write(chunk)
                bytes_written += len(chunk)
    except Exception:
        # Si algo falla (ej. límite de tamaño), borramos el archivo parcial.
        if filepath.exists():
            filepath.unlink()
        raise # Re-lanza la excepción original (ej. HTTP 413)

    return { "filename": safe_filename, "path": str(filepath), "bytes": bytes_written }
