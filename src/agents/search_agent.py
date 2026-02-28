from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.agents.prompts import SEARCH_AGENT_PROMPT
from src.agents.state import AgentState
from src.config.settings import settings
from src.core.logging import get_logger
from src.tools.web_search import run_web_search

logger = get_logger(__name__)


def _format_search_results(results: list[dict]) -> str:
    """Format search results into a readable context string.

    Args:
        results: List of result dicts with url, title, content.

    Returns:
        Formatted string with numbered results.
    """
    if not results:
        return "Nenhum resultado encontrado."

    parts = []
    for i, result in enumerate(results, start=1):
        title = result.get("title", "Sem título")
        content = result.get("content", "")
        url = result.get("url", "")
        parts.append(f"[{i}] {title}\nURL: {url}\n{content}")

    return "\n\n".join(parts)


def _extract_sources(results: list[dict]) -> list[str]:
    """Extract URLs from search results as source references.

    Args:
        results: List of result dicts from Tavily.

    Returns:
        List of URL strings.
    """
    return [r.get("url", "") for r in results if r.get("url")]


def search_agent_node(state: AgentState) -> dict:
    """Search Agent node: performs web search and synthesizes answer with LLM.

    Args:
        state: Current graph state with the user question.

    Returns:
        State update with search_response and sources.
    """
    question = state["question"]
    logger.info("search_agent.start", question=question)

    results = run_web_search(question)
    logger.info("search_agent.results_retrieved", count=len(results))

    context = _format_search_results(results)
    new_sources = _extract_sources(results)

    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,  # type: ignore
        temperature=0,
    )

    messages = [
        SystemMessage(content=SEARCH_AGENT_PROMPT),
        HumanMessage(
            content=f"Pergunta: {question}\n\nResultados da busca:\n{context}"
        ),
    ]

    response = llm.invoke(messages)
    logger.info("search_agent.complete")

    existing_sources = state.get("sources") or []
    return {
        "search_response": response.content,
        "sources": existing_sources + new_sources,
    }
