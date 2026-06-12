# PROJECT_PRD.md — Product Requirements Document
## RAG-Based Technical Documentation Assistant

**Version:** 1.0.0
**Date:** 2025-06-11
**Owner:** AI/ML Engineering Team
**Status:** Approved for Development

---

## Executive Summary

This document defines the product requirements for a Retrieval-Augmented Generation (RAG) system that enables users to query a corpus of technical documentation and receive accurate, cited, grounded answers. The system employs a self-corrective LangGraph workflow, a FastAPI backend, and a vector-store-based retrieval engine. It is designed as an intern take-home assignment for Express Analytics, demonstrating competence in AI pipeline design, LangGraph orchestration, and production API development.

---

## Business Problem

Technical documentation is voluminous, fragmented, and difficult to navigate. Engineers, developers, and data scientists spend significant time searching through docs, README files, and API references to find answers. Static keyword search is insufficient — users need semantic, context-aware answers grounded in authoritative source material. Hallucinated or unsupported answers from raw LLMs are equally dangerous. The market needs a system that retrieves relevant documentation, validates it, and generates answers with verifiable citations.

---

## Product Vision

To build a trustworthy, self-corrective AI assistant that can answer natural language questions about any technical documentation corpus — transparently citing its sources, detecting when it doesn't know, and gracefully recovering through query rewriting and fallback strategies.

---

## Product Goals

| # | Goal | Priority |
|---|------|----------|
| G1 | Accept natural language queries and return accurate, cited answers | P0 |
| G2 | Implement a LangGraph StateGraph with at least 4 nodes | P0 |
| G3 | Self-correct when retrieved documents are irrelevant (document grading + query rewrite) | P0 |
| G4 | Expose a fully functional FastAPI application | P0 |
| G5 | Provide document ingestion and indexing capabilities | P0 |
| G6 | Support feedback collection on answers | P1 |
| G7 | Provide optional hallucination verification | P2 |
| G8 | Support optional web search fallback | P2 |
| G9 | Support optional conversation memory | P2 |
| G10 | Provide a minimal Streamlit/Gradio UI | P2 |

---

## Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Retrieval Precision@K | ≥ 0.75 | Manual eval / RAGAS |
| Answer Relevance Score | ≥ 0.80 | RAGAS framework |
| Faithfulness Score | ≥ 0.85 | RAGAS framework |
| Grading Accuracy | ≥ 0.90 | Manual annotation |
| Query Success Rate (no fallback needed) | ≥ 70% | Logged metrics |
| API p95 Latency | ≤ 8 seconds | Application logs |
| API Error Rate | < 2% | Monitoring dashboard |
| Retry Loop Termination | 100% (never infinite) | Retry counter assertion |

---

## Stakeholders

| Role | Name / Team | Interest |
|------|-------------|----------|
| Hiring Manager | Express Analytics Talent | Evaluates candidate competency |
| Technical Reviewer | Senior AI Architect | Evaluates architecture quality |
| Product Owner | AI/ML Intern Candidate | Builds and owns the system |
| End User (Persona) | Software Engineer | Uses system to query docs |
| Platform Team (Future) | DevOps | Deploys and monitors |

---

## Assumptions

> **[ASSUMPTION-001]** The document corpus is small (3–5 documents), so a local vector store (ChromaDB or FAISS) is sufficient — no managed vector DB is required.

> **[ASSUMPTION-002]** The LLM provider is chosen by the implementer. Groq (Llama 3) is recommended for the free tier; OpenAI GPT-4o-mini is recommended for quality.

> **[ASSUMPTION-003]** The system runs locally; production-scale deployment (Kubernetes, load balancing) is out of scope for MVP.

> **[ASSUMPTION-004]** Authentication/authorization is not required for MVP (local use only).

> **[ASSUMPTION-005]** The corpus consists of publicly available technical documentation (LangChain, FastAPI, Pydantic, etc.).

> **[ASSUMPTION-006]** Feedback data is stored locally (SQLite or JSON file) rather than a managed database.

> **[ASSUMPTION-007]** Retry limit for query rewriting is set to 2 iterations to prevent infinite loops.

---

## Constraints

| Constraint | Details |
|------------|---------|
| Time | 2-day implementation window |
| Budget | Zero/minimal API cost — use free-tier LLM providers where possible |
| Team Size | Solo intern implementation |
| Stack | Python, LangGraph, FastAPI (mandatory) |
| Deployment | Local execution required; cloud optional |
| Corpus Size | 3–5 technical documents |
| LLM API | Must use at least one external LLM provider |

---

## Scope

### In Scope

- LangGraph StateGraph with Query Analysis, Retrieval, Document Grading, Generation nodes
- Conditional routing based on grading outcome
- Query rewriting with retry limit enforcement
- Document ingestion pipeline (chunking, embedding, vector store storage)
- FastAPI endpoints: POST /query, POST /ingest, GET /documents, POST /feedback
- Citations in generated answers
- README with architecture description, setup instructions, design decisions
- Unit tests for core components
- Error handling and input validation

### Out of Scope

- Multi-tenant authentication and authorization
- Managed cloud vector stores (Pinecone, Weaviate, etc.)
- Real-time document sync
- Multi-language support
- Large-scale load testing infrastructure
- Mobile or native desktop clients
- Production Kubernetes deployment
- SLA/uptime guarantees

---

## User Personas

### Persona 1: "Alex" — The Library Integrator
- **Background:** Mid-level Python developer integrating LangChain into a project
- **Goal:** Quickly find how to use specific classes, methods, or configuration options
- **Pain Points:** Official docs are long; can't easily search across multiple pages
- **Technical Comfort:** High

### Persona 2: "Priya" — The API Consumer
- **Background:** Backend engineer consuming a third-party API
- **Goal:** Understand endpoint parameters, error codes, and authentication flows
- **Pain Points:** API references are dense and lack examples
- **Technical Comfort:** High

### Persona 3: "Jordan" — The New Joiner
- **Background:** Junior engineer onboarding onto a project
- **Goal:** Understand framework conventions and best practices quickly
- **Pain Points:** Can't tell which parts of the docs are relevant to their task
- **Technical Comfort:** Medium

---

## User Stories

| ID | As a... | I want to... | So that... | Priority |
|----|---------|--------------|------------|----------|
| US-01 | Developer | Submit a natural language question | I receive a grounded, cited answer | P0 |
| US-02 | Developer | See which source documents the answer came from | I can verify the answer | P0 |
| US-03 | Developer | Receive an honest "I don't know" response | I'm not misled by hallucinations | P0 |
| US-04 | Admin | Upload new documents to the corpus | The assistant can answer questions about them | P0 |
| US-05 | Admin | List all indexed documents | I know what the assistant has access to | P1 |
| US-06 | Developer | Submit thumbs up/down feedback | The team can improve the system | P1 |
| US-07 | Developer | Ask follow-up questions (with memory) | I don't have to repeat context | P2 |
| US-08 | Developer | Use a web UI | I don't have to use curl/Postman | P2 |

---

## User Journey

```
1. Admin ingests documents via POST /ingest
2. System chunks, embeds, and stores them in vector store
3. Developer submits question via POST /query
4. System rewrites/expands query (Node 1: Query Analysis)
5. System retrieves top-k chunks (Node 2: Retrieval)
6. System grades each chunk for relevance (Node 3: Document Grading)
   6a. All irrelevant → rewrite query → back to step 4 (max 2 retries)
   6b. All irrelevant after max retries → return "I don't know"
   6c. Some/all relevant → filter to relevant chunks
7. System generates answer with citations (Node 4: Generation)
8. Developer receives answer + source references
9. Developer optionally submits feedback via POST /feedback
```

---

## Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | The system SHALL accept a natural language question string as input | P0 |
| FR-02 | The system SHALL retrieve the top-k most semantically similar document chunks | P0 |
| FR-03 | The system SHALL grade each retrieved chunk as relevant or irrelevant using an LLM | P0 |
| FR-04 | The system SHALL filter out irrelevant chunks before generation | P0 |
| FR-05 | The system SHALL generate an answer grounded in the filtered context | P0 |
| FR-06 | The system SHALL include source citations in the generated answer | P0 |
| FR-07 | The system SHALL rewrite the query and retry retrieval when all chunks are irrelevant | P0 |
| FR-08 | The system SHALL enforce a maximum retry count (≥ 1) to prevent infinite loops | P0 |
| FR-09 | The system SHALL return an explicit "insufficient context" response after max retries | P0 |
| FR-10 | The system SHALL ingest documents from file uploads or URLs | P0 |
| FR-11 | The system SHALL chunk documents with configurable chunk size and overlap | P0 |
| FR-12 | The system SHALL generate and store embeddings in a vector store | P0 |
| FR-13 | The system SHALL expose a /documents endpoint listing all indexed documents | P1 |
| FR-14 | The system SHALL accept and store user feedback (thumbs up/down + comment) | P1 |
| FR-15 | The system SHALL validate all API inputs and return meaningful error messages | P0 |

---

## Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | API response time for /query | p95 ≤ 8 seconds |
| NFR-02 | API response time for /ingest | p95 ≤ 30 seconds per document |
| NFR-03 | System must handle corrupt or empty file uploads gracefully | 0 unhandled exceptions |
| NFR-04 | All API endpoints must return structured JSON responses | 100% |
| NFR-05 | Retry counter must be bounded (no infinite loops) | Always terminates |
| NFR-06 | System must be runnable with a single command after setup | `uvicorn main:app` |
| NFR-07 | All secrets (API keys) must be stored in environment variables, never in code | 100% |
| NFR-08 | Codebase must include at least basic docstrings and inline comments | ≥ 80% of functions |
| NFR-09 | README must be sufficient to set up and run the project from scratch | Reviewer validation |

---

## Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC-01 | POST /query returns an answer with at least one citation for an in-corpus question | Manual test |
| AC-02 | POST /query returns "I don't know" (or equivalent) for an out-of-corpus question | Manual test |
| AC-03 | Document grading node correctly filters irrelevant chunks | Unit test |
| AC-04 | Retry loop executes at most N times (configurable, default 2) | Unit test |
| AC-05 | POST /ingest successfully indexes a new document and makes it queryable | Integration test |
| AC-06 | GET /documents returns a non-empty list after ingestion | API test |
| AC-07 | POST /feedback stores feedback and returns 200 | API test |
| AC-08 | System runs end-to-end locally with README instructions | Manual reviewer test |
| AC-09 | All API inputs validated; invalid inputs return 4xx with error detail | API test |

---

## Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| R-01 | LLM API rate limits exceeded during grading | Medium | High | Use Groq free tier; cache responses |
| R-02 | Embedding model inconsistency between ingest and query time | Low | High | Lock model name in config; validate on startup |
| R-03 | Infinite retry loop due to edge case in grading logic | Low | High | Hard cap retry counter; unit test edge cases |
| R-04 | Hallucinated citations (LLM invents source names) | Medium | High | Inject real source metadata into prompt; verify citations post-generation |
| R-05 | Chunking strategy splits code blocks mid-statement | Medium | Medium | Use RecursiveCharacterTextSplitter with code-aware separators |
| R-06 | Vector store corruption on restart (FAISS in-memory) | Medium | Medium | Use ChromaDB persistent mode or serialize FAISS index to disk |

---

## Future Enhancements

| # | Enhancement | Value |
|---|-------------|-------|
| FE-01 | Hallucination verification node (Self-RAG) | Reduces incorrect answers |
| FE-02 | Web search fallback (Tavily/Serper) | Handles out-of-corpus questions |
| FE-03 | Conversation memory / session support | Better multi-turn UX |
| FE-04 | Streamlit/Gradio frontend | Non-technical user access |
| FE-05 | RAGAS-based automated evaluation pipeline | Continuous quality monitoring |
| FE-06 | Re-ranking with cross-encoder (e.g., BGE-Reranker) | Improved retrieval precision |
| FE-07 | Multi-corpus support (namespace per project) | Multi-tenant capability |
| FE-08 | Async ingestion with background task queue | Faster API response on ingest |

---

## Release Plan

| Phase | Milestone | Duration |
|-------|-----------|----------|
| Phase 1 | Foundation: project structure, config, vector store | Day 1, Morning |
| Phase 2 | Ingestion pipeline: chunking, embedding, indexing | Day 1, Afternoon |
| Phase 3 | LangGraph workflow: all 4 nodes + conditional routing | Day 1, Evening |
| Phase 4 | FastAPI layer: all 4 endpoints, validation, error handling | Day 2, Morning |
| Phase 5 | Testing, README, cleanup, bonus features | Day 2, Afternoon |
| Phase 6 | Final review, GitHub push, submission | Day 2, Evening |

---

## MVP Definition

The MVP is defined as:

1. A working LangGraph StateGraph with Query Analysis → Retrieval → Document Grading → Generation nodes
2. Conditional routing: relevant → Generate, irrelevant → Rewrite + Retry (max 2), then fallback
3. ChromaDB or FAISS vector store with at least 3 ingested documents
4. FastAPI with POST /query, POST /ingest, GET /documents, POST /feedback
5. Citations in all generated answers
6. README sufficient for a reviewer to run the system from scratch
7. Basic input validation and error handling

Bonus features are explicitly excluded from MVP scope.