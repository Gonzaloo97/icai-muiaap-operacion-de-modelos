# Lienzo — Práctica 3.1: contrato y preprocesado



### 1. Entrenamiento, artefacto y datos nuevos

| Pieza | Qué es | Quién la usa |
|---|---|---|
| Datos de entrenamiento | CSV histórico de vinos tintos **con** la etiqueta de calidad | El docente, una sola vez, para entrenar |
| Artefacto | `models/wine_quality_classifier.joblib`: modelo ya entrenado + `feature_names` + `model_version` | Nuestro módulo: solo lo carga, no lo reentrena |
| Datos nuevos | `inference_samples.csv`: 5 muestras **sin** etiqueta | Nuestro módulo: les pide una predicción |

### 2. Tabla del contrato de entrada (11 campos)

| # | Campo | Tipo | Unidad | Límite razonable |
|---|---|---|---|---|
| 1 | `fixed_acidity` | float | g ácido tartárico / dm³ | 0 – 20 |
| 2 | `volatile_acidity` | float | g ácido acético / dm³ | 0 – 2 |
| 3 | `citric_acid` | float | g / dm³ | 0 – 2 |
| 4 | `residual_sugar` | float | g / dm³ | 0 – 20 |
| 5 | `chlorides` | float | g cloruro sódico / dm³ | 0 – 1 |
| 6 | `free_sulfur_dioxide` | float | mg / dm³ | 0 – 100 |
| 7 | `total_sulfur_dioxide` | float | mg / dm³ | 0 – 300 |
| 8 | `density` | float | g / cm³ | 0.98 – 1.01 |
| 9 | `ph` | float | sin unidad (escala pH) | 2.5 – 4.5 |
| 10 | `sulphates` | float | g sulfato potásico / dm³ | 0 – 3 |
| 11 | `alcohol` | float | % vol | 5 – 20 |

`sample_id` (texto, no vacío) identifica la fila, pero **no** entra en el modelo. No se permite ninguna columna adicional.

### 3. Ejemplos de fila

**Válida (red-001):**

```text
sample_id=red-001, fixed_acidity=7.4, volatile_acidity=0.7, citric_acid=0.0, residual_sugar=1.9,
chlorides=0.076, free_sulfur_dioxide=11.0, total_sulfur_dioxide=34.0, density=0.9978,
ph=3.51, sulphates=0.56, alcohol=9.4
```

**Inválida (columna no permitida):** la misma fila con `unexpected_field=not allowed` produce un error `extra_forbidden` y el script se detiene.

**Otros casos de fallo:** `ph=99` (fuera de rango), `alcohol=invalid` (no es un número), falta `alcohol` (campo obligatorio) y `sample_id` vacío.

### 4. Orden exacto del vector

`fixed_acidity, volatile_acidity, citric_acid, residual_sugar, chlorides, free_sulfur_dioxide, total_sulfur_dioxide, density, ph, sulphates, alcohol`

### 5. Criterios de aceptación del script de la clase 2

1. Una fila válida genera una predicción con `sample_id`, `quality_band`, `confidence`, `model_version` y `preprocessing_version`.
2. Una columna extra, un campo que falte o un valor fuera de rango detienen el script con un error claro (código de salida 2) y **no se escribe ningún CSV de salida**, ni siquiera parcial.
3. Si los `feature_names` del artefacto no coinciden con `FEATURE_NAMES`, el script se niega a predecir.

### Plan de implementación (clase 2)

- `contracts.py`: `WineQualityRequest` (11 campos, rangos, `extra="forbid"`) y `WineQualityPrediction`.
- `preprocess.py`: `FEATURE_NAMES`, `PREPROCESSING_VERSION` y `preprocess_wine_request`, que devuelve el vector ordenado.
- `inference.py`: cargar el `.joblib`, comprobar el clasificador y `feature_names`, y predecir categoría y confianza.
- `predict_file.py`: leer el CSV, validar e inferir **todas** las filas en memoria y escribir el CSV solo al final.
