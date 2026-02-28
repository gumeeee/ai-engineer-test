from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.agents.prompts import FAQ_AGENT_PROMPT
from src.agents.state import AgentState
from src.config.settings import settings
from src.core.logging import get_logger
from src.rag.retriever import get_retriever

logger = get_logger(__name__)


def _format_sources(docs: list) -> list[str]:
    """Extract and format source references from retrieved documents.

    Args:
        docs: List of retrieved Documents with metadata.

    Returns:
        Deduplicated list of formatted source strings.
    """
    sources = []
    for doc in docs:
        source = doc.metadata.get("source", "manual-politicas-viagem-blis.pdf")
        page = doc.metadata.get("page")
        if page is not None:
            sources.append(f"{source} - Página {int(page) + 1}")
        else:
            sources.append(source)
    return list(dict.fromkeys(sources))


def faq_agent_node(state: AgentState) -> dict:
    """FAQ Agent node: retrieves context from vector store and answers with LLM.

    Args:
        state: Current graph state with the user question.

    Returns:
        State update with faq_response and sources.
    """
    question = state["question"]
    logger.info("faq_agent.start", question=question)

    retriever = get_retriever()
    docs = retriever.invoke(question)
    logger.info("faq_agent.docs_retrieved", count=len(docs))

    context = "\n\n".join(doc.page_content for doc in docs)
    sources = _format_sources(docs)

    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,  # type: ignore
        temperature=0,
    )

    messages = [
        SystemMessage(content=FAQ_AGENT_PROMPT.format(context=context)),
        HumanMessage(content=question),
    ]

    response = llm.invoke(messages)
    logger.info("faq_agent.complete")

    return {"faq_response": response.content, "sources": sources}
