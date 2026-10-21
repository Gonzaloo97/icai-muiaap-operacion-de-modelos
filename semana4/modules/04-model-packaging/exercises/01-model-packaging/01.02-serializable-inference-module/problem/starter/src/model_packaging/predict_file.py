"""CLI de inferencia sobre un bundle: valida todo y escribe el CSV al final."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

from model_packaging.artifact import (
    DEFAULT_BUNDLE_PATH,
    infer_wine_quality,
    load_model_bundle,
)
from model_packaging.contracts import WineQualityRequest

# Columnas del CSV de salida, siempre en este orden (esquema estable)
OUTPUT_FIELDS = (
    "sample_id",
    "quality_band",
    "confidence",
    "model_version",
    "preprocessing_version",
)


def predict_file(
    input_path: Path,
    output_path: Path,
    bundle_path: Path,
) -> int:
    """Valida todas las filas y escribe el CSV solo al final."""

    bundle = load_model_bundle(bundle_path)  # 1. carga el bundle (ya validado)
    results = []  # aquí guardamos las predicciones (en memoria)

    with Path(input_path).open(encoding="utf-8") as file:  # 2. abrimos el CSV
        for row in csv.DictReader(file):  # cada fila es un diccionario
            sample_id = (row.pop("sample_id", None) or "").strip()  # sacamos el id
            if not sample_id:
                raise ValueError("Hay una fila con sample_id vacío")
            try:
                request = WineQualityRequest(**row)  # 3. valida la fila
                prediction = infer_wine_quality(bundle, request)  # 4. predice
            except ValueError as error:  # si falla, decimos en qué fila
                raise ValueError(f"Fila {sample_id}: {error}") from error
            results.append({"sample_id": sample_id, **prediction.model_dump()})

    # 5. Solo llegamos aquí si TODAS las filas eran válidas: ahora escribimos.
    #    Primero en un temporal y luego lo renombramos (nunca queda a medias).
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)  # crea .tmp/ si hace falta
    temporary_path = output_path.with_name(output_path.name + ".tmp")
    with temporary_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_FIELDS)  # columnas fijas
        writer.writeheader()  # cabecera
        writer.writerows(results)  # todas las predicciones
    os.replace(temporary_path, output_path)  # publicamos el CSV completo

    return len(results)  # cuántas filas hemos predicho


def parse_args() -> argparse.Namespace:
    """Declara la interfaz del comando público."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--bundle", default=DEFAULT_BUNDLE_PATH, type=Path)
    return parser.parse_args()


def main() -> int:
    """Ejecuta el comando y convierte los errores en un mensaje limpio."""

    arguments = parse_args()
    try:
        count = predict_file(
            input_path=arguments.input,
            output_path=arguments.output,
            bundle_path=arguments.bundle,
        )
    except (FileNotFoundError, ValueError) as error:  # cualquier fallo...
        print(f"error: {error}", file=sys.stderr)  # ...se muestra por stderr
        return 2  # código 2 = ha fallado
    print(f"Predicciones escritas: {count}")
    return 0  # código 0 = todo bien


if __name__ == "__main__":
    raise SystemExit(main())
