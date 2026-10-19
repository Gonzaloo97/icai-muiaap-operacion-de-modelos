def test_preprocess_preserves_feature_order() -> None:
    from model_inference.contracts import WineQualityRequest
    from model_inference.preprocess import preprocess_wine_request

    request = WineQualityRequest(
        fixed_acidity=1.0,
        volatile_acidity=0.5,
        citric_acid=0.2,
        residual_sugar=4.0,
        chlorides=0.05,
        free_sulfur_dioxide=6.0,
        total_sulfur_dioxide=70.0,
        density=0.998,
        ph=3.2,
        sulphates=1.0,
        alcohol=11.0,
    )

    features = preprocess_wine_request(request)

    assert features.as_vector() == [
        1.0,
        0.5,
        0.2,
        4.0,
        0.05,
        6.0,
        70.0,
        0.998,
        3.2,
        1.0,
        11.0,
    ]


class OnlyProbabilities:
    """Falso modelo: tiene predict_proba pero NO predict."""

    def predict_proba(self, features):
        return [[1.0]]


def test_load_rejects_an_estimator_without_predict(tmp_path) -> None:
    import joblib
    import pytest

    from model_inference.inference import load_wine_quality_model
    from model_inference.preprocess import FEATURE_NAMES

    model_path = tmp_path / "no_predict.joblib"
    joblib.dump(
        {
            "estimator": OnlyProbabilities(),
            "feature_names": list(FEATURE_NAMES),
            "model_version": "wine-quality-rf-v1",
        },
        model_path,
    )

    with pytest.raises(ValueError, match="clasificador compatible"):
        load_wine_quality_model(model_path)


def test_load_rejects_a_missing_model_version(tmp_path) -> None:
    import joblib
    import pytest
    from sklearn.dummy import DummyClassifier

    from model_inference.inference import load_wine_quality_model
    from model_inference.preprocess import FEATURE_NAMES

    estimator = DummyClassifier(strategy="constant", constant="acceptable")
    estimator.fit([[0.0] * len(FEATURE_NAMES)], ["acceptable"])
    model_path = tmp_path / "no_version.joblib"
    joblib.dump(
        {"estimator": estimator, "feature_names": list(FEATURE_NAMES)},
        model_path,
    )

    with pytest.raises(ValueError, match="model_version"):
        load_wine_quality_model(model_path)
