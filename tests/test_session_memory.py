"""Testes de memória de sessão: verifica que as mensagens do usuário e do LLM são salvas corretamente.

Estes testes cobrem:
- HumanMessage é adicionada ao estado em cada requisição recebida
- AIMessage é adicionada ao estado após cada resposta do agente
- O reducer add_messages acumula mensagens entre turnos sem sobrescrever
- AgentState.messages usa o reducer add_messages via Annotated
- O orquestrador inclui o histórico da conversa no prompt do LLM
- Integração completa: 2 turnos produzem 4 mensagens acumuladas via MemorySaver
"""

import typing
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import add_messages

from src.agents.state import AgentState


def _make_state(**kwargs) -> AgentState:
    defaults: AgentState = {
        "session_id": "test-session",
        "messages": [],
        "question": "Qual o limite de bagagem de mão?",
        "route": None,
        "faq_response": None,
        "search_response": None,
        "final_response": None,
        "agent_used": None,
        "sources": [],
    }
    defaults.update(kwargs)  # type: ignore
    return defaults


def test_build_initial_state_adds_human_message():
    """_build_initial_state deve encapsular a mensagem da requisição em uma HumanMessage."""
    from src.api.routes.chat import _build_initial_state
    from src.api.schemas.chat import ChatRequest

    request = ChatRequest(message="Qual o limite de bagagem?", session_id="s1")
    state = _build_initial_state(request)

    assert len(state["messages"]) == 1
    assert isinstance(state["messages"][0], HumanMessage)
    assert state["messages"][0].content == "Qual o limite de bagagem?"


def test_build_initial_state_question_matches_human_message():
    """_build_initial_state: o campo 'question' deve ser igual ao conteúdo da HumanMessage."""
    from src.api.routes.chat import _build_initial_state
    from src.api.schemas.chat import ChatRequest

    request = ChatRequest(message="Qual a franquia da GOL?", session_id="s2")
    state = _build_initial_state(request)

    assert state["question"] == state["messages"][0].content


def test_build_initial_state_always_starts_with_one_message():
    """_build_initial_state deve produzir exatamente uma mensagem (a requisição atual)."""
    from src.api.routes.chat import _build_initial_state
    from src.api.schemas.chat import ChatRequest

    request = ChatRequest(message="Alguma pergunta", session_id="s3")
    state = _build_initial_state(request)

    assert len(state["messages"]) == 1


def test_finalize_faq_adds_ai_message_with_correct_content():
    """finalize_node (rota faq) deve adicionar AIMessage cujo conteúdo é igual ao faq_response."""
    from src.agents.orchestrator import finalize_node

    result = finalize_node(_make_state(route="faq", faq_response="O limite é 10kg."))

    assert len(result["messages"]) == 1
    msg = result["messages"][0]
    assert isinstance(msg, AIMessage)
    assert msg.content == "O limite é 10kg."


def test_finalize_search_adds_ai_message_with_correct_content():
    """finalize_node (rota search) deve adicionar AIMessage cujo conteúdo é igual ao search_response."""
    from src.agents.orchestrator import finalize_node

    result = finalize_node(
        _make_state(route="search", search_response="Passagem custa R$3.000.")
    )

    msg = result["messages"][0]
    assert isinstance(msg, AIMessage)
    assert msg.content == "Passagem custa R$3.000."


def test_finalize_out_of_scope_adds_ai_message():
    """finalize_node (rota out_of_scope) deve adicionar uma AIMessage não-vazia."""
    from src.agents.orchestrator import finalize_node

    result = finalize_node(_make_state(route="out_of_scope"))

    msg = result["messages"][0]
    assert isinstance(msg, AIMessage)
    assert len(msg.content) > 0


@patch("src.agents.orchestrator.ChatOpenAI")
def test_finalize_both_adds_ai_message_with_consolidated_content(mock_chat_openai):
    """finalize_node (rota both) deve adicionar AIMessage com a resposta consolidada pelo LLM."""
    from src.agents.orchestrator import finalize_node

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Resposta consolidada.")
    mock_chat_openai.return_value = mock_llm

    result = finalize_node(
        _make_state(
            route="both",
            faq_response="Regra: 10kg.",
            search_response="Promoção: R$2.500.",
        )
    )

    msg = result["messages"][0]
    assert isinstance(msg, AIMessage)
    assert msg.content == "Resposta consolidada."


def test_add_messages_appends_to_existing_list():
    """add_messages deve acrescentar novas mensagens à lista existente sem substituí-la."""
    existing = [HumanMessage(content="Pergunta 1")]
    update = [AIMessage(content="Resposta 1")]

    result = add_messages(existing, update)  # type: ignore

    assert len(result) == 2  # type: ignore
    assert result[0].content == "Pergunta 1"  # type: ignore
    assert result[1].content == "Resposta 1"  # type: ignore


def test_add_messages_accumulates_over_multiple_turns():
    """add_messages deve acumular mensagens corretamente ao longo de múltiplos turnos."""
    messages: list = []

    messages = add_messages(messages, [HumanMessage(content="Pergunta 1")])  # type: ignore
    messages = add_messages(messages, [AIMessage(content="Resposta 1")])  # type: ignore
    messages = add_messages(messages, [HumanMessage(content="Pergunta 2")])  # type: ignore
    messages = add_messages(messages, [AIMessage(content="Resposta 2")])  # type: ignore

    assert len(messages) == 4
    assert messages[0].content == "Pergunta 1"
    assert messages[1].content == "Resposta 1"
    assert messages[2].content == "Pergunta 2"
    assert messages[3].content == "Resposta 2"


def test_add_messages_does_not_replace_existing_messages():
    """add_messages não deve sobrescrever mensagens anteriores ao adicionar novas."""
    first = [HumanMessage(content="Não me esqueça")]
    second = [AIMessage(content="Nova resposta")]

    result = add_messages(first, second)  # type: ignore

    assert any(m.content == "Não me esqueça" for m in result)  # type: ignore
    assert any(m.content == "Nova resposta" for m in result)  # type: ignore


def test_agent_state_messages_field_uses_add_messages_reducer():
    """O campo messages do AgentState deve usar add_messages como reducer via Annotated."""
    hints = typing.get_type_hints(AgentState, include_extras=True)
    messages_hint = hints["messages"]

    assert hasattr(messages_hint, "__metadata__"), (
        "O campo messages deve ser Annotated — __metadata__ ausente"
    )
    assert add_messages in messages_hint.__metadata__, (
        "O reducer add_messages deve estar declarado nos metadados do Annotated de messages"
    )


@patch("src.agents.orchestrator.ChatOpenAI")
def test_orchestrator_injects_prior_messages_into_llm_prompt(mock_chat_openai):
    """orchestrator_node deve incluir as mensagens anteriores da conversa na chamada ao LLM."""
    from src.agents.orchestrator import orchestrator_node

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(
        content='{"route": "faq", "reasoning": "continuidade"}'
    )
    mock_chat_openai.return_value = mock_llm

    history = [
        HumanMessage(content="Qual o limite de bagagem de mão?"),
        AIMessage(content="O limite é 10kg."),
        HumanMessage(content="E a bagagem despachada?"),
    ]
    orchestrator_node(_make_state(question="E a bagagem despachada?", messages=history))

    call_messages = mock_llm.invoke.call_args[0][0]

    human_prompt = next(m for m in call_messages if isinstance(m, HumanMessage))
    assert "Qual o limite de bagagem de mão?" in human_prompt.content


@patch("src.agents.orchestrator.ChatOpenAI")
def test_orchestrator_with_no_history_still_sends_current_question(mock_chat_openai):
    """orchestrator_node sem histórico deve enviar ao menos a pergunta atual ao LLM."""
    from src.agents.orchestrator import orchestrator_node

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(
        content='{"route": "faq", "reasoning": "bagagem"}'
    )
    mock_chat_openai.return_value = mock_llm

    question = "Qual o limite de bagagem?"
    orchestrator_node(_make_state(question=question, messages=[]))

    call_messages = mock_llm.invoke.call_args[0][0]
    human_prompt = next(m for m in call_messages if isinstance(m, HumanMessage))
    assert question in human_prompt.content


@patch("src.agents.orchestrator.ChatOpenAI")
def test_orchestrator_limits_history_to_recent_messages(mock_chat_openai):
    """orchestrator_node não deve enviar um histórico ilimitado ao LLM."""
    from src.agents.orchestrator import orchestrator_node

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(
        content='{"route": "faq", "reasoning": "ok"}'
    )
    mock_chat_openai.return_value = mock_llm

    long_history = []
    for i in range(10):
        long_history.append(HumanMessage(content=f"Pergunta {i}"))
        long_history.append(AIMessage(content=f"Resposta {i}"))

    orchestrator_node(_make_state(messages=long_history))

    assert mock_llm.invoke.call_count == 1


@patch("src.agents.faq_agent.ChatOpenAI")
@patch("src.agents.faq_agent.get_retriever")
def test_faq_agent_includes_history_in_llm_call(mock_get_retriever, mock_faq_llm_cls):
    """faq_agent_node deve incluir o histórico de conversa nas mensagens enviadas ao LLM."""
    from src.agents.faq_agent import faq_agent_node

    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = []
    mock_get_retriever.return_value = mock_retriever

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Resposta com contexto.")
    mock_faq_llm_cls.return_value = mock_llm

    history = [
        HumanMessage(content="Qual o limite de bagagem de mão?"),
        AIMessage(content="O limite é 10kg."),
        HumanMessage(content="E a bagagem despachada?"),
    ]
    faq_agent_node(_make_state(question="E a bagagem despachada?", messages=history))

    call_messages = mock_llm.invoke.call_args[0][0]

    assert len(call_messages) == 4
    assert isinstance(call_messages[0], SystemMessage)

    assert call_messages[1].content == "Qual o limite de bagagem de mão?"
    assert call_messages[2].content == "O limite é 10kg."
    assert call_messages[3].content == "E a bagagem despachada?"


@patch("src.agents.faq_agent.ChatOpenAI")
@patch("src.agents.faq_agent.get_retriever")
def test_faq_agent_without_history_appends_question_as_human_message(
    mock_get_retriever, mock_faq_llm_cls
):
    """faq_agent_node sem histórico deve adicionar a pergunta como HumanMessage ao final."""
    from src.agents.faq_agent import faq_agent_node

    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = []
    mock_get_retriever.return_value = mock_retriever

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Resposta.")
    mock_faq_llm_cls.return_value = mock_llm

    question = "Qual o limite de bagagem?"
    faq_agent_node(_make_state(question=question, messages=[]))

    call_messages = mock_llm.invoke.call_args[0][0]
    assert len(call_messages) == 2
    assert isinstance(call_messages[0], SystemMessage)
    assert isinstance(call_messages[1], HumanMessage)
    assert call_messages[1].content == question


@patch("src.agents.faq_agent.get_retriever")
@patch("src.agents.faq_agent.ChatOpenAI")
@patch("src.agents.orchestrator.ChatOpenAI")
async def test_graph_accumulates_human_and_ai_messages_across_two_turns(
    mock_orch_llm_cls,
    mock_faq_llm_cls,
    mock_retriever_fn,
):
    """Após 2 turnos com a mesma sessão, o estado deve conter 4 mensagens:
    HumanMessage(turno1) → AIMessage(turno1) → HumanMessage(turno2) → AIMessage(turno2).
    """
    from src.agents.orchestrator import build_graph

    mock_orch_instance = MagicMock()
    mock_orch_instance.invoke.side_effect = [
        MagicMock(content='{"route": "faq", "reasoning": "turno 1"}'),
        MagicMock(content='{"route": "faq", "reasoning": "turno 2"}'),
    ]
    mock_orch_llm_cls.return_value = mock_orch_instance

    mock_faq_instance = MagicMock()
    mock_faq_instance.invoke.side_effect = [
        MagicMock(content="Resposta da primeira pergunta."),
        MagicMock(content="Resposta da segunda pergunta."),
    ]
    mock_faq_llm_cls.return_value = mock_faq_instance

    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = [
        Document(page_content="Bagagem de mão: 10kg", metadata={"page": 0})
    ]
    mock_retriever_fn.return_value = mock_retriever

    graph = build_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "memory-integration-test"}}

    state_turn1 = _make_state(
        session_id="memory-integration-test",
        messages=[HumanMessage(content="Qual o limite de bagagem de mão?")],
        question="Qual o limite de bagagem de mão?",
    )
    result1 = await graph.ainvoke(state_turn1, config=config)  # type: ignore

    assert result1["final_response"] == "Resposta da primeira pergunta."
    assert len(result1["messages"]) == 2
    assert isinstance(result1["messages"][0], HumanMessage)
    assert isinstance(result1["messages"][1], AIMessage)
    assert result1["messages"][0].content == "Qual o limite de bagagem de mão?"
    assert result1["messages"][1].content == "Resposta da primeira pergunta."

    state_turn2 = _make_state(
        session_id="memory-integration-test",
        messages=[HumanMessage(content="E a bagagem despachada?")],
        question="E a bagagem despachada?",
    )
    result2 = await graph.ainvoke(state_turn2, config=config)  # type: ignore

    assert result2["final_response"] == "Resposta da segunda pergunta."
    assert len(result2["messages"]) == 4
    assert isinstance(result2["messages"][0], HumanMessage)
    assert isinstance(result2["messages"][1], AIMessage)
    assert isinstance(result2["messages"][2], HumanMessage)
    assert isinstance(result2["messages"][3], AIMessage)
    assert result2["messages"][0].content == "Qual o limite de bagagem de mão?"
    assert result2["messages"][2].content == "E a bagagem despachada?"
