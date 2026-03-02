## 🌐 API em produção

> **URL pública**: `http://18.211.161.111:8000`

Teste agora sem instalar nada:

```bash
curl -X POST http://18.211.161.111:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Qual o limite de bagagem de mão na LATAM?"}'
  

Arquitetura

Cliente (HTTP)
    │
    ▼
FastAPI (POST /chat, POST /chat/stream, GET /health)
    │
    ▼
Orchestrator Agent (LangGraph StateGraph)
    │
    ├──► FAQ Agent ──► ChromaDB (RAG sobre manual de políticas)
    │
    └──► Search Agent ──► Tavily (busca web em tempo real)
         │
         ▼
     Finalize Node ──► Resposta consolidada

Checkpointer: Redis para persistência de sessões entre requisições.
Fluxo para "both": Orchestrator → FAQ Agent → Search Agent → Finalize.

---
Pré-requisitos

┌─────────────────────────┬───────────────┐
│       Ferramenta        │ Versão mínima │
├─────────────────────────┼───────────────┤
│ Python                  │ 3.12+         │
├─────────────────────────┼───────────────┤
│ uv                      │ latest        │
├─────────────────────────┼───────────────┤
│ Docker + Docker Compose │ 27+ / 2+      │
├─────────────────────────┼───────────────┤
│ OpenAI API Key          │ —             │
├─────────────────────────┼───────────────┤
│ Tavily API Key          │ —             │
└─────────────────────────┴───────────────┘

---
Setup local

1. Clonar e instalar dependências

git clone <url-do-repositorio>
cd ai-engineer-test
uv sync

2. Configurar variáveis de ambiente

cp .env.example .env
# Edite o .env e preencha OPENAI_API_KEY e TAVILY_API_KEY

3. Ingerir o documento PDF no ChromaDB

make ingest

4. Rodar a API

make dev

A API estará disponível em http://localhost:8000.

---
Como rodar com Docker

# Subir app + Redis
docker compose up --build -d

# Ingerir o PDF (primeira vez)
docker compose exec app python scripts/ingest.py

# Verificar saúde
curl http://localhost:8000/health

Para parar:

docker compose down

---
Variáveis de ambiente

┌────────────────────┬─────────────────────────────────────────────┬────────────────────────┐
│      Variável      │                  Descrição                  │         Padrão         │
├────────────────────┼─────────────────────────────────────────────┼────────────────────────┤
│ OPENAI_API_KEY     │ Chave da API OpenAI                         │ obrigatório            │
├────────────────────┼─────────────────────────────────────────────┼────────────────────────┤
│ TAVILY_API_KEY     │ Chave da API Tavily                         │ obrigatório            │
├────────────────────┼─────────────────────────────────────────────┼────────────────────────┤
│ REDIS_URL          │ URL de conexão Redis                        │ redis://localhost:6379 │
├────────────────────┼─────────────────────────────────────────────┼────────────────────────┤
│ APP_ENV            │ Ambiente (development, production, testing) │ development            │
├────────────────────┼─────────────────────────────────────────────┼────────────────────────┤
│ LOG_LEVEL          │ Nível de log (INFO, DEBUG)                  │ INFO                   │
├────────────────────┼─────────────────────────────────────────────┼────────────────────────┤
│ DEBUG              │ Modo debug                                  │ false                  │
├────────────────────┼─────────────────────────────────────────────┼────────────────────────┤
│ CHROMA_PERSIST_DIR │ Diretório de persistência do ChromaDB       │ ./data/chroma          │
├────────────────────┼─────────────────────────────────────────────┼────────────────────────┤
│ DOCUMENTS_DIR      │ Diretório com os PDFs para ingestão         │ ./docs/data            │
├────────────────────┼─────────────────────────────────────────────┼────────────────────────┤
│ OPENAI_MODEL       │ Modelo OpenAI a usar                        │ gpt-4o-mini            │
└────────────────────┴─────────────────────────────────────────────┴────────────────────────┘

Custo: O modelo gpt-4o-mini é o mais barato da OpenAI (~$0.15/1M tokens de entrada).
Tavily: O free tier oferece 1.000 buscas/mês.

---
Endpoints

GET /health

curl http://localhost:8000/health

{
  "status": "healthy",
  "redis": "connected",
  "vectorstore": "ready",
  "version": "0.1.0"
}

---
POST /chat

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "minha-sessao",
    "message": "Qual o limite de bagagem de mão na LATAM?"
  }'

{
  "session_id": "minha-sessao",
  "response": "A bagagem de mão na LATAM tem dimensão máxima de 115cm e peso máximo de 10kg...",
  "agent_used": "faq",
  "sources": ["manual-politicas-viagem-blis.pdf - Página 3"]
}

O campo session_id é opcional — se omitido, um UUID é gerado automaticamente.

---
POST /chat/stream — SSE Streaming

curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "Quais documentos preciso para viajar para os EUA?"}' \
  --no-buffer

Retorna eventos text/event-stream com atualizações de cada nó do grafo em tempo real.

---
Testes

make test

Ou diretamente:

uv run pytest -v --tb=short

A suíte cobre: configuração, RAG pipeline, FAQ Agent, Search Agent, Orchestrator e endpoints REST + SSE.

---
Deploy (AWS EC2)

A API está hospedada em uma instância EC2 t2.micro (Ubuntu 22.04) com Docker Compose gerenciando app + Redis.

CI/CD com GitHub Actions

- Push em qualquer branch → roda lint (Ruff) + testes (pytest)
- Push na main → lint + testes + deploy automático via SSH na EC2

### Exemplos reais de como a IA me ajudou

**Geração de código:**

O Projeto foi guiado pelo Claude Code seguindo as fases definidas no `CLAUDE.md`. Com isso foi possível desenvolver em Conjunto com Claude Code como meu pair programming, garantindo consistência arquitetural e aderência às melhores práticas, com isso não ficando perdido no meu desenvolvimento. Exemplos:
- Pipeline RAG completo: `loader.py` → `vectorstore.py` → `retriever.py` → `scripts/ingest.py`
- Grafo LangGraph com roteamento condicional (`orchestrator.py`) — incluindo a lógica de fallback para JSON inválido do LLM
- Workflows GitHub Actions para lint + testes + deploy automático via SSH na AWS EC2
- MCP server expondo os agentes como ferramentas nativas

**Debug com análise de logs:**

- **`RedisSaver` retornando `_GeneratorContextManager`**: O traceback apontava `TypeError: Invalid checkpointer provided`. O
Claude identificou que `RedisSaver.from_conn_string()` retorna um context manager, não uma instância. Solução: refatorar
`checkpointer.py` para `@contextmanager` e atualizar o lifespan do FastAPI para usar `with checkpointer_context() as
checkpointer`.

- **ChromaDB `Nothing found on disk`**: Erro no Docker após ingest bem-sucedido. Análise dos logs identificou que volumes nomeados
 Docker impedem o backend Rust (HNSW) de encontrar os arquivos de índice em disco. Solução: trocar para bind mount
(`./data/chroma:/app/data/chroma`).

- **`TavilySearchResults` deprecado**: O wrapper LangChain falhou com parâmetros inconsistentes entre versões. Claude sugeriu
migrar para `TavilyClient` do pacote `tavily-python` diretamente, com interface estável e retorno previsível (`list[dict]`).

- **Patch incorreto nos testes RAG**: `test_get_retriever_configured` falhava porque o patch estava em
`src.rag.vectorstore.get_vectorstore` ao invés de `src.rag.retriever.get_vectorstore`. Claude identificou a regra: *"patch where
the function is used, not where it's defined"*.

**Decisões arquiteturais discutidas:**

- Escolha entre Railway vs AWS EC2 para deploy (trade-offs de complexidade vs controle)
- `TavilyClient` direto vs wrappers LangChain
- Bind mount vs volume nomeado para ChromaDB
- Singleton `MemorySaver` vs `RedisSaver` por ambiente

---

### O que funcionou bem

- Geração de código consistente com a arquitetura definida em todas as 11 fases do projeto
- Identificação rápida de causas raiz em erros de runtime a partir de tracebacks completos
- Manutenção de convenções (Conventional Commits, LAYER.md, tipagem forte, Pydantic v2) ao longo de todo o desenvolvimento
- Sugestão de padrões corretos que não eram óbvios: context manager para Redis, bind mount para ChromaDB, `asyncio` mock para SSE
nos testes

### O que precisei corrigir manualmente

- **Rota SSE com 404**: O endpoint `POST /chat/stream` estava sem o decorator `@router.post` — foi perdido durante uma edição
intermediária. Identifiquei inspecionando o arquivo diretamente e corrigi.
- **Typo em log**: `logger.pdf_loaded` ao invés de `loader.pdf_loaded` em `loader.py` — erro de digitação no nome do evento
estruturado, corrigido manualmente.
- **Ruff B008**: Falso positivo flagando `Depends()` do FastAPI. Necessitou adicionar `"B008"` ao `ignore` do `pyproject.toml`.
- **Ruff E402**: Imports do `mcp_server.py` posicionados após código de inicialização. Necessitou reordenar todos os imports para
o topo do arquivo.
- **Security Group SSH**: A regra de entrada na EC2 estava restrita ao IP pessoal, bloqueando o runner do GitHub Actions.
Necessitou abrir a porta 22 para `0.0.0.0/0` no console da AWS.

---
