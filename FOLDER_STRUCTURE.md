# FOLDER_STRUCTURE.md — Project Folder Structure
## RAG-Based Technical Documentation Assistant

**Version:** 1.0.0

---

## Complete Structure

```
rag-documentation-assistant/
│
├── app/                                # Main application package
│   ├── __init__.py
│   ├── main.py                         # FastAPI app creation, startup/shutdown hooks
│   ├── config.py                       # Pydantic Settings — all environment variables
│   ├── dependencies.py                 # FastAPI Depends() factories; service singletons
│   │
│   ├── api/                            # API presentation layer
│   │   ├── __init__.py
│   │   ├── routes/                     # One file per logical resource group
│   │   │   ├── __init__.py
│   │   │   ├── query.py                # POST /query
│   │   │   ├── ingest.py               # POST /ingest
│   │   │   ├── documents.py            # GET /documents, DELETE /documents/{id}
│   │   │   ├── feedback.py             # POST /feedback, GET /feedback
│   │   │   └── health.py               # GET /health
│   │   └── schemas/                    # Pydantic request/response models
│   │       ├── __init__.py
│   │       ├── query.py                # QueryRequest, QueryResponse, SourceReference
│   │       ├── ingest.py               # IngestRequest, IngestResponse
│   │       ├── documents.py            # DocumentRecord, DocumentListResponse
│   │       ├── feedback.py             # FeedbackRequest, FeedbackResponse
│   │       └── common.py               # ErrorResponse, PaginationParams
│   │
│   ├── workflow/                       # LangGraph domain layer
│   │   ├── __init__.py
│   │   ├── graph.py                    # build_rag_graph() — compiles the StateGraph
│   │   ├── state.py                    # RAGState TypedDict + all state models
│   │   ├── routing.py                  # Conditional edge functions
│   │   ├── prompts.py                  # All prompt templates as constants
│   │   └── nodes/                      # One file per node
│   │       ├── __init__.py
│   │       ├── query_analysis.py       # Node 1: Rewrite + classify query
│   │       ├── retrieval.py            # Node 2: Vector similarity search
│   │       ├── document_grading.py     # Node 3: LLM relevance grading
│   │       ├── generation.py           # Node 4: Grounded answer generation
│   │       ├── query_rewrite.py        # Retry node: generate new query
│   │       └── hallucination_check.py  # Bonus: Self-RAG verification
│   │
│   ├── services/                       # Business logic / use-case layer
│   │   ├── __init__.py
│   │   ├── query_service.py            # Orchestrates workflow invocation
│   │   ├── ingestion_service.py        # Orchestrates doc load → chunk → embed → store
│   │   └── feedback_service.py         # Feedback persistence
│   │
│   ├── infrastructure/                 # External system adapters
│   │   ├── __init__.py
│   │   ├── vector_store/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # VectorStoreBase ABC
│   │   │   ├── chroma.py               # ChromaVectorStore implementation
│   │   │   └── faiss.py                # FAISSVectorStore implementation (alternative)
│   │   ├── embeddings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # EmbeddingModelBase ABC
│   │   │   ├── sentence_transformers.py # Local SentenceTransformer adapter
│   │   │   └── openai.py               # OpenAI embedding adapter
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # LLMClientBase ABC
│   │   │   ├── groq.py                 # Groq adapter
│   │   │   ├── openai.py               # OpenAI adapter
│   │   │   ├── anthropic.py            # Anthropic adapter
│   │   │   └── google.py               # Google Gemini adapter
│   │   └── document_loader/
│   │       ├── __init__.py
│   │       ├── base.py                 # DocumentLoaderBase ABC
│   │       ├── file_loader.py          # Load from .md, .txt, .html, .pdf
│   │       └── url_loader.py           # Fetch and parse from URL
│   │
│   ├── repositories/                   # Data access layer for SQLite stores
│   │   ├── __init__.py
│   │   ├── document_repository.py      # CRUD for documents table
│   │   └── feedback_repository.py      # CRUD for feedback table
│   │
│   ├── core/                           # Cross-cutting concerns
│   │   ├── __init__.py
│   │   ├── logging.py                  # JSON logger setup
│   │   ├── exceptions.py               # Custom exception classes
│   │   ├── middleware.py               # Request ID, timing middleware
│   │   └── database.py                 # SQLite connection factory
│   │
│   └── utils/                          # Pure utility functions
│       ├── __init__.py
│       ├── text.py                     # Text cleaning, truncation helpers
│       ├── hashing.py                  # SHA256 file hash
│       └── chunking.py                 # Text splitting helpers
│
├── ingestion/                          # Standalone ingestion scripts
│   ├── __init__.py
│   ├── ingest_corpus.py                # CLI: ingest all docs in ./corpus/
│   └── fetch_urls.py                   # Fetch docs from URLs defined in corpus_urls.txt
│
├── corpus/                             # Document corpus (source documents)
│   ├── langchain_tools.md              # LangChain tools documentation
│   ├── fastapi_tutorial.md             # FastAPI getting started guide
│   ├── pydantic_v2.md                  # Pydantic v2 docs
│   ├── langgraph_concepts.md           # LangGraph concepts docs
│   └── README.md                       # Explains what each doc is and why chosen
│
├── tests/                              # All tests
│   ├── __init__.py
│   ├── conftest.py                     # Shared fixtures (mock LLM, mock vector store)
│   ├── unit/                           # Pure unit tests (no I/O)
│   │   ├── __init__.py
│   │   ├── test_routing.py             # route_after_grading logic
│   │   ├── test_state.py               # State schema validation
│   │   ├── test_chunking.py            # Chunking strategy
│   │   ├── test_grading_parser.py      # JSON grading response parsing
│   │   └── test_prompts.py             # Prompt template rendering
│   ├── integration/                    # Tests requiring real ChromaDB
│   │   ├── __init__.py
│   │   ├── test_ingestion.py           # Full ingest pipeline
│   │   ├── test_retrieval.py           # Embed → store → retrieve
│   │   └── test_workflow.py            # Full LangGraph workflow (mocked LLM)
│   ├── api/                            # FastAPI TestClient tests
│   │   ├── __init__.py
│   │   ├── test_query_endpoint.py
│   │   ├── test_ingest_endpoint.py
│   │   ├── test_documents_endpoint.py
│   │   └── test_feedback_endpoint.py
│   └── rag_eval/                       # RAG quality evaluation
│       ├── __init__.py
│       ├── eval_dataset.json           # Q&A pairs with expected sources
│       └── run_ragas_eval.py           # RAGAS evaluation runner
│
├── data/                               # Runtime data (gitignored)
│   ├── .gitkeep
│   ├── registry.db                     # SQLite document registry
│   └── feedback.db                     # SQLite feedback store
│
├── chroma_db/                          # ChromaDB persistent storage (gitignored)
│   └── .gitkeep
│
├── scripts/                            # Development / ops scripts
│   ├── setup_env.sh                    # Create venv, install deps
│   ├── reset_db.sh                     # Clear vector store and SQLite
│   └── run_eval.sh                     # Run RAGAS evaluation
│
├── docs/                               # Project documentation (this package)
│   ├── PROJECT_PRD.md
│   ├── SYSTEM_DESIGN.md
│   ├── TECHNICAL_ARCHITECTURE.md
│   ├── LANGGRAPH_DESIGN.md
│   ├── AI_ENGINEERING.md
│   ├── DATABASE_DESIGN.md
│   ├── API_SPECIFICATION.md
│   ├── FOLDER_STRUCTURE.md
│   ├── IMPLEMENTATION_ROADMAP.md
│   ├── TESTING_STRATEGY.md
│   ├── SECURITY.md
│   ├── DEPLOYMENT.md
│   ├── REVIEWER_EXPECTATIONS.md
│   └── ARCHITECTURE_DECISIONS.md
│
├── .github/
│   └── workflows/
│       ├── ci.yml                      # GitHub Actions: lint + test on push
│       └── deploy.yml                  # GitHub Actions: deploy to Render on merge to main
│
├── .env.example                        # Template .env with all required variables
├── .env                                # Actual secrets (gitignored)
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt                    # Production dependencies
├── requirements-dev.txt                # Dev dependencies (pytest, ruff, etc.)
├── pyproject.toml                      # Project metadata, tool config (ruff, pytest)
└── README.md                           # World-class project README
```

---

## File-by-File Explanation

### Root Level

| File | Purpose |
|------|---------|
| `README.md` | Primary entry point for any reviewer. Overview, setup, examples. |
| `Dockerfile` | Container build instructions |
| `docker-compose.yml` | Local multi-container orchestration (app + optional UI) |
| `requirements.txt` | Pinned production dependencies |
| `requirements-dev.txt` | Dev tools: pytest, ruff, black, pre-commit |
| `pyproject.toml` | Project metadata, ruff config, pytest config, mypy config |
| `.env.example` | Committed template showing all env vars without values |
| `.env` | Actual secrets — **never committed** |
| `.gitignore` | Excludes: `.env`, `chroma_db/`, `data/*.db`, `__pycache__/`, `.venv/` |

### `app/` — Application Code

| Path | Purpose |
|------|---------|
| `app/main.py` | FastAPI `app` instance. Startup/shutdown handlers. Router registration. |
| `app/config.py` | `Settings` class (Pydantic BaseSettings). Single source for all config values. |
| `app/dependencies.py` | FastAPI dependency injection. Service singletons initialized at startup. |
| `app/api/routes/` | One router per API resource. Thin route handlers — no business logic. |
| `app/api/schemas/` | Pydantic models for request/response validation. |
| `app/workflow/graph.py` | `build_rag_graph()` — the factory that returns a compiled LangGraph. |
| `app/workflow/state.py` | `RAGState` TypedDict — the data contract between all nodes. |
| `app/workflow/routing.py` | Pure functions for conditional edge routing logic. |
| `app/workflow/prompts.py` | All prompt templates as module-level string constants. |
| `app/workflow/nodes/` | One file per LangGraph node. Each exports a factory function. |
| `app/services/` | Use-case orchestration. Services call infrastructure, not each other. |
| `app/infrastructure/` | Adapters for external systems (ChromaDB, LLM APIs, embeddings). |
| `app/repositories/` | SQLite data access objects. SQL queries centralized here. |
| `app/core/logging.py` | Structured JSON logging setup. Used throughout the app. |
| `app/core/exceptions.py` | Custom exception classes: `LLMError`, `VectorStoreError`, etc. |
| `app/core/middleware.py` | Request ID injection, timing middleware. |
| `app/utils/` | Pure functions with no side effects. No imports from `app/services/`. |

### `corpus/` — Document Corpus

| File | Contents |
|------|---------|
| `langchain_tools.md` | LangChain tools and toolkits documentation |
| `fastapi_tutorial.md` | FastAPI getting started and routing guide |
| `pydantic_v2.md` | Pydantic v2 models and validation docs |
| `langgraph_concepts.md` | LangGraph StateGraph and node concepts |
| `README.md` | Why these documents were chosen; how to add more |

### `tests/`

| Directory | Purpose |
|-----------|---------|
| `tests/unit/` | Fast, no I/O, mock everything external |
| `tests/integration/` | Require real ChromaDB; use temp directories |
| `tests/api/` | FastAPI TestClient; mock LLM and vector store |
| `tests/rag_eval/` | RAGAS-based quality evaluation; requires live LLM |
| `tests/conftest.py` | Shared pytest fixtures: mock LLM, in-memory ChromaDB, test client |

### `data/` and `chroma_db/`

Both directories are gitignored (contain runtime state). `.gitkeep` files ensure the directories exist in the repository so the application can write to them without errors.

---

## `.gitignore` Contents

```gitignore
# Environment
.env
.env.*
!.env.example

# Runtime data
data/*.db
chroma_db/
*.sqlite3

# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Test artifacts
.pytest_cache/
.coverage
htmlcov/
```

---

## `pyproject.toml` Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
filterwarnings = ["ignore::DeprecationWarning"]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true
strict = false
```
