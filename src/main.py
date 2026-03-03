from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.agents.orchestrator import build_graph
from src.api.routes import chat, health
from src.config.settings import settings
from src.core.checkpointer import checkpointer_context
from src.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup and clean up on shutdown."""
    setup_logging(settings.log_level)
    logger.info("app.starting", env=settings.app_env, version=settings.app_version)

    async with checkpointer_context() as checkpointer:
        app.state.graph = build_graph(checkpointer=checkpointer)
        logger.info("app.graph_ready")
        yield

    logger.info("app.shutdown")


app = FastAPI(
    title="Blis AI Travel Agents",
    description="Multi-agent API for travel industry Q&A",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(health.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, e: Exception) -> JSONResponse:
    logger.error("app.unhandled_exception", path=request.url.path, erorr=str(e))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )
