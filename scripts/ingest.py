"""Script to ingest PDF documents into the ChromaDB vector store."""

from pathlib import Path

from src.config.settings import settings
from src.core.logging import get_logger, setup_logging
from src.rag.loader import load_and_split
from src.rag.vectorstore import ingest_documents, is_vectorstore_populated

setup_logging(settings.log_level)
logger = get_logger(__name__)


def main() -> None:
    """Run document ingestion pipeline."""
    documents_dir = Path(settings.documents_dir)

    if not documents_dir.exists():
        logger.error("ingest.documents_dir_not_found", path=str(documents_dir))

    pdf_files = list(documents_dir.glob("*.pdf"))

    if not pdf_files:
        logger.error("ingest.no_pdf_files_found", path=str(documents_dir))

    if is_vectorstore_populated():
        logger.info("ingest.already_populated_skipping")
        return

    all_chunks: list = []
    for pdf_file in pdf_files:
        logger.info("ingest.processing", file=pdf_file.name)
        chunks = load_and_split(pdf_file)
        all_chunks.extend(chunks)

    logger.info("ingest.total_chunks", count=len(all_chunks))
    ingest_documents(all_chunks)
    logger.info("ingest.complete")


if __name__ == "__main__":
    main()
