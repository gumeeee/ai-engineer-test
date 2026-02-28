# RAG Layer

## Responsabilidade
Ingestão de documentos PDF, chunking, embedding e retrieval via ChromaDB.

## Dependências
- `src.config` (settings para paths, modelos e API keys)
- `src.core` (logging)

## Exporta
- `get_retriever()` — retorna o retriever configurado
- `load_and_split(file_path)` — carrega e divide um PDF em chunks
- `ingest_documents(documents)` — ingere chunks no ChromaDB
- `is_vectorstore_populated()` — verifica se o vector store já tem dados

## Regras
- NÃO conhece agentes, NÃO conhece FastAPI
- Puramente focado em document processing e vector search
- Ingestão deve ser idempotente: verificar antes de reingerir