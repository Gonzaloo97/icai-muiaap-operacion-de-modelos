# Práctica 5.1 — Miniapp Churn: pruebas y QA

## 1. Predicciones anticipadas (tarea 01)

Antes de programar, leyendo la regla de `predict()`:

| Perfil (meses, gasto €, llamadas, contrato anual) | Resultado esperado | Por qué |
|---|---|---|
| `2, 95, 4, False` | **Baja probable**, score **0.95** | Cliente nuevo (+0,30), gasto alto (+0,20), muchas llamadas (+0,25) y sin contrato anual (+0,10) sobre la base de 0,25 |
| `36, 35, 0, True` | **Permanencia probable**, score **0.05** | Antigüedad alta (−0,15), gasto bajo (−0,05), sin llamadas y con contrato anual (−0,25) |

El score es una **regla docente**, no una probabilidad calibrada.

## 2. Pruebas automáticas

Desde `semana5/modules/05-streamlit-basic-model-ui/exercises/01-churn-streamlit/problem/starter`:

```bash
uv sync
uv run python -m pytest -q        # 13 passed
uv run ruff check app.py src tests
uv run ruff format --check app.py src tests
uv run streamlit run app.py
```

Salida:

```text
13 passed
All checks passed!
6 files already formatted
```

## 3. Checklist manual (4 casos)

| Caso | Acción | Resultado esperado | Resultado observado |
|---|---|---|---|
| 1. Arranque | Abrir la app | Título, explicación y un formulario con 4 widgets | ✅ Aparecen el título, el aviso de caso sintético, 2 sliders, 1 casilla numérica, 1 checkbox y el botón «Calcular riesgo». Mensaje: «Rellena el perfil y pulsa «Calcular riesgo».» |
| 2. Edición sin envío | Cambiar varios valores sin pulsar el botón | No se calcula ni se presenta una predicción | ✅ Los valores cambian, pero no aparece ningún resultado: 0 llamadas a `predict()` |
| 3. Submit válido | Pulsar «Calcular riesgo» con el perfil `2, 95, 4, False` | Una llamada; aparecen etiqueta, score y explicación | ✅ «Baja probable» (aviso amarillo), score **0.95** y la explicación de la regla |
| 4. Resultado actualizado | Cambiar al perfil `36, 35, 0, True` y volver a enviar | La salida refleja el nuevo perfil y no conserva la anterior | ✅ «Permanencia probable» (aviso verde), score **0.05**. El resultado anterior desaparece |

## 4. Puente hacia Wine (tarea 06)

Se conserva el **patrón**, no el código:

```text
formulario (st.form) → botón (st.form_submit_button) → UNA llamada a la inferencia → resultado o error amable
```

En la práctica 5.2 cambian los 4 campos de Churn por los 11 de Wine (`FIELD_SPECS`), y `predict()` por `gateway.predict(values)`, que usa el bundle real de la semana 4. La regla de **0 llamadas al editar y 1 al enviar** y el **error sin detalles técnicos** son los mismos.
