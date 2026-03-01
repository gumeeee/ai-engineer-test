from fastapi import Request


def get_graph(request: Request):
    """Inject the compiled LangGraph graph from app state.

    The graph is built once at startup via lifespan and stored in app.state.
    """
    return request.app.state.graph
