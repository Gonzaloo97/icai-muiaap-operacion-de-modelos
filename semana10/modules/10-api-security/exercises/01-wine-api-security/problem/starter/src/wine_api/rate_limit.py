"""Rate limiting por cliente con una ventana fija.

El contador vive en la memoria del proceso: sirve para un único worker y para
aprender. Con varios workers o réplicas cada uno contaría por su lado; en
producción el estado va a Redis o el límite lo aplica el API gateway.
"""

import logging
import math
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request, Response

from wine_api.errors import RateLimitExceededError
from wine_api.security import ClientDep

logger = logging.getLogger("wine_api.rate_limit")


@dataclass(frozen=True)
class RateLimitDecision:
    """Resultado de contar una petición."""

    allowed: bool
    remaining: int
    retry_after: int


class FixedWindowRateLimiter:
    """Cuenta peticiones por clave en ventanas de `window_seconds`.

    `clock` es inyectable para que los tests avancen el tiempo sin esperar.
    `_windows` guarda, por clave, `(inicio de la ventana, peticiones contadas)`.
    """

    def __init__(
        self,
        window_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.window_seconds = window_seconds
        self.clock = clock
        self._windows: dict[str, tuple[float, int]] = {}
        # Las dependencias `def` corren en un threadpool: protege el contador.
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int) -> RateLimitDecision:
        """Cuenta una petición de `key` si cabe en su cuota de `limit`."""

        with self._lock:
            now = self.clock()
            start, count = self._windows.get(key, (now, 0))
            if now - start >= self.window_seconds:
                start, count = now, 0
            if count >= limit:
                retry_after = math.ceil(self.window_seconds - (now - start))
                return RateLimitDecision(False, 0, retry_after)
            count += 1
            self._windows[key] = (start, count)
            return RateLimitDecision(True, limit - count, 0)

    def usage(self, key: str) -> int:
        """Peticiones contadas para `key` en la ventana actual."""

        with self._lock:
            start, count = self._windows.get(key, (0.0, 0))
            if self.clock() - start >= self.window_seconds:
                return 0
            return count


def get_rate_limiter(request: Request) -> FixedWindowRateLimiter:
    """Devuelve el limitador compartido por todas las peticiones del proceso."""

    return request.app.state.rate_limiter


RateLimiterDep = Annotated[FixedWindowRateLimiter, Depends(get_rate_limiter)]


def enforce_rate_limit(
    client: ClientDep, limiter: RateLimiterDep, response: Response
) -> None:
    """Cuenta la petición del cliente autenticado o lanza un `429`."""

    decision = limiter.hit(client.name, client.rate_limit_per_minute)
    if not decision.allowed:
        raise RateLimitExceededError(decision.retry_after)
    response.headers["X-RateLimit-Limit"] = str(client.rate_limit_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
