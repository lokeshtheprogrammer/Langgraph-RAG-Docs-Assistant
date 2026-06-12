import pytest

from app.workflow.graph import build_rag_graph
from app.workflow.state import DocumentChunk


@pytest.mark.asyncio
async def test_integration_grounded_flow(mock_llm_client, mock_embeddings, test_vector_store):
    """Test standard flow where retrieved documents are relevant and generation passes grounding."""
    # 1. Setup mock data in vector store
    mock_chunk = DocumentChunk(
        content="FastAPI is a fast, high-performance web framework.",
        source_file="fastapi.md",
        document_id="doc_fastapi",
        chunk_index=0
    )
    test_vector_store.add_chunks([mock_chunk], mock_embeddings.embed_documents([mock_chunk.content]))
    
    # 2. Setup mock LLM responses
    mock_llm_client.responses = {
        "Classify the query type": '{"rewritten_query": "What is FastAPI?", "query_type": "conceptual"}',
        "determine if the given document chunk is useful": '{"grade": "relevant"}',
        "You are a factual grounding checker": '{"score": 1.0, "supported": true, "unsupported_claims": []}',
        "Answer the user's question using ONLY": "FastAPI is a modern web framework. [Source: fastapi.md]"
    }
    
    # 3. Build and run graph
    graph = build_rag_graph(test_vector_store, mock_embeddings, mock_llm_client, web_search_client=None)
    initial_state = {
        "question": "What is FastAPI?",
        "session_id": "session_grounded",
        "retrieved_docs": [],
        "relevant_docs": [],
        "graded_docs": [],
        "retry_count": 0,
        "max_retries": 2,
        "should_fallback": False,
        "generation": None,
        "sources": [],
        "hallucination_score": None,
        "hallucination_check_passed": None,
        "regeneration_count": 0,
        "top_k": 3,
        "web_search_results": [],
        "web_search_used": False
    }
    
    result = await graph.ainvoke(initial_state)
    
    # 4. Assertions
    assert result["generation"] == "FastAPI is a modern web framework. [Source: fastapi.md]"
    assert result["hallucination_check_passed"] is True
    assert result["hallucination_score"] == 1.0
    assert result["regeneration_count"] == 0
    assert len(result["relevant_docs"]) > 0
    assert result["should_fallback"] is False

@pytest.mark.asyncio
async def test_integration_hallucination_correction_flow(mock_llm_client, mock_embeddings, test_vector_store):
    """Test flow where first generation fails grounding check but the regenerated version passes."""
    mock_chunk = DocumentChunk(
        content="Pydantic is data validation library.",
        source_file="pydantic.md",
        document_id="doc_pydantic",
        chunk_index=0
    )
    test_vector_store.add_chunks([mock_chunk], mock_embeddings.embed_documents([mock_chunk.content]))
    
    # We want hallucination check to fail the first time, succeed the second time.
    # To do this, we override mock_llm_client.ainvoke manually in this test.
    call_count = 0
    async def custom_ainvoke(messages: list[dict], **kwargs) -> str:
        nonlocal call_count
        prompt = messages[-1]["content"]
        if "Classify the query type" in prompt:
            return '{"rewritten_query": "What is Pydantic?", "query_type": "conceptual"}'
        elif "determine if the given document chunk is useful" in prompt:
            return '{"grade": "relevant"}'
        elif "You are a factual grounding checker" in prompt:
            call_count += 1
            if call_count == 1:
                return '{"score": 0.3, "supported": false, "unsupported_claims": ["hallucination"]}'
            return '{"score": 0.9, "supported": true, "unsupported_claims": []}'
        elif "Answer the user's question using ONLY" in prompt or "FAILED GROUNDING VERIFICATION" in prompt:
            return "Pydantic is a library. [Source: pydantic.md]"
        return "{}"
        
    mock_llm_client.ainvoke = custom_ainvoke
    
    graph = build_rag_graph(test_vector_store, mock_embeddings, mock_llm_client, web_search_client=None)
    initial_state = {
        "question": "What is Pydantic?",
        "session_id": "session_regen",
        "retrieved_docs": [],
        "relevant_docs": [],
        "graded_docs": [],
        "retry_count": 0,
        "max_retries": 2,
        "should_fallback": False,
        "generation": None,
        "sources": [],
        "hallucination_score": None,
        "hallucination_check_passed": None,
        "regeneration_count": 0,
        "top_k": 3,
        "web_search_results": [],
        "web_search_used": False
    }
    
    result = await graph.ainvoke(initial_state)
    
    assert result["generation"] == "Pydantic is a library. [Source: pydantic.md]"
    assert result["hallucination_check_passed"] is True
    assert result["regeneration_count"] == 1
    assert result["should_fallback"] is False

@pytest.mark.asyncio
async def test_integration_fallback_flow(mock_llm_client, mock_embeddings, test_vector_store):
    """Test flow where query fails grading repeatedly and routes to fallback."""
    # Do not add relevant documents to vector store
    mock_llm_client.responses = {
        "Classify the query type": '{"rewritten_query": "Invalid query", "query_type": "conceptual"}',
        "determine if the given document chunk is useful": '{"grade": "irrelevant"}',
        "The following query failed to retrieve": "another query attempt",
    }
    
    graph = build_rag_graph(test_vector_store, mock_embeddings, mock_llm_client, web_search_client=None)
    initial_state = {
        "question": "invalid irrelevant question",
        "session_id": "session_fallback",
        "retrieved_docs": [],
        "relevant_docs": [],
        "graded_docs": [],
        "retry_count": 0,
        "max_retries": 2,
        "should_fallback": False,
        "generation": None,
        "sources": [],
        "hallucination_score": None,
        "hallucination_check_passed": None,
        "regeneration_count": 0,
        "top_k": 3,
        "web_search_results": [],
        "web_search_used": False
    }
    
    result = await graph.ainvoke(initial_state)
    
    # check fallback response
    from app.workflow.nodes.generation import FALLBACK_ANSWER
    assert result["generation"] == FALLBACK_ANSWER
    assert result["should_fallback"] is True
    assert result["retry_count"] == 2
