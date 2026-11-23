import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wine_api.dependencies import get_predictor
from wine_api.export_openapi import render_openapi
from wine_api.predictor import UnavailablePredictor


def test_prediction_returns_503_when_model_is_unavailable(
    client: TestClient, valid_payload: dict
) -> None:
    client.app.dependency_overrides[get_predictor] = lambda: UnavailablePredictor()
    try:
        response = client.post("/v1/predictions", json=valid_payload)
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "model_unavailable"
        assert response.headers["X-Request-Id"] == response.json()["request_id"]
    finally:
        client.app.dependency_overrides.pop(get_predictor, None)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("alcohol", 4.99),
        ("alcohol", 20.01),
        ("ph", 2.49),
        ("ph", 4.51),
        ("density", None),
        ("sulphates", "mucho"),
        ("fixed_acidity", False),
    ],
)
def test_out_of_contract_values_are_rejected(
    client: TestClient, valid_payload: dict, field: str, value: object
) -> None:
    valid_payload["features"][field] = value
    response = client.post("/v1/predictions", json=valid_payload)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert [item["field"] for item in error["fields"]] == [f"features.{field}"]


@pytest.mark.parametrize("alcohol", [5, 20])
def test_range_limits_are_inclusive(
    client: TestClient, valid_payload: dict, alcohol: int
) -> None:
    valid_payload["features"]["alcohol"] = alcohol
    assert client.post("/v1/predictions", json=valid_payload).status_code == 200


def test_openapi_matches_versioned_contract() -> None:
    path = Path(__file__).parents[1] / "contracts/openapi.json"
    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(render_openapi())
