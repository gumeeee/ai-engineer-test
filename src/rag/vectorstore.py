from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from src.config.settings import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

COLLECTION_NAME = "blist_travel_policies"


def get_embeddings() -> OpenAIEmbeddings:
    """Return configured OpenAI embeddings instance.

    Returns:
        OpenAIEmbeddings configured with model from settings.
    """
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,  # type: ignore
    )


def get_vectorstore() -> Chroma:
    """Return the ChromaDB vector store, creating persist dir if needed.

    Returns:
        Chroma vector store instance.
    """
    persist_dir = Path(settings.chroma_persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=str(persist_dir),
    )


def is_vectorstore_populated() -> bool:
    """Check if the vector store already contains documents.

    Returns:
        True if the collection has at least one document.
    """
    try:
        vectorstore = get_vectorstore()
        count = vectorstore._collection.count()
        logger.info("vectorstore.document_count", count=count)
        return count > 0
    except Exception as e:
        logger.warning("vectorstore.check_failed", error=str(e))
        return False


def ingest_documents(documents: list[Document]) -> Chroma:
    """Add documents to the vector store.

    Args:
        documents: List of Documents to ingest.

    Returns:
        The updated Chroma vector store.
    """
    vectorstore = get_vectorstore()
    vectorstore.add_documents(documents)
    logger.info("vectorstore.ingestion_complete", total=len(documents))
    return vectorstore
