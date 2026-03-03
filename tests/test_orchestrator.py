from unittest.mock import MagicMock, patch

from src.agents.state import AgentState


def _make_state(**kwargs) -> AgentState:
    defaults: AgentState = {
        "session_id": "test-session",
        "messages": [],
        "question": "Qual o limite de bagagem na LATAM?",
        "route": None,
        "faq_response": None,
        "search_response": None,
        "final_response": None,
        "agent_used": None,
        "sources": [],
    }
    defaults.update(kwargs)  # type: ignore
    return defaults


@patch("src.agents.orchestrator.ChatOpenAI")
def test_orchestrator_routes_to_faq(mock_chat_openai):
    """orchestrator_node deve retornar route='faq' para perguntas de políticas."""
    from src.agents.orchestrator import orchestrator_node

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(
        content='{"route": "faq", "reasoning": "pergunta sobre política de bagagem"}'
    )
    mock_chat_openai.return_value = mock_llm

    result = orchestrator_node(_make_state())

    assert result["route"] == "faq"


@patch("src.agents.orchestrator.ChatOpenAI")
def test_orchestrator_routes_to_search(mock_chat_openai):
    """orchestrator_node deve retornar route='search' para perguntas de preços."""
    from src.agents.orchestrator import orchestrator_node

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(
        content='{"route": "search", "reasoning": "requer informação em tempo real"}'
    )
    mock_chat_openai.return_value = mock_llm

    result = orchestrator_node(
        _make_state(question="Qual o preço do voo SP-Lisboa hoje?")
    )

    assert result["route"] == "search"


@patch("src.agents.orchestrator.ChatOpenAI")
def test_orchestrator_routes_to_both(mock_chat_openai):
    """orchestrator_node deve retornar route='both' quando necessário."""
    from src.agents.orchestrator import orchestrator_node

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(
        content='{"route": "both", "reasoning": "envolve políticas e preços atuais"}'
    )
    mock_chat_openai.return_value = mock_llm

    result = orchestrator_node(_make_state())

    assert result["route"] == "both"


@patch("src.agents.orchestrator.ChatOpenAI")
def test_orchestrator_fallback_on_invalid_json(mock_chat_openai):
    """orchestrator_node deve usar 'faq' como fallback se o LLM retornar JSON inválido."""
    from src.agents.orchestrator import orchestrator_node

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="não é json válido")
    mock_chat_openai.return_value = mock_llm

    result = orchestrator_node(_make_state())

    assert result["route"] == "faq"


@patch("src.agents.orchestrator.ChatOpenAI")
def test_orchestrator_fallback_on_invalid_route_value(mock_chat_openai):
    """orchestrator_node deve usar 'faq' se a route retornada for inválida."""
    from src.agents.orchestrator import orchestrator_node

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(
        content='{"route": "invalido", "reasoning": "..."}'
    )
    mock_chat_openai.return_value = mock_llm

    result = orchestrator_node(_make_state())

    assert result["route"] == "faq"


def test_finalize_node_faq_route():
    """finalize_node deve expor faq_response como final_response para route='faq'."""
    from src.agents.orchestrator import finalize_node

    state = _make_state(route="faq", faq_response="O limite é 10kg.")
    result = finalize_node(state)

    assert result["final_response"] == "O limite é 10kg."
    assert result["agent_used"] == "faq"


def test_finalize_node_search_route():
    """finalize_node deve expor search_response como final_response para route='search'."""
    from src.agents.orchestrator import finalize_node

    state = _make_state(route="search", search_response="Passagem custa R$3000.")
    result = finalize_node(state)

    assert result["final_response"] == "Passagem custa R$3000."
    assert result["agent_used"] == "search"


@patch("src.agents.orchestrator.ChatOpenAI")
def test_finalize_node_both_consolidates(mock_chat_openai):
    """finalize_node deve chamar LLM para consolidar quando route='both'."""
    from src.agents.orchestrator import finalize_node

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Resposta consolidada completa.")
    mock_chat_openai.return_value = mock_llm

    state = _make_state(
        route="both",
        faq_response="Regra: limite de 10kg.",
        search_response="Promoção: R$2500.",
    )
    result = finalize_node(state)

    assert result["final_response"] == "Resposta consolidada completa."
    assert result["agent_used"] == "both"
    mock_llm.invoke.assert_called_once()


def test_route_after_orchestrator_faq():
    from src.agents.orchestrator import _route_after_orchestrator

    assert _route_after_orchestrator(_make_state(route="faq")) == "faq_agent"


def test_route_after_orchestrator_both_starts_with_faq():
    from src.agents.orchestrator import _route_after_orchestrator

    assert _route_after_orchestrator(_make_state(route="both")) == "faq_agent"


def test_route_after_orchestrator_search():
    from src.agents.orchestrator import _route_after_orchestrator

    assert _route_after_orchestrator(_make_state(route="search")) == "search_agent"


def test_route_after_faq_goes_to_finalize():
    from src.agents.orchestrator import _route_after_faq

    assert _route_after_faq(_make_state(route="faq")) == "finalize"


def test_route_after_faq_both_continues_to_search():
    from src.agents.orchestrator import _route_after_faq

    assert _route_after_faq(_make_state(route="both")) == "search_agent"


def test_build_graph_compiles_without_error():
    """build_graph deve compilar o grafo sem lançar exceções."""
    from langgraph.checkpoint.memory import MemorySaver

    from src.agents.orchestrator import build_graph

    graph = build_graph(checkpointer=MemorySaver())
    assert graph is not None
