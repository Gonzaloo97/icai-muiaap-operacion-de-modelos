"""Tarea 06: casos de fallo propios y el mensaje que deben dar."""

import json
from pathlib import Path

import joblib
import pytest
from test_artifact import make_estimator
from test_predict_file import write_bundle, write_input

from model_packaging.artifact import (
    create_manifest,
    load_model_bundle,
    save_model_bundle,
)
from model_packaging.create_bundle import bundle_from_legacy
from model_packaging.predict_file import predict_file
from model_packaging.preprocess import FEATURE_NAMES


def test_load_rejects_a_corrupt_manifest(tmp_path: Path) -> None:
    """Un manifest.json roto se rechaza antes de cargar el modelo."""

    bundle_path = tmp_path / "bundle"
    write_bundle(bundle_path)
    (bundle_path / "manifest.json").write_text("{esto no es json", encoding="utf-8")

    with pytest.raises(ValueError, match="no es un JSON válido"):
        load_model_bundle(bundle_path)


def test_load_rejects_a_missing_manifest(tmp_path: Path) -> None:
    """Sin manifiesto no hay forma de saber si el modelo es compatible."""

    bundle_path = tmp_path / "bundle"
    write_bundle(bundle_path)
    (bundle_path / "manifest.json").unlink()

    with pytest.raises(FileNotFoundError, match="manifest.json"):
        load_model_bundle(bundle_path)


def test_load_rejects_another_preprocessing_version(tmp_path: Path) -> None:
    """Si el modelo espera otro preprocesado, no se carga."""

    bundle_path = tmp_path / "bundle"
    write_bundle(bundle_path)
    manifest_path = bundle_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["preprocessing_version"] = "wine-red-features-v2"
    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match="preprocessing_version"):
        load_model_bundle(bundle_path)


def test_load_rejects_a_different_estimator_type(tmp_path: Path) -> None:
    """El binario debe ser del tipo que declara el manifiesto."""

    bundle_path = tmp_path / "bundle"
    write_bundle(bundle_path)
    manifest_path = bundle_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["estimator_type"] = "RandomForestClassifier"
    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match="estimator_type"):
        load_model_bundle(bundle_path)


class NoPredict:
    """Objeto que no sabe predecir."""


def test_save_rejects_an_estimator_without_predict(tmp_path: Path) -> None:
    """No se empaqueta algo que no tenga predict y predict_proba."""

    estimator = make_estimator()
    with pytest.raises(ValueError, match="predict"):
        save_model_bundle(
            tmp_path / "bundle", NoPredict(), create_manifest(estimator, "v1")
        )


def test_cli_rejects_an_out_of_range_row_without_output(tmp_path: Path) -> None:
    """Una fila con ph=99 detiene el comando, dice cuál es y no deja CSV."""

    bundle_path = tmp_path / "bundle"
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "predictions.csv"
    write_bundle(bundle_path)
    write_input(input_path)
    text = input_path.read_text(encoding="utf-8").replace(",3.51,", ",99,")
    input_path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="red-001"):
        predict_file(input_path, output_path, bundle_path)

    assert not output_path.exists()


def test_legacy_week3_model_becomes_a_bundle(tmp_path: Path) -> None:
    """El .joblib de la semana 3 se convierte en un bundle que se puede cargar."""

    legacy_path = tmp_path / "wine_quality_classifier.joblib"
    joblib.dump(
        {
            "estimator": make_estimator(),
            "feature_names": list(FEATURE_NAMES),
            "model_version": "wine-quality-rf-v1",
        },
        legacy_path,
    )

    bundle_from_legacy(legacy_path, tmp_path / "bundle")
    loaded = load_model_bundle(tmp_path / "bundle")

    assert loaded.manifest.model_version == "wine-quality-rf-v1"
