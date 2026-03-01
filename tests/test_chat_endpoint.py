from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

MOCK_RESULT = {
    "session_id": "test-session-123",
    "question": "Qual o limite de bagagem de mão?",
    "route": "faq",
    "faq_response": "O limite é 10kg.",
    "search_response": None,
    "final_response": "O limite de bagagem de mão na LATAM é 10kg.",
    "agent_used": "faq",
    "sources": ["manual-politicas-viagem-blis.pdf - Página 1"],
}


@pytest.fixture
def mock_graph():
    graph = MagicMock()
    graph.ainvoke = AsyncMock(return_value=MOCK_RESULT)

    async def _astream(*args, **kwargs):
        yield {"orchestrator": {"route": "faq"}}
        yield {
            "faq_agent": {
                "faq_response": "O limite é 10kg.",
                "sources": ["manual.pdf - Página 1"],
            }
        }
        yield {
            "finalize": {
                "final_response": "O limite de bagagem de mão na LATAM é 10kg.",
                "agent_used": "faq",
            }
        }

    graph.astream = _astream
    return graph


@pytest.fixture
def client(mock_graph):
    with patch("src.main.build_graph", return_value=mock_graph):
        from src.main import app

        with TestClient(app) as c:
            yield c


def test_health_returns_200(client):
    """GET /health deve retornar 200 com campos obrigatórios."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "redis" in data
    assert "vectorstore" in data
    assert "version" in data


def test_chat_returns_correct_schema(client):
    """POST /chat deve retornar schema correto."""
    response = client.post(
        "/chat",
        json={
            "session_id": "test-session-123",
            "message": "Qual o limite de bagagem de mão?",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-123"
    assert data["response"] == "O limite de bagagem de mão na LATAM é 10kg."
    assert data["agent_used"] == "faq"
    assert isinstance(data["sources"], list)


def test_chat_calls_graph_ainvoke(client, mock_graph):
    """POST /chat deve chamar graph.ainvoke uma vez."""
    client.post(
        "/chat",
        json={
            "session_id": "session-abc",
            "message": "Pergunta teste",
        },
    )

    mock_graph.ainvoke.assert_called_once()


def test_chat_passes_correct_thread_id(client, mock_graph):
    """POST /chat deve usar session_id como thread_id no config."""
    client.post(
        "/chat",
        json={
            "session_id": "minha-sessao",
            "message": "Pergunta",
        },
    )

    call_kwargs = mock_graph.ainvoke.call_args
    config = (
        call_kwargs[1]["config"] if "config" in call_kwargs[1] else call_kwargs[0][1]
    )
    assert config["configurable"]["thread_id"] == "minha-sessao"


def test_chat_auto_generates_session_id(client):
    """POST /chat sem session_id deve gerar um automaticamente."""
    response = client.post("/chat", json={"message": "Pergunta sem session"})

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"]
    assert len(data["session_id"]) > 0


def test_chat_stream_returns_event_stream(client):
    """POST /chat/stream deve retornar content-type text/event-stream."""
    response = client.post(
        "/chat/stream",
        json={
            "session_id": "stream-test",
            "message": "Pergunta streaming",
        },
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    # Verifica que há eventos SSE no corpo da resposta
    assert "data:" in response.text
