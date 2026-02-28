# CLAUDE.md — Projeto: Blis AI Travel Agents

> **REGRA FUNDAMENTAL**: Você é um assistente de arquitetura e engenharia de software. Você **NÃO executa comandos** e **NÃO escreve código diretamente nos arquivos**. Você fornece **instruções claras, completas e passo a passo** para que EU implemente. Sempre me diga exatamente o que fazer, em qual arquivo, e por quê.

---

## 🎯 Visão Geral do Projeto

Estamos construindo uma **API REST multi-agent** para o setor de turismo usando **FastAPI + LangGraph**. O sistema possui três agentes que colaboram para responder perguntas sobre viagens:

1. **Orchestrator Agent** — Recebe a pergunta, decide qual agente acionar (ou ambos), consolida a resposta final
2. **FAQ Agent (RAG)** — Responde perguntas frequentes sobre políticas de bagagem, check-in, documentação, remarcação, reembolsos etc., usando RAG sobre o documento `manual-politicas-viagem-blis.pdf`
3. **Search Agent** — Usa Tavily para buscar informações em tempo real (preços, conexões, novidades de companhias aéreas)

### Fluxo da Arquitetura

```
Cliente (HTTP) → FastAPI → Orchestrator Agent
                              ├── FAQ Agent (RAG com ChromaDB)
                              └── Search Agent (Tavily Web Search)
```

---

## 🏗️ Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Runtime | Python 3.12+ |
| Package Manager | **uv** (astral-sh/uv) |
| Framework Web | FastAPI + Uvicorn |
| Orquestração de Agentes | LangGraph |
| LLM | OpenAI GPT-4o-mini (ou Claude via API — custo baixo) |
| Vector Store (RAG) | ChromaDB (persistente em disco) |
| Embeddings | OpenAI text-embedding-3-small |
| Web Search Tool | Tavily API |
| Checkpointer de Sessões | Redis via `langgraph-checkpoint-redis` |
| Containerização | Docker + Docker Compose |
| Testes | pytest + pytest-asyncio |
| Linting/Formatting | Ruff |
| Type Checking | Pydantic v2 para models, tipagem forte em todo lugar |

---

## 📁 Estrutura do Projeto

```
blis-travel-agents/
├── .github/
│   └── workflows/
│       ├── ci.yml               # Lint + Testes em push/PR
│       └── deploy.yml           # Deploy automático na main (opcional)
├── deploy/
│   ├── railway.toml             # Config Railway
│   └── render.yaml              # Config Render (alternativa)
├── docs/
│   ├── ARCHITECTURE.md          # Decisões de arquitetura
│   └── data/
│       └── manual-politicas-viagem-blis.pdf
├── src/
│   ├── __init__.py
│   ├── main.py              # Entrypoint FastAPI
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py      # Pydantic Settings (env vars)
│   │   └── LAYER.md         # Documentação desta camada
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py      # POST /chat + SSE streaming
│   │   │   └── health.py    # GET /health
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── chat.py      # Request/Response Pydantic models
│   │   ├── dependencies.py  # Dependency injection FastAPI
│   │   └── LAYER.md
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py  # Orchestrator Agent (LangGraph graph)
│   │   ├── faq_agent.py     # FAQ Agent (RAG)
│   │   ├── search_agent.py  # Search Agent (Tavily)
│   │   ├── state.py         # TypedDict do estado compartilhado
│   │   ├── prompts.py       # System prompts dos agentes
│   │   └── LAYER.md
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── vectorstore.py   # Setup ChromaDB + ingestão
│   │   ├── retriever.py     # Retrieval logic
│   │   ├── loader.py        # PDF loader + text splitter
│   │   └── LAYER.md
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── web_search.py    # Tavily tool wrapper
│   │   └── LAYER.md
│   └── core/
│       ├── __init__.py
│       ├── logging.py       # Logging estruturado (structlog)
│       ├── checkpointer.py  # Redis checkpointer setup
│       └── LAYER.md
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Fixtures compartilhadas
│   ├── test_chat_endpoint.py
│   ├── test_faq_agent.py
│   ├── test_search_agent.py
│   └── test_orchestrator.py
├── scripts/
│   └── ingest.py            # Script para popular o vector store
├── .env.example             # Template de variáveis de ambiente
├── .gitignore
├── .python-version          # 3.12
├── pyproject.toml           # Config do projeto (uv)
├── docker-compose.yml       # App + Redis
├── Dockerfile
├── Makefile                 # Atalhos úteis
├── README.md
└── CLAUDE.md                # Este arquivo (contexto para o AI agent)
```

---

## 📋 Arquivos LAYER.md — Contexto por Camada

Cada diretório principal dentro de `src/` deve conter um arquivo `LAYER.md` que documenta:

1. **Responsabilidade** da camada
2. **Dependências** (o que essa camada importa)
3. **Interfaces públicas** (o que ela exporta)
4. **Regras** (o que NÃO deve existir nesta camada)

Isso serve para que eu (e qualquer AI agent) entenda o escopo de cada módulo ao navegar o projeto.

### Exemplos de conteúdo dos LAYER.md:

**`src/config/LAYER.md`**:
```markdown
# Config Layer
## Responsabilidade
Gerenciar todas as configurações via variáveis de ambiente usando Pydantic Settings.
## Exporta
- `Settings` (classe singleton com todas as configs)
## Regras
- NUNCA importar nada de `agents/`, `rag/`, `api/`
- Apenas tipos primitivos e Pydantic
```

**`src/agents/LAYER.md`**:
```markdown
# Agents Layer
## Responsabilidade
Definir o grafo LangGraph com Orchestrator, FAQ Agent e Search Agent.
## Dependências
- `src.rag` (retriever para o FAQ Agent)
- `src.tools` (Tavily para o Search Agent)
- `src.config` (settings)
- `src.core` (checkpointer, logging)
## Exporta
- `build_graph()` — função que retorna o grafo LangGraph compilado
- `AgentState` — TypedDict do estado
## Regras
- Lógica HTTP NÃO pertence aqui
- Prompts ficam em `prompts.py`, não inline
```

**`src/rag/LAYER.md`**:
```markdown
# RAG Layer
## Responsabilidade
Ingestão de documentos PDF, chunking, embedding e retrieval via ChromaDB.
## Dependências
- `src.config` (settings para paths e API keys)
## Exporta
- `get_retriever()` — retorna o retriever configurado
- `ingest_documents()` — função de ingestão
## Regras
- NÃO conhece agentes, NÃO conhece FastAPI
- Puramente focado em document processing e vector search
```

---

## 🔧 Convenções e Boas Práticas

### Python & Código

- **Tipagem forte em tudo**: type hints em todos os parâmetros, retornos e variáveis onde relevante
- **Pydantic v2** para todos os models de request/response e configuração
- **Docstrings** em todas as funções e classes públicas (estilo Google)
- **Ruff** como linter e formatter único (substituindo black, isort, flake8)
- **Imports absolutos**: sempre `from src.config.settings import Settings`, nunca imports relativos
- **Sem código morto**: nada comentado "para depois"
- **Funções pequenas**: cada função faz uma coisa. Se passar de 30 linhas, considere quebrar
- **Nomes descritivos**: `build_faq_agent_node()` ao invés de `faq()` ou `handle()`

### FastAPI

- **Dependency Injection** para tudo: graph, retriever, settings
- **Status codes explícitos** nas rotas
- **Exception handlers** globais
- **CORS middleware** configurado
- **Lifespan** do FastAPI para inicializar recursos (vector store, graph)
- **Response models** explícitos em cada endpoint

### LangGraph

- **State** definido como `TypedDict` com `Annotated` fields onde necessário
- **Nodes** são funções puras que recebem state e retornam updates
- **Conditional edges** para o roteamento do Orchestrator
- **Checkpointer Redis** como padrão; MemorySaver apenas em `if settings.debug`
- **Thread config** usando `session_id` do request como `thread_id`

### RAG

- **Chunk size**: 1000 tokens com overlap de 200
- **Metadata**: preservar número da página e seção do documento no metadata de cada chunk
- **Retriever**: top_k=4, com score threshold
- **Ingestão idempotente**: se o vector store já existe e está populado, não reingerir

### Git & Gitflow

- **Branch principal**: `main` (protegida)
- **Branch de desenvolvimento**: `develop`
- **Feature branches**: `feature/<nome-descritivo>` (ex: `feature/faq-agent-rag`)
- **Commits**: Conventional Commits em português
  - `feat: adiciona endpoint POST /chat`
  - `fix: corrige retrieval com chunks vazios`
  - `docs: adiciona README com instruções de setup`
  - `refactor: extrai prompts para arquivo dedicado`
  - `test: adiciona testes do FAQ Agent`
  - `chore: configura Docker Compose com Redis`
- **Ordem de desenvolvimento** (feature branches):
  1. `feature/project-setup` — uv init, pyproject.toml, .env.example, Docker
  2. `feature/config-and-core` — Settings, logging, checkpointer
  3. `feature/rag-pipeline` — Loader, chunking, ChromaDB, retriever
  4. `feature/faq-agent` — FAQ Agent node com RAG
  5. `feature/search-agent` — Search Agent node com Tavily
  6. `feature/orchestrator` — LangGraph graph completo
  7. `feature/api-endpoints` — FastAPI routes, schemas, SSE streaming
  8. `feature/docker` — Dockerfile, docker-compose.yml
  9. `feature/tests` — Testes básicos
  10. `feature/docs` — README final, seção de IA

---

## 🐳 Docker & Infraestrutura

### docker-compose.yml deve conter:

- **redis**: imagem `redis:7-alpine`, porta 6379
- **app**: build do Dockerfile, porta 8000, depende do redis
- **Volumes**: para persistência do ChromaDB e Redis

### Dockerfile:

- Multi-stage build
- Base: `python:3.12-slim`
- Instalar `uv` no container
- Copiar `pyproject.toml` e `uv.lock` primeiro (cache de layers)
- Rodar `uv sync` para instalar dependências
- Copiar código fonte
- CMD: `uv run uvicorn src.main:app --host 0.0.0.0 --port 8000`

### .env.example:

```env
# LLM
OPENAI_API_KEY=sk-...

# Tavily (Web Search)
TAVILY_API_KEY=tvly-...

# Redis
REDIS_URL=redis://localhost:6379

# App
APP_ENV=development
LOG_LEVEL=INFO
DEBUG=false

# RAG
CHROMA_PERSIST_DIR=./data/chroma
DOCUMENTS_DIR=./docs/data
```

---

## 📡 API Contract

### POST /chat

**Request:**
```json
{
  "session_id": "uuid-string",
  "message": "Qual o limite de bagagem de mão na LATAM?"
}
```

**Response (JSON):**
```json
{
  "session_id": "uuid-string",
  "response": "A bagagem de mão na LATAM tem dimensão máxima de 115cm (C+L+A) e peso máximo de 10kg. Você pode levar 1 mala + 1 item pessoal.",
  "agent_used": "faq",
  "sources": ["manual-politicas-viagem-blis.pdf - Seção 1.1"]
}
```

### POST /chat/stream (Diferencial — SSE)

Mesmo request body, mas retorna `text/event-stream` com chunks da resposta.

### GET /health

```json
{
  "status": "healthy",
  "redis": "connected",
  "vectorstore": "ready",
  "version": "0.1.0"
}
```

---

## 🤖 System Prompts dos Agentes

### Orchestrator Prompt

```
Você é o orquestrador de um sistema de atendimento a agências de viagem da Blis AI.

Sua função é analisar a pergunta do usuário e decidir qual agente deve respondê-la:

1. **FAQ Agent**: Para perguntas sobre políticas de bagagem, documentação para viagem, check-in, embarque, remarcação, cancelamento, reembolsos, itens especiais, necessidades especiais, programas de fidelidade, conexões e escalas. Ou seja, qualquer dúvida que possa ser respondida com o Manual de Políticas de Viagem da Blis AI.

2. **Search Agent**: Para perguntas que requerem informações em tempo real, como preços atuais de passagens, promoções, notícias de companhias aéreas, condições climáticas em destinos, ou qualquer informação que mude frequentemente e não esteja coberta pelo manual.

3. **Ambos**: Se a pergunta envolver tanto políticas fixas quanto informações atualizadas.

Responda APENAS com sua decisão de roteamento em formato JSON:
{"route": "faq" | "search" | "both", "reasoning": "breve justificativa"}
```

### FAQ Agent Prompt

```
Você é o agente especialista em políticas de viagem da Blis AI.

Você responde dúvidas de agências de viagem e passageiros com base EXCLUSIVAMENTE nos documentos da base de conhecimento fornecidos como contexto.

Regras:
- Responda SOMENTE com informações presentes no contexto fornecido
- Se a informação não estiver no contexto, diga claramente que não encontrou essa informação na base
- Cite a seção relevante do manual quando possível
- Seja preciso com números, valores e prazos
- Responda em português brasileiro, de forma profissional mas acessível
- Formate a resposta de forma clara, usando listas quando apropriado

Contexto recuperado:
{context}
```

### Search Agent Prompt

```
Você é o agente de pesquisa em tempo real da Blis AI.

Você busca informações atualizadas sobre viagens, companhias aéreas, preços e novidades do setor de turismo.

Regras:
- Use a ferramenta de busca para encontrar informações atualizadas
- Sempre mencione a fonte da informação
- Indique claramente quando uma informação é aproximada (ex: preços)
- Responda em português brasileiro
- Seja conciso e relevante
```

---

## ✅ Checklist de Implementação

Siga esta ordem. Cada item é um commit (ou conjunto de commits) em sua respectiva feature branch.

### Fase 1 — Setup (`feature/project-setup`)
- [ ] Inicializar projeto com `uv init`
- [ ] Configurar `pyproject.toml` com todas as dependências
- [ ] Criar `.python-version` (3.12)
- [ ] Criar `.env.example`
- [ ] Criar `.gitignore` (Python, venv, .env, __pycache__, chroma_data, .ruff_cache)
- [ ] Criar estrutura de diretórios vazia com `__init__.py`
- [ ] Configurar Ruff no `pyproject.toml`
- [ ] Criar `Makefile` com comandos úteis
- [ ] Commit: `chore: inicializa projeto com uv e estrutura base`

### Fase 2 — Config & Core (`feature/config-and-core`)
- [ ] Implementar `src/config/settings.py` com Pydantic Settings
- [ ] Implementar `src/core/logging.py` com structlog
- [ ] Implementar `src/core/checkpointer.py` (Redis + fallback MemorySaver)
- [ ] Criar LAYER.md de config e core
- [ ] Commit: `feat: adiciona configuração, logging estruturado e checkpointer`

### Fase 3 — RAG Pipeline (`feature/rag-pipeline`)
- [ ] Copiar PDF do manual para `docs/data/`
- [ ] Implementar `src/rag/loader.py` (PyPDFLoader + RecursiveCharacterTextSplitter)
- [ ] Implementar `src/rag/vectorstore.py` (ChromaDB setup)
- [ ] Implementar `src/rag/retriever.py`
- [ ] Criar `scripts/ingest.py`
- [ ] Criar LAYER.md do rag
- [ ] Testar ingestão manualmente
- [ ] Commit: `feat: implementa pipeline RAG com ChromaDB`

### Fase 4 — FAQ Agent (`feature/faq-agent`)
- [ ] Implementar `src/agents/state.py` (AgentState TypedDict)
- [ ] Implementar `src/agents/prompts.py`
- [ ] Implementar `src/agents/faq_agent.py` (node function)
- [ ] Criar LAYER.md dos agents
- [ ] Commit: `feat: implementa FAQ Agent com RAG`

### Fase 5 — Search Agent (`feature/search-agent`)
- [ ] Implementar `src/tools/web_search.py` (TavilySearchResults wrapper)
- [ ] Implementar `src/agents/search_agent.py` (node function)
- [ ] Criar LAYER.md das tools
- [ ] Commit: `feat: implementa Search Agent com Tavily`

### Fase 6 — Orchestrator (`feature/orchestrator`)
- [ ] Implementar `src/agents/orchestrator.py` com LangGraph StateGraph
- [ ] Definir conditional edges (router)
- [ ] Compilar graph com checkpointer
- [ ] Commit: `feat: implementa Orchestrator com LangGraph`

### Fase 7 — API (`feature/api-endpoints`)
- [ ] Implementar `src/api/schemas/chat.py` (Pydantic models)
- [ ] Implementar `src/api/dependencies.py`
- [ ] Implementar `src/api/routes/chat.py` (POST /chat)
- [ ] Implementar `src/api/routes/health.py` (GET /health)
- [ ] Implementar SSE streaming em `POST /chat/stream`
- [ ] Implementar `src/main.py` (FastAPI app com lifespan)
- [ ] Criar LAYER.md da api
- [ ] Commit: `feat: implementa endpoints REST e SSE streaming`

### Fase 8 — Docker (`feature/docker`)
- [ ] Criar `Dockerfile` (multi-stage com uv)
- [ ] Criar `docker-compose.yml` (app + redis)
- [ ] Testar `docker compose up`
- [ ] Commit: `chore: adiciona Docker e Docker Compose`

### Fase 9 — Testes (`feature/tests`)
- [ ] Criar `tests/conftest.py` com fixtures
- [ ] Testar endpoint /chat
- [ ] Testar FAQ Agent isolado
- [ ] Testar Search Agent isolado
- [ ] Testar roteamento do Orchestrator
- [ ] Commit: `test: adiciona testes básicos dos agentes e endpoints`

### Fase 10 — Deploy & CI/CD (`feature/deploy`) ⭐ DIFERENCIAL
- [ ] Criar `deploy/railway.toml` (ou `render.yaml`) com config de deploy
- [ ] Criar `.github/workflows/ci.yml` (lint + testes no push)
- [ ] Criar `.github/workflows/deploy.yml` (deploy automático na main)
- [ ] Configurar health check no serviço de deploy
- [ ] Fazer deploy real e obter URL pública funcional
- [ ] Adicionar badge de status do CI no README
- [ ] Commit: `ci: adiciona pipeline CI/CD e deploy automático`

### Fase 11 — Documentação (`feature/docs`)
- [ ] Escrever README.md completo
- [ ] Seção "Como usei IA no desenvolvimento"
- [ ] Criar `docs/ARCHITECTURE.md`
- [ ] Adicionar URL pública da API no README (se deploy feito)
- [ ] Commit: `docs: finaliza README e documentação de arquitetura`

---

## 🚀 Deploy & CI/CD (Diferencial)

O objetivo é que o avaliador consiga **testar a API sem instalar nada** — basta fazer um curl para a URL pública.

### Plataforma Recomendada: Railway

Railway é a melhor opção porque suporta **Docker Compose nativamente** (app + Redis juntos). Alternativas: Render (precisa de Redis separado via add-on).

**Estrutura de deploy:**

```
deploy/
├── railway.toml         # Config do Railway
└── Procfile             # Comando de start (fallback)
```

### `deploy/railway.toml`

```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

[service]
internalPort = 8000
```

### CI/CD com GitHub Actions

#### `.github/workflows/ci.yml` — Roda em todo push/PR

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"
      
      - name: Set up Python
        run: uv python install 3.12
      
      - name: Install dependencies
        run: uv sync --dev
      
      - name: Lint with Ruff
        run: uv run ruff check src/ tests/
      
      - name: Format check
        run: uv run ruff format --check src/ tests/
      
      - name: Run tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          TAVILY_API_KEY: ${{ secrets.TAVILY_API_KEY }}
          REDIS_URL: ""
          APP_ENV: testing
        run: uv run pytest -v --tb=short
```

### URL pública no README

Após o deploy, adicionar no topo do README:

```markdown
> 🌐 **API em produção**: https://blis-travel-agents.up.railway.app
>
> Teste agora sem instalar nada:
> ```bash
> curl -X POST https://blis-travel-agents.up.railway.app/chat \
>   -H "Content-Type: application/json" \
>   -d '{"session_id": "demo", "message": "Qual o limite de bagagem de mão na LATAM?"}'
> ```
```

### Custo estimado

| Serviço | Plano | Custo |
|---|---|---|
| Railway | Trial/Hobby | $5/mês (500h free no trial) |
| Render | Free tier | $0 (com cold starts de ~30s) |
| Redis (Railway) | Plugin | Incluído no plano |
| Redis (Render) | Upstash free | $0 (10k commands/day) |

### Alternativa Gratuita: Render

Se Railway não for opção, usar **Render** com:
- Web Service (free tier, Dockerfile)
- Redis via **Upstash** (free tier, 10k req/dia) como variável de ambiente
- `render.yaml` para Infrastructure as Code:

```yaml
services:
  - type: web
    name: blis-travel-agents
    runtime: docker
    plan: free
    healthCheckPath: /health
    envVars:
      - key: REDIS_URL
        value: <upstash-redis-url>
      - key: OPENAI_API_KEY
        sync: false
      - key: TAVILY_API_KEY
        sync: false
```

---

## 📝 Estrutura do README.md

O README deve conter obrigatoriamente:

1. **Título e descrição** do projeto
2. **URL pública da API** (se deploy feito) com exemplo de curl pronto para testar
3. **Badges** (CI status, Python version, License)
4. **Arquitetura** (diagrama ASCII ou Mermaid)
5. **Pré-requisitos** (Python 3.12+, uv, Docker, API keys)
6. **Setup local sem custo** (instruções para rodar com modelos gratuitos/baratos se possível, ou indicar que precisa de API key)
7. **Como rodar**:
   - Com Docker: `docker compose up`
   - Sem Docker: `uv sync && uv run python scripts/ingest.py && uv run uvicorn src.main:app`
8. **Variáveis de ambiente** (tabela com todas as vars)
9. **Exemplos de uso** (curl commands para cada endpoint)
10. **Como rodar testes**: `uv run pytest`
11. **Deploy** (como está publicado, onde, como fazer redeploy)
12. **Decisões técnicas** (por que cada tecnologia foi escolhida)
13. **Como usei IA no desenvolvimento** (seção obrigatória do teste)

---

## 🚨 Regras para o AI Agent (VOCÊ)

1. **NUNCA execute comandos por mim.** Me diga exatamente o que executar e eu executo.
2. **NUNCA escreva código diretamente.** Me dê o código completo do arquivo e eu crio/edito.
3. **Sempre explique o porquê** de cada decisão antes de dar a instrução.
4. **Respeite a estrutura de pastas** definida neste documento.
5. **Respeite a ordem de implementação** (Fases 1-11).
6. **Siga as convenções de commit** (Conventional Commits em PT-BR).
7. **Lembre-se dos LAYER.md** — me peça para criá-los a cada nova camada.
8. **Se eu perguntar algo fora de escopo**, me redirecione para a fase correta.
9. **Antes de cada fase**, recapitule o que já fizemos e o que vamos fazer agora.
10. **Ao final de cada fase**, me dê uma checklist de verificação para eu confirmar que tudo funciona.

---

## 📚 Base de Conhecimento RAG

O FAQ Agent utilizará o documento **"Manual de Políticas de Viagem — Blis AI v2.1"** que cobre:

| Seção | Conteúdo |
|---|---|
| 1 | Políticas de Bagagem (mão, despachada, excesso, itens proibidos) |
| 2 | Documentação para Viagem (doméstico, América do Sul, EUA/Europa, validade passaporte) |
| 3 | Check-in e Embarque (modalidades, prazos, seleção de assentos) |
| 4 | Remarcação e Cancelamento (regras por tarifa, direitos ANAC, procedimentos) |
| 5 | Reembolsos (prazos por companhia, taxas por antecedência) |
| 6 | Itens Especiais (animais, equipamentos esportivos) |
| 7 | Passageiros com Necessidades Especiais (códigos SSR, gestantes) |
| 8 | Programas de Fidelidade (LATAM Pass, Smiles, TudoAzul, etc.) |
| 9 | Conexões e Escalas (MCT por aeroporto, responsabilidades) |
| 10 | Responsabilidades e Contatos (canais das companhias, órgãos regulatórios) |

Este documento será ingerido via PyPDFLoader, dividido em chunks com metadata de seção e página, e armazenado no ChromaDB.

---

## 💡 Dicas de Custo Zero para Quem Rodar Localmente

No README, orientar que:
- **OpenAI API**: modelo `gpt-4o-mini` é o mais barato (~$0.15/1M input tokens). Alternativamente, pode-se usar `ollama` com modelos locais como fallback.
- **Tavily API**: free tier tem 1000 buscas/mês.
- **ChromaDB**: roda local, sem custo.
- **Redis**: roda via Docker, sem custo.

---

*Este arquivo deve estar na raiz do repositório como `CLAUDE.md` para servir de contexto ao AI coding agent em qualquer sessão futura.*

---

## 🧠 Como Usar Este Arquivo com o Claude Code

### Passo 1 — Preparar o repositório

Antes de abrir o Claude Code, crie o repositório e coloque este arquivo na raiz:

```bash
mkdir blis-travel-agents && cd blis-travel-agents
git init
git checkout -b develop
# Copie este arquivo como CLAUDE.md na raiz
# Copie o PDF do manual para docs/data/
```

### Passo 2 — Abrir o Claude Code

Abra o terminal na raiz do projeto e execute:

```bash
claude
```

O Claude Code **lê automaticamente o `CLAUDE.md`** da raiz do projeto ao iniciar. Este é o arquivo de contexto padrão que ele usa para entender o projeto.

### Passo 3 — Primeira mensagem

Na primeira interação, envie:

```
Leia o CLAUDE.md na raiz do projeto. Esse é nosso plano completo.
Vamos começar pela Fase 1 — Setup do projeto.
Me dê as instruções passo a passo para inicializar o projeto com uv.
```

### Passo 4 — Fluxo de trabalho por fase

Para cada fase, siga este ciclo:

```
1. Você pede: "Vamos para a Fase N"
2. Claude Code recapitula o que foi feito e dá instruções
3. Você implementa e executa
4. Você confirma: "Fase N concluída, tudo funcionando"
5. Você commita seguindo o padrão
6. Próxima fase
```

### Passo 5 — Se o Claude Code perder contexto

Em sessões longas, o Claude Code pode esquecer detalhes. Basta dizer:

```
Releia o CLAUDE.md e me diga em que fase estamos.
Último commit foi: feat: implementa FAQ Agent com RAG
```

### Dicas para extrair o máximo do Claude Code

- **Seja específico**: "Me dê o código completo do arquivo `src/agents/orchestrator.py`" é melhor que "faz o orchestrator"
- **Peça revisão**: "Revise o arquivo X considerando as regras do LAYER.md da camada agents"
- **Peça debug**: "Esse erro apareceu ao rodar: [cole o erro]. O que devo corrigir?"
- **Peça refactor**: "Esse arquivo ficou com 80 linhas. Sugira como quebrar seguindo as boas práticas do CLAUDE.md"
- **Documente tudo**: Ao final, peça "Me ajude a escrever a seção 'Como usei IA no desenvolvimento' do README com base no que fizemos juntos"