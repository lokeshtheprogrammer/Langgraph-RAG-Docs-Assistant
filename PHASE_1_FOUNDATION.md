# PHASE_1_FOUNDATION.md — Phase 1: Project Foundation
## RAG-Based Technical Documentation Assistant

---

## 1. Phase Goal

*   **Business Goal**: Establish a robust, standard project layout and execution runtime that ensures clean separation of concerns, structured configuration loading, and error traceability.
*   **Technical Goal**: Scaffolding the python workspace directory, defining Pydantic settings loading, structured logging, custom domain exceptions, and SQLite database utility.
*   **Completion Criteria**: A developer can launch the workspace, load configuration properties, and execute a shell command to initialize SQL tables idempotently.

---

## 2. Scope

### Included
*   Folder structure layout according to `FOLDER_STRUCTURE.md`.
*   Virtual environment configuration files (`pyproject.toml`, `requirements.txt`, `requirements-dev.txt`).
*   Environment settings setup utilizing `pydantic-settings` (loading `.env`).
*   Structured logging configuration (JSON logs wrapper).
*   Custom system exceptions hierarchy (BaseException, LLMError, DBError, etc.).
*   SQLite connection utility and DDL schema initialization.

### Excluded
*   FastAPI endpoint routers.
*   LangGraph workflow compilation.
*   Vector database storage setup.
*   ChromaDB indexing or SentenceTransformer models loading.

---

## 3. Dependencies

*   Python 3.11 installed on the system.
*   Visual Studio Build Tools (for any local compilation requirements).

---

## 4. Deliverables

*   `requirements.txt`
*   `requirements-dev.txt`
*   `pyproject.toml`
*   `app/config.py`
*   `app/core/logging.py`
*   `app/core/exceptions.py`
*   `app/core/database.py`

---

## 5. Sub-Phases

### Phase 1.1: Dependency Scaffolding & Setup
*   **Goal**: Create environment configuration files and initialize standard directory folders.
*   **Tasks**:
    1. Create directory tree structure (`app/api/routes`, `app/api/schemas`, `app/workflow/nodes`, `app/infrastructure/vector_store`, `app/infrastructure/embeddings`, `app/infrastructure/llm`, `app/infrastructure/document_loader`, `app/repositories`, `app/core`, `app/utils`, `ingestion`, `corpus`, `tests/unit`, `tests/integration`, `tests/api`, `data`, `chroma_db`).
    2. Write `requirements.txt` listing all baseline packages.
    3. Write `requirements-dev.txt` listing development tools.
    4. Write `pyproject.toml` configuration for linters (Ruff/MyPy) and pytest settings.
*   **Files**:
    - `requirements.txt`
    - `requirements-dev.txt`
    - `pyproject.toml`
*   **Acceptance Criteria**: Running `pip install` works, directories are properly initialized, and config files match expectations.
*   **Verification**: Ensure python environment activates and dependencies resolve.

---

### Phase 1.2: Configuration & Logging
*   **Goal**: Load settings from environment variables and setup JSON logs.
*   **Tasks**:
    1. Implement `app/config.py` using `pydantic-settings`.
    2. Implement `app/core/logging.py` with custom formatting for structured logs.
    3. Write `.env.example` file.
*   **Files**:
    - `app/config.py`
    - `app/core/logging.py`
    - `.env.example`
*   **Acceptance Criteria**: Configurations can be loaded from `.env` or system environment, defaulting correctly, and logger outputs JSON lines.
*   **Verification**: Check settings outputs using a python test script.

---

### Phase 1.3: Custom Exceptions & SQLite Database Setup
*   **Goal**: Define error mappings and build SQLite connection factory to setup databases.
*   **Tasks**:
    1. Implement `app/core/exceptions.py` mapping domain errors.
    2. Implement `app/core/database.py` containing connection context and tables setup.
*   **Files**:
    - `app/core/exceptions.py`
    - `app/core/database.py`
*   **Acceptance Criteria**: Database initialization script executes idempotently, creating `documents` and `feedback` tables with indices.
*   **Verification**: Executing table creation script creates `./data/registry.db` and `./data/feedback.db`.

---

## 6. AI Build Prompt (`AI_BUILD_PROMPT.md`)

```markdown
# AI Build Prompt: Phase 1 (Foundation)

## Goal
Build the foundation infrastructure for the RAG-Based Technical Documentation Assistant. This includes directory layout, configurations, logging, exceptions, and SQLite storage initialization.

## Files to Create
1. **requirements.txt**: Pin dependencies:
   - fastapi>=0.111.0
   - uvicorn[standard]>=0.30.0
   - langgraph>=0.1.0
   - langchain>=0.2.0
   - langchain-community>=0.2.0
   - chromadb>=0.5.0
   - sentence-transformers>=3.0.0
   - pydantic>=2.7.0
   - pydantic-settings>=2.2.0
   - python-dotenv>=1.0.0
   - groq>=0.9.0
   - openai>=1.30.0
   - google-genai>=0.1.0
   - python-multipart>=0.0.9
   - aiofiles>=23.2.0
   - httpx>=0.27.0
2. **requirements-dev.txt**: pytest, pytest-asyncio, pytest-cov, ruff, black
3. **pyproject.toml**: Configure Ruff, Pytest (asyncio auto mode), MyPy
4. **app/config.py**: Class Settings inheriting from BaseSettings:
   - LLM_PROVIDER (str, default "google")
   - LLM_MODEL (str, default "gemini-2.5-flash")
   - GEMINI_API_KEY (Optional[str])
   - GROQ_API_KEY (Optional[str])
   - OPENAI_API_KEY (Optional[str])
   - EMBEDDING_MODEL (str, default "sentence-transformers/all-MiniLM-L6-v2")
   - CHROMA_PERSIST_DIR (str, default "./chroma_db")
   - TOP_K (int, default 5)
   - MAX_RETRIES (int, default 2)
   - CHUNK_SIZE (int, default 512)
   - CHUNK_OVERLAP (int, default 64)
5. **app/core/logging.py**: Configure structured JSON log output formatting to stdout.
6. **app/core/exceptions.py**: Class hierarchy for custom exceptions:
   - RAGException (Base)
   - LLMProviderError
   - VectorStoreError
   - DatabaseError
   - IngestionError
7. **app/core/database.py**: Connection factory for SQLite. Define schema tables:
   - documents: id (TEXT PK), filename (TEXT), source_url (TEXT), file_hash (TEXT), file_size_bytes (INTEGER), file_type (TEXT), chunk_count (INTEGER), status (TEXT), ingestion_timestamp (TEXT), embedding_model (TEXT), error_message (TEXT).
   - feedback: id (INTEGER PK), feedback_id (TEXT UNIQUE), query (TEXT), answer (TEXT), rating (TEXT), comment (TEXT), sources_used (TEXT), session_id (TEXT), query_type (TEXT), retry_count (INTEGER), response_time_ms (INTEGER), created_at (TEXT).
   Write an idempotent function `initialize_db()` that runs on module load/startup.

## Constraints
- Do not import any non-existent packages.
- Ensure type annotations are strictly followed.
- Use native sqlite3 module for simplicity and to avoid bloated ORM dependencies.

## Acceptance Criteria
- Run a simple script to verify database creation.
- Check that configuration settings parse standard `.env` properties.
```

---

## 7. Verification Package

### Manual Verification
1. Install all dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt -r requirements-dev.txt
   ```
2. Run database initialization check:
   ```bash
   python -c "from app.core.database import initialize_db; initialize_db(); print('DB Ready')"
   ```

### Expected Results
*   The script should execute cleanly, print "DB Ready".
*   `data/registry.db` and `data/feedback.db` (or a single `data/app.db` containing both tables) should be created successfully in the folder structure.

### Failure Conditions
*   SQLite script crashes with SQL syntax errors.
*   Config initialization fails because of missing environment variables (ensure optional values are handled correctly).

---

## 8. Review Gates

- [ ] All required files created successfully.
- [ ] Requirements pinned with exact or minimum versions.
- [ ] Idempotent DB initialization logic verified manually.
- [ ] No secrets stored directly in `app/config.py`.
- [ ] Log output formatting verified.
- [ ] Python linter commands (`ruff check .`) return no major issues.
