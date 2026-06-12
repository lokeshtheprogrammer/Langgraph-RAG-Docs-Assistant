import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.utils.chunking import split_text
from app.workflow.nodes.document_grading import parse_grade
from app.workflow.nodes.hallucination_check import parse_hallucination_check
from app.workflow.routing import route_after_grading, route_after_hallucination_check
from app.workflow.state import DocumentChunk
from app.workflow.nodes.web_search import web_search_node
from app.infrastructure.web_search.base import WebSearchResult, WebSearchClientBase
from app.infrastructure.web_search.duckduckgo import DuckDuckGoSearchClient


# 1. Test split_text
def test_split_text_empty():
    assert split_text("", 100, 10) == []

def test_split_text_normal():
    text = "Hello world. This is a simple test of splitting text. It should break it down."
    chunks = split_text(text, chunk_size=30, chunk_overlap=5)
    assert len(chunks) > 0
    # verify chunks reconstruct original text or parts of it
    assert any("Hello world" in chunk for chunk in chunks)

# 2. Test parse_grade
@pytest.mark.parametrize("response, expected", [
    ('{"grade": "relevant"}', "relevant"),
    ('{"grade": "irrelevant"}', "irrelevant"),
    ('```json\n{"grade": "relevant"}\n```', "relevant"),
    ('```\n{"grade": "irrelevant"}\n```', "irrelevant"),
    ('invalid json', "irrelevant"),
    ('{"grade": "other"}', "irrelevant"),
    ('', "irrelevant")
])
def test_parse_grade(response, expected):
    assert parse_grade(response) == expected

# 3. Test parse_hallucination_check
@pytest.mark.parametrize("response, expected_score, expected_supported", [
    ('{"score": 0.9, "supported": true}', 0.9, True),
    ('{"score": 0.5, "supported": false}', 0.5, False),
    ('```json\n{"score": 0.8, "supported": true}\n```', 0.8, True),
    ('invalid json', 0.0, False),
    ('{"score": 0.75}', 0.75, True), # default to score >= 0.7 if supported missing
    ('{"score": 0.6}', 0.6, False), # default to score >= 0.7 if supported missing
])
def test_parse_hallucination_check(response, expected_score, expected_supported):
    score, supported = parse_hallucination_check(response)
    assert score == expected_score
    assert supported == expected_supported

# 4. Test route_after_grading
def test_route_after_grading_relevant():
    mock_chunk = DocumentChunk(content="test", source_file="a.md", document_id="1", chunk_index=0)
    state = {
        "relevant_docs": [mock_chunk],
        "retry_count": 0,
        "max_retries": 2
    }
    assert route_after_grading(state) == "generate"

def test_route_after_grading_rewrite():
    state = {
        "relevant_docs": [],
        "retry_count": 0,
        "max_retries": 2
    }
    assert route_after_grading(state) == "rewrite"

def test_route_after_grading_web_search():
    state = {
        "relevant_docs": [],
        "retry_count": 2,
        "max_retries": 2
    }
    assert route_after_grading(state) == "web_search"

# 5. Test route_after_hallucination_check
def test_route_after_hallucination_passed():
    state = {
        "hallucination_check_passed": True,
        "regeneration_count": 0
    }
    assert route_after_hallucination_check(state) == "end"

def test_route_after_hallucination_failed_retry():
    state = {
        "hallucination_check_passed": False,
        "regeneration_count": 0
    }
    assert route_after_hallucination_check(state) == "regenerate"

def test_route_after_hallucination_failed_max():
    state = {
        "hallucination_check_passed": False,
        "regeneration_count": 1
    }
    assert route_after_hallucination_check(state) == "end"


# 6. Tests for web_search_node
@pytest.mark.asyncio
async def test_web_search_node_no_client():
    """When web_search_client is None, should skip web search and set should_fallback=True."""
    state = {"question": "What is FastAPI?", "rewritten_query": None}
    node_fn = web_search_node(None)
    result = await node_fn(state)
    assert result["web_search_results"] == []
    assert result["web_search_used"] is False
    assert result["should_fallback"] is True

@pytest.mark.asyncio
async def test_web_search_node_uses_rewritten_query():
    """Should prefer rewritten_query over question if available."""
    mock_client = MagicMock(spec=WebSearchClientBase)
    mock_client.search = AsyncMock(return_value=[])
    state = {"question": "original", "rewritten_query": "rewritten"}
    node_fn = web_search_node(mock_client)
    result = await node_fn(state)
    mock_client.search.assert_called_once_with("rewritten", num_results=5)
    assert result["web_search_used"] is True

@pytest.mark.asyncio
async def test_web_search_node_with_results():
    """When search returns results, should convert them to DocumentChunks and set relevant_docs."""
    mock_results = [
        WebSearchResult(title="FastAPI Docs", url="https://fastapi.tiangolo.com", snippet="FastAPI is a modern web framework."),
        WebSearchResult(title="Pydantic Docs", url="https://docs.pydantic.dev", snippet="Pydantic is data validation.", content="Pydantic full content here."),
    ]
    mock_client = MagicMock(spec=WebSearchClientBase)
    mock_client.search = AsyncMock(return_value=mock_results)

    state = {"question": "What is FastAPI?", "rewritten_query": None}
    node_fn = web_search_node(mock_client)
    result = await node_fn(state)

    assert result["web_search_used"] is True
    assert result["should_fallback"] is False
    assert len(result["web_search_results"]) == 2
    assert len(result["retrieved_docs"]) == 2
    assert len(result["relevant_docs"]) == 2

    # Check chunk with content field:
    # content is only used when len(content) > len(snippet)
    # "Pydantic full content here." (25 chars) < "Pydantic is data validation." (29 chars)
    # So snippet is used instead
    chunk_with_content = result["relevant_docs"][1]
    assert "Pydantic is data validation." in chunk_with_content.content

    # Check chunk without content field (uses snippet)
    chunk_without_content = result["relevant_docs"][0]
    assert "FastAPI is a modern web framework." in chunk_without_content.content

    # Check metadata
    assert chunk_without_content.source_file == "[Web] FastAPI Docs"
    assert chunk_without_content.document_id.startswith("web_")

@pytest.mark.asyncio
async def test_web_search_node_empty_results():
    """When search returns empty list, should set should_fallback=True."""
    mock_client = MagicMock(spec=WebSearchClientBase)
    mock_client.search = AsyncMock(return_value=[])
    state = {"question": "What is FastAPI?", "rewritten_query": None}
    node_fn = web_search_node(mock_client)
    result = await node_fn(state)
    assert result["web_search_results"] == []
    assert result["web_search_used"] is True
    assert result["should_fallback"] is True

@pytest.mark.asyncio
async def test_web_search_node_exception():
    """When search raises exception, should gracefully return fallback."""
    mock_client = MagicMock(spec=WebSearchClientBase)
    mock_client.search = AsyncMock(side_effect=Exception("Network error"))
    state = {"question": "What is FastAPI?", "rewritten_query": None}
    node_fn = web_search_node(mock_client)
    result = await node_fn(state)
    assert result["web_search_results"] == []
    assert result["web_search_used"] is True
    assert result["should_fallback"] is True

# 7. Tests for DuckDuckGoSearchClient
@pytest.mark.asyncio
async def test_duckduckgo_search_api_success():
    """Test DuckDuckGo API JSON response parsing."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "AbstractText": "FastAPI is a modern web framework for building APIs.",
        "AbstractURL": "https://fastapi.tiangolo.com",
        "AbstractSource": "Wikipedia",
        "RelatedTopics": [
            {"Text": "Pydantic - Data validation", "FirstURL": "https://pydantic.dev"},
            {"Text": "Uvicorn - ASGI server", "FirstURL": "https://uvicorn.org"},
        ]
    }

    client = DuckDuckGoSearchClient()
    with patch.object(client, "client") as mock_http:
        mock_http.get = AsyncMock(return_value=mock_response)
        results = await client.search("FastAPI", num_results=3)

    assert len(results) == 3
    assert results[0].title == "Wikipedia"
    assert results[0].url == "https://fastapi.tiangolo.com"
    assert "FastAPI is a modern web framework" in results[0].snippet
    assert results[1].title == "Pydantic - Data validation"
    assert results[2].title == "Uvicorn - ASGI server"

    await client.close()

@pytest.mark.asyncio
async def test_duckduckgo_search_api_fallback_to_html():
    """When API returns no results, should fall back to HTML scraping."""
    mock_api_response = MagicMock()
    mock_api_response.status_code = 200
    mock_api_response.json.return_value = {
        "AbstractText": "",
        "AbstractURL": "",
        "RelatedTopics": []
    }

    mock_html_response = MagicMock()
    mock_html_response.status_code = 200
    mock_html_response.text = """
    <html>
        <div class="result">
            <h2 class="result__title"><a href="https://example.com/page1">Result 1</a></h2>
            <p class="result__snippet">Snippet content 1</p>
        </div>
        <div class="result">
            <h2 class="result__title"><a href="https://example.com/page2">Result 2</a></h2>
            <p class="result__snippet">Snippet content 2</p>
        </div>
    </html>
    """

    client = DuckDuckGoSearchClient()
    with patch.object(client, "client") as mock_http:
        mock_http.get = AsyncMock(side_effect=[mock_api_response, mock_html_response])
        results = await client.search("FastAPI", num_results=3)

    assert len(results) == 2
    assert results[0].title == "Result 1"
    assert results[1].title == "Result 2"

    await client.close()

@pytest.mark.asyncio
async def test_duckduckgo_search_api_failure_then_html_failure():
    """When both API and HTML scraping fail, should return empty list."""
    client = DuckDuckGoSearchClient()
    with patch.object(client, "client") as mock_http:
        mock_http.get = AsyncMock(side_effect=Exception("Network error"))
        results = await client.search("FastAPI", num_results=3)

    assert results == []
    await client.close()

# 8. Tests for WebSearchResult model
def test_web_search_result_model():
    """Test WebSearchResult Pydantic model creation."""
    result = WebSearchResult(
        title="Test Title",
        url="https://example.com",
        snippet="Test snippet"
    )
    assert result.title == "Test Title"
    assert result.url == "https://example.com"
    assert result.snippet == "Test snippet"
    assert result.content is None

    result_with_content = WebSearchResult(
        title="Test",
        url="https://example.com",
        snippet="snippet",
        content="Full content here"
    )
    assert result_with_content.content == "Full content here"
