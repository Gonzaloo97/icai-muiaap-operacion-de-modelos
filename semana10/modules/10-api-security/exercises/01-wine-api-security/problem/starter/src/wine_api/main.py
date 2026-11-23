"""Punto de entrada de la API: `fastapi dev` usa `wine_api.main:app`."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from wine_api.errors import install_error_handlers
from wine_api.predictor import Predictor, build_predictor
from wine_api.rate_limit import FixedWindowRateLimiter
from wine_api.request_id import request_id_middleware
from wine_api.routers import admin, health, predictions
from wine_api.settings import Settings

API_VERSION = "2.0.0"

API_DESCRIPTION = """
Las rutas protegidas requieren `X-API-Key`.
El scope `predict` permite predecir y `admin` permite consultar el consumo.
Sin clave válida se devuelve 401; sin permiso, 403.
Al agotar la cuota se devuelve 429 y `Retry-After` indica los segundos de espera.
`GET /health` es público y no consume cuota.

Servicio de inferencia del proyecto **Wine Quality** de Operación de Modelos.

- Todas las respuestas incluyen `request_id` y la cabecera `X-Request-Id`.
- Todos los errores comparten el sobre `ErrorResponse`; programa contra
  `error.code`, no contra `error.message`.
- La predicción es determinista y docente: no es una garantía de calidad.
"""

OPENAPI_TAGS = [
    {"name": "admin", "description": "Consumo por cliente; requiere permiso admin."},
    {"name": "health", "description": "Disponibilidad del servicio y del modelo."},
    {"name": "predictions", "description": "Inferencia de calidad de vino tinto."},
]


def create_app(
    predictor: Predictor | None = None,
    settings: Settings | None = None,
    rate_limiter: FixedWindowRateLimiter | None = None,
) -> FastAPI:
    """Crea la aplicación; los tests inyectan predictor, configuración y reloj."""

    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.predictor = predictor or build_predictor(settings.mode)
        yield

    app = FastAPI(
        title="Wine Quality API",
        version=API_VERSION,
        summary="Predicción de la banda de calidad de vinos tintos.",
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.state.settings = settings
    app.state.rate_limiter = rate_limiter or FixedWindowRateLimiter()

    app.middleware("http")(request_id_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
        expose_headers=["X-Request-Id", "Retry-After", "X-RateLimit-Remaining"],
    )
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(predictions.router)
    app.include_router(admin.router)
    return app


app = create_app()
