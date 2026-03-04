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

_OPENAPI_TAGS = [
    {
        "name": "chat",
        "description": (
            "Endpoints de conversa com os agentes de viagem. "
            "Suporta resposta JSON síncrona (`POST /chat`) e streaming "
            "token-a-token via Server-Sent Events (`POST /chat/stream`)."
        ),
    },
    {
        "name": "health",
        "description": (
            "Verificação de saúde da aplicação. "
            "Retorna o status dos serviços dependentes: Redis e ChromaDB."
        ),
    },
]


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
    description=(
        "API REST multi-agente para o setor de turismo.\n\n"
        "## Agentes\n\n"
        "| Agente | Função |\n"
        "|--------|--------|\n"
        "| **Orchestrator** | Analisa a pergunta e decide o roteamento |\n"
        "| **FAQ Agent** | Responde com base no Manual de Políticas de Viagem (RAG + ChromaDB) |\n"
        "| **Search Agent** | Busca informações em tempo real via Tavily |\n\n"
        "## Fluxo de roteamento\n\n"
        "```\n"
        "Pergunta → Orchestrator\n"
        "               ├── faq    → FAQ Agent (RAG)\n"
        "               ├── search → Search Agent (Tavily)\n"
        "               └── both   → FAQ Agent → Search Agent → Finalize\n"
        "```\n\n"
        "## Session memory\n\n"
        "Utilize o mesmo `session_id` em múltiplas requisições para manter "
        "o contexto da conversa. O histórico é persistido no Redis.\n\n"
        "## Segurança\n\n"
        "A API aplica guardrail de escopo — perguntas não relacionadas a viagens "
        "são recusadas. Proteção contra prompt injection está ativa."
    ),
    version=settings.app_version,
    contact={"name": "Blis AI", "url": "https://github.com/gumeeee/ai-engineer-test"},
    openapi_tags=_OPENAPI_TAGS,
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
