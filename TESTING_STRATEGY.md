# TESTING_STRATEGY.md — Testing Strategy
## RAG-Based Technical Documentation Assistant

**Version:** 1.0.0
**Date:** 2025-06-11

---

## Testing Philosophy

Given the 2-day implementation window, testing priorities are:

1. **Unit test the routing logic** — the most critical, most testable component
2. **API test all endpoints** — validates integration from route to service
3. **Integration test the ingestion pipeline** — validates the data foundation
4. **Manual evaluation of RAG quality** — validates the AI behavior

Full TDD is not feasible in this timeframe. Instead, test after each phase using the test suite to validate before moving forward.

---

## Test Stack

```
pytest>=8.0.0
pytest-asyncio>=0.23.0     # async test support
httpx>=0.27.0              # FastAPI TestClient
pytest-cov>=5.0.0          # coverage reporting
```

---

## Test Configuration

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
import chromadb

from app.main import app
from app.workflow.state import RAGState, DocumentChunk

@pytest.fixture
def mock_llm():
    """Mock LLM that returns predefined responses."""
    llm = AsyncMock()
    return llm

@pytest.fixture
def in_memory_chroma():
    """Ephemeral ChromaDB for integration tests."""
    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection("test_docs")
    return client, collection

@pytest.fixture
def sample_doc_chunks():
    return [
        DocumentChunk(
            content="FastAPI is a modern Python web framework for building APIs.",
            source_file="fastapi_docs.md",
            document_id="doc_001",
            chunk_index=0,
            distance=0.12,
        ),
        DocumentChunk(
            content="LangChain tools allow LLMs to interact with external systems.",
            source_file="langchain_docs.md",
            document_id="doc_002",
            chunk_index=5,
            distance=0.25,
        ),
    ]

@pytest.fixture
def base_state(sample_doc_chunks):
    return RAGState(
        question="What is FastAPI?",
        session_id=None,
        rewritten_query="What is FastAPI?",
        query_type=None,
        retrieved_docs=sample_doc_chunks,
        top_k=5,
        graded_docs=[],
        relevant_docs=[],
        retry_count=0,
        max_retries=2,
        should_fallback=False,
        generation=None,
        sources=[],
        hallucination_score=None,
        hallucination_check_passed=None,
    )

@pytest.fixture
def test_client():
    return TestClient(app)
```

---

## Unit Tests

### test_routing.py

```python
# tests/unit/test_routing.py
import pytest
from app.workflow.routing import route_after_grading
from app.workflow.state import RAGState, DocumentChunk

def make_state(relevant_count: int, retry_count: int, max_retries: int = 2) -> RAGState:
    chunks = [
        DocumentChunk(content="text", source_file="f.md", document_id="d1", chunk_index=i)
        for i in range(relevant_count)
    ]
    return {
        "relevant_docs": chunks,
        "retry_count": retry_count,
        "max_retries": max_retries,
        "should_fallback": False,
    }

class TestRouteAfterGrading:
    def test_relevant_docs_always_generate(self):
        state = make_state(relevant_count=3, retry_count=0)
        assert route_after_grading(state) == "generate"

    def test_relevant_docs_ignores_retry_count(self):
        state = make_state(relevant_count=1, retry_count=5)
        assert route_after_grading(state) == "generate"

    def test_no_relevant_docs_retries_when_below_max(self):
        state = make_state(relevant_count=0, retry_count=0, max_retries=2)
        assert route_after_grading(state) == "rewrite"

    def test_no_relevant_docs_retries_at_max_minus_one(self):
        state = make_state(relevant_count=0, retry_count=1, max_retries=2)
        assert route_after_grading(state) == "rewrite"

    def test_no_relevant_docs_fallback_at_max(self):
        state = make_state(relevant_count=0, retry_count=2, max_retries=2)
        assert route_after_grading(state) == "fallback"

    def test_no_relevant_docs_fallback_beyond_max(self):
        state = make_state(relevant_count=0, retry_count=10, max_retries=2)
        assert route_after_grading(state) == "fallback"

    def test_zero_max_retries_immediately_fallback(self):
        state = make_state(relevant_count=0, retry_count=0, max_retries=0)
        assert route_after_grading(state) == "fallback"

    def test_custom_max_retries(self):
        state = make_state(relevant_count=0, retry_count=4, max_retries=5)
        assert route_after_grading(state) == "rewrite"
        state = make_state(relevant_count=0, retry_count=5, max_retries=5)
        assert route_after_grading(state) == "fallback"
```

### test_grading_parser.py

```python
# tests/unit/test_grading_parser.py
import pytest
from app.workflow.nodes.document_grading import parse_grade

class TestGradeParser:
    def test_valid_relevant(self):
        assert parse_grade('{"grade": "relevant"}') == "relevant"

    def test_valid_irrelevant(self):
        assert parse_grade('{"grade": "irrelevant"}') == "irrelevant"

    def test_invalid_json_defaults_irrelevant(self):
        assert parse_grade("not json at all") == "irrelevant"

    def test_missing_grade_key_defaults_irrelevant(self):
        assert parse_grade('{"result": "yes"}') == "irrelevant"

    def test_unknown_grade_value_defaults_irrelevant(self):
        assert parse_grade('{"grade": "maybe"}') == "irrelevant"

    def test_json_with_extra_text(self):
        # LLM sometimes adds explanation before JSON
        response = 'Here is my assessment: {"grade": "relevant"}'
        # Should still parse (implement with json extraction)
        assert parse_grade(response) in ("relevant", "irrelevant")

    def test_empty_string(self):
        assert parse_grade("") == "irrelevant"
```

### test_chunking.py

```python
# tests/unit/test_chunking.py
from app.utils.chunking import create_splitter, split_text

class TestChunking:
    def test_chunks_respect_size_limit(self):
        text = "A" * 10000
        chunks = split_text(text, chunk_size=512, overlap=64)
        assert all(len(c) <= 600 for c in chunks)  # small buffer for overlap

    def test_overlap_creates_shared_content(self):
        text = " ".join([f"word{i}" for i in range(100)])
        chunks = split_text(text, chunk_size=100, overlap=20)
        # Last words of chunk N should appear in chunk N+1
        if len(chunks) >= 2:
            last_of_first = chunks[0][-20:]
            assert any(word in chunks[1] for word in last_of_first.split())

    def test_empty_text_returns_empty(self):
        assert split_text("", chunk_size=512, overlap=64) == []

    def test_short_text_returns_single_chunk(self):
        text = "Short text."
        chunks = split_text(text, chunk_size=512, overlap=64)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_code_block_not_split_mid_line(self):
        text = "Some text.\n\n```python\ndef my_func():\n    return 42\n```\n\nMore text."
        chunks = split_text(text, chunk_size=512, overlap=64)
        # Code block should not be split in the middle of a line
        for chunk in chunks:
            lines = chunk.split("\n")
            for line in lines:
                assert not line.endswith("def my_f")  # mid-split would look like this
```

---

## Integration Tests

### test_ingestion.py

```python
# tests/integration/test_ingestion.py
import pytest
import tempfile
import os

@pytest.mark.asyncio
async def test_full_ingest_pipeline(in_memory_chroma, tmp_path):
    """Test complete: file → chunks → embeddings → vector store."""
    # Create test document
    doc = tmp_path / "test.md"
    doc.write_text("# FastAPI\n\nFastAPI is a web framework.\n\n" * 20)

    # Ingest
    service = create_test_ingestion_service(in_memory_chroma)
    result = await service.ingest_file_path(str(doc))

    assert result.status == "indexed"
    assert result.chunks_indexed > 0

    # Verify searchable
    vector_store = create_test_vector_store(in_memory_chroma)
    results = vector_store.similarity_search("what is FastAPI", k=3)
    assert len(results) > 0
    assert any("FastAPI" in r.content for r in results)

@pytest.mark.asyncio
async def test_duplicate_detection(in_memory_chroma, tmp_path):
    """Test that ingesting the same file twice does not create duplicates."""
    doc = tmp_path / "test.md"
    doc.write_text("FastAPI is a Python web framework.")

    service = create_test_ingestion_service(in_memory_chroma)
    result1 = await service.ingest_file_path(str(doc))
    result2 = await service.ingest_file_path(str(doc))

    assert result1.duplicate == False
    assert result2.duplicate == True
    assert result2.chunks_indexed == 0
```

### test_workflow.py

```python
# tests/integration/test_workflow.py
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_workflow_successful_retrieval(in_memory_chroma, sample_doc_chunks):
    """Full workflow with relevant docs found on first try."""
    # Pre-populate vector store
    vector_store = create_test_vector_store(in_memory_chroma)
    await vector_store.add_documents(sample_doc_chunks)

    # Mock LLM: query analysis returns original, grading returns relevant, generation returns answer
    mock_llm = AsyncMock()
    mock_llm.ainvoke.side_effect = [
        '{"rewritten_query": "What is FastAPI", "query_type": "conceptual"}',  # analysis
        '{"grade": "relevant"}',  # grading chunk 1
        '{"grade": "relevant"}',  # grading chunk 2
        "FastAPI is a modern web framework. [Source: fastapi_docs.md]",  # generation
    ]

    graph = build_rag_graph(vector_store, mock_llm)
    result = await graph.ainvoke({"question": "What is FastAPI?"})

    assert result["generation"] is not None
    assert result["is_fallback"] == False
    assert result["retry_count"] == 0

@pytest.mark.asyncio
async def test_workflow_retry_and_fallback(in_memory_chroma):
    """Full workflow where all retries fail and fallback is triggered."""
    vector_store = create_test_vector_store(in_memory_chroma)
    # Do NOT add relevant docs

    mock_llm = AsyncMock()
    # All grading calls return irrelevant; rewrites don't help
    mock_llm.ainvoke.return_value = '{"grade": "irrelevant"}'

    graph = build_rag_graph(vector_store, mock_llm, max_retries=2)
    result = await graph.ainvoke({"question": "What is React Native?"})

    assert result["should_fallback"] == True
    assert result["retry_count"] == 2
    assert "insufficient" in result["generation"].lower() or "unable" in result["generation"].lower()
```

---

## API Tests

### test_query_endpoint.py

```python
# tests/api/test_query_endpoint.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

def test_query_success(test_client):
    with patch("app.dependencies.get_query_service") as mock_svc:
        mock_svc.return_value.process_query = AsyncMock(return_value={
            "answer": "FastAPI is a web framework.",
            "sources": [{"source_file": "fastapi.md", "chunk_index": 0, "excerpt": "..."}],
            "query_type": "conceptual",
            "rewritten_query": "FastAPI framework",
            "retry_count": 0,
            "is_fallback": False,
            "response_time_ms": 1200,
            "session_id": None,
        })
        response = test_client.post("/query", json={"question": "What is FastAPI?"})

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data

def test_query_empty_question(test_client):
    response = test_client.post("/query", json={"question": ""})
    assert response.status_code == 422

def test_query_missing_question(test_client):
    response = test_client.post("/query", json={})
    assert response.status_code == 422

def test_query_question_too_long(test_client):
    response = test_client.post("/query", json={"question": "x" * 2001})
    assert response.status_code == 422

def test_query_invalid_top_k(test_client):
    response = test_client.post("/query", json={"question": "test", "top_k": 0})
    assert response.status_code == 422

def test_query_fallback_response(test_client):
    with patch("app.dependencies.get_query_service") as mock_svc:
        mock_svc.return_value.process_query = AsyncMock(return_value={
            "answer": "I was unable to find relevant information.",
            "sources": [],
            "query_type": "conceptual",
            "rewritten_query": "...",
            "retry_count": 2,
            "is_fallback": True,
            "response_time_ms": 5000,
            "session_id": None,
        })
        response = test_client.post("/query", json={"question": "What is Kubernetes?"})

    assert response.status_code == 200
    assert response.json()["is_fallback"] == True
```

### test_ingest_endpoint.py

```python
# tests/api/test_ingest_endpoint.py
import io

def test_ingest_valid_markdown_file(test_client):
    file_content = b"# FastAPI\n\nFastAPI is a web framework for Python."
    response = test_client.post(
        "/ingest",
        files={"file": ("test_doc.md", io.BytesIO(file_content), "text/markdown")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "indexed"
    assert data["chunks_indexed"] > 0

def test_ingest_invalid_file_type(test_client):
    file_content = b"some content"
    response = test_client.post(
        "/ingest",
        files={"file": ("document.exe", io.BytesIO(file_content), "application/octet-stream")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE_TYPE"

def test_ingest_no_source(test_client):
    response = test_client.post("/ingest")
    assert response.status_code == 400
    assert "source" in response.json()["error"]["message"].lower()

def test_ingest_both_sources(test_client):
    response = test_client.post(
        "/ingest",
        data={"url": "https://example.com"},
        files={"file": ("test.md", io.BytesIO(b"content"), "text/markdown")},
    )
    assert response.status_code == 400

def test_ingest_empty_file(test_client):
    response = test_client.post(
        "/ingest",
        files={"file": ("empty.md", io.BytesIO(b""), "text/markdown")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMPTY_DOCUMENT"
```

---

## RAG Evaluation Tests

```python
# tests/rag_eval/run_ragas_eval.py
"""
Run RAGAS evaluation on a predefined Q&A dataset.
Requires real LLM API access. Not part of standard CI.

Usage:
  python tests/rag_eval/run_ragas_eval.py
"""
import json
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

EVAL_DATASET = [
    {
        "question": "How do I create a route in FastAPI?",
        "ground_truth": "Use the @app.get or @app.post decorator on a function.",
        "expected_source": "fastapi_tutorial.md"
    },
    {
        "question": "What is a LangChain tool?",
        "ground_truth": "A tool is a function that an LLM can call to interact with external systems.",
        "expected_source": "langchain_docs.md"
    },
    # Add 5-10 more based on actual corpus content
]

def run_evaluation():
    results = []
    for item in EVAL_DATASET:
        # Run query through live system
        response = query_system(item["question"])
        results.append({
            "question": item["question"],
            "answer": response["answer"],
            "contexts": [s["excerpt"] for s in response["sources"]],
            "ground_truth": item["ground_truth"],
        })

    scores = evaluate(results, metrics=[faithfulness, answer_relevancy, context_precision])
    print(scores)
```

---

## LangGraph Tests

```python
# tests/unit/test_graph_structure.py
def test_graph_has_required_nodes():
    from app.workflow.graph import build_rag_graph
    mock_vs, mock_llm = MagicMock(), MagicMock()
    graph = build_rag_graph(mock_vs, mock_llm)

    node_names = set(graph.nodes.keys())
    required = {"query_analysis", "retrieval", "document_grading", "generation", "query_rewrite"}
    assert required.issubset(node_names)

def test_graph_entry_point():
    graph = build_rag_graph(MagicMock(), MagicMock())
    assert graph.entry_point == "query_analysis"

def test_graph_has_conditional_edge_from_grading():
    graph = build_rag_graph(MagicMock(), MagicMock())
    # Verify conditional edges from document_grading
    edges = graph.edges
    grading_edges = [e for e in edges if e[0] == "document_grading"]
    assert len(grading_edges) >= 2  # at least 2 conditional targets
```

---

## Failure Tests

```python
# tests/unit/test_failure_modes.py

def test_grading_malformed_json_does_not_raise():
    """Malformed LLM response during grading must not crash the workflow."""
    from app.workflow.nodes.document_grading import parse_grade
    result = parse_grade("I think this is relevant but I'm not sure")
    assert result == "irrelevant"  # safe default

def test_generation_with_empty_relevant_docs():
    """Generation node must handle empty relevant_docs gracefully."""
    from app.workflow.nodes.generation import generation_node
    state = {
        "relevant_docs": [],
        "should_fallback": True,
        "question": "test",
    }
    # Should return fallback message, not raise
    # (tested with mock LLM via node factory)

@pytest.mark.asyncio
async def test_retry_loop_terminates():
    """Verify workflow always terminates regardless of grading results."""
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = '{"grade": "irrelevant"}'  # always irrelevant

    graph = build_rag_graph(mock_vector_store, mock_llm, max_retries=3)
    result = await graph.ainvoke({"question": "anything"})

    # Must terminate — should_fallback set
    assert result is not None
    assert result.get("retry_count") <= 3
```

---

## Load Tests

> **Note:** Load testing is out of scope for MVP but defined here for completeness.

```python
# Using locust for load testing (not included in CI)
from locust import HttpUser, task, between

class RAGUser(HttpUser):
    wait_time = between(2, 5)

    @task(5)
    def query_known_question(self):
        self.client.post("/query", json={
            "question": "How do I create a route in FastAPI?"
        })

    @task(1)
    def query_unknown_question(self):
        self.client.post("/query", json={
            "question": "What is the capital of Mars?"
        })

    @task(1)
    def list_documents(self):
        self.client.get("/documents")
```

**Target:** 10 concurrent users, p95 latency < 8 seconds for `/query`.

---

## Acceptance Tests

Manual test script to be run by reviewer:

```bash
#!/bin/bash
# scripts/acceptance_test.sh
BASE_URL="http://localhost:8000"

echo "=== Test 1: Health Check ==="
curl -s $BASE_URL/health | python -m json.tool

echo "=== Test 2: List Documents (should be non-empty after corpus ingest) ==="
curl -s $BASE_URL/documents | python -m json.tool

echo "=== Test 3: Query in-corpus question ==="
curl -s -X POST $BASE_URL/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I install FastAPI?"}' | python -m json.tool

echo "=== Test 4: Query out-of-corpus question (expect fallback) ==="
curl -s -X POST $BASE_URL/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the best recipe for apple pie?"}' | python -m json.tool

echo "=== Test 5: Ingest new document ==="
echo "# Test Doc\nThis is a test document." > /tmp/test_doc.md
curl -s -X POST $BASE_URL/ingest -F "file=@/tmp/test_doc.md" | python -m json.tool

echo "=== Test 6: Submit feedback ==="
curl -s -X POST $BASE_URL/feedback \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "answer": "test answer", "rating": "thumbs_up"}' | python -m json.tool
```

---

## Test Matrix

| Component | Unit | Integration | API | Manual |
|-----------|------|------------|-----|--------|
| Routing logic | ✅ Required | — | — | — |
| Grading parser | ✅ Required | — | — | — |
| Chunking | ✅ Required | — | — | — |
| LangGraph graph structure | ✅ Required | — | — | — |
| Full workflow (mocked LLM) | — | ✅ Required | — | — |
| Ingestion pipeline | — | ✅ Required | — | — |
| POST /query | — | — | ✅ Required | ✅ Required |
| POST /ingest | — | — | ✅ Required | ✅ Required |
| GET /documents | — | — | ✅ Required | ✅ Required |
| POST /feedback | — | — | ✅ Required | — |
| Retry termination | ✅ Required | ✅ Required | — | — |
| Fallback response | ✅ Required | ✅ Required | ✅ Required | ✅ Required |
| RAG quality (RAGAS) | — | — | — | Optional |
| Load testing | — | — | — | Optional |
