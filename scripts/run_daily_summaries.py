#!/usr/bin/env python3
import os
import sys
import yaml
import argparse
from pathlib import Path
from datetime import datetime, timedelta, time
from filelock import FileLock, Timeout
import logging

# Añadir el directorio raíz al path para poder importar desde 'app'
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.models import schemas
from app.services import summarizer
from app.services.group_service import get_group_memory_path, _load_group_settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def should_run_summary(group_id: str, state: dict) -> bool:
    """
    Comprueba si se debe generar un resumen para un grupo basado en la configuración
    de su perfil y si ya se ha generado uno hoy.
    """
    group_settings = _load_group_settings(group_id)
    summary_time_str = group_settings.get("daily_summary_time_utc")

    if not summary_time_str:
        logging.info(f"[{group_id}] No hay 'daily_summary_time_utc' configurado. Saltando.")
        return False

    try:
        summary_time = time.fromisoformat(summary_time_str)
    except ValueError:
        logging.warning(f"[{group_id}] Formato de hora inválido para 'daily_summary_time_utc': {summary_time_str}. Saltando.")
        return False

    now_utc = datetime.utcnow()

    # Comprobar si ya se generó un resumen hoy
    meta = state.get("meta", {})
    last_summary_ts_str = meta.get("last_daily_summary_ts")
    if last_summary_ts_str:
        last_summary_ts = datetime.fromisoformat(last_summary_ts_str)
        if last_summary_ts.date() == now_utc.date():
            logging.info(f"[{group_id}] El resumen diario ya se generó hoy. Saltando.")
            return False

    # Comprobar si estamos en la ventana de tiempo para generar el resumen (e.g., +/- 15 min)
    run_window_start = datetime.combine(now_utc.date(), summary_time) - timedelta(minutes=15)
    run_window_end = datetime.combine(now_utc.date(), summary_time) + timedelta(minutes=15)

    if not (run_window_start <= now_utc <= run_window_end):
        logging.debug(f"[{group_id}] Fuera de la ventana de tiempo para el resumen. Hora actual: {now_utc.time()}, Hora configurada: {summary_time}")
        return False

    return True

def process_group(group_id: str):
    """
    Genera y guarda un resumen diario para un grupo específico si se cumplen las condiciones.
    """
    logging.info(f"Procesando grupo: {group_id}")
    filepath = get_group_memory_path(group_id)
    if not filepath.exists():
        logging.warning(f"No se encontró el fichero de memoria para el grupo {group_id}. Saltando.")
        return

    lock_path = filepath.with_suffix(".yaml.lock")
    try:
        with FileLock(lock_path, timeout=10):
            with open(filepath, "r", encoding="utf-8") as f:
                state = yaml.safe_load(f) or {}

            if not should_run_summary(group_id, state):
                return

            logging.info(f"[{group_id}] Generando resumen diario...")

            # Filtrar logs de las últimas 24 horas
            since_ts = datetime.utcnow() - timedelta(hours=24)
            recent_logs = [
                r for r in state.get("log", [])
                if datetime.fromisoformat(r.get("ts", "1970-01-01T00:00:00")).replace(tzinfo=None) > since_ts
            ]

            if not recent_logs:
                logging.info(f"[{group_id}] No hay logs recientes para resumir. Saltando.")
                return

            summary_details_data = summarizer.generate_daily_summary(recent_logs)
            summary_details = schemas.DailySummaryDetails(**summary_details_data)
            summary_record = schemas.DailySummaryRecord(details=summary_details)

            state.setdefault("log", []).append(summary_record.model_dump(mode='json'))
            state.setdefault("meta", {})["last_daily_summary_ts"] = datetime.utcnow().isoformat()

            with open(filepath, "w", encoding="utf-8") as f:
                yaml.dump(state, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            logging.info(f"[{group_id}] Resumen diario guardado con éxito.")

    except Timeout:
        logging.error(f"No se pudo adquirir el bloqueo para el grupo {group_id} en 10 segundos.")
    except Exception as e:
        logging.error(f"Error inesperado procesando el grupo {group_id}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Genera resúmenes diarios para grupos de RLx.")
    parser.add_argument("--group_id", help="Procesar solo un grupo específico.", type=str)
    args = parser.parse_args()

    groups_dir = Path("local_bundle/groups")

    if args.group_id:
        process_group(args.group_id)
    else:
        logging.info("Procesando todos los grupos...")
        if not groups_dir.exists():
            logging.warning(f"El directorio de grupos '{groups_dir}' no existe.")
            return
        for group_file in groups_dir.glob("*.yaml"):
            group_id = group_file.stem
            process_group(group_id)

if __name__ == "__main__":
    main()
