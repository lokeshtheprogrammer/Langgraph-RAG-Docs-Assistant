# TECHNICAL_ARCHITECTURE.md — Technical Architecture
## RAG-Based Technical Documentation Assistant

**Version:** 1.0.0
**Date:** 2025-06-11

---

## Backend Architecture

The backend is a Python monolith structured as a layered architecture. It is intentionally not microservices — given the 2-day scope and solo implementation, a well-structured monolith is the correct tradeoff.

### Layer Overview

```
┌──────────────────────────────────────────────┐
│             Presentation Layer               │
│           FastAPI (routes + schemas)         │
├──────────────────────────────────────────────┤
│              Service Layer                   │
│  QueryService │ IngestionService │ FeedbackSvc│
├──────────────────────────────────────────────┤
│              Domain Layer                    │
│  LangGraph Workflow │ Grader │ Generator      │
├──────────────────────────────────────────────┤
│           Infrastructure Layer               │
│  VectorStore │ EmbeddingModel │ LLMClient     │
├──────────────────────────────────────────────┤
│              Storage Layer                   │
│  ChromaDB │ SQLite (feedback) │ FileSystem    │
└──────────────────────────────────────────────┘
```

---

## Service Layer Design

### QueryService

**Responsibility:** Accept a validated query request, invoke the LangGraph workflow, return a structured response.

```python
class QueryService:
    def __init__(self, workflow: RAGWorkflow):
        self.workflow = workflow

    async def process_query(self, request: QueryRequest) -> QueryResponse:
        state = RAGState(
            question=request.question,
            session_id=request.session_id,
            retry_count=0,
            max_retries=settings.MAX_RETRIES,
        )
        result = await self.workflow.ainvoke(state)
        return QueryResponse(
            answer=result["generation"],
            sources=result["sources"],
            query_type=result["query_type"],
            retry_count=result["retry_count"],
        )
```

### IngestionService

**Responsibility:** Load, chunk, embed, and index documents. Register documents in the document registry.

```python
class IngestionService:
    def __init__(self, loader, splitter, embedder, vector_store, registry):
        ...

    async def ingest_file(self, file: UploadFile) -> IngestionResult:
        raw_text = await self._load_file(file)
        chunks = self._split(raw_text, file.filename)
        doc_ids = await self._embed_and_store(chunks)
        await self.registry.register(file.filename, len(chunks))
        return IngestionResult(document_id=..., chunks_indexed=len(chunks))

    async def ingest_url(self, url: str) -> IngestionResult:
        ...
```

### FeedbackService

**Responsibility:** Persist user feedback for offline analysis.

```python
class FeedbackService:
    def __init__(self, db: FeedbackRepository):
        self.db = db

    async def submit(self, request: FeedbackRequest) -> FeedbackResponse:
        record = FeedbackRecord(
            query=request.query,
            answer=request.answer,
            rating=request.rating,
            comment=request.comment,
            timestamp=datetime.utcnow(),
        )
        await self.db.insert(record)
        return FeedbackResponse(status="recorded")
```

---

## API Layer Design

FastAPI is used for its async support, automatic OpenAPI generation, and Pydantic integration.

### Route Structure

```python
# app/api/routes/query.py
router = APIRouter(prefix="/query", tags=["Query"])

@router.post("", response_model=QueryResponse, status_code=200)
async def query(
    request: QueryRequest,
    service: QueryService = Depends(get_query_service),
) -> QueryResponse:
    ...

# app/api/routes/ingest.py
router = APIRouter(prefix="/ingest", tags=["Ingestion"])

@router.post("", response_model=IngestionResponse, status_code=201)
async def ingest(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    service: IngestionService = Depends(get_ingest_service),
) -> IngestionResponse:
    ...
```

### Dependency Injection

All services are initialized once at startup and injected via FastAPI's `Depends()` mechanism.

```python
# app/dependencies.py
_query_service: Optional[QueryService] = None

def get_query_service() -> QueryService:
    if _query_service is None:
        raise RuntimeError("Services not initialized")
    return _query_service

async def startup():
    global _query_service
    vector_store = ChromaVectorStore(settings.CHROMA_PERSIST_DIR)
    embedding_model = EmbeddingModel(settings.EMBEDDING_MODEL)
    llm_client = LLMClient(settings.LLM_PROVIDER, settings.LLM_MODEL)
    workflow = RAGWorkflow(vector_store, embedding_model, llm_client)
    _query_service = QueryService(workflow)
```

### Error Handling Middleware

```python
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.exception_handler(LLMProviderError)
async def llm_error_handler(request, exc):
    return JSONResponse(status_code=503, content={"detail": "LLM service unavailable"})
```

---

## Domain Layer

### LangGraph Workflow (`app/workflow/graph.py`)

```python
from langgraph.graph import StateGraph, END
from app.workflow.state import RAGState
from app.workflow.nodes import (
    query_analysis_node,
    retrieval_node,
    document_grading_node,
    generation_node,
    query_rewrite_node,
)
from app.workflow.routing import route_after_grading

def build_rag_graph(vector_store, llm_client) -> CompiledStateGraph:
    graph = StateGraph(RAGState)

    graph.add_node("query_analysis", query_analysis_node(llm_client))
    graph.add_node("retrieval", retrieval_node(vector_store))
    graph.add_node("document_grading", document_grading_node(llm_client))
    graph.add_node("generation", generation_node(llm_client))
    graph.add_node("query_rewrite", query_rewrite_node(llm_client))

    graph.set_entry_point("query_analysis")
    graph.add_edge("query_analysis", "retrieval")
    graph.add_edge("retrieval", "document_grading")
    graph.add_conditional_edges(
        "document_grading",
        route_after_grading,
        {
            "generate": "generation",
            "rewrite": "query_rewrite",
            "fallback": "generation",
        }
    )
    graph.add_edge("query_rewrite", "retrieval")
    graph.add_edge("generation", END)

    return graph.compile()
```

---

## Infrastructure Layer

### VectorStore Abstraction

```python
# app/infrastructure/vector_store.py
from abc import ABC, abstractmethod

class VectorStoreBase(ABC):
    @abstractmethod
    def add_documents(self, chunks: List[DocumentChunk]) -> List[str]: ...

    @abstractmethod
    def similarity_search(self, query: str, k: int) -> List[DocumentChunk]: ...

    @abstractmethod
    def list_documents(self) -> List[DocumentMeta]: ...

class ChromaVectorStore(VectorStoreBase):
    def __init__(self, persist_dir: str, embedding_fn):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="technical_docs",
            metadata={"hnsw:space": "cosine"}
        )
        self.embedding_fn = embedding_fn

    def similarity_search(self, query: str, k: int = 5) -> List[DocumentChunk]:
        embedding = self.embedding_fn.embed_query(query)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )
        return self._parse_results(results)
```

### Embedding Model Abstraction

```python
# app/infrastructure/embeddings.py
class EmbeddingModel:
    def __init__(self, model_name: str):
        if model_name.startswith("sentence-transformers"):
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name.split("/", 1)[1])
            self._embed = lambda texts: self.model.encode(texts).tolist()
        elif "text-embedding" in model_name:
            from openai import OpenAI
            self.client = OpenAI()
            self._embed = lambda texts: [
                r.embedding for r in self.client.embeddings.create(
                    input=texts, model=model_name
                ).data
            ]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text])[0]
```

### LLM Client Abstraction

```python
# app/infrastructure/llm_client.py
class LLMClient:
    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model
        self._client = self._init_client()

    def _init_client(self):
        if self.provider == "groq":
            from groq import Groq
            return Groq()
        elif self.provider == "openai":
            from openai import OpenAI
            return OpenAI()
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            return Anthropic()
        raise ValueError(f"Unknown provider: {self.provider}")

    def invoke(self, messages: List[dict], **kwargs) -> str:
        # Normalize to provider-specific API
        ...

    async def ainvoke(self, messages: List[dict], **kwargs) -> str:
        # Async version
        ...
```

---

## AI Layer

### Node Implementations

```python
# app/workflow/nodes.py

def query_analysis_node(llm: LLMClient):
    async def node(state: RAGState) -> dict:
        prompt = QUERY_ANALYSIS_PROMPT.format(question=state["question"])
        response = await llm.ainvoke([{"role": "user", "content": prompt}])
        parsed = parse_query_analysis(response)
        return {
            "rewritten_query": parsed["rewritten_query"],
            "query_type": parsed["query_type"],
        }
    return node

def retrieval_node(vector_store: VectorStoreBase):
    async def node(state: RAGState) -> dict:
        query = state.get("rewritten_query") or state["question"]
        docs = vector_store.similarity_search(query, k=state.get("top_k", 5))
        return {"retrieved_docs": docs}
    return node

def document_grading_node(llm: LLMClient):
    async def node(state: RAGState) -> dict:
        graded = []
        for doc in state["retrieved_docs"]:
            prompt = GRADING_PROMPT.format(
                question=state["question"],
                chunk=doc.content
            )
            response = await llm.ainvoke([{"role": "user", "content": prompt}])
            grade = parse_grade(response)  # "relevant" or "irrelevant"
            graded.append((doc, grade))

        relevant = [doc for doc, grade in graded if grade == "relevant"]
        return {
            "graded_docs": graded,
            "relevant_docs": relevant,
        }
    return node

def generation_node(llm: LLMClient):
    async def node(state: RAGState) -> dict:
        if state.get("should_fallback"):
            return {
                "generation": "I don't have sufficient information in my knowledge base to answer this question.",
                "sources": [],
            }
        context = build_context(state["relevant_docs"])
        prompt = GENERATION_PROMPT.format(
            context=context,
            question=state["question"]
        )
        answer = await llm.ainvoke([{"role": "user", "content": prompt}])
        sources = extract_sources(state["relevant_docs"])
        return {"generation": answer, "sources": sources}
    return node

def query_rewrite_node(llm: LLMClient):
    async def node(state: RAGState) -> dict:
        prompt = REWRITE_PROMPT.format(
            question=state["question"],
            rewritten_query=state.get("rewritten_query", state["question"]),
            retry_count=state["retry_count"],
        )
        new_query = await llm.ainvoke([{"role": "user", "content": prompt}])
        return {
            "rewritten_query": new_query.strip(),
            "retry_count": state["retry_count"] + 1,
        }
    return node
```

---

## Vector Database Layer

**Technology Choice:** ChromaDB (persistent mode)

**Rationale:** ChromaDB is purpose-built for embedding storage, runs locally without external infrastructure, supports persistent storage to disk, and integrates natively with LangChain. FAISS is faster but requires manual serialization and lacks built-in metadata filtering.

**Collection schema:**

```python
{
    "id": "chunk_abc123",
    "embedding": [...],  # float32 vector
    "document": "chunk text content",
    "metadata": {
        "source_file": "langchain_docs.md",
        "document_id": "doc_001",
        "chunk_index": 3,
        "total_chunks": 47,
        "ingestion_timestamp": "2025-06-11T10:00:00Z",
        "char_count": 487
    }
}
```

---

## Embedding Layer

**Default Model:** `sentence-transformers/all-MiniLM-L6-v2`
- Dimension: 384
- Runs locally, no API cost
- Well-suited for semantic similarity on English text
- Suitable for technical documentation

**Alternative:** `text-embedding-3-small` (OpenAI)
- Dimension: 1536
- Higher quality, especially for domain-specific terminology
- Small API cost (~$0.002/1M tokens)

**Consistency guarantee:** The same embedding model must be used at ingestion time and query time. The model name is stored in a configuration file and validated at startup.

---

## LLM Integration Layer

The LLM is used for three purposes:
1. Query analysis and rewriting (lightweight)
2. Document grading (per-chunk, structured JSON output)
3. Answer generation (full response)

**Provider selection logic:**

```python
LLM_PROVIDER_MAP = {
    "groq": GroqLLMAdapter,
    "openai": OpenAILLMAdapter,
    "anthropic": AnthropicLLMAdapter,
    "google": GoogleLLMAdapter,
}
```

**Recommended model per task:**
- Grading: any fast/cheap model (Groq Llama3-8b, GPT-4o-mini, Gemini Flash)
- Generation: better model preferred (Llama3-70b, GPT-4o-mini, Claude Haiku)

---

## Storage Layer

| Store | Technology | Purpose | Persistence |
|-------|-----------|---------|-------------|
| Vector Store | ChromaDB | Embeddings + chunks + metadata | Disk (./chroma_db) |
| Document Registry | SQLite | Tracks ingested documents | Disk (./data/registry.db) |
| Feedback Store | SQLite | User feedback records | Disk (./data/feedback.db) |
| Session Store (optional) | In-memory dict | Conversation history | Per-process (lost on restart) |

---

## Configuration Management

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama3-8b-8192"
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # Embedding
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Vector Store
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # Retrieval
    TOP_K: int = 5
    MAX_RETRIES: int = 2

    # Chunking
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64

    # API
    MAX_QUERY_LENGTH: int = 2000
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_EXTENSIONS: list = [".md", ".txt", ".html", ".pdf"]

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Logging Strategy

```python
# app/core/logging.py
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "extra": getattr(record, "extra", {}),
        })

logger = logging.getLogger("rag_assistant")
```

**Log events:**
- Every query received (question hash, not plain text, for privacy)
- Retrieval result count
- Grading outcomes (N relevant, M irrelevant)
- Retry count on each loop iteration
- Generation success/failure
- LLM API errors with provider/model info
- Ingestion events (document name, chunk count, duration)

---

## Monitoring Strategy

For MVP: structured JSON logs to stdout, parseable by any log aggregator.

Future: integrate with Prometheus + Grafana or Langfuse for LLM observability.

**Key metrics to track:**
- `query_latency_ms` — end-to-end query time
- `retrieval_k_results` — number of chunks retrieved
- `grading_relevant_ratio` — ratio of relevant chunks per query
- `retry_count_histogram` — distribution of retry counts
- `fallback_rate` — % of queries that hit the fallback
- `llm_tokens_used` — for cost tracking

---

## Error Handling Strategy

| Error Type | Handling |
|---|---|
| `ValidationError` (Pydantic) | Return 422 with field-level detail |
| `LLMAPIError` | Retry with exponential backoff; return 503 after max retries |
| `VectorStoreError` | Return 503; log with full traceback |
| `JSONDecodeError` (grading parse) | Default grade to "irrelevant"; log warning |
| `FileValidationError` | Return 400 with specific message |
| `MaxRetriesExceeded` | Return 200 with fallback answer (not a 5xx error) |
| Unhandled exceptions | Caught by global handler; return 500 with request ID |

---

## Dependency Management

```
# requirements.txt
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
langgraph>=0.1.0
langchain>=0.2.0
langchain-community>=0.2.0
chromadb>=0.5.0
sentence-transformers>=3.0.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
python-dotenv>=1.0.0
groq>=0.9.0
openai>=1.30.0
anthropic>=0.28.0
python-multipart>=0.0.9
aiofiles>=23.2.0
httpx>=0.27.0

# Optional
streamlit>=1.35.0
tavily-python>=0.3.0

# Dev
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0  # for TestClient
```

---

## Design Patterns Used

| Pattern | Where Used | Why |
|---------|-----------|-----|
| Strategy Pattern | LLM provider selection | Swap providers without changing workflow |
| Factory Pattern | Node creation in graph builder | Inject dependencies cleanly |
| Repository Pattern | VectorStore, FeedbackStore | Abstract storage from business logic |
| Dependency Injection | FastAPI `Depends()` | Testability, single initialization |
| State Machine | LangGraph StateGraph | Natural fit for RAG pipeline flow |
| Chain of Responsibility | Node pipeline | Each node transforms and passes state |
| Template Method | Prompt templates | Consistent prompt structure |

---

## Architectural Decisions

### Decision 1: LangGraph over LangChain Expression Language (LCEL)

**Context:** Both LangGraph and LCEL can orchestrate LLM pipelines.
**Decision:** LangGraph.
**Rationale:** LangGraph is explicitly required by the assignment. Additionally, LangGraph's StateGraph model is better suited for workflows with conditional branching and retry loops, which LCEL chains struggle with.

### Decision 2: ChromaDB over FAISS

**Context:** Both are local vector stores. FAISS is faster; ChromaDB is more feature-rich.
**Decision:** ChromaDB persistent mode.
**Rationale:** ChromaDB supports persistent storage out of the box without manual serialization. It also supports metadata filtering and has a clean Python API. For a prototype with a 3-5 document corpus, performance difference is negligible.

### Decision 3: Monolith over Microservices

**Context:** Could split ingestion, query, feedback into separate services.
**Decision:** Single FastAPI application.
**Rationale:** 2-day timeline, solo developer, prototype scope. Microservices add operational complexity (service discovery, inter-service comms) without value at this scale.

### Decision 4: sentence-transformers as default embedding model

**Context:** OpenAI embeddings are higher quality; sentence-transformers are free.
**Decision:** Default to `all-MiniLM-L6-v2` with OpenAI as configurable override.
**Rationale:** Zero cost, runs locally, eliminates API dependency for the embedding step. Quality is sufficient for a 3-5 document corpus.

---

## Tradeoffs

| Decision | Pro | Con |
|---------|-----|-----|
| Local ChromaDB | No infra setup, free, persistent | Not horizontally scalable |
| sentence-transformers embedding | Free, local, no latency | Lower quality than OpenAI embeddings |
| Synchronous grading (one chunk at a time) | Simple, correct | Slower than batching |
| SQLite for feedback/registry | Zero setup | Not suitable for high concurrency |
| JSON-structured grading output | Easy to parse | Fragile if LLM deviates from schema |
| In-memory session store | Simple | Lost on restart, no multi-process support |