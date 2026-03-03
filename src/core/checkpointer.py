from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from langgraph.checkpoint.memory import MemorySaver

from src.config.settings import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def checkpointer_context() -> AsyncGenerator:
    """
    Async context manager that yields a ready-to-use LangGraph checkpointer.

    Uses AsyncRedisSaver in production, falls back to MemorySaver
    when Redis is unavailable or in testing mode.
    """
    if settings.app_env == "testing" or not settings.redis_url:
        logger.info("checkpointer.using_memory_saver")
        yield MemorySaver()  # type: ignore
        return

    try:
        from langgraph.checkpoint.redis import AsyncRedisSaver

        async with AsyncRedisSaver.from_conn_string(settings.redis_url) as checkpointer:
            await checkpointer.setup()
            logger.info("checkpointer.using_redis", url=settings.redis_url)
            yield checkpointer
    except Exception as e:
        logger.warning(
            "checkpointer.redis_failed_fallback",
            error=str(e),
        )
        yield MemorySaver()
