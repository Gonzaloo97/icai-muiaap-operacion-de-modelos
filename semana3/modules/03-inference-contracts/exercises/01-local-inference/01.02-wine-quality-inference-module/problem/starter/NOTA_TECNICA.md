# Nota técnica — Práctica 3.2: módulo local de inferencia

Especificación de partida: [lienzo de la práctica 3.1](../../../01.01-contract-and-preprocess-canvas/problem/LIENZO.md).

## 1. Flujo de una fila

```text
CSV ──► predict_file ──► contracts ──► preprocess ──► inference ──► contracts ──► CSV de salida
        (lee y orquesta)  (valida entrada)  (vector ordenado)  (modelo)   (valida salida)  (solo al final)
```

## 2. Responsabilidad de cada módulo

| Módulo | Responsabilidad | Lo que NO hace |
|---|---|---|
| `contracts.py` | Define la frontera de datos. `WineQualityRequest` exige las 11 features como `float`, con rangos razonables, y prohíbe columnas extra (`extra="forbid"`). `WineQualityPrediction` exige `sample_id` no vacío, una `quality_band` permitida (`needs_review`, `acceptable`, `excellent`), una `confidence` entre 0 y 1 y las dos versiones. | No lee ficheros ni llama al modelo. |
| `preprocess.py` | Convierte una petición ya validada en el vector numérico. Fija `FEATURE_NAMES` (el orden del entrenamiento) y `PREPROCESING_VERSION`. Excluye `sample_id`. | No lee el CSV ni valida rangos: eso ya lo hizo el contrato. |
| `inference.py` | Carga el `.joblib` y lo comprueba **antes** de inferir: (1) es un diccionario, (2) el estimador tiene `predict` y `predict_proba`, (3) `feature_names` coincide exactamente con `FEATURE_NAMES` y (4) `model_version` es un texto no vacío. Después predice la categoría y la confianza de un vector. | No conoce el CSV ni escribe ficheros. |
| `predict_file.py` | Orquesta el comando: lee el CSV, separa `sample_id`, encadena contrato → preprocesado → inferencia → contrato de salida y escribe el CSV. Convierte cualquier error en un mensaje por `stderr` y un código de salida 2. | No carga el `.joblib` directamente ni reimplementa validaciones. |

## 3. Decisiones de diseño

### Decisión 1: todo o nada en el CSV de salida (atomicidad)

Las predicciones se acumulan **en memoria** y el fichero de salida solo se abre cuando **todas** las filas han pasado la validación y la inferencia. Si la fila 2 es inválida, el error salta antes de abrir el fichero, así que no queda ningún CSV parcial.

- **Por qué:** un CSV con 1 de 5 filas parece un resultado válido, y otro proceso podría consumirlo sin saber que está incompleto. Es preferible fallar de forma visible.
- **Coste:** todas las predicciones se guardan en memoria. Con 5 muestras no importa; con millones de filas habría que escribir en un fichero temporal y renombrarlo al final.
- **Test:** `test_predict_file_leaves_no_output_when_a_later_row_is_invalid`.

### Decisión 2: validar el artefacto al cargarlo, no confiar en él

Antes de la primera predicción, el cargador comprueba la interfaz del estimador (`predict` y `predict_proba`), el orden de `feature_names` y la existencia de `model_version`.

- **Por qué:** el modelo solo ve números. Si se intercambian `density` y `alcohol`, sigue recibiendo 11 valores y predice **sin dar error**, pero mal. Comparar `feature_names` con `FEATURE_NAMES` convierte ese error silencioso en un error explícito. Sin `model_version`, la salida no sería trazable.
- **Coste:** un artefacto antiguo sin metadatos deja de cargarse y hay que regenerarlo.
- **Tests:** `test_predict_file_rejects_an_incompatible_model_artifact`, `test_predict_file_rejects_an_incomplete_model_artifact`, `test_load_rejects_an_estimator_without_predict` y `test_load_rejects_a_missing_model_version`.

## 4. Comprobación

Desde `problem/starter/`:

```bash
uv sync
uv run pytest                      # 13 passed
uv run ruff check src tests        # All checks passed!
uv run ruff format --check src tests
uv run python -m model_inference.predict_file --input assets/inference_samples.csv --output .tmp/wine_predictions.csv
```

Salida del último comando, con un clasificador de prueba de los tests (`DummyClassifier`) guardado en `models/wine_quality_classifier.joblib`:

```text
sample_id,quality_band,confidence,model_version,preprocessing_version
red-001,acceptable,1.0,wine-quality-rf-v1,wine-red-features-v1
red-002,acceptable,1.0,wine-quality-rf-v1,wine-red-features-v1
red-003,acceptable,1.0,wine-quality-rf-v1,wine-red-features-v1
red-004,acceptable,1.0,wine-quality-rf-v1,wine-red-features-v1
red-005,acceptable,1.0,wine-quality-rf-v1,wine-red-features-v1
```

Con el artefacto real del docente, la categoría y la confianza variarán por muestra; las columnas y las versiones son las mismas.
