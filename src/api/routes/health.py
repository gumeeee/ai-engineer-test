from fastapi import APIRouter

from src.api.schemas.chat import HealthResponse
from src.config.settings import settings
from src.core.logging import get_logger

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint verifying Redis and vector store status."""
    redis_status = _check_redis()
    vectorstore_status = _check_vectorstore()

    return HealthResponse(
        status="healthy",
        redis=redis_status,
        vectorstore=vectorstore_status,
        version=settings.app_version,
    )


def _check_redis() -> str:
    try:
        import redis

        r = redis.from_url(settings.redis_url, socket_connect_timeout=2)
        r.ping()
        return "connected"
    except Exception as e:
        logger.warning("health.redis_unavailable", error=str(e))
        return "disconnected"


def _check_vectorstore() -> str:
    try:
        from src.rag.vectorstore import is_vectorstore_populated

        return "ready" if is_vectorstore_populated() else "empty"
    except Exception as exc:
        logger.warning("health.vectorstore_error", error=str(exc))
        return "error"
