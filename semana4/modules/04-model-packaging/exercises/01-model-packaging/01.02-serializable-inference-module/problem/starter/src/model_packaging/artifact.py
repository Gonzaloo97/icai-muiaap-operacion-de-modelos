"""Bundle serializado: manifiesto JSON + modelo joblib, con validación."""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import joblib
from pydantic import BaseModel, ConfigDict, Field, model_validator

from model_packaging.contracts import (
    QualityBand,
    WineQualityPrediction,
    WineQualityRequest,
)
from model_packaging.preprocess import (
    FEATURE_NAMES,
    PREPROCESSING_VERSION,
    preprocess_wine_request,
)

ARTIFACT_SCHEMA_VERSION = "wine-quality-bundle-v1"
DEFAULT_BUNDLE_PATH = Path("models/wine_quality_bundle")
MANIFEST_FILENAME = "manifest.json"
MODEL_FILENAME = "model.joblib"
OUTPUT_LABELS: tuple[QualityBand, ...] = (
    "needs_review",
    "acceptable",
    "excellent",
)


class WineQualityEstimator(Protocol):
    """Interfaz mínima que debe cumplir el estimador cargado."""

    def predict(self, features: list[list[float]]) -> Sequence[str]:
        """Devuelve una etiqueta por fila."""

    def predict_proba(self, features: list[list[float]]) -> Sequence[Sequence[float]]:
        """Devuelve probabilidades por fila."""


class ArtifactManifest(BaseModel):
    """El "prospecto" del modelo: metadatos legibles y validados."""

    model_config = ConfigDict(extra="forbid")  # prohíbe claves desconocidas

    schema_version: str
    model_version: str = Field(min_length=1)
    preprocessing_version: str
    feature_names: tuple[str, ...]
    output_labels: tuple[QualityBand, ...]
    estimator_type: str = Field(min_length=1)

    @model_validator(mode="after")
    def check_compatibility(self) -> ArtifactManifest:
        """Comprueba que el manifiesto encaja con NUESTRO código."""

        # 1. ¿El formato del bundle es el que sabemos leer?
        if self.schema_version != ARTIFACT_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version incompatible: se esperaba {ARTIFACT_SCHEMA_VERSION}"
            )
        # 2. ¿El modelo espera el mismo preprocesado que tenemos?
        if self.preprocessing_version != PREPROCESSING_VERSION:
            raise ValueError(
                f"preprocessing_version incompatible: se esperaba "
                f"{PREPROCESSING_VERSION}"
            )
        # 3. ¿Las 11 features están en el mismo orden con el que se entrenó?
        if self.feature_names != FEATURE_NAMES:
            raise ValueError("feature_names no coincide con FEATURE_NAMES")
        # 4. ¿Las etiquetas de salida son las que admite el contrato?
        if self.output_labels != OUTPUT_LABELS:
            raise ValueError("output_labels no coincide con OUTPUT_LABELS")
        return self  # todo encaja


@dataclass(frozen=True)
class LoadedModelBundle:
    """Bundle cargado; no modificar esta interfaz pública."""

    estimator: WineQualityEstimator
    manifest: ArtifactManifest


def check_estimator(estimator: object) -> None:
    """Falla si el objeto no sabe predecir categoría y confianza."""

    if not hasattr(estimator, "predict") or not hasattr(estimator, "predict_proba"):
        raise ValueError("El estimador debe tener predict y predict_proba")


def create_manifest(
    estimator: WineQualityEstimator, model_version: str
) -> ArtifactManifest:
    """Rellena el manifiesto con los 6 datos obligatorios."""

    return ArtifactManifest(
        schema_version=ARTIFACT_SCHEMA_VERSION,  # formato del bundle
        model_version=model_version,  # qué modelo es
        preprocessing_version=PREPROCESSING_VERSION,  # qué preprocesado espera
        feature_names=FEATURE_NAMES,  # orden de las 11 features
        output_labels=OUTPUT_LABELS,  # categorías permitidas
        estimator_type=type(estimator).__name__,  # p. ej. "RandomForestClassifier"
    )


def save_model_bundle(
    bundle_path: Path,
    estimator: WineQualityEstimator,
    manifest: ArtifactManifest | None = None,
) -> ArtifactManifest:
    """Escribe manifest.json y model.joblib dentro de bundle_path."""

    check_estimator(estimator)  # no guardamos algo que no sabe predecir
    if manifest is None:
        raise ValueError("Hace falta un manifiesto: usa create_manifest()")

    bundle_path = Path(bundle_path)
    bundle_path.mkdir(parents=True, exist_ok=True)  # crea la carpeta si no existe

    # Escribimos primero en ficheros temporales y luego los renombramos.
    # Así nunca queda un manifest.json o un model.joblib a medio escribir.
    model_tmp = bundle_path / (MODEL_FILENAME + ".tmp")
    manifest_tmp = bundle_path / (MANIFEST_FILENAME + ".tmp")

    # El modelo va dentro de un diccionario {"estimator": ...}: es el formato
    # del bundle de la asignatura (lo leen también la semana 5 y siguientes)
    joblib.dump({"estimator": estimator}, model_tmp)
    manifest_text = json.dumps(manifest.model_dump(), indent=2)  # dict -> texto JSON
    manifest_tmp.write_text(manifest_text, encoding="utf-8")

    os.replace(model_tmp, bundle_path / MODEL_FILENAME)  # renombrado atómico
    os.replace(manifest_tmp, bundle_path / MANIFEST_FILENAME)
    return manifest


def load_model_bundle(bundle_path: Path) -> LoadedModelBundle:
    """Valida el manifiesto ANTES de cargar el estimador."""

    bundle_path = Path(bundle_path)
    manifest_path = bundle_path / MANIFEST_FILENAME
    model_path = bundle_path / MODEL_FILENAME

    # 1. Los dos ficheros tienen que existir
    if not manifest_path.is_file():
        raise FileNotFoundError(f"No existe {manifest_path}")
    if not model_path.is_file():
        raise FileNotFoundError(f"No existe {model_path}")

    # 2. El manifiesto tiene que ser un JSON legible...
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"manifest.json no es un JSON válido: {error}") from error

    # 3. ...y compatible con nuestro código (claves, versiones, orden, etiquetas)
    manifest = ArtifactManifest.model_validate(data)

    # 4. Solo ahora, con el manifiesto validado, cargamos el binario
    payload = joblib.load(model_path)  # un diccionario {"estimator": ...}
    if not isinstance(payload, dict):
        raise ValueError('model.joblib debe contener un diccionario {"estimator": ...}')
    estimator = payload.get("estimator")  # sacamos el modelo del diccionario
    check_estimator(estimator)

    # 5. El binario tiene que ser del tipo que dice el manifiesto
    if type(estimator).__name__ != manifest.estimator_type:
        raise ValueError(
            f"estimator_type incompatible: el manifiesto dice "
            f"{manifest.estimator_type} y el modelo es {type(estimator).__name__}"
        )

    return LoadedModelBundle(estimator=estimator, manifest=manifest)


def infer_wine_quality(
    bundle: LoadedModelBundle,
    request: WineQualityRequest,
) -> WineQualityPrediction:
    """Preprocesa, invoca el estimador y valida la respuesta."""

    features = preprocess_wine_request(request)  # vector en el orden correcto
    fila = [features.as_vector()]  # el modelo quiere una lista de filas

    quality_band = str(bundle.estimator.predict(fila)[0])  # categoría
    confidence = float(max(bundle.estimator.predict_proba(fila)[0]))  # confianza

    # La etiqueta tiene que estar entre las que declara el manifiesto
    if quality_band not in bundle.manifest.output_labels:
        raise ValueError(f"quality_band no permitida: {quality_band}")

    # WineQualityPrediction vuelve a validar todo (etiqueta, 0-1, versiones)
    return WineQualityPrediction(
        quality_band=quality_band,
        confidence=round(confidence, 2),
        model_version=bundle.manifest.model_version,
        preprocessing_version=bundle.manifest.preprocessing_version,
    )
