import httpx
from bs4 import BeautifulSoup

from app.core.exceptions import IngestionError
from app.core.logging import logger
from app.infrastructure.document_loader.base import DocumentLoaderBase


class UrlDocumentLoader(DocumentLoaderBase):
    """Loads document content by fetching a remote URL and extracting raw text."""

    def load(self, source: str) -> str:
        logger.info(f"Scraping document URL content: {source}...")
        try:
            # Fetch content with timeout
            response = httpx.get(source, timeout=15.0, follow_redirects=True)
            if response.status_code != 200:
                logger.error(f"URL load failed with HTTP code {response.status_code} for URL: {source}")
                raise IngestionError(f"HTTP request failed with status {response.status_code}")
                
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove scripts and style elements to clean text
            for script in soup(["script", "style", "header", "footer", "nav"]):
                script.decompose()
                
            text = soup.get_text(separator="\n")
            
            # Simple whitespace cleanup
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk)
            
            logger.info("URL content successfully fetched and cleaned.")
            return text
        except httpx.HTTPError as e:
            logger.error(f"HTTP connection failed for URL {source}: {e}")
            raise IngestionError(f"Network request failed for URL: {e}") from e
        except Exception as e:
            logger.error(f"Failed to scrape URL {source}: {e}")
            raise IngestionError(f"URL parsing failed: {e}") from e
