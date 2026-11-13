"""Cliente HTTP que adapta la API Wine al contrato de inferencia de la UI."""

from __future__ import annotations

from collections.abc import Mapping
from threading import local
from typing import Any

import requests
from pydantic import ValidationError

from model_ui.contracts import PredictionPayload
from model_ui.errors import (
    ArtifactUnavailableError,
    BackendInferenceError,
    InferenceTimeoutError,
    InputContractError,
)


class HttpInferenceGateway:
    """Implementa la frontera de inferencia mediante una llamada HTTP REST."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 5.0,
        session: Any | None = None,
    ) -> None:
        normalized = base_url.strip().rstrip("/")
        if not normalized:
            raise ValueError("base_url no puede estar vacia")
        if timeout <= 0:
            raise ValueError("timeout debe ser positivo")

        self._prediction_url = f"{normalized}/v1/predictions"
        self._timeout = float(timeout)
        self._session = session if session is not None else requests.Session()
        self._request_context = local()
        self.last_request_id: str | None = None

    @property
    def last_request_id(self) -> str | None:
        """Devuelve el identificador de la ultima llamada en el contexto actual."""

        return getattr(self._request_context, "request_id", None)

    @last_request_id.setter
    def last_request_id(self, value: str | None) -> None:
        self._request_context.request_id = value

    def predict(self, values: Mapping[str, object]) -> PredictionPayload:
        """Envia la muestra por HTTP y devuelve el contrato interno de S6."""

        # Cada petición empieza sin el identificador de la anterior.
        self.last_request_id = None
        try:
            response = self._session.post(
                self._prediction_url,
                json={"features": dict(values)},
                headers={"Accept": "application/json"},
                timeout=self._timeout,
            )
        except requests.Timeout as error:
            raise InferenceTimeoutError("La API ha tardado demasiado.") from error
        except requests.ConnectionError as error:
            raise ArtifactUnavailableError(
                "No se puede conectar con la API."
            ) from error
        except requests.RequestException as error:
            raise BackendInferenceError("No se pudo enviar la petición.") from error

        # Miramos el estado antes del JSON: un error podría llegar como HTML.
        self.last_request_id = self._header_request_id(response)
        if response.status_code == 422:
            raise InputContractError("Los datos no cumplen el contrato de la API.")
        if response.status_code == 503:
            raise ArtifactUnavailableError("El modelo no está disponible.")
        if not 200 <= response.status_code < 300:
            raise BackendInferenceError(
                f"La API respondió HTTP {response.status_code}."
            )

        body = self._read_object(response)
        self.last_request_id = self._request_id(response, body)
        try:
            return PredictionPayload.model_validate(body.get("prediction"))
        except ValidationError as error:
            raise BackendInferenceError(
                "La predicción recibida no es válida."
            ) from error

    @staticmethod
    def _read_object(response: Any) -> dict[str, Any]:
        """Lee una respuesta JSON que debe representar un objeto."""

        try:
            body = response.json()
        except ValueError as error:
            raise BackendInferenceError("La respuesta no es JSON válido.") from error
        if not isinstance(body, dict):
            raise BackendInferenceError("La respuesta debe ser un objeto JSON.")
        return body

    @staticmethod
    def _request_id(response: Any, body: dict[str, Any]) -> str | None:
        """Obtiene request_id del cuerpo y usa la cabecera como alternativa."""

        request_id = body.get("request_id")
        if isinstance(request_id, str) and request_id.strip():
            return request_id
        return HttpInferenceGateway._header_request_id(response)

    @staticmethod
    def _header_request_id(response: Any) -> str | None:
        headers = getattr(response, "headers", {})
        return headers.get("X-Request-Id")
