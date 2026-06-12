# PHASE_4_API_LAYER.md — Phase 4: API Layer
## RAG-Based Technical Documentation Assistant

---

## 1. Phase Goal

*   **Business Goal**: Expose the corrective RAG engine and ingestion services via standard, authenticated, documented REST endpoints.
*   **Technical Goal**: Implement FastAPI application containing routes for querying, doc ingestion (multipart upload / URL scrape), listing current registry catalog, deleting entries, and storing feedback metrics.
*   **Completion Criteria**: Starting the uvicorn API server allows Swagger UI documentation access, and HTTP clients successfully execute queries, uploads, and feedback submissions.

---

## 2. Scope

### Included
*   FastAPI application setup with strict CORS configurations.
*   Pydantic request and response schemas for all endpoints.
*   FastAPI dependency injection provider mapping singleton connections.
*   Routes implementations:
    - `POST /query`: Invokes LangGraph, returns response with references.
    - `POST /ingest`: Accepts file uploads or remote URLs.
    - `GET /documents`: Lists registered documents with stats.
    - `DELETE /documents/{document_id}`: Removes document vectors and meta records.
    - `POST /feedback`: Records user ratings (thumbs up/down) to SQLite.
    - `GET /feedback`: Fetches feedback catalog.
    - `GET /health`: Diagnostic checking.
*   Custom error handler middleware returning structured JSON responses.

### Excluded
*   Frontend UI implementation.
*   Multi-tenant API keys or JWT authorization handlers.

---

## 3. Dependencies

*   Phases 1, 2, and 3 completed successfully.
*   LangGraph StateGraph compiled and verified.
*   SQLite databases verified.

---

## 4. Deliverables

*   `app/api/schemas/common.py`
*   `app/api/schemas/query.py`
*   `app/api/schemas/ingest.py`
*   `app/api/schemas/documents.py`
*   `app/api/schemas/feedback.py`
*   `app/api/routes/query.py`
*   `app/api/routes/ingest.py`
*   `app/api/routes/documents.py`
*   `app/api/routes/feedback.py`
*   `app/api/routes/health.py`
*   `app/dependencies.py`
*   `app/services/query_service.py`
*   `app/services/feedback_service.py`
*   `app/repositories/feedback_repository.py`
*   `app/core/middleware.py`
*   `app/main.py`

---

## 5. Sub-Phases

### Phase 4.1: API Schemas & Core Setup
*   **Goal**: Create validation models and setup core FastAPI application.
*   **Tasks**:
    1. Define Pydantic request/response schemas for query, ingestion, documents, and feedback.
    2. Setup FastAPI application scaffold inside `app/main.py` with CORS.
    3. Write custom timing and logging middleware in `app/core/middleware.py`.
*   **Files**:
    - `app/api/schemas/*.py`
    - `app/core/middleware.py`
    - `app/main.py` (scaffold)
*   **Acceptance Criteria**: Running uvicorn starts the server and parses Swagger details without schema conflicts.
*   **Verification**: Navigate to `http://localhost:8000/docs` in browser.

---

### Phase 4.2: Dependency Injection & Services
*   **Goal**: Setup resource factories and build intermediate business services.
*   **Tasks**:
    1. Write `app/dependencies.py` initializing database connections and LangGraph singletons.
    2. Write query broker service `app/services/query_service.py` coordinating the LangGraph executions.
    3. Write database repository `app/repositories/feedback_repository.py` storing user reviews.
    4. Write `app/services/feedback_service.py`.
*   **Files**:
    - `app/dependencies.py`
    - `app/services/query_service.py`
    - `app/repositories/feedback_repository.py`
    - `app/services/feedback_service.py`
*   **Acceptance Criteria**: Server startup executes resource allocations idempotently. Query and feedback services map dependencies correctly.
*   **Verification**: Write a short execution check testing uvicorn launches with initialized services.

---

### Phase 4.3: Query, Feedback & Diagnostics Routes
*   **Goal**: Implement the routing modules for execution queries, feedbacks, and health statuses.
*   **Tasks**:
    1. Write query router `app/api/routes/query.py` invoking query service.
    2. Write feedback router `app/api/routes/feedback.py` recording ratings.
    3. Write diagnostic router `app/api/routes/health.py` validating storage and LLM client connectivity.
*   **Files**:
    - `app/api/routes/query.py`
    - `app/api/routes/feedback.py`
    - `app/api/routes/health.py`
*   **Acceptance Criteria**: Submitting questions via query route executes the LangGraph pipeline. Health router verifies database health status.
*   **Verification**: Submit HTTP curl queries and assert response states.

---

### Phase 4.4: Ingestion & Catalog Routes
*   **Goal**: Implement the document ingestion routes (file/URL) and catalog listing.
*   **Tasks**:
    1. Write ingestion router `app/api/routes/ingest.py` supporting file uploads and remote URL scrapes.
    2. Write catalog router `app/api/routes/documents.py` for listing and deletion operations.
    3. Wire all routers into the main application.
*   **Files**:
    - `app/api/routes/ingest.py`
    - `app/api/routes/documents.py`
    - `app/main.py` (updated)
*   **Acceptance Criteria**: Files uploaded via multipart routes get ingested and indexed. Registry listings correctly update document count attributes.
*   **Verification**: Test PDF/MD uploads and delete files verifying DB states update.

---

## 6. AI Build Prompt (`AI_BUILD_PROMPT.md`)

```markdown
# AI Build Prompt: Phase 4 (API Layer)

## Goal
Expose the RAG pipeline and ingestion systems through a FastAPI REST API with validation schemas, service mapping dependencies, and structured exception handlers.

## Files to Create/Modify
- **app/api/schemas/common.py**: Standard error response model: `{"error": {"code": str, "message": str, "details": dict}, "request_id": str}`.
- **app/api/schemas/query.py**: QueryRequest, QueryResponse, SourceReference models.
- **app/api/schemas/ingest.py**: IngestRequest, IngestResponse models.
- **app/api/schemas/documents.py**: DocumentRecord, DocumentListResponse models.
- **app/api/schemas/feedback.py**: FeedbackRequest, FeedbackResponse models.
- **app/api/routes/health.py**: GET /health returning check status of databases and providers.
- **app/api/routes/query.py**: POST /query routing questions to query service.
- **app/api/routes/ingest.py**: POST /ingest handling file upload (multipart) or URL scraping.
- **app/api/routes/documents.py**: GET /documents (paginated) and DELETE /documents/{id} removing records.
- **app/api/routes/feedback.py**: POST /feedback recording thumbs up/down and comments to SQLite.
- **app/dependencies.py**: Startup resource initialization mapping database clients and graph compilers.
- **app/services/query_service.py**: Runs async execution tasks using compiled StateGraph.
- **app/repositories/feedback_repository.py**: Inserts records to SQLite feedback table.
- **app/services/feedback_service.py**: Stores rating metrics.
- **app/core/middleware.py**: Custom timing middleware logging execution times.
- **app/main.py**: Initializes FastAPI application mapping exception handlers and registering routers.

## Constraints
- File uploads must not exceed 10MB.
- Return structured error formatting on validation exceptions (Pydantic 422 errors).
- Cleanly release SQLite connections at endpoint completions.

## Acceptance Criteria
- Starting server via `uvicorn app.main:app` runs cleanly, and tests endpoints using Swagger `/docs`.
```

---

## 7. Verification Package

### Manual Verification
1. Start API server locally:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
2. Test health check endpoint:
   ```bash
   curl http://127.0.0.1:8000/health
   ```
3. Submit question query:
   ```bash
   curl -X POST http://127.0.0.1:8000/query -H "Content-Type: application/json" -d "{\"question\": \"How do I install FastAPI?\"}"
   ```

### Expected Results
*   Health endpoint returns `{"status": "healthy", ...}`.
*   Query request prints JSON answer displaying source documentation citations.

### Failure Conditions
*   Incorrect input models return generic 500 crashes instead of validated 422 JSON errors.
*   Deleted documents remain searchable inside ChromaDB.

---

## 8. Review Gates

- [ ] FastAPI Swagger UI validates clean schema models.
- [ ] Ingestion route blocks files larger than 10MB.
- [ ] Exception wrappers translate LLM timeouts to standard 503 errors.
- [ ] Feedback records update SQLite tables correctly.
- [ ] Timing middlewares trace requests successfully.
