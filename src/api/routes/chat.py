import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from src.agents.state import AgentState
from src.api.dependencies import get_graph
from src.api.schemas.chat import ChatRequest, ChatResponse
from src.core.logging import get_logger

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)

_ANSWER_NODES = {"faq_agent", "search_agent", "finalize"}


def _build_initial_state(request: ChatRequest) -> AgentState:
    return AgentState(
        messages=[HumanMessage(content=request.message)],
        session_id=request.session_id,
        question=request.message,
        route=None,
        search_response=None,
        faq_response=None,
        final_response=None,
        agent_used=None,
        sources=[],
    )  # type: ignore


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, graph=Depends(get_graph)) -> ChatResponse:
    """
    Process a chat message and return the agent's response.

    Routes the question through the Orchestrator, FAQ Agent, and/or Search Agent.
    """
    logger.info("chat.request", session_id=request.session_id)
    config = {"configurable": {"thread_id": request.session_id}}
    state = _build_initial_state(request)

    result = await graph.ainvoke(state, config=config)
    logger.info(
        "chat.response", session_id=request.session_id, agent=result["agent_used"]
    )

    return ChatResponse(
        session_id=request.session_id,
        response=result["final_response"] or "",
        agent_used=result["agent_used"] or "",
        sources=result["sources"],
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    graph=Depends(get_graph),
) -> StreamingResponse:
    """
    Stream the agent response token-by-token using Server-Sent Events (SSE).

    Emits one 'token' event per LLM token as it is generated, followed by a
    final 'done' event containing session_id, agent_used and sources.
    """
    logger.info("chat.stream_request", session_id=request.session_id)

    async def event_generator():
        config = {"configurable": {"thread_id": f"{request.session_id}-stream"}}
        state = _build_initial_state(request)
        accumulated_sources: list[str] = []
        agent_used = "unknown"

        try:
            async for event in graph.astream_events(state, config=config, version="v2"):
                event_type = event["event"]
                node_name = event.get("metadata", {}).get("langgraph_node", "")

                if event_type == "on_chat_model_stream" and node_name in _ANSWER_NODES:
                    chunk = event["data"].get("chunk")
                    if chunk is not None:
                        content = chunk.content
                        if isinstance(content, str) and content:
                            yield f"data: {json.dumps({'token': content, 'done': False})}\n\n"
                        elif isinstance(content, list):  # type: ignore
                            for part in content:
                                if isinstance(part, dict) and part.get("text"):
                                    yield f"data: {json.dumps({'token': part['text'], 'done': False})}\n\n"
                elif event_type == "on_chain_end" and node_name in (
                    "faq_agent",
                    "search_agent",
                ):
                    raw = event["data"].get("output")
                    output = raw if isinstance(raw, dict) else {}
                    for src in output.get("sources", []):
                        if src not in accumulated_sources:
                            accumulated_sources.append(src)

                elif event_type == "on_chain_end" and node_name == "finalize":
                    raw = event["data"].get("output")
                    output = raw if isinstance(raw, dict) else {}
                    agent_used = output.get("agent_used", agent_used)

            yield f"data: {json.dumps({'session_id': request.session_id, 'agent_used': agent_used, 'sources': accumulated_sources, 'done': True})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error("chat.stream_error", error=str(e))
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
