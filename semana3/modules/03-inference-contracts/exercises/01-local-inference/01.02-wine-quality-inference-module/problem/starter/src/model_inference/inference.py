"""Carga del .joblib e inferencia sobre características preparadas."""

from pathlib import Path

import joblib

from model_inference.preprocess import FEATURE_NAMES

DEFAULT_MODEL_PATH = Path("models/wine_quality_classifier.joblib")


def load_wine_quality_model(model_path):  # la función que carga el modelo
    artifact = joblib.load(model_path)  # abre el .joblib: dentro hay un diccionario
    modelo = artifact.get("estimator")  # saca el modelo (None si no está)
    if not hasattr(modelo, "predict_proba"):  # ¿el modelo sabe predecir?
        raise ValueError("El artefacto no contiene un clasificador compatible")
    if list(artifact["feature_names"]) != list(FEATURE_NAMES):  # ¿mismo orden?
        raise ValueError("feature_names no coincide con FEATURE_NAMES")
    return artifact  # devuelve el diccionario entero


def infer_wine_quality(artifact, features):
    modelo = artifact["estimator"]  # saca el modelo del diccionario
    fila = [features.as_vector()]  # el modelo quiere una lista de filas
    quality_band = modelo.predict(fila)[0]  # categoría de la primera (y única) fila
    confidence = max(modelo.predict_proba(fila)[0])  # la probabilidad más alta
    return str(quality_band), round(float(confidence), 2)  # devolvemos las dos