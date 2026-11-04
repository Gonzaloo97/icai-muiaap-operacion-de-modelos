"""Starter: conecta una función de inferencia pura con Streamlit."""

from collections.abc import Callable
from typing import Any

from churn_demo.model import ChurnPrediction, predict

Predictor = Callable[..., ChurnPrediction]


def collect_profile(st: Any) -> tuple[bool, dict[str, object]]:
    """Renderiza cuatro widgets dentro de un único formulario."""
    # Todo lo que va dentro del "with" pertenece al formulario "churn_form".
    # Mientras se edita, Streamlit NO envía nada: solo al pulsar el botón.
    with st.form("churn_form"):
        # Slider: etiqueta, mínimo, máximo y valor inicial
        tenure = st.slider("Meses como cliente", 0, 120, 12, key="tenure_months")
        # Casilla numérica para el gasto mensual (admite decimales)
        spend = st.number_input(
            "Gasto mensual (€)",
            min_value=0.0,
            max_value=300.0,
            value=60.0,
            key="monthly_spend_eur",
        )
        # Slider para las llamadas a soporte
        calls = st.slider("Llamadas a soporte", 0, 20, 1, key="support_calls")
        # Casilla de sí/no para el contrato anual
        annual = st.checkbox(
            "Tiene contrato anual", value=False, key="has_annual_contract"
        )
        # El botón: devuelve True solo en la ejecución en la que se pulsa
        submitted = st.form_submit_button("Calcular riesgo")

    # Guardamos los 4 valores en un diccionario con los nombres de predict()
    values = {
        "tenure_months": tenure,
        "monthly_spend_eur": spend,
        "support_calls": calls,
        "has_annual_contract": annual,
    }
    return submitted, values  # (¿se pulsó el botón?, valores del formulario)


def render_prediction(st: Any, result: ChurnPrediction) -> None:
    """Muestra etiqueta, score orientativo y explicación."""
    # La etiqueta: en amarillo si hay riesgo de baja, en verde si no
    if result["will_churn"]:
        st.warning(result["label"])
    else:
        st.success(result["label"])
    # El score tal cual lo devuelve predict() (no lo recalculamos)
    st.metric("Score de riesgo (orientativo)", result["risk_score"])
    # La explicación de por qué sale ese score
    st.write(result["explanation"])


def run_app(st: Any, predictor: Predictor) -> None:
    """Conecta submit, llamada al predictor y actualización visible."""
    submitted, values = collect_profile(st)  # 1. dibujamos el formulario

    if not submitted:  # 2. si NO se ha pulsado el botón...
        st.info("Rellena el perfil y pulsa «Calcular riesgo».")
        return  # ...salimos sin llamar al modelo (0 llamadas)

    try:
        result = predictor(**values)  # 3. UNA sola llamada al modelo
    except ValueError:
        # 4. Si el modelo rechaza los datos, mensaje amable SIN el error técnico
        st.error("No se pudo calcular el riesgo. Revisa los valores del formulario.")
        return

    render_prediction(st, result)  # 5. mostramos el resultado


def main() -> None:
    """Configura la página real y delega el flujo comprobable en run_app."""
    import streamlit as st

    st.set_page_config(page_title="Churn sintético · S5", page_icon="📉")
    st.title("¿Qué cliente podría darse de baja?")
    st.caption("Caso docente sintético; el score no es una probabilidad calibrada.")
    run_app(st, predict)


if __name__ == "__main__":
    main()
