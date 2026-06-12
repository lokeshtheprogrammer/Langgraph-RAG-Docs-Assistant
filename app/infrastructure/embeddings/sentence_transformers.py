from sentence_transformers import SentenceTransformer

from app.core.logging import logger
from app.infrastructure.embeddings.base import EmbeddingModelBase


class SentenceTransformerAdapter(EmbeddingModelBase):
    """Local SentenceTransformer embedding provider implementation."""
    
    def __init__(self, model_name: str):
        logger.info(f"Loading local SentenceTransformer model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        logger.info("SentenceTransformer model loaded successfully.")
        
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        try:
            embeddings = self.model.encode(texts)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Failed to generate document embeddings: {e}")
            raise
            
    def embed_query(self, text: str) -> list[float]:
        try:
            embedding = self.model.encode([text])[0]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise
