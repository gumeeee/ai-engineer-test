from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config.settings import settings


def get_graph(request: Request):
    """Inject the compiled LangGraph graph from app state.

    The graph is built once at startup via lifespan and stored in app.state.
    """
    return request.app.state.graph


def _build_limiter() -> Limiter:
    """
    Build the rate limiter, using Redis backend when available.
    """
    if settings.redis_url:
        return Limiter(
            key_func=get_remote_address,
            storage_uri=settings.redis_url,
            in_memory_fallback_enabled=True,
        )
    return Limiter(key_func=get_remote_address)


limiter = _build_limiter()
