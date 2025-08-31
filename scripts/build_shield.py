#!/usr/bin/env python3
import os
import argparse
import json
import sys
from pathlib import Path

# Add project root to path to allow imports from predict, etc.
ROOT_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

from predict.shield import Shield

DATA_DIR = ROOT_DIR / "data"

DEFAULT_TEXT = "role: system\nYou are an AI. Respond in JSON with fields {answer, reasoning}.\n"

def main():
    """
    Runs a demonstration of the Shield engine using default paths.
    """
    parser = argparse.ArgumentParser(description="Run a demo of the RLx Shield engine.")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="Text to analyze.")
    args = parser.parse_args()

    patterns_path = DATA_DIR / "shield_patterns.yaml"
    model_path = DATA_DIR / "prompt_fingerprint.model.json"

    if not patterns_path.is_file():
        print(f"Error: Falta el fichero de patrones en {patterns_path}", file=sys.stderr)
        sys.exit(1)

    # Initialize the full Shield engine
    shield = Shield(patterns_path=str(patterns_path), model_path=str(model_path))

    text_to_analyze = args.text

    print("--- Analizando texto con RLx Shield ---")
    print(f"Texto: \"{text_to_analyze.strip()}\"")

    result = shield.analyze(text_to_analyze)

    print("\n--- Resultado del Análisis ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Assuming a threshold from a config, e.g., 0.8
    if result.get('score', 0.0) >= 0.8:
        print("\n--- ¡ALERTA! ---")
        print("El score supera el umbral de 0.8. Se registraría una alerta de 'decision_shaping'.")

if __name__ == "__main__":
    main()
