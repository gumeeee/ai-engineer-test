# Tools Layer

## Responsabilidade
Wrappers finos sobre ferramentas externas usadas pelos agentes.

## Dependências
- `src.config` (settings para API keys)
- `src.core` (logging)

## Exporta
- `get_search_tool()` — retorna instância configurada do TavilySearchResults

## Regras
- NÃO conhece agentes, NÃO conhece FastAPI, NÃO conhece RAG
- Apenas wrappers sobre SDKs externos
- Toda configuração vem de settings, nunca hardcoded