"""MCP Server — Blis AI Travel Agents.

Expõe os agentes de viagem como ferramentas para AI assistants
compatíveis com o Model Context Protocol (MCP).
"""

import uuid

from mcp.server.fastmcp import FastMCP

from src.config.settings import settings
from src.core.logging import get_logger, setup_logging

setup_logging(settings.log_level)
logger = get_logger(__name__)

mcp = FastMCP(
    "Blis AI Travel Agents",
    instructions=(
        "Você tem acesso ao sistema de agentes de viagem da Blis AI. "
        "Use query_travel_agent para perguntas gerais sobre viagens, políticas "
        "de bagagem, preços ou qualquer dúvida do setor de turismo. "
        "Use search_travel_policies para buscar trechos específicos do manual "
        "de políticas sem passar pelo pipeline completo de agentes."
    ),
)

from langgraph.checkpoint.memory import MemorySaver

from src.agents.orchestrator import build_graph

_graph = build_graph(checkpointer=MemorySaver())
logger.info("mcp_server.graph_initialized")


@mcp.tool()
async def query_travel_agent(message: str, session_id: str = "") -> str:
    """Consulta o agente de viagens Blis AI.

    Utiliza múltiplos agentes (FAQ com RAG e busca web em tempo real) para
    responder perguntas sobre políticas de bagagem, check-in, documentação,
    remarcação, reembolsos, preços de passagens e novidades do setor aéreo.

    Args:
        message: Pergunta sobre viagens a ser respondida.
        session_id: ID de sessão para manter contexto entre chamadas.
                    Gerado automaticamente se não informado.
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    config = {"configurable": {"thread_id": session_id}}

    result = await _graph.ainvoke(
        {
            "session_id": session_id,
            "question": message,
            "route": None,
            "faq_response": None,
            "search_response": None,
            "final_response": None,
            "agent_used": None,
            "sources": [],
        },
        config=config,  # type: ignore
    )

    response = result.get("final_response") or "Não foi possível obter uma resposta."
    agent_used = result.get("agent_used", "unknown")
    sources = result.get("sources", [])

    output = f"{response}\n\n**Agente utilizado:** {agent_used}"
    if sources:
        output += f"\n**Fontes:** {', '.join(sources)}"

    logger.info(
        "mcp_server.query_completed", agent_used=agent_used, session_id=session_id
    )
    return output


@mcp.tool()
def search_travel_policies(query: str) -> str:
    """Busca trechos relevantes do manual de políticas de viagem da Blis AI.

    Realiza busca por similaridade semântica no ChromaDB e retorna os chunks
    mais relevantes do manual, com indicação da página de origem.

    Args:
        query: Termo ou pergunta para buscar no manual de políticas.
    """
    from src.rag.retriever import get_retriever

    retriever = get_retriever()
    docs = retriever.invoke(query)

    if not docs:
        return (
            "Nenhuma informação encontrada para esta consulta no manual de políticas."
        )

    chunks = []
    for i, doc in enumerate(docs, 1):
        page = doc.metadata.get("page", 0) + 1
        source = doc.metadata.get("source", "manual-politicas-viagem-blis.pdf")
        chunks.append(f"**[{i}] {source} — Página {page}**\n{doc.page_content}")

    logger.info("mcp_server.search_completed", results=len(docs))
    return "\n\n---\n\n".join(chunks)


if __name__ == "__main__":
    mcp.run()
