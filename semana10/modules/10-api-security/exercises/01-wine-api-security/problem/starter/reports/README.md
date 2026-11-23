# S10.7 - Informe de carga

## Cómo se ha medido

| Dato | Valor |
| --- | --- |
| Fecha | 23/11/2026 |
| Comando de la API | `uv run fastapi dev` (un proceso servidor) |
| Comando de Locust | `uv run --group load locust -f locustfile.py --headless -u 20 -r 5 -t 1m --host http://127.0.0.1:8000 --csv reports/s10` |
| Carga | Hasta 20 usuarios, incorporando 5 por segundo, durante 1 minuto |
| Cliente usado | `front`; los 20 usuarios comparten su clave y cuota |
| `rate_limit_per_minute` | 60 |
| Máquina | Windows 11, compilación 26200; CPU Intel64 Family 6 Model 142 Stepping 12, GenuineIntel |

La clave se lee de `LOCUST_API_KEY`, sin incluirla en el código ni en este informe.
Los archivos de evidencia son `s10_stats.csv`, `s10_failures.csv`,
`s10_stats_history.csv` y `s10_exceptions.csv`.

## Resultados

| Endpoint | Peticiones | RPS | p50 (ms) | p95 (ms) | Fallos | % 429 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `POST /v1/predictions` | 718 | 12,10 | 9 | 140 | 664 | 92,48 % |
| `/v1/predictions [422]` | 86 | 1,45 | 9 | 190 | 80 | 93,02 % |
| `GET /health` | 102 | 1,72 | 7 | 140 | 0 | 0,00 % |
| Aggregated | 906 | 15,27 | 8 | 140 | 744 | 82,12 % |

El porcentaje de 429 de cada fila se calcula como sus respuestas 429 divididas
entre sus peticiones, multiplicado por 100. Por ejemplo, en las predicciones
válidas: `664 / 718 × 100 = 92,48 %`. En el total: `744 / 906 × 100 = 82,12 %`.
Los 6 resultados 422 de entradas inválidas se cuentan como éxitos de la prueba,
porque son la respuesta esperada. Los 80 resultados 429 de esa tarea se cuentan
como fallos porque impiden llegar a la validación de la entrada.

## Análisis

- Se solicitaron 804 predicciones: 718 con entrada válida y 86 con entrada inválida.
- La cuota dejó pasar exactamente 60: 54 predicciones correctas y 6 errores de validación esperados; las otras 744 recibieron 429.
- Los usuarios simulados comparten el cliente `front`, por lo que la cuota no se multiplica por 20.
- Las 102 consultas a `/health` se completaron sin fallos, porque no consumen cuota.
- `/health` tuvo p50 de 7 ms y p95 de 140 ms; las predicciones válidas tuvieron 9 ms y 140 ms, respectivamente.
- La latencia de predicciones incluye los rechazos 429, por lo que no representa solo el tiempo de inferencia. La prueba demuestra la cuota, no la capacidad máxima del servicio.
- Los dos tipos de fallo registrados son respuestas 429; no se registraron otros errores HTTP ni excepciones en Locust.
- Con dos workers, cada proceso tendría su propio contador y la cuota global podría llegar a duplicarse; un contador compartido en Redis o un API gateway evitaría esa separación.
- Para medir capacidad usaría un cliente de pruebas con permiso `predict` y una cuota bastante superior a la carga prevista, comprobando que no aparecen 429.
