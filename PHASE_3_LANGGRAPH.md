# PHASE_3_LANGGRAPH.md — Phase 3: Core LangGraph Engine
## RAG-Based Technical Documentation Assistant

---

## 1. Phase Goal

*   **Business Goal**: Build a reliable agentic workflow that rewrites search parameters to find better matches, filters irrelevant data, and outputs grounded answers.
*   **Technical Goal**: Construct a LangGraph StateGraph comprising nodes for Query Analysis, Vector Retrieval, Document Grading, Query Rewrite, and Grounded Generation, using Groq or Gemini only.
*   **Completion Criteria**: Invoking the StateGraph with a test question executes the self-corrective pipeline and returns an answer with correct inline source citations.

---

## 2. Scope

### Included
*   RAGState schema dictionary and Pydantic models.
*   Prompts templates definitions for all core nodes.
*   LLM provider adapter class supporting **Groq and Gemini ONLY**.
*   StateGraph nodes implementations:
    - **Query Analysis**: Refines query and classifies type.
    - **Retrieval**: Searches persistent ChromaDB.
    - **Document Grading**: Filters out irrelevant text chunks.
    - **Generation**: Formulates answers citing source files.
    - **Query Rewrite**: Re-evaluates queries if all search results are irrelevant.
*   Conditional and fixed routing edges.
*   Retry counter logic ensuring loop termination.

### Excluded
*   Hallucination Verification node (moved to Phase 5).
*   FastAPI HTTP routes endpoints.

---

## 3. Dependencies

*   Phase 1 (Foundation) & Phase 2 (Ingestion) completed.
*   ChromaDB seeded with default corpus documents.
*   Valid external LLM provider API key (`GEMINI_API_KEY` or `GROQ_API_KEY`).

---

## 4. Deliverables

*   `app/workflow/state.py`
*   `app/workflow/prompts.py`
*   `app/workflow/routing.py`
*   `app/workflow/nodes/query_analysis.py`
*   `app/workflow/nodes/retrieval.py`
*   `app/workflow/nodes/document_grading.py`
*   `app/workflow/nodes/generation.py`
*   `app/workflow/nodes/query_rewrite.py`
*   `app/workflow/graph.py`
*   `app/infrastructure/llm/base.py`
*   `app/infrastructure/llm/adapters.py`

---

## 5. Sub-Phases

### Phase 3.1: LLM Client Adapters & State definitions
*   **Goal**: Create LLM communication wrapper classes and define the core LangGraph state keys.
*   **Tasks**:
    1. Define base abstract interface for LLM operations.
    2. Write adapters support for **Google Gemini and Groq clients ONLY** using async methods. Remove any OpenAI or Anthropic adapters.
    3. Define `RAGState` TypedDict structure inside `app/workflow/state.py`.
*   **Files**:
    - `app/infrastructure/llm/base.py`
    - `app/infrastructure/llm/adapters.py`
    - `app/workflow/state.py`
*   **Acceptance Criteria**: State schema compiles successfully, and the LLM adapter invokes model requests and parses responses asynchronously.
*   **Verification**: Execute a test connection to verify async model responses.

---

### Phase 3.2: RAG Workflows - Core Nodes
*   **Goal**: Implement the core query analysis, retrieval, and document grading functions.
*   **Tasks**:
    1. Define text prompts inside `app/workflow/prompts.py`.
    2. Write `query_analysis` node rewriting questions and classifying query types.
    3. Write `retrieval` node pulling chunks from ChromaDB.
    4. Write `document_grading` node checking similarity chunks and filtering irrelevant elements.
*   **Files**:
    - `app/workflow/prompts.py`
    - `app/workflow/nodes/query_analysis.py`
    - `app/workflow/nodes/retrieval.py`
    - `app/workflow/nodes/document_grading.py`
*   **Acceptance Criteria**: Query analysis returns clean query models. Grading node processes chunks and discards invalid ones.
*   **Verification**: Invoke nodes with sample states and assert output changes.

---

### Phase 3.3: Generation Node
*   **Goal**: Implement answer formulation and citations formatting.
*   **Tasks**:
    1. Write `generation` node compiling relevant chunks context and formatting inline citations like `[Source: filename, chunk X]`.
*   **Files**:
    - `app/workflow/nodes/generation.py`
*   **Acceptance Criteria**: Answers contain valid inline citations. If no relevant docs are found, returns fallback message.
*   **Verification**: Verify citation strings structure and grounding checks outcomes.

---

### Phase 3.4: Graph Assembly & Routing Edges
*   **Goal**: Tie all nodes together in a compiled StateGraph containing conditional edge branches.
*   **Tasks**:
    1. Write routing edge checks in `app/workflow/routing.py` managing retries.
    2. Build, construct, and compile StateGraph inside `app/workflow/graph.py`.
*   **Files**:
    - `app/workflow/routing.py`
    - `app/workflow/graph.py`
*   **Acceptance Criteria**: Graph executes from end to end. If retrieval fails, it loops to rewrite (up to max retries).
*   **Verification**: Run a local execution test showing full logs and node transitions.

---

## 6. AI Build Prompt (`AI_BUILD_PROMPT.md`)

```markdown
# AI Build Prompt: Phase 3 (Core LangGraph Engine)

## Goal
Construct the LangGraph StateGraph engine for the corrective RAG workflow with Groq or Google Gemini.

## Files to Create/Modify
- **app/infrastructure/llm/base.py**: Base LLM adapter interface.
- **app/infrastructure/llm/adapters.py**: Google Gemini and Groq ONLY async LLM wrappers.
- **app/workflow/state.py**: Defines `RAGState` TypedDict containing:
  - `question`: str (immutable)
  - `rewritten_query`: str
  - `query_type`: Optional[str]
  - `retrieved_docs`: List[DocumentChunk]
  - `graded_docs`: List[GradedDoc]
  - `relevant_docs`: List[DocumentChunk]
  - `retry_count`: int
  - `max_retries`: int
  - `should_fallback`: bool
  - `generation`: Optional[str]
  - `sources`: List[SourceReference]
- **app/workflow/prompts.py**: Prompt constants for:
  - Query expansion/classification
  - Relevance grading (JSON output formatting)
  - Answer generation (requiring inline citations `[Source: filename, chunk X]`)
- **app/workflow/nodes/**: Implement functions wrapping LLM adapters for query analysis, retrieval, grading, generation, and rewriting.
- **app/workflow/routing.py**: Conditional functions:
  - `route_after_grading(state)`: returns "generate" (if relevant docs > 0), "rewrite" (if 0 relevant and retry < max), or "fallback" (if retry >= max).
- **app/workflow/graph.py**: Compiles `StateGraph` linking:
  - query_analysis -> retrieval -> document_grading
  - document_grading -> route_after_grading -> query_rewrite (loops to retrieval) / generation / fallback
  - query_rewrite -> retrieval
  - generation -> END
  - fallback -> END

## Constraints
- Use close-to-zero LLM temperatures for grading nodes to ensure determinism.
- Handlers must parse potential markdown wrappers (e.g. ```json ... ```) surrounding JSON LLM replies.
- Support only Gemini and Groq; do not build unnecessary adapters.

## Acceptance Criteria
- Run a pipeline execution script and verify log outputs trace the correct path.
```

---

## 7. Verification Package

### Manual Verification
1. Run local test graph runner:
   ```bash
   python -c "import asyncio; from app.workflow.graph import build_rag_graph; from app.infrastructure.vector_store.chroma import ChromaVectorStore; from app.infrastructure.llm.adapters import GoogleLLMAdapter; from app.config import settings; vs = ChromaVectorStore(settings.CHROMA_PERSIST_DIR, None); llm = GoogleLLMAdapter(settings.LLM_MODEL); g = build_rag_graph(vs, llm); print(asyncio.run(g.ainvoke({'question': 'What is FastAPI?', 'retry_count': 0, 'max_retries': 2, 'should_fallback': False})))"
   ```

### Expected Results
*   The script prints the complete state trace.
*   State contains non-empty `"generation"` and `"sources"`.

### Failure Conditions
*   Workflows lock in infinite loops (retry checks fail).
*   LLM JSON structure changes crash parser logic.

---

## 8. Review Gates

- [ ] LLM adapters load correctly from `.env` keys (only Groq or Gemini used).
- [ ] Relevance grading node filters documents accurately.
- [ ] Retry count increments on every rewrite.
- [ ] Safe default responses configured for LLM timeouts.
