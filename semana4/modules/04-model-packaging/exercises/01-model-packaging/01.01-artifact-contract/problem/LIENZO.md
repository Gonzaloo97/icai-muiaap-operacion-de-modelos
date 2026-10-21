# Lienzo — Práctica 4.1: contrato del artefacto y manifiesto

Versión ejecutada con todas las respuestas: [01-artefacto-y-manifiesto-alumno.ipynb](01-artefacto-y-manifiesto-alumno.ipynb).  
Implementación que lo cumple: [nota de compatibilidad de la práctica 4.2](../../01.02-serializable-inference-module/problem/starter/NOTA_COMPATIBILIDAD.md).

## 1. Tabla de almacenamiento: binario, manifiesto y código

| Elemento | ¿Dónde vive? | ¿Qué riesgo evita? |
| --- | --- | --- |
| Estimador entrenado | **model.joblib** | Es el objeto ejecutable. Separarlo permite revisar los metadatos **sin** deserializarlo, porque `joblib.load` puede ejecutar código. |
| Versión del esquema | **manifest.json** (`schema_version`) | Que el cargador intente leer un bundle de un formato que no conoce (claves con otro significado). |
| Orden y nombres de features | **manifest.json** (`feature_names`) + comparado en el **código** con `FEATURE_NAMES` | Que el modelo reciba las 11 columnas en otro orden y prediga mal **sin dar error**. |
| Versión del preprocesado | **manifest.json** (`preprocessing_version`) + comparada en el **código** con `PREPROCESSING_VERSION` | Usar el modelo con una transformación de datos distinta a la del entrenamiento. |
| Etiquetas de salida permitidas | **manifest.json** (`output_labels`) + validadas en el **código** con `WineQualityPrediction` | Que la respuesta exponga una categoría que la interfaz no conoce (`unknown`). |
| Versión del modelo | **manifest.json** (`model_version`) | Salidas no trazables: no saber qué modelo generó cada predicción. |
| Tipo de estimador | **manifest.json** (`estimator_type`) + comprobado en el **código** contra el binario cargado | Que se haya cambiado el binario por otro objeto distinto del declarado. |
| Reglas de validación (rangos, `extra="forbid"`, todo o nada) | **Código** (`contracts.py`, `artifact.py`, `predict_file.py`) y **tests** | Son comportamiento, no datos: se versionan con el código y se prueban. |

## 2. Manifiesto propuesto

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

- `model_version` identifica **el modelo entrenado**; `preprocessing_version` identifica **la transformación de los datos**. Son cosas distintas: se puede reentrenar el modelo sin cambiar el preprocesado, y al revés.
- `output_labels` limita las categorías que puede exponer la respuesta a las tres del contrato de la semana 3.

## 3. Invariantes del cargador

Bloquean la carga o la inferencia **antes** de escribir resultados:

1. **El manifiesto existe, es JSON válido y tiene exactamente las 6 claves** (sin claves extra).
2. **`schema_version` y `preprocessing_version` coinciden** con las que entiende el código.
3. **`feature_names` coincide exactamente** (nombres y orden) con `FEATURE_NAMES` de la semana 3.
4. **El estimador tiene `predict` y `predict_proba`**, y su clase coincide con `estimator_type`.
5. **Cada respuesta usa una etiqueta de `output_labels`** y una confianza entre 0 y 1.

## 4. Matriz de compatibilidad (romper el contrato)

| Cambio | Frontera que debe rechazarlo | Mensaje útil esperado | ¿Se escribe CSV? |
| --- | --- | --- | --- |
| Se intercambian `density` y `alcohol` | **Carga del bundle**: validación del manifiesto, antes de deserializar `model.joblib` | `feature_names no coincide con FEATURE_NAMES` | **No** |
| Cambia `preprocessing_version` | **Carga del bundle**: validación del manifiesto | `preprocessing_version incompatible: se esperaba wine-red-features-v1` | **No** |
| El modelo devuelve `unknown` | **Inferencia**: validación de la salida (`output_labels` / `WineQualityPrediction`) | `quality_band no permitida: unknown` | **No** (el error para todo el lote) |
| La petición incluye `ph = 99` | **Entrada**: `WineQualityRequest`, antes de preprocesar | `Fila red-001: ph … less than or equal to 4.5` | **No** |
| `estimator_type` no coincide con el binario | **Carga del bundle**: después de deserializar, antes de inferir | `estimator_type incompatible` | **No** |

## 5. Política de errores: filas inválidas y salida atómica

Si la segunda fila del CSV es inválida después de una primera correcta, el comando **se detiene**, informa de la fila y el campo (`error: Fila red-002: …`), sale con código **2** y **no publica ningún CSV**, ni siquiera con la primera fila.

**Por qué:** una salida parcial parece un resultado válido. Otro proceso podría consumirla sin saber que faltan filas, y el error pasaría desapercibido. Por eso las predicciones se acumulan en memoria y el fichero se escribe solo al final: primero como `.tmp` y después se renombra (`os.replace`), de modo que nunca existe un CSV a medio escribir.

**Límite:** el manifiesto comprueba **compatibilidad**, no seguridad. `joblib.load` puede ejecutar código, así que el binario solo debe cargarse si viene de una fuente de confianza.
