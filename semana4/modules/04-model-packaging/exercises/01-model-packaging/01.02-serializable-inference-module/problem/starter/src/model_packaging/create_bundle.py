"""Genera el bundle (manifest.json + model.joblib) en la carpeta indicada.

Dos formas de usarlo:

- Con el modelo real de la semana 3 (recomendado):
    uv run python -m model_packaging.create_bundle \
        --legacy RUTA/A/wine_quality_classifier.joblib
- Sin el modelo real, con un clasificador de demostración:
    uv run python -m model_packaging.create_bundle --demo
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib
from sklearn.dummy import DummyClassifier

from model_packaging.artifact import (
    DEFAULT_BUNDLE_PATH,
    create_manifest,
    save_model_bundle,
)
from model_packaging.preprocess import FEATURE_NAMES


def bundle_from_legacy(legacy_path: Path, output_path: Path) -> None:
    """Convierte el .joblib de la semana 3 al nuevo formato de bundle."""

    if not legacy_path.is_file():
        raise FileNotFoundError(f"No existe el modelo de la semana 3: {legacy_path}")

    payload = joblib.load(legacy_path)  # en S3 era un diccionario de 3 claves
    if not isinstance(payload, dict):
        raise ValueError("El modelo de la semana 3 debe ser un diccionario")
    if tuple(payload.get("feature_names", [])) != FEATURE_NAMES:
        raise ValueError("feature_names del modelo antiguo no coincide")

    estimator = payload.get("estimator")  # el modelo entrenado
    model_version = payload.get("model_version")  # su versión
    if not isinstance(model_version, str) or not model_version:
        raise ValueError("El modelo de la semana 3 no declara model_version")

    manifest = create_manifest(estimator, model_version)  # rellenamos el prospecto
    save_model_bundle(output_path, estimator, manifest)  # guardamos los 2 ficheros


def demo_bundle(output_path: Path) -> None:
    """Crea un bundle con un clasificador mínimo (siempre dice 'acceptable')."""

    estimator = DummyClassifier(strategy="constant", constant="acceptable")
    estimator.fit([[0.0] * len(FEATURE_NAMES)], ["acceptable"])  # 'entrenamiento'
    manifest = create_manifest(estimator, "wine-quality-demo-v1")
    save_model_bundle(output_path, estimator, manifest)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=DEFAULT_BUNDLE_PATH, type=Path)
    origin = parser.add_mutually_exclusive_group(required=True)  # una de las dos
    origin.add_argument("--legacy", type=Path, help="ruta al .joblib de semana 3")
    origin.add_argument("--demo", action="store_true", help="modelo de demostración")
    arguments = parser.parse_args()

    try:
        if arguments.legacy:
            bundle_from_legacy(arguments.legacy, arguments.output)
        else:
            demo_bundle(arguments.output)
    except (FileNotFoundError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(f"Bundle escrito en: {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
