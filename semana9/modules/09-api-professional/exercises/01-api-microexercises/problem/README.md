# Ejercicio 01 — Microejercicios de la clase 1

Cuatro microejercicios de 5 minutos, uno al final de cada bloque de teoría. Se
hacen sobre las demos de [`examples/`](../../../examples/README.md) y no
requieren escribir una API nueva.

Prepara el entorno una vez, desde `semana9/modules/09-api-professional`:

```bash
uv sync --locked
```

## M1 — Serialización (bloque 1)

Arranca `uv run fastapi dev examples/serialization_demo.py` y compara
`/v1/scores/leaky` con `/v1/scores/public`.

1. Anota qué campos aparecen en la primera respuesta y no en la segunda.
2. Explica en una frase por qué `/v1/scores/filtered` tampoco los devuelve,
   aunque la función devuelve un `dict` con todos ellos.
3. En `/docs`, abre el esquema `PublicScore`: ¿aparece `is_reliable`?

**Comprobación:** tu respuesta a la pregunta 2 menciona `response_model` y
qué hace con los campos que no declara.

## M2 — Errores (bloque 2)

Arranca `uv run fastapi dev examples/errors_demo.py` y envía, desde `/docs` o
con `curl`, tres peticiones a `POST /v1/scores`:

- `{"age": 30, "income": 1000}`
- `{"age": "treinta", "income": 1000}`
- `{"age": 30}`

Después llama a `GET /v1/nada` y a `GET /v1/boom`.

1. Rellena una tabla con status, `error.code` y `error.fields` de cada caso.
2. ¿Qué devolvería FastAPI en el segundo caso si borraras `handle_validation`?
   Pruébalo comentando el decorador y restáuralo después.

**Comprobación:** las cinco respuestas de error tienen la clave `error` en la
raíz y ninguna contiene el texto `TU_SECRETO`.

## M3 — OpenAPI (bloque 3)

Arranca `uv run fastapi dev examples/openapi_demo.py`.

1. Localiza en `/openapi.json` dónde terminan `summary`, el docstring y
   `responses` de `create_score`.
2. Ejecuta el ejemplo `minor` desde Swagger con «Try it out».
3. Añade un tercer ejemplo `no_income` sin el campo `income` y comprueba que
   aparece en el desplegable.

**Comprobación:** `uv run pytest -q` sigue en verde y el desplegable muestra
tres ejemplos. Deshaz el cambio al terminar o adapta el test que cuenta los
ejemplos.

## M4 — Tests (bloque 4)

Abre [`tests/test_examples.py`](../../../tests/test_examples.py).

1. Ejecuta `uv run pytest -q` y localiza el test que usa `dependency_overrides`.
2. Elimina temporalmente `raise_server_exceptions=False` del fixture
   `errors_client` y vuelve a ejecutar. Explica qué cambia.
3. Escribe un test nuevo que compruebe que `income: 0` devuelve `422` con
   `fields[0].field == "income"`.

**Comprobación:** la suite vuelve a estar en verde con tu test incluido.

La [solución comentada](../solution/README.md) se comparte al final de la clase.

## Respuestas

### M1

1. `/leaky` muestra `raw_score` y `threshold_config`; `/public` no los muestra.
2. `response_model=PublicScore` valida la salida y filtra los campos que no declara, aunque la función devuelva un diccionario con ellos.
3. Sí: `is_reliable` aparece como booleano de solo lectura, calculado a partir de `confidence`.

### M2

| Petición | Status | `error.code` | `error.fields` |
| --- | --- | --- | --- |
| `POST /v1/scores`, `{"age":30,"income":1000}` | 200 | No hay error | No aparece; respuesta `{"score":0.01}` |
| `POST /v1/scores`, `{"age":"treinta","income":1000}` | 422 | `validation_error` | `[{"field":"age","message":"Input should be a valid integer, unable to parse string as an integer"}]` |
| `POST /v1/scores`, `{"age":30}` | 422 | `validation_error` | `[{"field":"income","message":"Field required"}]` |
| `GET /v1/nada` | 404 | `not_found` | No aparece |
| `GET /v1/boom` | 500 | `internal_error` | No aparece |

La primera petición es válida: hay cuatro respuestas de error, no cinco.
Sin el manejador personalizado, FastAPI devuelve 422 con `detail`, que contiene `type`, `loc`, `msg` e `input`, en lugar del sobre `error`.
El 500 devuelve un mensaje genérico y no muestra el texto de la excepción.

### M3

En `paths["/v1/scores"]["post"]`, el resumen está en `summary`, el docstring en `description` y los códigos de respuesta en `responses`.
El ejemplo `minor` devuelve 422 porque `age=16` incumple el mínimo de 18.
Se ha añadido `no_income` con `{"age":30}`; devuelve 422 porque falta `income`.
El contrato incluye los tres ejemplos `valid`, `minor` y `no_income`; el test comprueba los tres.

### M4

El test `test_dependency_override_simulates_unavailable_model` sustituye `get_model` por un modelo no disponible y comprueba el 503.
Sin `raise_server_exceptions=False`, la llamada a `/v1/boom` propaga `RuntimeError` al test en lugar de permitir comprobar la respuesta 500.
El test añadido, `test_zero_income_returns_422`, comprueba el status 422, `validation_error` y `fields[0].field == "income"`.
