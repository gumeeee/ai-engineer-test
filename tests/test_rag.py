from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from src.rag.loader import split_documents


def test_load_pdf_raises_if_not_found():
    """Deve lançar FileNotFoundError para arquivo inexistente."""
    from src.rag.loader import load_pdf

    with pytest.raises(FileNotFoundError):
        load_pdf("/tmp/arquivo_inexistente.pdf")


def test_split_documents_creates_multiple_chunks():
    """Texto longo deve gerar mais de um chunk."""
    from src.rag.loader import split_documents

    docs = [Document(page_content="palavra " * 500, metadata={"page": 0})]
    chunks = split_documents(docs)

    assert len(chunks) > 1


def test_split_documents_preserves_metadata():
    """Metadata da página deve ser preservada nos chunks."""

    docs = [
        Document(
            page_content="texto " * 300, metadata={"page": 5, "source": "test.pdf"}
        )
    ]
    chunks = split_documents(docs)

    for chunk in chunks:
        assert chunk.metadata["page"] == 5
        assert chunk.metadata["source"] == "test.pdf"


def test_split_documents_chunk_size():
    """Nenhum chunk deve exceder significativamente o chunk_size configurado."""
    from src.config.settings import settings
    from src.rag.loader import split_documents

    docs = [Document(page_content="a " * 5000, metadata={})]
    chunks = split_documents(docs)

    for chunk in chunks:
        assert (
            len(chunk.page_content)
            <= settings.rag_chunk_size + settings.rag_chunk_overlap
        )


@patch("src.rag.vectorstore.Chroma")
@patch("src.rag.vectorstore.OpenAIEmbeddings")
def test_get_vectorstore_creates_persist_dir(
    mock_embeddings, mock_chroma, tmp_path, monkeypatch
):
    """get_vectorstore deve criar o diretório de persistência."""
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))

    import importlib

    import src.config.settings as settings_mod
    import src.rag.vectorstore as vs_mod

    importlib.reload(settings_mod)
    importlib.reload(vs_mod)

    vs_mod.get_vectorstore()

    assert (tmp_path / "chroma").exists()


@patch("src.rag.vectorstore.Chroma")
@patch("src.rag.vectorstore.OpenAIEmbeddings")
def test_ingest_documents_calls_add(mock_embeddings, mock_chroma):
    """ingest_documents deve chamar add_documents no vector store."""

    from src.rag.vectorstore import ingest_documents

    mock_vs_instance = MagicMock()
    mock_chroma.return_value = mock_vs_instance

    docs = [Document(page_content="conteúdo de teste", metadata={})]
    ingest_documents(docs)

    mock_vs_instance.add_documents.assert_called_once_with(docs)


@patch("src.rag.vectorstore.get_vectorstore")
def test_get_retriever_configured(mock_get_vs):
    """get_retriever deve chamar as_retriever com os parâmetros corretos."""
    from src.config.settings import settings
    from src.rag.retriever import get_retriever

    mock_vs = MagicMock()
    mock_get_vs.return_value = mock_vs

    get_retriever()

    mock_vs.as_retriever.assert_called_once_with(
        search_type="similarity",
        search_kwargs={"k": settings.rag_top_k},
    )
