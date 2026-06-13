
from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    source_file: str = Field(..., description="The name of the source document")
    document_id: str = Field(..., description="Unique ID of the document")
    chunk_index: int = Field(..., description="Index of the chunk in the document")
    excerpt: str = Field(..., description="Snippet snippet content of the chunk")

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="Natural language user question")
    session_id: str | None = Field(None, pattern=r"^[0-9a-fA-F-]{36}$", description="UUID for conversation session memory")
    top_k: int | None = Field(5, ge=1, le=20, description="Number of context chunks to retrieve")
    max_retries: int | None = Field(None, ge=0, le=5, description="Override maximum retry count")
    filter_filenames: list[str] | None = Field(None, description="Scope retrieval to these filenames only (uploaded document focus)")

class DebugChunk(BaseModel):
    content: str = Field(..., description="Text content of the chunk")
    source_file: str = Field(..., description="Source document filename")
    chunk_index: int = Field(..., description="Index of the chunk")
    grade: str | None = Field(None, description="Relevance grade: relevant or irrelevant")
    distance: float | None = Field(None, description="Semantic distance score from the query")

class QueryResponse(BaseModel):
    answer: str = Field(..., description="System response text with citations")
    sources: list[SourceReference] = Field(..., description="List of document citations used")
    query_type: str = Field(..., description="Inferred question intent category")
    rewritten_query: str = Field(..., description="The query string used to retrieve records")
    retry_count: int = Field(..., description="Count of rewrite iterations performed")
    is_fallback: bool = Field(..., description="Indicates if context search yielded no results")
    response_time_ms: int = Field(..., description="Latency tracking duration in ms")
    session_id: str | None = Field(None, description="The session identifier")
    llm_provider_status: str = Field(..., description="Active LLM provider status (primary_groq, fallback_gemini, retrieval_only)")
    # Debug trace fields
    retrieved_chunks: list[DebugChunk] | None = Field(None, description="Raw chunks retrieved from vector store")
    graded_chunks: list[DebugChunk] | None = Field(None, description="Chunks with relevance grades")
    hallucination_score: float | None = Field(None, description="Grounding verification score (0.0-1.0)")
    confidence_score: float | None = Field(
        None,
        description="Overall answer confidence (0.0-1.0) combining grounding, retrieval quality, and retry penalty"
    )
    retrieval_count: int | None = Field(None, description="Number of chunks retrieved from the vector store")
    relevant_chunk_count: int | None = Field(None, description="Number of chunks graded as relevant")

