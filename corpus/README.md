# Document Corpus

This directory contains the source documents used for the RAG assistant.

## Documents

| File | Description |
|------|-------------|
| `fastapi_tutorial.md` | FastAPI getting started guide and routing documentation |
| `langchain_tools.md` | LangChain tools and toolkit documentation |
| `langgraph_concepts.md` | LangGraph StateGraph and node concepts |
| `pydantic_v2.md` | Pydantic v2 models and validation documentation |

## Adding Documents

Add Markdown (`.md`), Text (`.txt`), HTML (`.html`), or PDF (`.pdf`) files to this directory,
then run the ingestion script:

```bash
python -m ingestion.ingest_corpus
```

Or upload via the API:

```bash
curl -X POST -F "file=@path/to/document.md" http://localhost:8000/ingest
```
