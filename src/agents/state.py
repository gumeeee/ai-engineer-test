from typing import TypedDict


class AgentState(TypedDict):
    """Shared state across all nodes in the LangGraph graph."""

    session_id: str
    question: str
    route: str | None
    faq_response: str | None
    search_response: str | None
    final_response: str | None
    agent_used: str | None
    sources: list[str]
