"""Estado de sesión de Streamlit aislado para poder probarlo sin Streamlit."""

from __future__ import annotations

from collections.abc import MutableMapping

from model_ui.contracts import UiState
from model_ui.telemetry import Telemetry

LAST_STATE_KEY = "last_state"
TELEMETRY_KEY = "telemetry"
LAST_VALUES_KEY = "last_values"


def initialize_session_state(
    session_state: MutableMapping[str, object],
) -> None:
    """Crea solo las entradas de sesión que todavía no existan."""

    # session_state funciona como un diccionario que sobrevive a cada rerun.
    # Solo creamos cada clave si NO existe: si ya existe, no la tocamos
    # (así no se pierde el resultado ni los contadores al recargar).
    if LAST_STATE_KEY not in session_state:
        session_state[LAST_STATE_KEY] = UiState(phase="idle")  # sin resultado aún
    if TELEMETRY_KEY not in session_state:
        session_state[TELEMETRY_KEY] = Telemetry()  # contadores a cero
    if LAST_VALUES_KEY not in session_state:
        session_state[LAST_VALUES_KEY] = {}  # últimos valores, para reintentar


def clear_last_state(session_state: MutableMapping[str, object]) -> None:
    """Vuelve a idle sin perder la telemetría acumulada."""

    session_state[LAST_STATE_KEY] = UiState(phase="idle")  # borra el resultado
    session_state[LAST_VALUES_KEY] = {}  # borra los valores del último envío
    # La telemetría NO se toca: los contadores de la sesión se conservan.
