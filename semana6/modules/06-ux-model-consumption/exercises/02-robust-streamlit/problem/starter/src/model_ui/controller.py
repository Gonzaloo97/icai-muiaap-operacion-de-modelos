"""TODOs del controlador de estados independiente de Streamlit."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from time import perf_counter
from uuid import uuid4

from model_ui.contracts import PredictionPayload, UiState
from model_ui.gateway import InferenceGateway
from model_ui.presentation import build_prediction_view, to_user_facing_error
from model_ui.telemetry import Telemetry

StateEmitter = Callable[[UiState], None]
Clock = Callable[[], float]
RequestIdFactory = Callable[[], str]


class PredictionController:
    """Orquesta loading, gateway, errores y telemetría."""

    def __init__(
        self,
        gateway: InferenceGateway,
        *,
        telemetry: Telemetry | None = None,
        clock: Clock = perf_counter,
        request_id_factory: RequestIdFactory | None = None,
    ) -> None:
        self.gateway = gateway
        self.telemetry = telemetry or Telemetry()
        self._clock = clock
        self._request_id_factory = request_id_factory or (lambda: uuid4().hex[:10])

    def submit(
        self,
        values: Mapping[str, object],
        *,
        emit: StateEmitter | None = None,
    ) -> UiState:
        """Emite loading, mide, valida la salida y devuelve success/error."""

        request_id = self._request_id_factory()  # identificador de esta petición

        # 1. Avisamos a la pantalla de que empezamos ("cargando...")
        self._emit(emit, UiState(phase="loading", request_id=request_id))

        start = self._clock()  # 2. ponemos en marcha el cronómetro
        try:
            prediction = self.gateway.predict(values)  # 3. UNA llamada al modelo
            # 4. Volvemos a validar la salida: no nos fiamos ciegamente del modelo
            prediction = PredictionPayload.model_validate(prediction.model_dump())
        except Exception as error:  # noqa: BLE001 - todo fallo se vuelve estado
            latency_ms = self._elapsed_ms(start)
            user_error = to_user_facing_error(error, request_id)  # texto seguro
            # 5a. Telemetría: solo el código del error y el tiempo, nunca los datos
            self.telemetry.record_error(user_error.code, latency_ms)
            state = UiState(phase="error", request_id=request_id, error=user_error)
            self._emit(emit, state)
            return state

        latency_ms = self._elapsed_ms(start)  # 6. paramos el cronómetro
        view = build_prediction_view(prediction, latency_ms)  # textos de la vista
        # 5b. Telemetría: tiempo y versiones, nunca los valores del formulario
        self.telemetry.record_success(
            latency_ms,
            model_version=prediction.model_version,
            preprocessing_version=prediction.preprocessing_version,
        )
        state = UiState(phase="success", request_id=request_id, view=view)
        self._emit(emit, state)
        return state

    def _elapsed_ms(self, start: float) -> float:
        """Milisegundos transcurridos desde ``start``, con 3 decimales."""

        return round((self._clock() - start) * 1000, 3)

    @staticmethod
    def _emit(emit: StateEmitter | None, state: UiState) -> None:
        """Avisa a la pantalla solo si alguien está escuchando."""

        if emit is not None:
            emit(state)
