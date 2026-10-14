"""Punto de extensión del CLI de inferencia sobre un bundle."""

from __future__ import annotations

import argparse
from pathlib import Path

import csv

from model_packaging.artifact import (
    DEFAULT_BUNDLE_PATH,
    infer_wine_quality,
    load_model_bundle,
)
from model_packaging.contracts import WineQualityRequest


def predict_file(
    input_path: Path,
    output_path: Path,
    bundle_path: Path,
) -> int:
    """Valida todas las filas y escribe el CSV solo al final."""

    bundle = load_model_bundle(bundle_path)  # cargamos el modelo
    results = []  # aquí guardamos las predicciones (en memoria)

    with input_path.open(encoding="utf-8") as file:  # abrimos el CSV de entrada
        for row in csv.DictReader(file):  # leemos fila a fila como diccionario
            sample_id = row.pop("sample_id")  # sacamos el id; quedan las medidas
            request = WineQualityRequest(**row)  # valida (si falla -> ValueError)
            prediction = infer_wine_quality(bundle, request)  # predecimos
            results.append({"sample_id": sample_id, **prediction.model_dump()})

    # Solo llegamos aquí si TODAS las filas eran válidas: ahora escribimos
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())  # columnas
        writer.writeheader()  # escribimos la cabecera
        writer.writerows(results)  # escribimos todas las predicciones

    return len(results)  # devolvemos cuántas filas hemos predicho


def parse_args() -> argparse.Namespace:
    """Declara la interfaz del comando público."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--bundle", default=DEFAULT_BUNDLE_PATH, type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    raise SystemExit(
        predict_file(
            input_path=arguments.input,
            output_path=arguments.output,
            bundle_path=arguments.bundle,
        )
    )
