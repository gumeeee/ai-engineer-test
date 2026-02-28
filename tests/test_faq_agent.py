from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from src.agents.state import AgentState


def _make_state(**kwargs) -> AgentState:
    """Helper to build a minimal AgentState for tests."""
    defaults: AgentState = {
        "session_id": "test-session",
        "question": "Qual o limite de bagagem de mão na LATAM?",
        "route": "faq",
        "faq_response": None,
        "search_response": None,
        "final_response": None,
        "agent_used": None,
        "sources": [],
    }

    defaults.update(kwargs)  # type: ignore
    return defaults


def test_agent_state_has_required_keys():
    """AgentState deve conter todas as chaves necessárias."""
    state = _make_state()
    required_keys = {
        "session_id",
        "question",
        "route",
        "faq_response",
        "search_response",
        "final_response",
        "agent_used",
        "sources",
    }
    assert required_keys == set(state.keys())


def test_format_sources_with_page_metadata():
    """_format_sources deve incluir número de página quando disponível."""
    from src.agents.faq_agent import _format_sources

    docs = [
        Document(page_content="texto", metadata={"source": "manual.pdf", "page": 0}),
        Document(page_content="texto", metadata={"source": "manual.pdf", "page": 2}),
    ]
    sources = _format_sources(docs)

    assert "manual.pdf - Página 1" in sources
    assert "manual.pdf - Página 3" in sources


def test_format_sources_deduplicates():
    """_format_sources não deve retornar fontes duplicadas."""
    from src.agents.faq_agent import _format_sources

    docs = [
        Document(page_content="a", metadata={"source": "manual.pdf", "page": 0}),
        Document(page_content="b", metadata={"source": "manual.pdf", "page": 0}),
    ]
    sources = _format_sources(docs)

    assert len(sources) == 1


def test_format_sources_without_page_metadata():
    """_format_sources deve funcionar sem metadado de página."""
    from src.agents.faq_agent import _format_sources

    docs = [Document(page_content="texto", metadata={})]
    sources = _format_sources(docs)

    assert sources == ["manual-politicas-viagem-blis.pdf"]


@patch("src.agents.faq_agent.ChatOpenAI")
@patch("src.agents.faq_agent.get_retriever")
def test_faq_agent_node_returns_response(mock_get_retriever, mock_chat_openai):
    """faq_agent_node deve retornar faq_response e sources no estado."""
    from src.agents.faq_agent import faq_agent_node

    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = [
        Document(
            page_content="Bagagem de mão: máximo 10kg e 115cm.",
            metadata={"source": "manual.pdf", "page": 0},
        )
    ]
    mock_get_retriever.return_value = mock_retriever

    mock_llm_instance = MagicMock()
    mock_llm_instance.invoke.return_value = MagicMock(
        content="O limite de bagagem de mão na LATAM é 10kg."
    )
    mock_chat_openai.return_value = mock_llm_instance

    state = _make_state()
    result = faq_agent_node(state)

    assert result["faq_response"] == "O limite de bagagem de mão na LATAM é 10kg."
    assert len(result["sources"]) > 0


@patch("src.agents.faq_agent.ChatOpenAI")
@patch("src.agents.faq_agent.get_retriever")
def test_faq_agent_node_calls_retriever_with_question(
    mock_get_retriever, mock_chat_openai
):
    """faq_agent_node deve chamar o retriever com a pergunta do estado."""
    from src.agents.faq_agent import faq_agent_node

    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = []
    mock_get_retriever.return_value = mock_retriever

    mock_llm_instance = MagicMock()
    mock_llm_instance.invoke.return_value = MagicMock(
        content="Não encontrei essa informação."
    )
    mock_chat_openai.return_value = mock_llm_instance

    question = "Qual a franquia de bagagem despachada?"
    state = _make_state(question=question)
    faq_agent_node(state)

    mock_retriever.invoke.assert_called_once_with(question)
