# Semana 7: respuestas

### Ejercicio 1: llamada local frente a HTTP

| Caso | ¿Sale del proceso? | ¿Usa HTTP? | Acción o recurso |
| --- | --- | --- | --- |
| A: `infer_measurements(payload)` | No | No | Es una función local; no tiene ruta HTTP |
| B: `POST /runPumpModel` | Sí | Sí | Acción: ejecutar un modelo |
| C: `POST /v1/predictions` | Sí | Sí | Recurso: predicciones |

### Ejercicio 2: partes de una URL

Para `http://127.0.0.1:8000/v1/predictions/pred-42?include=explanation&limit=1`:

| Parte | Valor |
| --- | --- |
| Scheme / protocolo | `http` |
| Host | `127.0.0.1` |
| Puerto | `8000` |
| Path | `/v1/predictions/pred-42` |
| Query | `include=explanation` y `limit=1` |

El ID de la predicción va en el path. El límite de resultados va en la query.
Las cuatro medidas de la bomba van en el body JSON del POST.

### Ejercicio 3: JSON válido

```json
{"machine_id": "pump-017", "ready": true, "comment": null, "axes": [1, 2]}
```

JSON utiliza `true`, `null` y arrays con corchetes. En Python eran `True`,
`None` y una tupla. Esta comprobación convierte el JSON en un diccionario:

```python
import json

texto = '{"machine_id": "pump-017", "ready": true, "comment": null, "axes": [1, 2]}'
datos = json.loads(texto)
assert datos["ready"] is True
assert datos["comment"] is None
assert datos["axes"] == [1, 2]
```

### Ejercicio 4: códigos HTTP

| Caso | Código | Motivo |
| --- | --- | --- |
| Predicción correcta | 200 | La API ha procesado la petición |
| JSON truncado o ilegible | 400 | El cuerpo no se puede interpretar como JSON |
| `vibration_mm_s` vale `"alta"` | 422 | El JSON se puede leer, pero el dato no cumple el contrato |
| Modelo no disponible temporalmente | 503 | El servicio no puede atender la petición ahora |

### Ejercicio 5: crear y consultar

- Crear: `POST /v1/predictions`, con mediciones en el body JSON.
- Consultar: `GET /v1/predictions/pred-42`, con el ID en el path.
- Crear no es seguro y no se garantiza que sea idempotente: repetir el POST
  podría crear dos predicciones o ejecutar dos veces el cálculo.
- Consultar es seguro e idempotente: repetir el GET no debe modificar el recurso.

La ruta de consulta por ID forma parte del ejercicio de diseño; no se ha
añadido al servidor de caja negra, que solo ofrece salud y predicción.

**No se reintenta un POST a ciegas:** un timeout no demuestra que el servidor
no lo haya procesado; al repetirlo podríamos duplicar la operación.

## Contrato y errores de Wine

El recorrido es: Streamlit recoge el formulario; el controlador llama al
gateway; el gateway envía HTTP a la API; la API calcula la predicción; el
gateway valida el resultado y se lo devuelve al controlador para mostrarlo.

| Elemento | Contrato |
| --- | --- |
| Salud | `GET /health` |
| Inferencia | `POST /v1/predictions` |
| Cabeceras | `Accept: application/json`; `requests` añade `Content-Type: application/json` con `json=` |
| Entrada | `{"features": {...11 variables del vino...}}` |
| Salida | `{"prediction": {"quality_band": ..., "confidence": ..., "model_version": ..., "preprocessing_version": ...}, "request_id": ...}` |
| Espera máxima | 5 segundos por defecto |
| ID remoto | `last_request_id`, solo para diagnóstico; se conserva el ID local del controlador |

| Problema | Traducción en el gateway |
| --- | --- |
| HTTP 422 | `InputContractError`: corregir los datos |
| HTTP 503 | `ArtifactUnavailableError`: modelo temporalmente indisponible |
| Timeout | `InferenceTimeoutError`: se agotó la espera |
| Conexión fallida | `ArtifactUnavailableError`: revisar API y URL |
| Otro estado no 2xx, JSON incorrecto o salida incompatible | `BackendInferenceError` |

Los errores se clasifican antes de leer el body. Así también se reconoce un
503 aunque el servidor devuelva HTML. No se muestra el cuerpo remoto al usuario.
Los ejemplos JSON completos ya están en `modules/07-http-rest-clients/examples/wine-quality-api/samples/`.
