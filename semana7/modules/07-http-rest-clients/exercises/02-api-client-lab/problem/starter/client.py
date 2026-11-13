"""Cliente sencillo para pedir una predicción a la API de bombas."""

from __future__ import annotations

from typing import Any

import requests


class PredictionClientError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


def request_prediction(
    payload: dict[str, Any],
    *,
    base_url: str = "http://127.0.0.1:8000",
    timeout: float = 5.0,
    session: Any | None = None,
) -> dict[str, Any]:
    """Envía una predicción y devuelve un objeto JSON de respuesta."""
    client = session if session is not None else requests
    url = base_url.rstrip("/") + "/v1/predictions"

    # json= convierte el diccionario a JSON y añade el Content-Type correcto.
    try:
        response = client.post(
            url,
            json=payload,
            headers={"Accept": "application/json"},
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.Timeout as error:
        raise PredictionClientError("La API ha tardado demasiado.") from error
    except requests.ConnectionError as error:
        raise PredictionClientError(
            "No se puede conectar. Comprueba la URL y que la API esté encendida."
        ) from error
    except requests.HTTPError as error:
        status = error.response.status_code if error.response is not None else None
        raise PredictionClientError(
            f"La API ha respondido con HTTP {status}.", status_code=status
        ) from error
    except requests.RequestException as error:
        raise PredictionClientError("No se ha podido enviar la petición.") from error

    try:
        body = response.json()
    except ValueError as error:
        raise PredictionClientError("La respuesta no contiene JSON válido.") from error
    if not isinstance(body, dict):
        raise PredictionClientError("La respuesta debe ser un objeto JSON.")
    return body
