# Práctica 6.2 — Evolución robusta de la interfaz de S5: ejecución y QA

Diseño de partida: [notebook de la práctica 6.1](../../../01-ui-contract/problem/01-estado-streamlit-alumno.ipynb).

## 1. Qué se conserva de S5 y qué se añade en S6

| Se conserva de S5 (sin cambios) | Se añade en S6 |
|---|---|
| `FEATURE_FIELDS` con los 11 campos del contrato | `session.py`: `last_state`, `telemetry` y `last_values` en `st.session_state`, creados una sola vez |
| `collect_values()`: un único `st.form` y el botón «Ejecutar inferencia» | `policies.py`: confianza baja < 0,60 ≤ media < 0,85 ≤ alta; latencia ≤ 300 ms dentro del objetivo |
| `InferenceGateway` como única frontera con el modelo (`DemoGateway` y bundle de S4) | `presentation.py`: `PredictionView` con textos prudentes y errores traducidos a código, mensaje, recuperación y `request_id` |
| Contrato de S4 (`WineQualityRequest`, `PredictionPayload`) | `controller.py`: `loading` → medir latencia → validar salida → `success`/`error`, con telemetría agregada |
| | `app.py`: gateway en `st.cache_resource`, `render_state()` para los 4 estados, botones «Reintentar» y «Limpiar último resultado» |

## 2. Comprobaciones

Desde `semana6/modules/06-ux-model-consumption/exercises/02-robust-streamlit/problem/starter`:

```bash
uv sync --extra app
uv run pytest -q                        # 8 passed
uv run ruff check src tests app.py      # All checks passed!
uv run ruff format --check src tests app.py
```

Arranque con el bundle de S4 (Git Bash):

```bash
export MODEL_UI_BUNDLE=/c/master/mlops/semana4/modules/04-model-packaging/exercises/01-model-packaging/01.02-serializable-inference-module/problem/starter/models/wine_quality_bundle
uv run streamlit run app.py
```

Sin `MODEL_UI_BUNDLE`, la app usa el `DemoGateway` heredado de S5. Con una ruta inválida, muestra el error «Modelo no disponible».

## 3. Recorridos (capturas en [`evidencias/`](evidencias/))

| Recorrido | Cómo provocarlo | Qué se observa | Evidencia |
|---|---|---|---|
| Inicio (`idle`) | Abrir la app con el bundle de S4 | Formulario de S5 en dos columnas y «Completa el formulario y pulsa «Ejecutar inferencia».». Telemetría a cero | `evidencias/1_inicio.png` |
| Éxito (`loading` → `success`) | Pulsar «Ejecutar inferencia» | `st.status` «Inferencia completada» y tres métricas: categoría, confianza y latencia. Mensaje de confianza y expander «Trazabilidad» con `request_id` y versiones | `evidencias/2_exito.png` |
| Rerun | Cambiar un campo **sin** enviar | El último resultado **sigue visible** (vive en `session_state`) | `evidencias/3_rerun.png` |
| Error (`error`) | Relanzar con `MODEL_UI_BUNDLE=/no/existe` y enviar | «Modelo no disponible. No se pudo cargar el modelo configurado.», la recuperación y el `request_id`. Sin traceback ni rutas | `evidencias/4_error.png` |
| Reintentar | Pulsar «Reintentar» | Nuevo intento con los mismos valores, nuevo `request_id`. La telemetría suma otro `artifact_unavailable` | `evidencias/5_reintentar.png` |
| Limpiar | Pulsar «Limpiar último resultado» | Vuelve a `idle`, pero la telemetría **conserva** los contadores | `evidencias/6_limpiar.png` |

`loading` dura solo unos milisegundos con el modelo local, así que en pantalla se ve cómo termina el `st.status`. Que el controlador emite `loading` antes de llamar al gateway lo comprueban los tests (`test_controller_emits_loading_then_success_...` y `..._error_...`).

**Respuesta lenta:** una salida válida con más de 300 ms sigue en `success` y solo añade el aviso «Por encima del objetivo». Lo comprueba `test_latency_and_confidence_are_explained_to_the_user` (450 ms → `above_target`, confianza 0,42 → `low` con el mensaje «requiere revisión… no es una garantía»).

## 4. Caché

Con `st.cache_resource` se cachea **el gateway** (el bundle cargado), construido por `build_gateway(MODEL_UI_BUNDLE)` y con la ruta del bundle como clave. Así el modelo se lee del disco **una sola vez** y no en cada rerun. **No** contiene datos de ninguna petición: la entrada y la predicción de cada persona viven solo en su `st.session_state`, porque un recurso cacheado se comparte entre sesiones.

## 5. Telemetría sin features

La sección «Telemetría de la sesión» muestra solo agregados. Ejemplo tras un éxito:

```json
{"requests_total": 1, "requests_success": 1, "requests_error": 0, "errors_by_code": {},
 "latency_mean_ms": 3.494, "latency_p95_ms": 3.494,
 "model_versions": ["wine-quality-rf-v1"], "preprocessing_versions": ["wine-red-features-v1"]}
```

No aparece ningún valor del formulario (`fixed_acidity`, `ph`…). Lo comprueba `test_controller_emits_loading_then_error_without_payload_telemetry`.

## 6. Qué se conserva para S7 (gateway HTTP)

- `PredictionController` no importa Streamlit: en S7 solo cambia el gateway que recibe.
- La interfaz `InferenceGateway.predict(values) -> PredictionPayload` es la misma, sea el bundle local o un cliente HTTP.
- Los errores se traducen por **tipo** (`InputContractError`, `ArtifactUnavailableError`, `InferenceTimeoutError`). Un cliente HTTP solo tendrá que convertir 422, 503 y timeout a esos mismos tipos.
- `session_state`, `cache_resource`, `render_state()` y la telemetría no cambian.
