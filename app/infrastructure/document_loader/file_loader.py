import os

from app.core.exceptions import IngestionError
from app.core.logging import logger
from app.infrastructure.document_loader.base import DocumentLoaderBase


class LocalFileLoader(DocumentLoaderBase):
    """Loads document content from local files based on file extension."""

    def load(self, source: str) -> str:
        if not os.path.exists(source):
            logger.error(f"File not found: {source}")
            raise IngestionError(f"Document file does not exist: {source}")

        _, ext = os.path.splitext(source.lower())
        
        try:
            if ext in (".txt", ".md"):
                with open(source, encoding="utf-8") as f:
                    return f.read()
            elif ext == ".html":
                from bs4 import BeautifulSoup
                with open(source, encoding="utf-8") as f:
                    soup = BeautifulSoup(f.read(), "html.parser")
                    return soup.get_text(separator="\n")
            elif ext == ".pdf":
                # Ephemeral import to handle pdf if pypdf or PyPDF2 is installed
                try:
                    import pypdf
                    reader = pypdf.PdfReader(source)
                    text_parts = []
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    return "\n\n".join(text_parts)
                except ImportError:
                    logger.warning("pypdf package is not installed. PDF parsing not supported. Returning placeholder.")
                    raise IngestionError("PDF parsing is not supported because 'pypdf' package is missing.") from None
            else:
                raise IngestionError(f"Unsupported file type: {ext}")
        except Exception as e:
            logger.error(f"Failed to read file {source}: {e}")
            raise IngestionError(f"Error reading file content: {e}") from e
