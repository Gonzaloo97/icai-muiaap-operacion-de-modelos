import logging
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Security
from fastapi.security import APIKeyHeader

from wine_api.dependencies import RequestIdDep, SettingsDep
from wine_api.errors import AuthenticationError, PermissionDeniedError
from wine_api.settings import Scope

logger = logging.getLogger("wine_api.security")
API_KEY_HEADER = "X-API-Key"
api_key_header = APIKeyHeader(
    name=API_KEY_HEADER,
    auto_error=False,
    description="Clave del cliente. Predicciones requiere predict; consumo, admin.",
)


@dataclass(frozen=True)
class AuthenticatedClient:
    name: str
    scopes: frozenset[str]
    rate_limit_per_minute: int


def authenticate_client(
    settings: SettingsDep,
    request_id: RequestIdDep,
    api_key: Annotated[str | None, Security(api_key_header)],
) -> AuthenticatedClient:
    if api_key:
        for name, config in settings.clients.items():
            if secrets.compare_digest(
                api_key.encode(), config.key.get_secret_value().encode()
            ):
                return AuthenticatedClient(
                    name=name,
                    scopes=frozenset(config.scopes),
                    rate_limit_per_minute=config.rate_limit_per_minute,
                )
    logger.warning("Authentication failed request_id=%s", request_id)
    raise AuthenticationError()


ClientDep = Annotated[AuthenticatedClient, Security(authenticate_client)]


def require_scope(scope: Scope) -> Callable[..., AuthenticatedClient]:
    def check_scope(client: ClientDep) -> AuthenticatedClient:
        if scope not in client.scopes:
            raise PermissionDeniedError()
        return client

    return check_scope
