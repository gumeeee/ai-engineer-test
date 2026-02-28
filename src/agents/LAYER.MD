# Agents Layer

## Responsabilidade
Definir o grafo LangGraph com Orchestrator, FAQ Agent e Search Agent.
Cada agente é um nó (função pura) que recebe o estado e retorna updates.

## Dependências
- `src.rag` (retriever para o FAQ Agent)
- `src.tools` (Tavily para o Search Agent)
- `src.config` (settings)
- `src.core` (logging)

## Exporta
- `build_graph()` — função que retorna o grafo LangGraph compilado (Fase 6)
- `AgentState` — TypedDict do estado compartilhado
- `faq_agent_node` — nó do FAQ Agent
- `search_agent_node` — nó do Search Agent (Fase 5)

## Regras
- Lógica HTTP NÃO pertence aqui
- Prompts ficam em `prompts.py`, nunca inline nos nós
- Nós são funções puras: recebem state, retornam dict com updates