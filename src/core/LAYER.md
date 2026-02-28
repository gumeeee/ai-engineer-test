# Core Layer

## Responsabilidade
Infraestrutura transversal: logging estruturado e checkpointer de sessões.

## Dependências
- `src.config` (settings)

## Exporta
- `setup_logging(log_level)` — configura o structlog globalmente
- `get_logger(name)` — retorna logger nomeado
- `get_checkpointer()` — retorna checkpointer Redis ou MemorySaver

## Regras
- NÃO conhece agentes, NÃO conhece FastAPI, NÃO conhece RAG
- Sem lógica de negócio — apenas infraestrutura