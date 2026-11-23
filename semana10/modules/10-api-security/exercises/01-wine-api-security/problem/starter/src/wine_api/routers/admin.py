from fastapi import APIRouter, Depends

from wine_api.dependencies import RequestIdDep, SettingsDep
from wine_api.rate_limit import RateLimiterDep
from wine_api.schemas import ClientUsage, ErrorResponse, UsageResponse
from wine_api.security import require_scope

router = APIRouter(
    prefix="/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_scope("admin"))],
    responses={
        401: {"model": ErrorResponse, "description": "Clave ausente o incorrecta."},
        403: {"model": ErrorResponse, "description": "Falta el permiso admin."},
    },
)


@router.get(
    "/usage",
    summary="Consultar el consumo de los clientes",
    response_description="Peticiones y cuota de cada cliente en la ventana actual.",
)
def read_usage(
    settings: SettingsDep, limiter: RateLimiterDep, request_id: RequestIdDep
) -> UsageResponse:
    """Consulta las peticiones contadas durante la ventana actual de cada cliente.

    Requiere el permiso `admin`. Devuelve los nombres ordenados, el consumo y
    el límite por minuto. Las claves no forman parte de esta respuesta.
    """
    return UsageResponse(
        clients=[
            ClientUsage(
                client=name,
                requests_in_window=limiter.usage(name),
                limit=config.rate_limit_per_minute,
            )
            for name, config in sorted(settings.clients.items())
        ],
        request_id=request_id,
    )
