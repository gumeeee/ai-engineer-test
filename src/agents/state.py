from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """Shared state across all nodes in the LangGraph graph."""

    session_id: str
    messages: Annotated[list[BaseMessage], add_messages]
    question: str
    route: str | None
    faq_response: str | None
    search_response: str | None
    final_response: str | None
    agent_used: str | None
    sources: list[str]
