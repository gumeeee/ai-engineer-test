from collections.abc import Generator
from contextlib import contextmanager

from langgraph.checkpoint.memory import MemorySaver

from src.config.settings import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


@contextmanager
def checkpointer_context() -> Generator:
    """
    Context manager that yields a ready-to-use LangGraph checkpointer.

    Uses RedisSaver in development/production, falls back to MemorySaver
    when Redis is unavailable or in testing mode.
    """
    if settings.app_env == "testing" or not settings.redis_url:
        logger.info("checkpointer.using_memory_saver")
        yield MemorySaver()
        return

    try:
        from langgraph.checkpoint.redis import RedisSaver

        with RedisSaver.from_conn_string(settings.redis_url) as checkpointer:
            checkpointer.setup()
            logger.info("checkpointer.using_redis", url=settings.redis_url)
            yield checkpointer
    except Exception as e:
        logger.warning(
            "checkpointer.redis_failed_fallback",
            error=str(e),
        )
        yield MemorySaver()
