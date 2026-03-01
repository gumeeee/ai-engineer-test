# API Layer

## Responsabilidade
Expor os agentes como API REST via FastAPI. Gerencia requests HTTP,
validação de schema, dependency injection e SSE streaming.

## Dependências
- `src.agents` (orchestrator graph via dependency injection)
- `src.rag` (para health check do vectorstore)
- `src.config` (settings)
- `src.core` (logging)

## Exporta
- `app` em `src.main` — instância FastAPI
- `POST /chat` — resposta síncrona completa
- `POST /chat/stream` — streaming SSE por nó do grafo
- `GET /health` — status do Redis e vector store

## Regras
- NÃO contém lógica de negócio — apenas orquestra requests e responses
- Lógica dos agentes fica em `src.agents`
- Schemas Pydantic em `src/api/schemas/`, nunca inline nas rotas
- O graph é injetado via `app.state`, nunca instanciado diretamente nas rotas