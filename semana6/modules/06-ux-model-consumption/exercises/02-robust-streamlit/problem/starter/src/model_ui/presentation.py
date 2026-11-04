"""TODOs de la vista UX: copy de salida y traducción de errores."""

from __future__ import annotations

from model_ui.contracts import PredictionPayload, PredictionView, UserFacingError
from model_ui.errors import (
    ArtifactUnavailableError,
    InferenceTimeoutError,
    InputContractError,
)
from model_ui.policies import (
    DEFAULT_CONFIDENCE_POLICY,
    DEFAULT_LATENCY_POLICY,
    ConfidencePolicy,
    LatencyPolicy,
    classify_confidence,
    classify_latency,
)

# Textos de cada error: (título, qué ha pasado, qué puede hacer la persona)
ERROR_COPY = {
    "invalid_input": (
        "Datos no válidos",
        "Algún valor del formulario no cumple el contrato de entrada.",
        "Revisa los valores del formulario y vuelve a enviarlo.",
    ),
    "artifact_unavailable": (
        "Modelo no disponible",
        "No se pudo cargar el modelo configurado.",
        "Comprueba la variable MODEL_UI_BUNDLE y vuelve a abrir la aplicación.",
    ),
    "timeout": (
        "La inferencia tardó demasiado",
        "El modelo no respondió a tiempo.",
        "Espera unos segundos y pulsa «Reintentar».",
    ),
    "prediction_error": (
        "No se pudo obtener una predicción",
        "El modelo no devolvió una respuesta válida.",
        "Pulsa «Reintentar»; si el fallo continúa, avisa con el request_id.",
    ),
}

QUALITY_LABELS = {
    "needs_review": "Requiere revisión",
    "acceptable": "Resultado aceptable",
    "excellent": "Resultado excelente",
}

CONFIDENCE_COPY = {
    "low": (
        "Confianza baja",
        "El resultado es orientativo y requiere revisión; "
        "la confianza no es una garantía.",
    ),
    "medium": (
        "Confianza intermedia",
        "Usa el resultado como señal orientativa y revisa su contexto antes de actuar.",
    ),
    "high": (
        "Confianza alta",
        "La confianza es alta para este modelo, pero no garantiza "
        "que la decisión sea correcta.",
    ),
}

LATENCY_COPY = {
    "within_target": (
        "Dentro del objetivo",
        "La respuesta quedó dentro del objetivo de la demo.",
    ),
    "above_target": (
        "Por encima del objetivo",
        "La respuesta llegó, pero la latencia supera el objetivo técnico de la demo.",
    ),
}


def build_prediction_view(
    prediction: PredictionPayload,
    latency_ms: float,
    *,
    confidence_policy: ConfidencePolicy = DEFAULT_CONFIDENCE_POLICY,
    latency_policy: LatencyPolicy = DEFAULT_LATENCY_POLICY,
) -> PredictionView:
    """Construye la vista con etiquetas, confianza, latencia y versiones."""

    # 1. Clasificamos la confianza (low/medium/high) y la latencia
    confidence_level = classify_confidence(prediction.confidence, confidence_policy)
    latency_status = classify_latency(latency_ms, latency_policy)

    # 2. Buscamos los textos que corresponden a cada clasificación
    confidence_label, confidence_message = CONFIDENCE_COPY[confidence_level]
    latency_label, latency_message = LATENCY_COPY[latency_status]

    # 3. Lo juntamos todo en un único objeto listo para pintar
    return PredictionView(
        quality_band=prediction.quality_band,
        quality_label=QUALITY_LABELS[prediction.quality_band],
        confidence=prediction.confidence,
        confidence_level=confidence_level,
        confidence_label=confidence_label,
        confidence_message=confidence_message,
        latency_ms=latency_ms,
        latency_status=latency_status,
        latency_label=latency_label,
        latency_message=latency_message,
        model_version=prediction.model_version,
        preprocessing_version=prediction.preprocessing_version,
    )


def to_user_facing_error(error: Exception, request_id: str) -> UserFacingError:
    """Asigna código estable, mensaje accionable y recuperación."""

    # Elegimos el código según el TIPO de error. Nunca usamos el texto del
    # error original: podría contener rutas, datos o detalles internos.
    if isinstance(error, InputContractError):
        code = "invalid_input"
    elif isinstance(error, ArtifactUnavailableError):
        code = "artifact_unavailable"
    elif isinstance(error, InferenceTimeoutError):
        code = "timeout"
    else:
        code = "prediction_error"  # cualquier otro fallo

    title, message, recovery = ERROR_COPY[code]  # textos fijos y seguros
    return UserFacingError(
        code=code,
        title=title,
        message=message,
        recovery=recovery,
        request_id=request_id,  # identificador para buscar el fallo en los logs
    )
