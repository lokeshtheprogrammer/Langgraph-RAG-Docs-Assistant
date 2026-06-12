# PHASE_2_INGESTION.md — Phase 2: Document Ingestion Pipeline
## RAG-Based Technical Documentation Assistant

---

## 1. Phase Goal

*   **Business Goal**: Process and store technical source documents so they are available for vector search queries.
*   **Technical Goal**: Create loader utilities for local files and URLs, construct a recursive character text splitter, build local sentence-transformer and ChromaDB vector store wrappers, and implement a CLI seed script.
*   **Completion Criteria**: Running the ingestion script loads all test markdown documents inside the corpus directory, generates embeddings, stores them inside ChromaDB, and registers them in SQLite database.

---

## 2. Scope

### Included
*   Abstract interfaces for loaders, embeddings, and vector stores.
*   Local Markdown/PDF/TXT loader and remote URL fetch loader.
*   Recursive splitting utility ensuring code-block integrity.
*   Embedding model adapter loading `sentence-transformers/all-MiniLM-L6-v2` locally.
*   ChromaDB vector store adapter configured for persistent database operations.
*   Document registration repository (`app/repositories/document_repository.py`).
*   Ingestion manager service orchestrating the process.
*   Seed script `ingestion/ingest_corpus.py`.
*   Standard markdown corpus documents (`fastapi_tutorial.md`, `pydantic_v2.md`, `langgraph_concepts.md`, `langchain_tools.md`).

### Excluded
*   LangGraph nodes and StateGraph assembly.
*   FastAPI endpoints.
*   Feedback storage interactions.

---

## 3. Dependencies

*   Phase 1 completed successfully.
*   Database tables initialized.

---

## 4. Deliverables

*   `app/infrastructure/vector_store/base.py`
*   `app/infrastructure/vector_store/chroma.py`
*   `app/infrastructure/embeddings/base.py`
*   `app/infrastructure/embeddings/sentence_transformers.py`
*   `app/infrastructure/document_loader/base.py`
*   `app/infrastructure/document_loader/file_loader.py`
*   `app/infrastructure/document_loader/url_loader.py`
*   `app/repositories/document_repository.py`
*   `app/services/ingestion_service.py`
*   `app/utils/chunking.py`
*   `app/utils/hashing.py`
*   `ingestion/ingest_corpus.py`
*   `corpus/` (containing target markdown files)

---

## 5. Sub-Phases

### Phase 2.1: Infrastructure Adapters (Embeddings & Vector Store)
*   **Goal**: Create wrappers around local sentence transformers and ChromaDB.
*   **Tasks**:
    1. Define base interfaces for embedding model and vector store.
    2. Write sentence-transformer implementation loading the model locally.
    3. Write ChromaDB vector store adapter. Configure PersistentClient with similarity metric `cosine`.
*   **Files**:
    - `app/infrastructure/embeddings/base.py`
    - `app/infrastructure/embeddings/sentence_transformers.py`
    - `app/infrastructure/vector_store/base.py`
    - `app/infrastructure/vector_store/chroma.py`
*   **Acceptance Criteria**: Running a simple python script instantiates the embedding model and performs local cosine similarity searches using ChromaDB.
*   **Verification**: Embed a single text string and verify the resulting vector dimension is 384.

---

### Phase 2.2: Document Loaders & Splitters
*   **Goal**: Extract raw text from files or URLs and partition them into semantically consistent chunks.
*   **Tasks**:
    1. Define base interface for document loaders.
    2. Write local file loader that parses `.md`, `.txt`, `.html`, `.pdf`.
    3. Write remote URL loader that fetches and parses web content.
    4. Write `app/utils/chunking.py` utilizing `RecursiveCharacterTextSplitter` with separators prioritizing code fences and paragraph boundaries.
    5. Write `app/utils/hashing.py` computing SHA256 checksums to detect duplicate uploads.
*   **Files**:
    - `app/infrastructure/document_loader/base.py`
    - `app/infrastructure/document_loader/file_loader.py`
    - `app/infrastructure/document_loader/url_loader.py`
    - `app/utils/chunking.py`
    - `app/utils/hashing.py`
*   **Acceptance Criteria**: Text chunks respect boundary constraints and do not break code formatting blocks. Duplicate files are identified by their SHA256 hashes.
*   **Verification**: Parse a test file and assert the chunk size and counts match criteria.

---

### Phase 2.3: Ingestion Service & CLI Runner
*   **Goal**: Coordinate loading, chunking, embedding, database storage, and registry transactions.
*   **Tasks**:
    1. Write document database repository (`app/repositories/document_repository.py`).
    2. Write orchestration manager service (`app/services/ingestion_service.py`) tracking task states.
    3. Write corpus runner CLI `ingestion/ingest_corpus.py` loading target documents.
*   **Files**:
    - `app/repositories/document_repository.py`
    - `app/services/ingestion_service.py`
    - `ingestion/ingest_corpus.py`
*   **Acceptance Criteria**: CLI execution indexes all markdown docs in the corpus directory, inserts meta records in SQLite, and writes chunks to ChromaDB.
*   **Verification**: Run CLI pipeline and run verification assertions.

---

## 6. AI Build Prompt (`AI_BUILD_PROMPT.md`)

```markdown
# AI Build Prompt: Phase 2 (Ingestion)

## Goal
Implement the document ingestion pipeline. This includes loading, chunking, embedding, vector store storage, duplicate checking, and catalog registry.

## Files to Create/Modify
- **app/infrastructure/embeddings/base.py**: Abstract class EmbeddingModelBase.
- **app/infrastructure/embeddings/sentence_transformers.py**: Implements EmbeddingModelBase using local `sentence-transformers/all-MiniLM-L6-v2`.
- **app/infrastructure/vector_store/base.py**: Abstract class VectorStoreBase.
- **app/infrastructure/vector_store/chroma.py**: Implements VectorStoreBase using `chromadb.PersistentClient`.
- **app/infrastructure/document_loader/base.py**: Abstract class DocumentLoaderBase.
- **app/infrastructure/document_loader/file_loader.py**: File loader supporting `.md`, `.txt`, `.html` (and optionally simple `.pdf` parsing).
- **app/infrastructure/document_loader/url_loader.py**: URL loader fetching HTML content using `httpx` and stripping tags using `BeautifulSoup` (or regex).
- **app/utils/chunking.py**: Function `split_text(text: str, chunk_size: int, overlap: int) -> List[str]` wrapping `RecursiveCharacterTextSplitter`.
- **app/utils/hashing.py**: Hash helper: `calculate_sha256(content: bytes) -> str`.
- **app/repositories/document_repository.py**: Database operations on `documents` table: `insert_document()`, `get_document_by_hash()`, `list_documents()`, `delete_document()`.
- **app/services/ingestion_service.py**: Ingestion manager coordinating document loaders, splitting, hashing, embedding generations, ChromaDB inserts, and SQLite registrations. Handles duplicate checks.
- **ingestion/ingest_corpus.py**: Python CLI script that loops through the files in `corpus/` and invokes IngestionService to seed the vector store.

## Constraints
- Ensure ChromaDB persistently writes to config property `CHROMA_PERSIST_DIR`.
- Embedding models must load locally without making online network calls during queries.
- Recursive character text splitter should use separators `["\n\n", "\n", "```", ".", " ", ""]` to keep code blocks intact.

## Acceptance Criteria
- Run a verification script verifying indexed files count in SQLite database and vectors count in ChromaDB matches.
```

---

## 7. Verification Package

### Manual Verification
1. Setup seed corpus files in `corpus/` folder.
2. Run ingestion command:
   ```bash
   python ingestion/ingest_corpus.py
   ```
3. Run verification check query:
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('data/registry.db'); print(conn.cursor().execute('SELECT filename, chunk_count, status FROM documents').fetchall())"
   ```

### Expected Results
*   The ingest runner prints indexing status for all documents.
*   The check query output displays a list containing filenames, their respective chunk counts, and `indexed` status.
*   ChromaDB directory `./chroma_db` is created containing index assets.

### Failure Conditions
*   ChromaDB query fails with database mismatch errors.
*   Duplicate files are ingested twice instead of being skipped.

---

## 8. Review Gates

- [ ] local sentence-transformer models load without network errors.
- [ ] Document hash deduplication handles uploads correctly.
- [ ] Markdown files parsed and chunk size remains within limits.
- [ ] SQLite registry records track files states.
- [ ] Clean log records printed during chunking and vector storage.
