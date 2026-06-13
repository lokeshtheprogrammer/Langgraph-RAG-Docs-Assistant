# Express Analytics AI/ML Engineer Intern Assignment - Requirements Mapping

This document maps all the requirements of the Express Analytics AI/ML Engineer Intern Take-Home Assignment to the corresponding source files in this repository.

---

## 1. LangGraph Workflow

| Requirement | Implemented In | Status | Notes |
|---|---|---|---|
| **Query Analysis Node** | [query_analysis.py](file:///c:/Users/aimpr/Downloads/RAG/app/workflow/nodes/query_analysis.py) | **Completed** | Classifies query intent (conceptual, coding, conversational) and extracts key terms. |
| **Retrieval Node** | [retrieval.py](file:///c:/Users/aimpr/Downloads/RAG/app/workflow/nodes/retrieval.py) | **Completed** | Handles hybrid search (BM25 + Vector), file scoping filters, and calls the Cross-Encoder reranker. |
| **Document Grading Node** | [document_grading.py](file:///c:/Users/aimpr/Downloads/RAG/app/workflow/nodes/document_grading.py) | **Completed** | Evaluates document relevance to the query, filtering out irrelevant chunks. |
| **Query Rewrite Node** | [query_rewrite.py](file:///c:/Users/aimpr/Downloads/RAG/app/workflow/nodes/query_rewrite.py) | **Completed** | Reformulates query to improve search precision if document grading fails. |
| **Generation Node** | [generation.py](file:///c:/Users/aimpr/Downloads/RAG/app/workflow/nodes/generation.py) | **Completed** | Synthesizes final grounded answer using LLM context with expanded sources. |
| **Conditional Routing Logic** | [routing.py](file:///c:/Users/aimpr/Downloads/RAG/app/workflow/routing.py) <br/> [graph.py](file:///c:/Users/aimpr/Downloads/RAG/app/workflow/graph.py) | **Completed** | Defines the workflow edges, retry counts, fallback state machines, and compiles the LangGraph StateGraph. |

---

## 2. Document Ingestion Pipeline

| Requirement | Implemented In | Status | Notes |
|---|---|---|---|
| **Document Loading** | [file_loader.py](file:///c:/Users/aimpr/Downloads/RAG/app/infrastructure/document_loader/file_loader.py) <br/> [url_loader.py](file:///c:/Users/aimpr/Downloads/RAG/app/infrastructure/document_loader/url_loader.py) | **Completed** | Loads local Markdown (`.md`), PDF (`.pdf`), Text (`.txt`), and HTML (`.html`) files and URLs. |
| **Chunking Strategy** | [chunking.py](file:///c:/Users/aimpr/Downloads/RAG/app/utils/chunking.py) | **Completed** | Implements structural **Markdown Header-Aware Chunks** with parent section prefix tracking. |
| **Embedding Generation** | [sentence_transformers.py](file:///c:/Users/aimpr/Downloads/RAG/app/infrastructure/embeddings/sentence_transformers.py) | **Completed** | Offline-capable local embeddings utilizing `sentence-transformers/all-MiniLM-L6-v2`. |
| **ChromaDB Storage** | [chroma.py](file:///c:/Users/aimpr/Downloads/RAG/app/infrastructure/vector_store/chroma.py) <br/> [hybrid_store.py](file:///c:/Users/aimpr/Downloads/RAG/app/infrastructure/vector_store/hybrid_store.py) | **Completed** | Stores document vectors in persistent ChromaDB storage with active document scopes and RRF hybrid indexing. |

---

## 3. FastAPI Endpoints

| Endpoint | Implemented In | Status | Description |
|---|---|---|---|
| `POST /query` | [query.py](file:///c:/Users/aimpr/Downloads/RAG/app/api/routes/query.py) | **Completed** | Evaluates user questions, runs the LangGraph RAG workflow, updates memory, and logs metrics. |
| `POST /ingest` | [ingest.py](file:///c:/Users/aimpr/Downloads/RAG/app/api/routes/ingest.py) | **Completed** | Uploads, chunks, embeds, and indexes document files or URLs with SHA-256 duplicate checking. |
| `GET /documents` | [documents.py](file:///c:/Users/aimpr/Downloads/RAG/app/api/routes/documents.py) | **Completed** | Lists all indexed files, chunk counts, and registration details from SQLite. |
| `DELETE /documents/{id}` | [documents.py](file:///c:/Users/aimpr/Downloads/RAG/app/api/routes/documents.py) | **Completed** | Deletes document metadata from SQLite and removes associated chunks from ChromaDB. |
| `POST /feedback` | [feedback.py](file:///c:/Users/aimpr/Downloads/RAG/app/api/routes/feedback.py) | **Completed** | Logs positive/negative user feedback, queries, and answers to SQLite database. |
| `GET /health` | [health.py](file:///c:/Users/aimpr/Downloads/RAG/app/api/routes/health.py) | **Completed** | Checks availability of database connections and ChromaDB collection status. |
| `GET /metrics` | [metrics.py](file:///c:/Users/aimpr/Downloads/RAG/app/api/routes/metrics.py) | **Completed** | Exposes system-wide usage counts, average latencies, and positive/negative feedback ratio. |

---

## 4. Bonus Features

| Requirement | Implemented In | Status | Notes |
|---|---|---|---|
| **Hallucination Check** | [hallucination_check.py](file:///c:/Users/aimpr/Downloads/RAG/app/workflow/nodes/hallucination_check.py) | **Completed** | Grade grounding using LLM evaluation; rejects response and regenerates if grounding fails. |
| **Web Search Fallback** | [web_search.py](file:///c:/Users/aimpr/Downloads/RAG/app/workflow/nodes/web_search.py) <br/> [duckduckgo.py](file:///c:/Users/aimpr/Downloads/RAG/app/infrastructure/web_search/duckduckgo.py) | **Completed** | Automatically searches the web via DuckDuckGo (or Tavily) and creates temporary chunks if DB has zero relevant facts. |
| **Conversation Memory** | [chat_history.py](file:///c:/Users/aimpr/Downloads/RAG/app/repositories/chat_history.py) <br/> [query_service.py](file:///c:/Users/aimpr/Downloads/RAG/app/services/query_service.py) | **Completed** | SQLite conversation turns logger. Context is injected into subsequent user queries dynamically. |
| **Streamlit UI** | [streamlit_app.py](file:///c:/Users/aimpr/Downloads/RAG/streamlit_app.py) | **Completed** | Dark-mode interface, drag-and-drop file uploaders, live DB metrics, interactive citation expanders, and debug panel. |
| **Advanced: Hybrid Search** | [hybrid_store.py](file:///c:/Users/aimpr/Downloads/RAG/app/infrastructure/vector_store/hybrid_store.py) | **Completed** | Implements BM25 keyword + HNSW Vector search using Reciprocal Rank Fusion (RRF). |
| **Advanced: Re-Ranker** | [cross_encoder.py](file:///c:/Users/aimpr/Downloads/RAG/app/infrastructure/reranker/cross_encoder.py) | **Completed** | Reranks candidate document chunks using the `ms-marco-MiniLM-L-6-v2` cross-encoder model. |

---

## 5. Deliverables

| Deliverable | Location | Status | Description |
|---|---|---|---|
| **Source Code** | `/app` | **Completed** | Clean modular architecture adhering to SOLID design principles and separation of concerns. |
| **README** | [README.md](file:///c:/Users/aimpr/Downloads/RAG/README.md) | **Completed** | Comprehensive documentation detailing overview, setup, Mermaid diagram, APIs, and design rationale. |
| **Working FastAPI App** | `/app/main.py` | **Completed** | High-performance FastAPI server with clean logging and OpenAPI specification. |
| **Corpus** | `/corpus` | **Completed** | Pre-packaged folder containing complete reference files for FastAPI, Streamlit, ChromaDB, LangGraph, and Pydantic. |
| **Architecture Write-up** | `walkthrough.md` <br/> `SYSTEM_DESIGN.md` | **Completed** | Comprehensive architecture specifications detailing routing states, data contracts, and design rationale. |
