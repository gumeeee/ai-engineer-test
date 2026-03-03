import json
import re
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from src.agents.faq_agent import faq_agent_node
from src.agents.prompts import ORCHESTRATOR_PROMPT
from src.agents.search_agent import search_agent_node
from src.agents.state import AgentState
from src.config.settings import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


def orchestrator_node(state: AgentState) -> dict:
    """Orchestrator node: analyzes the question and decides routing.

    Args:
        state: Current graph state with the user question.

    Returns:
        State update with route decision (faq | search | both).
    """
    question = state["question"]
    messages = state.get("messages", [])
    logger.info("orchestrator.start", question=question)

    history_text = ""
    history_msgs = [m for m in messages[:-1] if hasattr(m, "type")]
    if history_msgs:
        lines = []
        for msg in history_msgs[-6:]:
            role = "Usuário" if msg.type == "human" else "Assistente"
            lines.append(f"{role}: {str(msg.content)[:300]}")
        history_text = "Histórico da conversa:\n" + "\n".join(lines) + "\n\nf"

    prompt_content = f"{history_text}Pergunta atual: {question}"

    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,  # type: ignore
        temperature=0,
    )
    messages = [
        SystemMessage(content=ORCHESTRATOR_PROMPT),
        HumanMessage(content=prompt_content),
    ]

    response = llm.invoke(messages)

    content = (
        re.sub(r"```(?:json)?\n?", "", response.content).strip().rstrip("```").strip()  # type: ignore  # noqa: B005
    )

    try:
        data = json.loads(content)
        route = data.get("route", "faq")
    except json.JSONDecodeError:
        logger.warning("orchestrator.json_parse_failed", content=content)
        route = "faq"

    if route not in ("faq", "search", "both", "out_of_scope"):
        logger.warning("orchestrator.invalid_route_fallback", route=route)
        route = "faq"

    logger.info("orchestrator.route_decided", route=route)
    return {"route": route}


def finalize_node(state: AgentState) -> dict:
    """Finalize node: consolidates agent responses into final_response.

    For single-agent routes, sets final_response directly.
    For 'both', uses LLM to consolidate faq and search responses.

    Args:
        state: Current graph state with agent responses.

    Returns:
        State update with final_response and agent_used.
    """
    route = state.get("route", "faq")

    if route == "out_of_scope":
        final_response = (
            "Sou especialista em viagens e posso ajudar com dúvidas sobre "
            "bagagem, documentação, check-in, remarcações, reembolsos e "
            "informações sobre companhias aéreas. Como posso ajudá-lo com sua viagem?"
        )
        logger.info("finalize.out_of_scope")
        return {
            "final_response": final_response,
            "agent_used": "none",
            "messages": [AIMessage(content=final_response)],
        }

    if route == "faq":
        logger.info("finalize.single_agent", agent="faq")
        final_response = state.get("faq_response", "")
        return {
            "final_response": final_response,
            "agent_used": "faq",
            "messages": [AIMessage(content=final_response) or ""],
        }

    if route == "search":
        logger.info("finalize.single_agent", agent="search")
        final_response = state.get("search_response", "")
        return {
            "final_response": final_response,
            "agent_used": "search",
            "messages": [AIMessage(content=final_response) or ""],
        }

    logger.info("finalize.consolidating")
    faq = state.get("faq_response") or ""
    search = state.get("search_response") or ""

    consolidation_prompt = f"""Você recebeu respostas de dois agentes especializados sobre a mesma pergunta. Consolide-as
   em uma resposta única, coerente e completa em português brasileiro.

  Resposta do Agente FAQ (políticas e regras do manual):
  {faq}

  Resposta do Agente de Busca (informações atualizadas da web):
  {search}

  Apresente uma resposta unificada, aproveitando o melhor de cada fonte. Não repita informações desnecessariamente."""

    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,  # type: ignore
        temperature=0,
    )

    response = llm.invoke([HumanMessage(content=consolidation_prompt)])
    final_response = str(response.content)
    logger.info("finalize.consolidation_complete")

    return {
        "final_response": final_response,
        "agent_used": "both",
        "messages": [AIMessage(content=final_response)],
    }


def _route_after_orchestrator(
    state: AgentState,
) -> Literal["faq_agent", "search_agent", "finalize"]:
    """Conditional edge: route to first agent after orchestrator decision."""
    route = state.get("route")
    if route == "out_of_scope":
        return "finalize"
    if route == "search":
        return "search_agent"
    return "faq_agent"


def _route_after_faq(
    state: AgentState,
) -> Literal["search_agent", "finalize"]:
    """Conditional edge: after FAQ agent, continue to search only if route='both'."""
    if state.get("route") == "both":
        return "search_agent"
    return "finalize"


def build_graph(checkpointer=None):
    """Build and compile the LangGraph multi-agent graph.

    Graph flow:
        START → orchestrator → (faq_agent | search_agent) → finalize → END
        For 'both': orchestrator → faq_agent → search_agent → finalize → END

    Args:
        checkpointer: LangGraph checkpointer. Defaults to get_checkpointer().

    Returns:
        Compiled LangGraph graph ready for invocation.
    """
    from langgraph.checkpoint.memory import MemorySaver

    if checkpointer is None:
        checkpointer = MemorySaver()

    graph = StateGraph(AgentState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("faq_agent", faq_agent_node)
    graph.add_node("search_agent", search_agent_node)
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        _route_after_orchestrator,
        {
            "faq_agent": "faq_agent",
            "search_agent": "search_agent",
            "finalize": "finalize",
        },
    )

    graph.add_conditional_edges(
        "faq_agent",
        _route_after_faq,
        {"search_agent": "search_agent", "finalize": "finalize"},
    )

    graph.add_edge("search_agent", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile(checkpointer=checkpointer)  # type: ignore
