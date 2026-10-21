# Nota de compatibilidad — Práctica 4.2: bundle serializado

Diseño de partida: [lienzo de la práctica 4.1](../../../01.01-artifact-contract/problem/LIENZO.md).

## 1. Qué es el bundle

```text
models/wine_quality_bundle/
├── manifest.json   # metadatos legibles: se valida PRIMERO
└── model.joblib    # estimador serializado: solo se carga si el manifiesto encaja
```

`manifest.json` generado en local a partir del modelo del docente de la semana 3 (`create_bundle --legacy`):

```json
{
  "schema_version": "wine-quality-bundle-v1",
  "model_version": "wine-quality-rf-v1",
  "preprocessing_version": "wine-red-features-v1",
  "feature_names": ["fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
                    "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide", "density",
                    "ph", "sulphates", "alcohol"],
  "output_labels": ["needs_review", "acceptable", "excellent"],
  "estimator_type": "RandomForestClassifier"
}
```

`estimator_type` se toma de la clase real del estimador guardado.

## 2. Responsabilidades

| Archivo | Responsabilidad |
|---|---|
| `contracts.py` (S3) | Valida cada fila de entrada y cada predicción de salida. Sin cambios. |
| `preprocess.py` (S3) | Fija el orden de las 11 features y la versión del preprocesado. Sin cambios. |
| `artifact.py` | Define `ArtifactManifest`, guarda el bundle, lo carga validando el manifiesto **antes** del binario e infiere validando la respuesta. |
| `predict_file.py` | Orquesta CSV → validación → bundle → CSV. Escribe la salida solo cuando todas las filas son válidas, primero en un temporal que después renombra. |
| `create_bundle.py` | Convierte el `.joblib` de la semana 3 al nuevo bundle (`--legacy`) o crea uno de demostración (`--demo`). |

## 3. Comprobaciones de compatibilidad (en orden)

| # | Comprobación | Dónde | Error si falla |
|---|---|---|---|
| 1 | Existen `manifest.json` y `model.joblib` | `load_model_bundle` | `FileNotFoundError` |
| 2 | `manifest.json` es un JSON válido | `load_model_bundle` | `ValueError: manifest.json no es un JSON válido` |
| 3 | El manifiesto tiene exactamente las 6 claves (`extra="forbid"`) | `ArtifactManifest` | `ValueError: Extra inputs are not permitted` |
| 4 | `schema_version`, `preprocessing_version`, `feature_names` y `output_labels` coinciden con el código | `ArtifactManifest` | `ValueError: … incompatible / no coincide` |
| 5 | Solo entonces se carga el binario, que debe tener `predict` y `predict_proba` | `load_model_bundle` | `ValueError: El estimador debe tener predict y predict_proba` |
| 6 | La clase del binario coincide con `estimator_type` | `load_model_bundle` | `ValueError: estimator_type incompatible` |
| 7 | Cada respuesta usa una etiqueta de `output_labels` y una confianza entre 0 y 1 | `infer_wine_quality` | `ValueError: quality_band no permitida` |

## 4. Dos cambios que deben bloquearse, y por qué

### Cambio 1: se reordenan las `feature_names` (por ejemplo, se intercambian `density` y `alcohol`)

- **Qué pasaría sin el bloqueo:** el modelo seguiría recibiendo 11 números y predeciría **sin dar error**, pero leería el alcohol (≈ 9.4) como densidad y la densidad (≈ 0.997) como alcohol. El resultado sería incorrecto en silencio, que es el peor fallo posible porque nadie lo detecta.
- **Dónde se bloquea:** en `ArtifactManifest`, al cargar, antes de deserializar `model.joblib`.
- **Tests:** `test_load_rejects_a_reordered_feature_contract`.

### Cambio 2: cambia `preprocessing_version` (por ejemplo, de `wine-red-features-v1` a `v2`)

- **Qué pasaría sin el bloqueo:** el modelo se entrenó con datos transformados de una forma concreta. Si el preprocesado cambia (otra escala, otra columna derivada…) pero el modelo no, los números que recibe ya no significan lo mismo que en el entrenamiento. `model_version` no lo detecta, porque el modelo sigue siendo el mismo: lo que ha cambiado es lo que lo rodea.
- **Dónde se bloquea:** en `ArtifactManifest`, al cargar.
- **Tests:** `test_load_rejects_another_preprocessing_version`.

**Otros cambios bloqueados:** `schema_version` desconocida, claves extra en el manifiesto, un `estimator_type` que no coincide con el binario (`test_load_rejects_a_different_estimator_type`), un manifiesto corrupto (`test_load_rejects_a_corrupt_manifest`) o ausente (`test_load_rejects_a_missing_manifest`), y una etiqueta de salida desconocida (`test_inference_rejects_an_unknown_model_label`).

**Límite:** el manifiesto comprueba **compatibilidad**, no **seguridad**. `joblib.load` puede ejecutar código, así que el `.joblib` solo debe cargarse si viene de una fuente de confianza.

**Riesgo observado y todavía no bloqueado: la versión de scikit-learn.** Al generar el bundle en local, scikit-learn avisó con `InconsistentVersionWarning`: el modelo del docente se serializó con la 1.9.0 y se cargó con la 1.9.1. El manifiesto actual no registra esa versión, así que el cargador no puede detectarlo; solo queda el aviso de la librería. Una mejora natural del esquema (`wine-quality-bundle-v2`) sería añadir una clave `sklearn_version` y rechazar, o al menos avisar, cuando no coincida con la del entorno. Mientras tanto, la versión queda fijada por `uv.lock`.

## 5. Política de filas: todo o nada

Si la fila `red-004` es inválida después de tres filas correctas, el comando termina con código 2, indica la fila (`error: Fila red-004: … ph …`) y **no publica ningún CSV**. Las predicciones se guardan en memoria y el fichero se escribe solo al final, primero como `.tmp` y después renombrado con `os.replace`.

- **Tests:** `test_predict_file_writes_nothing_when_a_later_row_is_invalid` y `test_cli_rejects_an_out_of_range_row_without_output`.

## 6. Comprobación

Desde `semana4/modules/04-model-packaging/exercises/01-model-packaging/01.02-serializable-inference-module/problem/starter/`:

```bash
uv sync
uv run pytest                          # 14 passed
uv run ruff check src tests            # All checks passed!
uv run ruff format --check src tests   # already formatted

# Bundle a partir del modelo del docente de la semana 3 (ruta absoluta:
# en Windows la ruta relativa con ../ supera el límite de 260 caracteres)
uv run python -m model_packaging.create_bundle --legacy /c/master/mlops/semana3/modules/03-inference-contracts/exercises/01-local-inference/01.02-wine-quality-inference-module/problem/starter/models/wine_quality_classifier.joblib

# Inferencia sobre las 5 muestras
uv run python -m model_packaging.predict_file --bundle models/wine_quality_bundle --input /c/master/mlops/semana3/assets/03-wine-quality/inference_samples.csv --output .tmp/wine_predictions.csv
```

Salida real con el modelo del docente (`RandomForestClassifier`, `wine-quality-rf-v1`):

```text
Predicciones escritas: 5

sample_id,quality_band,confidence,model_version,preprocessing_version
red-001,needs_review,0.86,wine-quality-rf-v1,wine-red-features-v1
red-002,needs_review,0.82,wine-quality-rf-v1,wine-red-features-v1
red-003,acceptable,0.62,wine-quality-rf-v1,wine-red-features-v1
red-004,needs_review,0.76,wine-quality-rf-v1,wine-red-features-v1
red-005,needs_review,0.73,wine-quality-rf-v1,wine-red-features-v1
```

Si no se dispone del modelo del docente, `create_bundle --demo` genera un bundle con un clasificador mínimo para comprobar la interfaz.

La carpeta `models/` está en `.gitignore`: el bundle se genera en local y no se sube al repositorio.
