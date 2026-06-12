# IMPLEMENTATION_ROADMAP.md — Implementation Roadmap
## RAG-Based Technical Documentation Assistant

**Timeline:** 2 days (16 hours effective development time)
**Developer:** 1 intern-level engineer

---

## Effort Estimation Key

| Label | Estimate |
|-------|---------|
| XS | 15-30 minutes |
| S | 30-60 minutes |
| M | 1-2 hours |
| L | 2-4 hours |
| XL | 4+ hours |

---

## Phase 1: Foundation
**Day 1 | Morning Block (2 hours)**

### Objective
Set up project skeleton, configuration system, dependency management, and verify all external dependencies are accessible.

### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 1.1 | Initialize Git repository, create folder structure | XS | `mkdir` commands, `git init` |
| 1.2 | Create `pyproject.toml`, `requirements.txt` | XS | Pin all versions |
| 1.3 | Set up virtual environment, install dependencies | S | `pip install -r requirements.txt` |
| 1.4 | Create `app/config.py` with `pydantic-settings` | S | All env vars as typed fields |
| 1.5 | Create `.env.example` and `.env` | XS | Add LLM API key(s) |
| 1.6 | Verify LLM API access (test call) | XS | One `curl` or Python snippet |
| 1.7 | Create `app/core/logging.py` | XS | JSON structured logger |
| 1.8 | Create `app/core/exceptions.py` | XS | Custom exception classes |
| 1.9 | Create `app/main.py` scaffold (FastAPI app, no routes yet) | XS | `uvicorn app.main:app` works |
| 1.10 | Create `corpus/` directory with 3-5 docs | M | Download or copy from official sources |

### Deliverable
`uvicorn app.main:app --reload` starts without errors. LLM API key validated.

---

## Phase 2: Document Ingestion Pipeline
**Day 1 | Late Morning (2.5 hours)**

### Objective
Build the complete document loading → chunking → embedding → vector store pipeline.

### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 2.1 | Create `app/infrastructure/vector_store/base.py` (ABC) | XS | |
| 2.2 | Create `app/infrastructure/vector_store/chroma.py` | M | Persistent client, add/query/list |
| 2.3 | Create `app/infrastructure/embeddings/sentence_transformers.py` | S | embed_query + embed_documents |
| 2.4 | Create `app/infrastructure/document_loader/file_loader.py` | S | .md, .txt, .html via LangChain loaders |
| 2.5 | Create `app/infrastructure/document_loader/url_loader.py` | S | httpx fetch + BeautifulSoup parse |
| 2.6 | Create `app/utils/chunking.py` with RecursiveCharacterTextSplitter | S | chunk_size=512, overlap=64 |
| 2.7 | Create `app/repositories/document_repository.py` | S | SQLite CRUD |
| 2.8 | Create `app/services/ingestion_service.py` | M | Orchestrate 2.1-2.7 |
| 2.9 | Create `ingestion/ingest_corpus.py` CLI script | S | Run once to seed corpus |
| 2.10 | Run ingest script; verify chunks in ChromaDB | XS | ChromaDB `.count()` call |

### Deliverable
`python ingestion/ingest_corpus.py` successfully indexes all corpus documents. ChromaDB shows correct chunk counts.

---

## Phase 3: Vector Search
**Day 1 | Early Afternoon (1 hour)**

### Objective
Validate that semantic search over the ingested corpus returns relevant results.

### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 3.1 | Write smoke test: embed query → search → print top-5 results | S | Interactive Python script |
| 3.2 | Tune top_k value; verify result quality manually | S | 5 queries against known docs |
| 3.3 | Add metadata filtering support to ChromaVectorStore | S | Optional: filter by document_id |
| 3.4 | Write unit tests for vector store interface | S | Mock the ChromaDB client |

### Deliverable
Query "how do I install FastAPI?" returns relevant chunks from `fastapi_tutorial.md`.

---

## Phase 4: LangGraph Workflow
**Day 1 | Afternoon (3.5 hours)**

### Objective
Build and verify the complete LangGraph StateGraph with all required nodes, conditional routing, and retry logic.

### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 4.1 | Create `app/workflow/state.py` (RAGState TypedDict) | S | Include all fields from design |
| 4.2 | Create `app/workflow/prompts.py` (all prompt templates) | S | Query analysis, grading, generation, rewrite |
| 4.3 | Create `app/infrastructure/llm/base.py` + provider adapters | M | Groq first; OpenAI as fallback |
| 4.4 | Implement `nodes/query_analysis.py` | S | JSON output parsing with fallback |
| 4.5 | Implement `nodes/retrieval.py` | XS | Calls vector store |
| 4.6 | Implement `nodes/document_grading.py` | M | Per-chunk LLM call + JSON parse |
| 4.7 | Implement `nodes/generation.py` | M | Context assembly, citation prompt |
| 4.8 | Implement `nodes/query_rewrite.py` | S | Plain text output |
| 4.9 | Create `app/workflow/routing.py` with `route_after_grading` | S | Pure function, test edge cases |
| 4.10 | Create `app/workflow/graph.py` with `build_rag_graph()` | M | Wire all nodes + edges |
| 4.11 | Smoke test: run graph end-to-end in Python REPL | S | One real query against real corpus |
| 4.12 | Verify retry loop terminates correctly | XS | Ask a question not in corpus |

### Deliverable
`graph.invoke({"question": "How do I use FastAPI routing?"})` returns a correct answer with citations. A question not in corpus triggers retry + fallback.

---

## Phase 5: API Layer
**Day 2 | Morning (2.5 hours)**

### Objective
Expose the LangGraph workflow and ingestion pipeline through a clean FastAPI REST API.

### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 5.1 | Create `app/api/schemas/` (all request/response models) | M | QueryRequest, IngestResponse, etc. |
| 5.2 | Create `app/dependencies.py` (service DI setup) | S | Startup initialization |
| 5.3 | Create `app/services/query_service.py` | S | Invoke graph, format response |
| 5.4 | Create `app/services/feedback_service.py` | S | SQLite insert |
| 5.5 | Implement `app/api/routes/query.py` | S | POST /query |
| 5.6 | Implement `app/api/routes/ingest.py` | M | POST /ingest (file + URL) |
| 5.7 | Implement `app/api/routes/documents.py` | S | GET /documents, DELETE /documents/{id} |
| 5.8 | Implement `app/api/routes/feedback.py` | S | POST /feedback |
| 5.9 | Implement `app/api/routes/health.py` | S | GET /health |
| 5.10 | Add exception handlers in `app/main.py` | S | 422, 503, 500 |
| 5.11 | Wire all routers in `app/main.py` | XS | |
| 5.12 | Manual API testing (Postman or curl) | M | All endpoints, happy + error paths |

### Deliverable
All 5 endpoints work correctly via `curl`. OpenAPI docs at `/docs` are complete and accurate.

---

## Phase 6: Testing
**Day 2 | Mid-Morning (2 hours)**

### Objective
Build a meaningful test suite covering routing logic, API endpoints, and ingestion pipeline.

### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 6.1 | Create `tests/conftest.py` with shared fixtures | M | Mock LLM, in-memory ChromaDB |
| 6.2 | Write `tests/unit/test_routing.py` | S | All branches of route_after_grading |
| 6.3 | Write `tests/unit/test_grading_parser.py` | S | Valid JSON, malformed JSON, missing field |
| 6.4 | Write `tests/unit/test_chunking.py` | S | Chunk size, overlap, edge cases |
| 6.5 | Write `tests/api/test_query_endpoint.py` | M | Success, fallback, validation errors |
| 6.6 | Write `tests/api/test_ingest_endpoint.py` | M | File upload, URL, bad extension, duplicate |
| 6.7 | Write `tests/api/test_documents_endpoint.py` | S | List, delete, not found |
| 6.8 | Run full test suite; fix failures | M | `pytest tests/` |
| 6.9 | Check test coverage | XS | `pytest --cov=app` |

### Deliverable
`pytest tests/unit/ tests/api/` passes with ≥ 80% coverage on core modules.

---

## Phase 7: Deployment Preparation
**Day 2 | Early Afternoon (1.5 hours)**

### Objective
Ensure the system is runnable by a fresh reviewer from just the README instructions.

### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 7.1 | Create `Dockerfile` | S | Python 3.11-slim base |
| 7.2 | Create `docker-compose.yml` | S | App service + volume mount |
| 7.3 | Test Docker build and run | S | `docker compose up` |
| 7.4 | Set up `.github/workflows/ci.yml` | S | ruff lint + pytest on push |
| 7.5 | Create `README.md` (complete, see Phase 8) | Handled in Phase 8 | |
| 7.6 | Create `scripts/setup_env.sh` | XS | One-command setup |
| 7.7 | Test fresh setup from scratch (delete venv, follow README) | S | Validate reviewer experience |

### Deliverable
A reviewer can clone the repo and run the API in under 5 minutes following the README.

---

## Phase 8: Documentation & README
**Day 2 | Afternoon (1.5 hours)**

### Objective
Write documentation that demonstrates deep understanding of the architecture and tradeoffs.

### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 8.1 | Write `README.md` (see README.md deliverable) | L | World-class quality |
| 8.2 | Verify corpus README explains document choice | S | |
| 8.3 | Update `app/workflow/` with docstrings on every function | S | |
| 8.4 | Write design decisions section in README | S | Chunking, LLM choice, vector store |
| 8.5 | Add example requests/responses to README | S | Copy from API testing |

---

## Phase 9: Bonus Features (If Time Permits)
**Day 2 | Late Afternoon**

Attempt in this order based on remaining time:

| # | Feature | Effort | Value |
|---|---------|--------|-------|
| B1 | Hallucination check node | M | High — directly mentioned in assignment |
| B2 | Streamlit UI | M | High — makes demo very easy for reviewer |
| B3 | Web search fallback (Tavily) | M | Medium — requires additional API key |
| B4 | Conversation memory (session store) | L | Medium — complex state management |

---

## Critical Path

The following tasks must complete in order. Delays here delay everything:

```
1.3 (install deps) 
  → 1.6 (verify LLM access) 
    → 2.2 (ChromaDB) 
      → 2.9 (ingest corpus) 
        → 4.6 (document grading node) 
          → 4.10 (compile graph) 
            → 5.5 (POST /query endpoint) 
              → 7.7 (verify reviewer experience)
```

---

## Risk Mitigation Schedule

| Risk | When | Mitigation |
|------|------|-----------|
| LLM API key doesn't work | End of Phase 1 | Switch provider; Groq has instant signup |
| ChromaDB persistence issues | End of Phase 2 | Fall back to in-memory mode for testing |
| LangGraph retry loop doesn't terminate | During Phase 4 | Add hard `assert retry_count < 10` check |
| API validation fails | During Phase 5 | Simplify schemas; document the gaps |
| Not enough time for tests | End of Phase 6 | Prioritize routing unit tests + query API test |
