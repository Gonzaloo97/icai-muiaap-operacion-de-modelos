# Lienzo — Práctica 3.1: contrato y preprocesado

Versión ejecutada con todas las respuestas: [01-inferencia-y-contratos-alumno.ipynb](01-inferencia-y-contratos-alumno.ipynb).
Implementación que lo cumple: [nota técnica de la práctica 3.2](../../01.02-wine-quality-inference-module/problem/starter/NOTA_TECNICA.md).

## 1. Entrenamiento, artefacto y datos nuevos

| Pieza | Qué es | Qué recibe esa frontera |
|---|---|---|
| Datos de entrenamiento | CSV histórico de vinos tintos **con** la etiqueta de calidad | Solo el docente, una vez, para entrenar. Nuestro módulo nunca lo ve. |
| Artefacto | `models/wine_quality_classifier.joblib`: `estimator` + `feature_names` + `model_version` | Nuestro módulo solo lo **carga y comprueba**; no lo reentrena. |
| Datos nuevos | `assets/inference_samples.csv`: 5 muestras **sin** etiqueta | Nuestro módulo las valida y les pide una predicción. |

## 2. Tabla del contrato de entrada (11 campos)

| # | Campo | Tipo | Unidad | Límite razonable | ¿Admite ausentes? |
|---|---|---|---|---|---|
| 1 | `fixed_acidity` | float | g ácido tartárico / dm³ | 0 – 20 | No |
| 2 | `volatile_acidity` | float | g ácido acético / dm³ | 0 – 2 | No |
| 3 | `citric_acid` | float | g / dm³ | 0 – 2 | No |
| 4 | `residual_sugar` | float | g / dm³ | 0 – 20 | No |
| 5 | `chlorides` | float | g cloruro sódico / dm³ | 0 – 1 | No |
| 6 | `free_sulfur_dioxide` | float | mg / dm³ | 0 – 100 | No |
| 7 | `total_sulfur_dioxide` | float | mg / dm³ | 0 – 300 | No |
| 8 | `density` | float | g / cm³ | 0.98 – 1.01 | No |
| 9 | `ph` | float | sin unidad (escala pH) | 2.5 – 4.5 | No |
| 10 | `sulphates` | float | g sulfato potásico / dm³ | 0 – 3 | No |
| 11 | `alcohol` | float | % vol | 5 – 20 | No |

- `sample_id` (texto, no vacío) identifica la fila, pero **no** entra en el vector del modelo.
- No se permite ninguna columna adicional (`extra="forbid"`).
- Ningún campo admite ausentes: el modelo no se entrenó con huecos y no se imputan valores.

**Contrato de salida:** `sample_id`, `quality_band` (`needs_review` | `acceptable` | `excellent`), `confidence` (0 – 1), `model_version` y `preprocessing_version`.

## 3. Mapa de flujo

```text
CSV ──► solicitud ──► preprocesado ──► vector ──► artefacto ──► predicción ──► CSV de salida
     (WineQuality     (FEATURE_NAMES)   (11 floats   (.joblib      (WineQuality    (solo si TODAS
      Request)                           ordenados)   comprobado)   Prediction)     las filas OK)
```

## 4. Orden exacto del vector

`fixed_acidity, volatile_acidity, citric_acid, residual_sugar, chlorides, free_sulfur_dioxide, total_sulfur_dioxide, density, ph, sulphates, alcohol`

**Por qué el orden es parte del contrato:** si se intercambian `density` (≈ 0.997) y `alcohol` (≈ 9.4), el vector sigue teniendo 11 números y el modelo predice **sin dar error**. Lee 9.4 como densidad y 0.997 como alcohol, así que la predicción es incorrecta en silencio. Por eso `FEATURE_NAMES` se define una sola vez y se compara con los `feature_names` del artefacto antes de predecir.

## 5. Casos de fallo y etapa de rechazo

| Caso | Entrada | Etapa en la que falla | Motivo |
|---|---|---|---|
| Válida | `red-001` tal cual del CSV | — (genera predicción) | Cumple tipos, rangos y columnas |
| Columna desconocida | `red-001` + `unexpected_field=not allowed` | **Solicitud** (`WineQualityRequest`) | `extra_forbidden`: columna fuera del contrato |
| Fuera de rango | `red-001` con `ph=99` | **Solicitud** (`WineQualityRequest`) | `less_than_equal`: pH imposible |
| Tipo imposible | `alcohol=invalid` | **Solicitud** (`WineQualityRequest`) | No se puede convertir a `float` |
| Campo ausente | fila sin `alcohol` | **Solicitud** (`WineQualityRequest`) | Campo obligatorio |
| Orden distinto en el artefacto | `feature_names` invertidos en el `.joblib` | **Artefacto** (al cargar) | No coincide con `FEATURE_NAMES` |
| Etiqueta no permitida | el modelo devuelve `unknown` | **Predicción** (`WineQualityPrediction`) | `quality_band` fuera de las tres categorías |

En todos los casos de fallo el comando termina con código 2, muestra el error por `stderr` y **no deja CSV de salida**.

## 6. Criterios de aceptación y comando local que los demuestra

Desde `semana3/.../01.02-wine-quality-inference-module/problem/starter/`:

| # | Criterio | Cómo se demuestra |
|---|---|---|
| 1 | Una fila válida genera una predicción con `sample_id`, `quality_band`, `confidence`, `model_version` y `preprocessing_version` | `uv run python -m model_inference.predict_file --input assets/inference_samples.csv --output .tmp/wine_predictions.csv` → `Predicciones escritas: 5` y un CSV con esas 5 columnas |
| 2 | Una columna extra, un campo ausente o un valor fuera de rango detienen el comando (código 2) y **no queda CSV de salida**, ni siquiera parcial | `uv run pytest tests/test_predict_file.py -k "rejects or leaves_no_output"` |
| 3 | Si el artefacto no tiene `predict`/`predict_proba`, `model_version` o el mismo orden de `feature_names`, el comando se niega a predecir | `uv run pytest tests/test_predict_file.py -k "artifact"` y `uv run pytest tests/test_inference_components.py` |

Comprobación completa en local:

```bash
uv sync
uv run pytest
uv run ruff check src tests
uv run ruff format --check src tests
uv run python -m model_inference.predict_file --input assets/inference_samples.csv --output .tmp/wine_predictions.csv
```

## Plan de implementación (clase 2)

- `contracts.py`: `WineQualityRequest` (11 campos, rangos, `extra="forbid"`) y `WineQualityPrediction`.
- `preprocess.py`: `FEATURE_NAMES`, la versión de preprocesado y `preprocess_wine_request`, que devuelve el vector ordenado.
- `inference.py`: cargar el `.joblib`, comprobar el clasificador, `feature_names` y `model_version`, y predecir categoría y confianza.
- `predict_file.py`: leer el CSV, validar e inferir **todas** las filas en memoria y escribir el CSV solo al final.
