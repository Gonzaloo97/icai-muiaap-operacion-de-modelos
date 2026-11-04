# Práctica 5.2 — Frontal Wine sobre el bundle de S4: ejecución y QA

## 1. Bundle de S4

La app carga el bundle generado en la semana 4 (rama `feature/s4-model-packaging`) a partir del modelo del docente:

```text
semana4/modules/04-model-packaging/exercises/01-model-packaging/01.02-serializable-inference-module/problem/starter/models/wine_quality_bundle/
├── manifest.json
└── model.joblib
```

El binario **no se sube al repositorio** (la carpeta `models/` está en `.gitignore`). Para regenerarlo, desde el starter de la semana 4:

```bash
uv run python -m model_packaging.create_bundle --legacy RUTA/A/wine_quality_classifier.joblib
```

## 2. Configuración y arranque

La ruta apunta a la **carpeta** del bundle, no a `model.joblib`.

Desde `semana5/modules/05-streamlit-basic-model-ui/exercises/02-first-streamlit/problem/starter`:

**Git Bash**

```bash
export MODEL_UI_BUNDLE=/c/master/mlops/semana4/modules/04-model-packaging/exercises/01-model-packaging/01.02-serializable-inference-module/problem/starter/models/wine_quality_bundle
uv sync
uv run python -m pytest -q                      # 27 passed
uv run ruff check app.py src tests
uv run ruff format --check app.py src tests
uv run --with 'streamlit>=1.40,<2.0' streamlit run app.py
```

**PowerShell**

```powershell
$env:MODEL_UI_BUNDLE = 'C:\master\mlops\semana4\modules\04-model-packaging\exercises\01-model-packaging\01.02-serializable-inference-module\problem\starter\models\wine_quality_bundle'
uv run --with 'streamlit>=1.40,<2.0' streamlit run app.py
```

Salida de las comprobaciones:

```text
27 passed
All checks passed!
13 files already formatted
```

## 3. Matriz de QA (4 casos)

Capturas en [`evidencias/`](evidencias/).

| Caso | Acción | Resultado esperado | Resultado observado | Evidencia |
|---|---|---|---|---|
| 1. Arranque con bundle | `MODEL_UI_BUNDLE` apuntando al bundle de S4 y abrir la app | Once campos y ninguna inferencia | ✅ Se muestran los 11 campos con sus valores por defecto y el mensaje «Completa el formulario y pulsa «Ejecutar inferencia».» | `evidencias/1_arranque.png` |
| 2. Edición sin envío | Cambiar uno o varios valores (p. ej. `Alcohol`) | El formulario cambia y no hay llamadas al gateway | ✅ Los valores cambian, pero no aparece ningún resultado | `evidencias/2_edicion.png` |
| 3. Submit válido | Pulsar «Ejecutar inferencia» | Una llamada y las cuatro salidas | ✅ Aparecen `quality_band`, `confidence`, `model_version: wine-quality-rf-v1` y `preprocessing_version: wine-red-features-v1` | `evidencias/3_submit.png` |
| 4. Bundle ausente | Quitar la variable (`unset MODEL_UI_BUNDLE`) y relanzar | Mensaje accionable con `MODEL_UI_BUNDLE`, sin ruta ni traceback | ✅ «No se pudo cargar el bundle de S4.» y «Configura MODEL_UI_BUNDLE y vuelve a ejecutar la aplicación.», sin rutas ni traceback | `evidencias/4_sin_bundle.png` |

## 4. Responsabilidades

- `app.py` solo dibuja el formulario (`collect_values`) y el resultado (`render_prediction`). No carga `joblib` ni preprocesa.
- `gateway.predict(values)` es la **única** frontera con el modelo: valida la muestra con el contrato de S3/S4 y llama al bundle.
- Los dobles del gateway (`RecordingGateway`, `FailingGateway`) existen solo en `tests/`.

## 5. Límites que se dejan para S6

1. **El resultado no se conserva:** al recargar la página o volver a abrir la app, la predicción desaparece, porque no hay estado de sesión (`session_state`).
2. **El bundle se carga en cada ejecución del script:** Streamlit re-ejecuta `app.py` en cada interacción y no hay caché del gateway, de modo que el modelo se vuelve a leer del disco una y otra vez.

Tampoco hay telemetría (latencia, número de errores) ni un control explícito de estados (cargando, éxito, error, reintento).
