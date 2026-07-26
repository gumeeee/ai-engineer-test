from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config.settings import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


def load_pdf(file_path: str | Path) -> list[Document]:
    file_path = Path(file_path).resolve(strict=True)
    if '..' in file_path.parts:
        raise ValueError('Invalid file path')
    """
    Load a PDF file and return one Document per page.

    Args:
        def load_pdf(file_path: str | Path) -> list[Document]:
            """
            Load a PDF file and return one Document per page.

            Args:
                def load_and_split(file_path: str | Path) -> list[Document]:
                    """Load a PDF and return split chunks ready for embedding.

                    Args:
                        file_path: Path to the PDF file.

                    Returns:
                        List of chunked Documents.
                    """
                    resolved_path = Path(file_path).resolve(strict=True)
                    if '..' in resolved_path.parts:
                        raise ValueError('Invalid file path.')
                    documents = load_pdf(resolved_path)
                    return split_documents(documents)

            Returns:
                List of Documents, one per page.

            Raises:
                FileNotFoundError: If the file does not exist.
            """
            path = Path(file_path).resolve(strict=True)
            if not path.exists() or '..' in path.parts:
                raise FileNotFoundError(f"PDF not found: {path}")

    Returns:
        List of Documents, one per page.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path).resolve(strict=True)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    logger.info("loader.loading_pdf", path=str(path))
    loader = PyPDFLoader(str(path))
    documents = loader.load()
    logger.info("loader.pdf_loaded", pages=len(documents))
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    """Split documents into chunks preserving page metadata.

    Args:
        documents: List of Documents to split.

    Returns:
        List of chunked Documents with metadata.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    chunks = splitter.split_documents(documents)
    logger.info("loader.split_complete", total_chunks=len(chunks))
    return chunks


def load_and_split(file_path: str | Path) -> list[Document]:
    file_path = Path(file_path).resolve(strict=True)
    if not file_path.is_file():
        raise ValueError('Invalid file path')
    from pathlib import Path

    # ...

    file_path = Path(file_path).resolve(strict=True)
    if not file_path.is_file():
        raise ValueError('Invalid file path')
    documents = load_pdf(file_path)
    return split_documents(documents)
    """Load a PDF and return split chunks ready for embedding.

    Args:
        file_path: Path to the PDF file.

    Returns:
        List of chunked Documents.
    """
    documents = load_pdf(file_path)
    return split_documents(documents)
