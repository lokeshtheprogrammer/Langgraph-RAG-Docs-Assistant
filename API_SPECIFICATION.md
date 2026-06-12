# API_SPECIFICATION.md — API Specification
## RAG-Based Technical Documentation Assistant

**Version:** 1.0.0
**Base URL:** `http://localhost:8000`
**OpenAPI Docs:** `http://localhost:8000/docs`
**ReDoc:** `http://localhost:8000/redoc`

---

## Global Response Conventions

All responses return `Content-Type: application/json`.

### Standard Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": {}
  },
  "request_id": "req_abc123"
}
```

### HTTP Status Code Reference

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created (new resource ingested) |
| 400 | Bad Request (invalid input) |
| 404 | Not Found |
| 422 | Unprocessable Entity (Pydantic validation failure) |
| 429 | Rate Limited |
| 503 | Service Unavailable (LLM or vector store down) |
| 500 | Internal Server Error |

---

## Endpoints

---

### POST /query

**Purpose:** Submit a natural language question and receive a grounded, cited answer from the documentation corpus.

#### Request Schema

```json
{
  "question": "string",         // required, 1-2000 chars
  "session_id": "string",       // optional, UUID for conversation memory
  "top_k": 5,                   // optional, 1-20, default 5
  "max_retries": 2              // optional, 0-5, default from config
}
```

#### Pydantic Model

```python
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000,
                          description="Natural language question")
    session_id: Optional[str] = Field(None, description="Session ID for conversation memory")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of chunks to retrieve")
    max_retries: Optional[int] = Field(None, ge=0, le=5,
                                       description="Override max retry count")
```

#### Response Schema

```json
{
  "answer": "string",           // generated answer text with inline citations
  "sources": [
    {
      "source_file": "string",
      "document_id": "string",
      "chunk_index": 0,
      "excerpt": "string"       // first 100 chars of chunk
    }
  ],
  "query_type": "string",       // conceptual | how-to | troubleshooting | api-reference
  "rewritten_query": "string",  // the query actually used for retrieval
  "retry_count": 0,             // number of query rewrites performed
  "is_fallback": false,         // true if insufficient context was found
  "response_time_ms": 1234,
  "session_id": "string"        // echoed back if provided
}
```

#### Validation Rules

- `question` must be 1-2000 characters
- `question` must not be empty or whitespace-only
- `top_k` must be between 1 and 20 (inclusive)
- `session_id` if provided must match UUID format: `^[0-9a-f-]{36}$`

#### Error Responses

| Code | Error Code | Condition |
|------|-----------|-----------|
| 422 | `VALIDATION_ERROR` | question exceeds 2000 chars or is empty |
| 503 | `LLM_UNAVAILABLE` | LLM provider API is down |
| 503 | `VECTOR_STORE_ERROR` | ChromaDB unavailable |
| 500 | `WORKFLOW_ERROR` | Unexpected error in LangGraph |

#### Example Request

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I create a custom tool in LangChain?",
    "top_k": 5
  }'
```

#### Example Response (Success)

```json
{
  "answer": "To create a custom tool in LangChain, you can use the @tool decorator or inherit from the BaseTool class. [Source: langchain_docs.md]\n\nUsing the decorator approach:\n```python\nfrom langchain.tools import tool\n\n@tool\ndef my_tool(input: str) -> str:\n    \"\"\"Describe what the tool does.\"\"\"\n    return f\"Result: {input}\"\n```\n[Source: langchain_docs.md, chunk 12]",
  "sources": [
    {
      "source_file": "langchain_docs.md",
      "document_id": "doc_001",
      "chunk_index": 12,
      "excerpt": "To create a custom tool, use the @tool decorator. The function's docstring..."
    }
  ],
  "query_type": "how-to",
  "rewritten_query": "LangChain custom tool creation @tool decorator BaseTool class",
  "retry_count": 0,
  "is_fallback": false,
  "response_time_ms": 2341,
  "session_id": null
}
```

#### Example Response (Fallback)

```json
{
  "answer": "I was unable to find relevant information in the documentation corpus to answer your question. Please check that your question is related to the indexed documents, or consider rephrasing it.",
  "sources": [],
  "query_type": "conceptual",
  "rewritten_query": "React hooks useEffect tutorial",
  "retry_count": 2,
  "is_fallback": true,
  "response_time_ms": 5876,
  "session_id": null
}
```

---

### POST /ingest

**Purpose:** Ingest a new document into the corpus. Accepts a file upload or a URL. The document is chunked, embedded, and stored in the vector store.

#### Request Schema (multipart/form-data)

```
file:    File (optional) — .md, .txt, .html, .pdf, max 10MB
url:     string (optional) — publicly accessible URL to fetch
```

At least one of `file` or `url` must be provided.

#### Validation Rules

- Exactly one of `file` or `url` must be provided (not both, not neither)
- Allowed file extensions: `.md`, `.txt`, `.html`, `.pdf`
- Maximum file size: 10MB
- URL must be a valid `http://` or `https://` URL
- File content must not be empty after loading

#### Response Schema

```json
{
  "document_id": "string",       // assigned document ID
  "filename": "string",          // original filename or URL-derived name
  "chunks_indexed": 42,          // number of chunks created and indexed
  "file_size_bytes": 12345,
  "status": "indexed",           // indexed | failed
  "message": "string",           // human-readable summary
  "duplicate": false             // true if document was already indexed (dedup check)
}
```

#### Error Responses

| Code | Error Code | Condition |
|------|-----------|-----------|
| 400 | `MISSING_SOURCE` | Neither file nor url provided |
| 400 | `BOTH_SOURCES` | Both file and url provided |
| 400 | `INVALID_FILE_TYPE` | File extension not allowed |
| 400 | `FILE_TOO_LARGE` | File exceeds 10MB |
| 400 | `EMPTY_DOCUMENT` | File has no extractable text content |
| 400 | `INVALID_URL` | URL is malformed |
| 400 | `URL_FETCH_FAILED` | URL could not be fetched (404, timeout, etc.) |
| 503 | `VECTOR_STORE_ERROR` | ChromaDB unavailable |

#### Example Request (File Upload)

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@langchain_docs.md"
```

#### Example Request (URL)

```bash
curl -X POST http://localhost:8000/ingest \
  -F "url=https://raw.githubusercontent.com/langchain-ai/langchain/master/README.md"
```

#### Example Response

```json
{
  "document_id": "doc_007",
  "filename": "langchain_docs.md",
  "chunks_indexed": 47,
  "file_size_bytes": 23041,
  "status": "indexed",
  "message": "Document 'langchain_docs.md' successfully indexed with 47 chunks.",
  "duplicate": false
}
```

#### Example Response (Duplicate)

```json
{
  "document_id": "doc_001",
  "filename": "langchain_docs.md",
  "chunks_indexed": 0,
  "file_size_bytes": 23041,
  "status": "indexed",
  "message": "Document 'langchain_docs.md' was already indexed. Skipping.",
  "duplicate": true
}
```

---

### GET /documents

**Purpose:** List all documents that have been ingested into the corpus.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | all | Filter by status: `indexed`, `failed`, `all` |
| `limit` | int | 50 | Max records to return (1-100) |
| `offset` | int | 0 | Pagination offset |

#### Response Schema

```json
{
  "documents": [
    {
      "document_id": "string",
      "filename": "string",
      "source_url": "string",
      "chunk_count": 47,
      "file_type": "md",
      "status": "indexed",
      "ingestion_timestamp": "2025-06-11T10:00:00Z",
      "file_size_bytes": 23041
    }
  ],
  "total": 5,
  "limit": 50,
  "offset": 0
}
```

#### Error Responses

| Code | Error Code | Condition |
|------|-----------|-----------|
| 422 | `VALIDATION_ERROR` | Invalid query parameter value |
| 503 | `REGISTRY_ERROR` | Document registry unavailable |

#### Example Request

```bash
curl http://localhost:8000/documents
curl "http://localhost:8000/documents?status=indexed&limit=10"
```

#### Example Response

```json
{
  "documents": [
    {
      "document_id": "doc_001",
      "filename": "langchain_docs.md",
      "source_url": "",
      "chunk_count": 47,
      "file_type": "md",
      "status": "indexed",
      "ingestion_timestamp": "2025-06-11T10:00:00Z",
      "file_size_bytes": 23041
    },
    {
      "document_id": "doc_002",
      "filename": "fastapi_tutorial.md",
      "source_url": "https://fastapi.tiangolo.com/tutorial/",
      "chunk_count": 31,
      "file_type": "md",
      "status": "indexed",
      "ingestion_timestamp": "2025-06-11T10:05:00Z",
      "file_size_bytes": 15600
    }
  ],
  "total": 2,
  "limit": 50,
  "offset": 0
}
```

---

### POST /feedback

**Purpose:** Submit user feedback (thumbs up/down) on a generated answer. Used for offline quality monitoring.

#### Request Schema

```json
{
  "query": "string",            // required, the question that was asked
  "answer": "string",           // required, the answer that was given
  "rating": "thumbs_up",        // required: "thumbs_up" | "thumbs_down"
  "comment": "string",          // optional, free text comment
  "session_id": "string",       // optional, for correlation
  "response_time_ms": 1234      // optional, from query response
}
```

#### Pydantic Model

```python
class FeedbackRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    answer: str = Field(..., min_length=1, max_length=10000)
    rating: Literal["thumbs_up", "thumbs_down"]
    comment: Optional[str] = Field(None, max_length=1000)
    session_id: Optional[str] = None
    response_time_ms: Optional[int] = Field(None, ge=0)
```

#### Response Schema

```json
{
  "feedback_id": "string",     // UUID assigned to this feedback record
  "status": "recorded",
  "message": "Thank you for your feedback."
}
```

#### Error Responses

| Code | Error Code | Condition |
|------|-----------|-----------|
| 422 | `VALIDATION_ERROR` | rating not one of allowed values |
| 422 | `VALIDATION_ERROR` | query or answer empty |
| 503 | `STORAGE_ERROR` | Feedback database unavailable |

#### Example Request

```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I create a custom tool in LangChain?",
    "answer": "To create a custom tool, use the @tool decorator...",
    "rating": "thumbs_up",
    "comment": "Very helpful, exactly what I needed"
  }'
```

#### Example Response

```json
{
  "feedback_id": "fb_d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
  "status": "recorded",
  "message": "Thank you for your feedback."
}
```

---

### GET /health

**Purpose:** Health check endpoint for load balancers and monitoring systems.

#### Response Schema

```json
{
  "status": "healthy",           // healthy | degraded | unhealthy
  "version": "1.0.0",
  "components": {
    "vector_store": "ok",        // ok | error
    "document_registry": "ok",
    "llm_provider": "ok",
    "embedding_model": "ok"
  },
  "corpus_size": 5,              // number of indexed documents
  "timestamp": "2025-06-11T10:00:00Z"
}
```

#### Example Request

```bash
curl http://localhost:8000/health
```

---

### DELETE /documents/{document_id}

**Purpose:** Remove a document and all its chunks from the vector store and registry.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `document_id` | string | The document ID from GET /documents |

#### Response Schema

```json
{
  "document_id": "string",
  "chunks_removed": 47,
  "status": "deleted",
  "message": "Document 'doc_001' and 47 chunks have been removed."
}
```

#### Error Responses

| Code | Error Code | Condition |
|------|-----------|-----------|
| 404 | `DOCUMENT_NOT_FOUND` | document_id does not exist |
| 503 | `VECTOR_STORE_ERROR` | ChromaDB unavailable |

#### Example Request

```bash
curl -X DELETE http://localhost:8000/documents/doc_001
```

---

### GET /feedback

**Purpose:** Retrieve stored feedback records for analysis (admin use).

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rating` | string | all | Filter: `thumbs_up`, `thumbs_down`, `all` |
| `limit` | int | 50 | Max records (1-100) |
| `offset` | int | 0 | Pagination offset |

#### Example Request

```bash
curl "http://localhost:8000/feedback?rating=thumbs_down&limit=20"
```

#### Example Response

```json
{
  "feedback": [
    {
      "feedback_id": "fb_abc123",
      "query": "How do I install FastAPI?",
      "rating": "thumbs_down",
      "comment": "Answer was about the wrong version",
      "created_at": "2025-06-11T11:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

## FastAPI Application Setup

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import query, ingest, documents, feedback, health

app = FastAPI(
    title="RAG Technical Documentation Assistant",
    description="Self-corrective RAG system powered by LangGraph",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router)
app.include_router(ingest.router)
app.include_router(documents.router)
app.include_router(feedback.router)
app.include_router(health.router)
```