from langchain_core.vectorstores import VectorStoreRetriever

from src.config.settings import settings
from src.core.logging import get_logger
from src.rag.vectorstore import get_vectorstore

logger = get_logger(__name__)


def get_retriever() -> VectorStoreRetriever:
    """Return a configured similarity retriever.

    Returns:
        VectorStoreRetriever with top_k from settings.
    """
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(
        search_type="similarity", search_kwargs={"k": settings.rag_top_k}
    )
    logger.info("retriever.initialized", top_k=settings.rag_top_k)
    return retriever
