import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.agents.state import AgentState
from src.api.dependencies import get_graph
from src.api.schemas.chat import ChatRequest, ChatResponse
from src.core.logging import get_logger

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)


def _build_initial_state(request: ChatRequest) -> AgentState:
    return AgentState(
        session_id=request.session_id,
        question=request.message,
        route=None,
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
    Stream the agent response using Server-Sent Events (SSE).

    Emits one event per graph node completion, and a final event with the response.
    """
    logger.info("chat.stream_request", session_id=request.session_id)

    async def event_generator():
        config = {"configurable": {"thread_id": f"{request.session_id}-stream"}}
        state = _build_initial_state(request)
        accumulated_sources: list[str] = []

        try:
            async for chunk in graph.astream(
                state, config=config, stream_mode="updates"
            ):
                node_name = next(iter(chunk))
                update = chunk[node_name]

                if "sources" in update:
                    accumulated_sources = update["sources"]

                if node_name == "finalize":
                    data = json.dumps(
                        {
                            "session_id": request.session_id,
                            "response": update.get("final_response", ""),
                            "agent_used": update.get("agent_used", ""),
                            "sources": accumulated_sources,
                            "done": True,
                        }
                    )
                    yield f"data: {data}\n\n"
                else:
                    yield f"data: {json.dumps({'node': node_name, 'done': False})}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error("chat.stream_error", error=str(e))
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
