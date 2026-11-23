import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from wine_api.errors import install_error_handlers
from wine_api.predictor import Predictor, build_predictor
from wine_api.request_id import request_id_middleware
from wine_api.routers import health, predictions

API_VERSION = "1.1.0"


def create_app(predictor: Predictor | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.predictor = predictor or build_predictor(
            os.environ.get("WINE_API_MODE", "ready")
        )
        yield

    app = FastAPI(
        title="Wine Quality API",
        version=API_VERSION,
        summary="Predicción de la banda de calidad de vinos tintos.",
        description=(
            "Servicio de inferencia de Wine Quality. "
            "Las respuestas incluyen `request_id` y la cabecera `X-Request-Id`. "
            "Los errores usan `ErrorResponse`, con `error.code`, "
            "`error.message` y `error.fields` cuando hay campos inválidos."
        ),
        openapi_tags=[
            {"name": "health", "description": "Estado del servicio y del modelo."},
            {"name": "predictions", "description": "Predicciones de calidad del vino."},
        ],
        lifespan=lifespan,
    )
    app.middleware("http")(request_id_middleware)
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(predictions.router)
    return app


app = create_app()
