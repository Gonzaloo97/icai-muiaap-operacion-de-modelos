"""Políticas explícitas que el alumnado puede reutilizar en la UI."""

from dataclasses import dataclass

from model_ui.contracts import ConfidenceLevel, LatencyStatus


@dataclass(frozen=True)
class ConfidencePolicy:
    """Umbrales de comunicación, no de aprobación del modelo."""

    low_below: float = 0.60
    high_from: float = 0.85


@dataclass(frozen=True)
class LatencyPolicy:
    """Objetivo técnico de la demo."""

    target_ms: float = 300.0


DEFAULT_CONFIDENCE_POLICY = ConfidencePolicy()
DEFAULT_LATENCY_POLICY = LatencyPolicy()


def classify_confidence(
    confidence: float, policy: ConfidencePolicy = DEFAULT_CONFIDENCE_POLICY
) -> ConfidenceLevel:
    """Valida [0, 1] y devuelve low/medium/high según policy."""

    # Una confianza es una probabilidad: tiene que estar entre 0 y 1
    if not 0 <= confidence <= 1:
        raise ValueError("La confianza debe estar entre 0 y 1")
    if confidence < policy.low_below:  # menos de 0.60 -> baja
        return "low"
    if confidence < policy.high_from:  # de 0.60 a 0.85 (sin incluir) -> media
        return "medium"
    return "high"  # 0.85 o más -> alta


def classify_latency(
    latency_ms: float, policy: LatencyPolicy = DEFAULT_LATENCY_POLICY
) -> LatencyStatus:
    """Devuelve within_target o above_target para una latencia válida."""

    # Un tiempo no puede ser negativo
    if latency_ms < 0:
        raise ValueError("La latencia no puede ser negativa")
    if latency_ms <= policy.target_ms:  # 300 ms o menos -> dentro del objetivo
        return "within_target"
    return "above_target"  # más de 300 ms -> lenta (pero NO es un error)
