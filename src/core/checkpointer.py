from langgraph.checkpoint.memory import MemorySaver

from src.config.settings import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


def get_checkpointer():
    """
    Return the appropriate checkpointer based on environment.

    Uses Redis in production/development, falls back to MemorySaver
    when Redis is unavailable or in testing mode.

    Returns:
        A LangGraph-compatible checkpointer instance.
    """
    if settings.app_env == "testing" or not settings.redis_url:
        logger.info("checkpointer.using_memory_saver")
        return MemorySaver()

    try:
        from langgraph.checkpoint.redis import RedisSaver

        checkpointer = RedisSaver.from_conn_string(settings.redis_url)
        logger.info("checkpointer.using_redis", url=settings.redis_url)
        return checkpointer
    except Exception as e:
        logger.warning(
            "checkpointer.redis_unavailable_fallback_to_memory",
            error=str(e),
        )
        return MemorySaver()
