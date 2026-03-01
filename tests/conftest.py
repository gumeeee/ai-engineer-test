import os

import pytest

os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-for-testing")
os.environ.setdefault("TAVILY_API_KEY", "tvly-test-key-for-testing")
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("CHROMA_PERSIST_DIR", "/tmp/chroma_test")
os.environ.setdefault("DOCUMENTS_DIR", "docs/data")


from src.agents.state import AgentState  # noqa: E402


@pytest.fixture
def make_state():
    """Factory de AgentState para uso nos testes.

    Usage:
        def test_algo(make_state):
            state = make_state(question="Minha pergunta", route="faq")
    """

    def _factory(**kwargs) -> AgentState:
        defaults: AgentState = {
            "session_id": "test-session",
            "question": "Qual o limite de bagagem de mão na LATAM?",
            "route": None,
            "faq_response": None,
            "search_response": None,
            "final_response": None,
            "agent_used": None,
            "sources": [],
        }
        defaults.update(kwargs)  # type: ignore
        return defaults

    return _factory
