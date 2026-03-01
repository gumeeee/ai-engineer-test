from unittest.mock import MagicMock, patch

from src.agents.state import AgentState


def _make_state(**kwargs) -> AgentState:
    defaults: AgentState = {
        "session_id": "test-session",
        "question": "Qual o preço da passagem São Paulo para Lisboa?",
        "route": "search",
        "faq_response": None,
        "search_response": None,
        "final_response": None,
        "agent_used": None,
        "sources": [],
    }
    defaults.update(kwargs)  # type: ignore
    return defaults


def test_format_search_results_with_results():
    from src.agents.search_agent import _format_search_results

    results = [
        {
            "title": "Passagens baratas",
            "url": "https://exemplo.com",
            "content": "A partir de R$2000",
        },
    ]
    formatted = _format_search_results(results)

    assert "[1]" in formatted
    assert "Passagens baratas" in formatted
    assert "https://exemplo.com" in formatted
    assert "A partir de R$2000" in formatted


def test_format_search_results_empty():
    from src.agents.search_agent import _format_search_results

    assert _format_search_results([]) == "Nenhum resultado encontrado."


def test_extract_sources_returns_urls():
    from src.agents.search_agent import _extract_sources

    results = [
        {"url": "https://site1.com", "content": "conteúdo 1"},
        {"url": "https://site2.com", "content": "conteúdo 2"},
        {"content": "sem url"},
    ]
    sources = _extract_sources(results)

    assert sources == ["https://site1.com", "https://site2.com"]


def test_extract_sources_empty():
    from src.agents.search_agent import _extract_sources

    assert _extract_sources([]) == []
    assert _extract_sources([{"content": "sem url"}]) == []


@patch("src.agents.search_agent.ChatOpenAI")
@patch("src.agents.search_agent.run_web_search")
def test_search_agent_node_returns_response(mock_run_search, mock_chat_openai):
    from src.agents.search_agent import search_agent_node

    mock_run_search.return_value = [
        {
            "title": "Voos SP-Lisboa",
            "url": "https://exemplo.com",
            "content": "A partir de R$3500",
        }
    ]
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(
        content="Passagens de SP para Lisboa a partir de R$3500."
    )
    mock_chat_openai.return_value = mock_llm

    result = search_agent_node(_make_state())

    assert (
        result["search_response"] == "Passagens de SP para Lisboa a partir de R$3500."
    )
    assert "https://exemplo.com" in result["sources"]


@patch("src.agents.search_agent.ChatOpenAI")
@patch("src.agents.search_agent.run_web_search")
def test_search_agent_node_calls_search_with_question(
    mock_run_search, mock_chat_openai
):
    from src.agents.search_agent import search_agent_node

    mock_run_search.return_value = []
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Sem resultados.")
    mock_chat_openai.return_value = mock_llm

    question = "Promoções de voos para o Japão"
    search_agent_node(_make_state(question=question))

    mock_run_search.assert_called_once_with(question)


@patch("src.agents.search_agent.ChatOpenAI")
@patch("src.agents.search_agent.run_web_search")
def test_search_agent_node_preserves_existing_sources(
    mock_run_search, mock_chat_openai
):
    from src.agents.search_agent import search_agent_node

    mock_run_search.return_value = [{"url": "https://novo.com", "content": "novo"}]
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Resposta.")
    mock_chat_openai.return_value = mock_llm

    result = search_agent_node(_make_state(sources=["https://existente.com"]))

    assert "https://existente.com" in result["sources"]
    assert "https://novo.com" in result["sources"]
