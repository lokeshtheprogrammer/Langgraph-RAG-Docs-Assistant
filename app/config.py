from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM Settings
    LLM_PROVIDER: str = Field("google", description="LLM provider: google or groq")
    LLM_MODEL: str = Field("gemini-2.5-flash", description="Model identifier")
    GEMINI_API_KEY: str | None = Field(None, description="API Key for Google Gemini")
    GROQ_API_KEY: str | None = Field(None, description="API Key for Groq")

    # Embeddings & Vector Store
    EMBEDDING_MODEL: str = Field("sentence-transformers/all-MiniLM-L6-v2", description="Local sentence transformers model name")
    CHROMA_PERSIST_DIR: str = Field("./chroma_db", description="Path to persistent ChromaDB folder")

    # Databases
    SQLITE_DB_PATH: str = Field("./data/app.db", description="Path to SQLite database")

    # Retrieval & Pipeline config
    TOP_K: int = Field(5, description="Number of context chunks to retrieve")
    MAX_RETRIES: int = Field(2, description="Maximum number of query rewrite iterations")
    CHUNK_SIZE: int = Field(512, description="Document chunk character size")
    CHUNK_OVERLAP: int = Field(64, description="Document chunk overlap size")

    # Web Search Fallback
    WEB_SEARCH_ENABLED: bool = Field(True, description="Enable web search fallback when corpus has no results")
    WEB_SEARCH_PROVIDER: str = Field("duckduckgo", description="Web search provider: duckduckgo or tavily")
    TAVILY_API_KEY: str | None = Field(None, description="API Key for Tavily web search")

    # API Validation Config
    MAX_QUERY_LENGTH: int = Field(2000, description="Max query characters")
    MAX_FILE_SIZE_MB: int = Field(10, description="Max uploaded file size in MB")
    ALLOWED_FILE_EXTENSIONS: list[str] = Field([".md", ".txt", ".html", ".pdf"], description="Allowed document extensions")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate config singleton
settings = Settings()
