"""Carga del .joblib e inferencia sobre características preparadas."""

from pathlib import Path

import joblib

from model_inference.preprocess import FEATURE_NAMES

DEFAULT_MODEL_PATH = Path("models/wine_quality_classifier.joblib")


def load_wine_quality_model(model_path):  # la función que carga el modelo
    artifact = joblib.load(model_path)  # abre el .joblib: dentro hay un diccionario
    if not isinstance(artifact, dict):  # 1. ¿es un diccionario?
        raise ValueError("El artefacto debe ser un diccionario con metadatos")

    modelo = artifact.get("estimator")  # saca el modelo (None si no está)
    # 2. ¿sabe predecir la categoría (predict) y la confianza (predict_proba)?
    if not hasattr(modelo, "predict") or not hasattr(modelo, "predict_proba"):
        raise ValueError("El artefacto no contiene un clasificador compatible")

    # 3. ¿las features están en el mismo orden con el que se entrenó?
    if list(artifact.get("feature_names", [])) != list(FEATURE_NAMES):
        raise ValueError("feature_names no coincide con FEATURE_NAMES")

    # 4. ¿trae una versión de modelo válida (texto no vacío)?
    model_version = artifact.get("model_version")
    if not isinstance(model_version, str) or not model_version.strip():
        raise ValueError("El artefacto no declara una model_version válida")

    return artifact  # todo comprobado: devolvemos el diccionario entero


def infer_wine_quality(artifact, features):
    modelo = artifact["estimator"]  # saca el modelo del diccionario
    fila = [features.as_vector()]  # el modelo quiere una lista de filas
    quality_band = modelo.predict(fila)[0]  # categoría de la primera (y única) fila
    confidence = max(modelo.predict_proba(fila)[0])  # la probabilidad más alta
    return str(quality_band), round(float(confidence), 2)  # devolvemos las dos
