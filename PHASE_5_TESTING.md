# PHASE_5_TESTING.md — Phase 5: Testing & Hallucination Check Enhancement
## RAG-Based Technical Documentation Assistant

---

## 1. Phase Goal

*   **Business Goal**: Assert factual grounding, eliminate regressions, and verify document retrieval precision.
*   **Technical Goal**: Implement the Hallucination Verification node as a graph enhancement, and construct a complete unit, integration, and API testing suite using pytest with LLM/database mock fixtures.
*   **Completion Criteria**: Pytest suite runs, achieving >= 80% coverage, and the compiled graph correctly executes the hallucination verification node to score answers.

---

## 2. Scope

### Included
*   **Hallucination Check Node**: Grounding validator inserted in graph: `Generation ➔ Hallucination Check ➔ Answer/END`.
*   pytest configuration and conftest fixtures.
*   Mocking utilities for LLM provider outputs.
*   Ephemeral ChromaDB and SQLite database test fixtures.
*   Unit tests for:
    - Routing logic branches.
    - JSON grading responses parsers.
    - Text splitting/chunking lengths and overlap splits.
*   Integration tests for:
    - Ingestion pipeline.
    - LangGraph StateGraph execution flows (successful paths, retry limit exhaustions, hallucination check routes).
*   API endpoint tests using `fastapi.testclient`.

### Excluded
*   Docker container setups (handled in Phase 6).
*   Production SSL certificates.

---

## 3. Dependencies

*   Phases 1 to 4 successfully completed and verified.
*   FastAPI routers and LangGraph nodes available for imports.

---

## 4. Deliverables

*   `app/workflow/nodes/hallucination_check.py`
*   `tests/conftest.py`
*   `tests/unit/test_routing.py`
*   `tests/unit/test_grading_parser.py`
*   `tests/unit/test_chunking.py`
*   `tests/integration/test_ingestion.py`
*   `tests/integration/test_workflow.py`
*   `tests/api/test_query_endpoint.py`
*   `tests/api/test_ingest_endpoint.py`
*   `tests/api/test_documents_endpoint.py`
*   `tests/api/test_feedback_endpoint.py`

---

## 5. Sub-Phases

### Phase 5.1: Hallucination Verification Node
*   **Goal**: Integrate hallucination check node into the graph workflow.
*   **Tasks**:
    1. Write `app/workflow/nodes/hallucination_check.py` to evaluate generated answers against the source chunks.
    2. Define prompt templates for the hallucination check.
    3. Update the compiled graph (`app/workflow/graph.py`) and routing logic (`app/workflow/routing.py`) to inject the node after generation.
*   **Files**:
    - `app/workflow/nodes/hallucination_check.py`
    - `app/workflow/graph.py` (updated)
    - `app/workflow/routing.py` (updated)
*   **Acceptance Criteria**: Running queries against the updated graph routes the state through the hallucination checker and sets `hallucination_check_passed`.
*   **Verification**: Check execution trace using local test script.

---

### Phase 5.2: Test Fixtures & Unit Tests
*   **Goal**: Create environment configuration parameters for testing and implement unit tests.
*   **Tasks**:
    1. Implement `tests/conftest.py` containing fixtures for mock LLMs, test configuration loaders, and database builders.
    2. Write unit tests for checking text chunk splitting limits inside `tests/unit/test_chunking.py`.
    3. Write unit tests for JSON parser functions inside `tests/unit/test_grading_parser.py`.
    4. Write routing unit checks inside `tests/unit/test_routing.py` (including routing after the hallucination check).
*   **Files**:
    - `tests/conftest.py`
    - `tests/unit/test_chunking.py`
    - `tests/unit/test_grading_parser.py`
    - `tests/unit/test_routing.py`
*   **Acceptance Criteria**: Running pytest on unit directory passes all test checks cleanly.
*   **Verification**: Run command `pytest tests/unit/`.

---

### Phase 5.3: Workflow & Ingestion Integration Tests
*   **Goal**: Implement tests asserting state transitions inside compiled StateGraph.
*   **Tasks**:
    1. Write document processing integration tests in `tests/integration/test_ingestion.py` using in-memory databases.
    2. Write StateGraph integration tests in `tests/integration/test_workflow.py`. Mock LLM calls to test grading success, retry loop bounds, and hallucination routing.
*   **Files**:
    - `tests/integration/test_ingestion.py`
    - `tests/integration/test_workflow.py`
*   **Acceptance Criteria**: Chunks write to local temporary vector storage and search results return matches. Graph flows terminates when max retries are reached.
*   **Verification**: Run command `pytest tests/integration/`.

---

### Phase 5.4: API Endpoints Tests
*   **Goal**: Implement endpoint request validations using FastAPI test client.
*   **Tasks**:
    1. Write routes tests for Query API inside `tests/api/test_query_endpoint.py`.
    2. Write routes tests for Ingest API inside `tests/api/test_ingest_endpoint.py`.
    3. Write routes tests for document and feedback APIs.
*   **Files**:
    - `tests/api/test_query_endpoint.py`
    - `tests/api/test_ingest_endpoint.py`
    - `tests/api/test_documents_endpoint.py`
    - `tests/api/test_feedback_endpoint.py`
*   **Acceptance Criteria**: Testing client queries return valid HTTP codes (200, 201, 400, 422). File uploads validations block invalid properties.
*   **Verification**: Run command `pytest tests/api/`.

---

## 6. AI Build Prompt (`AI_BUILD_PROMPT.md`)

```markdown
# AI Build Prompt: Phase 5 (Testing & Hallucination Check)

## Goal
Implement the hallucination check node and the pytest-based testing suite.

## Files to Create/Modify
- **app/workflow/nodes/hallucination_check.py**: Grounding check node returning JSON score.
- **app/workflow/graph.py**: Wire the hallucination check node to run after generation.
- **app/workflow/routing.py**: Implement routing edge after hallucination check.
- **tests/conftest.py**: Shared testing fixtures (mock LLM, test databases, client).
- **tests/unit/test_routing.py**: Route testing including routing after hallucination check.
- **tests/unit/test_grading_parser.py**: Test grading parser parsing.
- **tests/unit/test_chunking.py**: Test text splitting.
- **tests/integration/test_ingestion.py**: Integration test for ingestion.
- **tests/integration/test_workflow.py**: Workflow integration tests (with and without hallucination check).
- **tests/api/**: Tests for all FastAPI endpoints.

## Constraints
- Mock all LLM API invocations. Support Groq and Gemini interfaces ONLY.
```

---

## 7. Verification Package

### Manual Verification
1. Run complete test suite:
   ```bash
   pytest tests/
   ```
2. Verify code coverage parameters:
   ```bash
   pytest --cov=app --cov-report=term-missing tests/
   ```

### Expected Results
*   All tests execute and pass successfully.
*   Coverage report prints summary metrics showing >= 80% coverage on core files.

---

## 8. Review Gates

- [ ] Hallucination node integrated into compiled graph.
- [ ] Ephemeral database assets cleanup correctly at test teardown.
- [ ] Core routing decisions cover all branches in tests.
- [ ] No actual LLM provider API credentials loaded in test configurations.
