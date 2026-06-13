# ChromaDB — Complete Documentation Reference

Source: https://docs.trychroma.com/

---

## What is ChromaDB?

ChromaDB is an open-source, AI-native vector database designed for building applications with embeddings. It is the most popular embedding database for Python and is used extensively in RAG (Retrieval-Augmented Generation) applications.

ChromaDB stores, indexes, and queries vector embeddings alongside their associated metadata and documents. It supports both in-memory and persistent storage.

### Key features

- **Simple Python API**: Minimal setup with an intuitive interface.
- **Embedded and client-server modes**: Run in-process or as a standalone server.
- **Metadata filtering**: Filter search results with arbitrary metadata.
- **Multiple embedding functions**: Integrates with OpenAI, Cohere, HuggingFace, Google, and more.
- **Multimodal**: Supports text, images, and other modalities.
- **LangChain integration**: First-class integration with LangChain and LlamaIndex.

---

## Installation

```bash
pip install chromadb
```

---

## Quick Start

```python
import chromadb

# Create a client (in-memory)
client = chromadb.Client()

# Create a collection
collection = client.create_collection("my_docs")

# Add documents
collection.add(
    documents=["FastAPI is a modern Python web framework", 
               "ChromaDB is a vector database"],
    ids=["doc1", "doc2"],
    metadatas=[{"source": "fastapi_docs"}, {"source": "chroma_docs"}]
)

# Query
results = collection.query(
    query_texts=["What is FastAPI?"],
    n_results=2
)
```

---

## Client Types

### In-Memory Client (ephemeral)

```python
client = chromadb.Client()
# Data is lost when the Python process ends
```

### Persistent Client

```python
client = chromadb.PersistentClient(path="./chroma_db")
# Data is saved to disk at the specified path
```

### HTTP Client (remote server)

```python
client = chromadb.HttpClient(host="localhost", port=8000)
# Connect to a running ChromaDB server
```

### Start server

```bash
chroma run --path ./chroma_db --port 8000
```

---

## Collections

Collections are the primary organizational unit in ChromaDB — similar to a table in a relational database or an index in a search engine.

### Create a collection

```python
# Default: cosine distance metric
collection = client.create_collection("my_collection")

# Custom distance metric
collection = client.create_collection(
    name="my_collection",
    metadata={"hnsw:space": "cosine"}   # or "l2", "ip"
)
```

### Get or create

```python
collection = client.get_or_create_collection("my_collection")
```

### List and delete

```python
client.list_collections()
client.delete_collection("my_collection")
```

---

## Adding Documents

### With auto-generated embeddings

If you pass `documents`, ChromaDB uses its default embedding function (sentence-transformers) to generate embeddings:

```python
collection.add(
    documents=["This is document 1", "This is document 2"],
    ids=["id1", "id2"],
    metadatas=[{"source": "web"}, {"source": "pdf"}]
)
```

### With pre-computed embeddings

```python
collection.add(
    embeddings=[[0.1, 0.2, 0.3, ...], [0.4, 0.5, 0.6, ...]],
    documents=["doc1", "doc2"],
    ids=["id1", "id2"]
)
```

### Upsert (add or update)

```python
collection.upsert(
    documents=["Updated document text"],
    ids=["id1"]
)
```

---

## Querying

### Basic semantic search

```python
results = collection.query(
    query_texts=["What is a vector database?"],
    n_results=5
)

# Results structure
print(results["ids"])        # [["id1", "id3", ...]]
print(results["documents"])  # [["doc text", ...]]
print(results["distances"])  # [[ 0.12, 0.45, ...]]  (lower = more similar for L2/cosine)
print(results["metadatas"])  # [[{"source": "..."}, ...]]
```

### With pre-computed query embedding

```python
results = collection.query(
    query_embeddings=[[0.1, 0.2, 0.3, ...]],
    n_results=3
)
```

### Include specific fields

```python
results = collection.query(
    query_texts=["query"],
    n_results=5,
    include=["documents", "metadatas", "distances", "embeddings"]
)
```

---

## Metadata Filtering

ChromaDB supports rich metadata filtering using a `where` clause:

### Equality and comparison

```python
# Equal
results = collection.query(
    query_texts=["query"],
    where={"source": "fastapi_docs"}
)

# Not equal
where={"source": {"$ne": "old_docs"}}

# Greater / less than
where={"year": {"$gt": 2022}}
where={"page_count": {"$lte": 100}}
```

### Logical operators

```python
# AND — both conditions must match
where={
    "$and": [
        {"source": "fastapi_docs"},
        {"year": {"$gte": 2023}}
    ]
}

# OR — either condition must match
where={
    "$or": [
        {"source": "fastapi_docs"},
        {"source": "pydantic_docs"}
    ]
}
```

### In / not in

```python
where={"source": {"$in": ["fastapi_docs", "langgraph_docs"]}}
where={"source": {"$nin": ["old_docs"]}}
```

---

## Document Content Filtering

Filter by text content with `where_document`:

```python
results = collection.query(
    query_texts=["query"],
    where_document={"$contains": "FastAPI"}
)
```

---

## Embedding Functions

### Default (sentence-transformers)

```python
# Uses all-MiniLM-L6-v2 by default
collection = client.create_collection("my_collection")
```

### OpenAI embeddings

```python
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

ef = OpenAIEmbeddingFunction(api_key="sk-...", model_name="text-embedding-3-small")
collection = client.create_collection("my_collection", embedding_function=ef)
```

### Google Generative AI embeddings

```python
from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction

ef = GoogleGenerativeAiEmbeddingFunction(api_key="...", model_name="models/embedding-001")
collection = client.create_collection("my_collection", embedding_function=ef)
```

### HuggingFace local embeddings

```python
from chromadb.utils.embedding_functions import HuggingFaceEmbeddingFunction

ef = HuggingFaceEmbeddingFunction(api_key="hf_...", model_name="sentence-transformers/all-MiniLM-L6-v2")
```

### Custom embedding function

```python
from chromadb import EmbeddingFunction, Embeddings

class MyEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: list[str]) -> Embeddings:
        # Call your embedding API
        return my_model.encode(input).tolist()
```

---

## ChromaDB with LangChain

```python
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Create embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Create or load a ChromaDB vector store
vectorstore = Chroma(
    collection_name="langchain_docs",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

# Add documents
vectorstore.add_texts(
    texts=["Document 1 content", "Document 2 content"],
    metadatas=[{"source": "doc1.md"}, {"source": "doc2.md"}]
)

# Similarity search
docs = vectorstore.similarity_search("What is LangChain?", k=5)

# Similarity search with scores
docs_with_scores = vectorstore.similarity_search_with_score("query", k=3)
for doc, score in docs_with_scores:
    print(f"Score: {score:.4f} — {doc.page_content[:100]}")

# As retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
```

---

## Distance Metrics

| Metric | Symbol | Description | Best for |
|---|---|---|---|
| Cosine | `cosine` | Angle between vectors (0=identical, 2=opposite) | Text similarity |
| L2 (Euclidean) | `l2` | Straight-line distance | Normalized embeddings |
| Inner Product | `ip` | Dot product (higher=more similar) | Recommendation systems |

Default: `l2`

For text retrieval, `cosine` is typically preferred as it is invariant to vector magnitude.

---

## CRUD Operations

### Get by ID

```python
result = collection.get(ids=["id1", "id2"])
```

### Get all documents

```python
all_docs = collection.get()
```

### Update documents

```python
collection.update(
    ids=["id1"],
    documents=["Updated document text"],
    metadatas=[{"source": "updated"}]
)
```

### Delete documents

```python
collection.delete(ids=["id1", "id2"])
# Delete by filter
collection.delete(where={"source": "old_source"})
```

### Count documents

```python
count = collection.count()
```

---

## Peek at a Collection

```python
# Preview first 10 documents
sample = collection.peek(limit=10)
print(sample["ids"])
print(sample["documents"])
```

---

## ChromaDB in RAG Architecture

```
User Query
    ↓
Embed query → [0.12, -0.34, ...]
    ↓
ChromaDB.query(embedding, n_results=5)
    ↓
Top-K similar chunks + distances
    ↓
Filter by relevance threshold
    ↓
Build context string
    ↓
LLM Generation with context
    ↓
Answer with citations
```

---

## Production Considerations

- **Index type**: ChromaDB uses HNSW (Hierarchical Navigable Small World) for approximate nearest neighbor search.
- **Scaling**: For very large datasets (>1M docs), consider Weaviate, Qdrant, or Pinecone.
- **Persistence**: Always use `PersistentClient` in production.
- **Batch size**: Add documents in batches of ~1000 for performance.
- **Embedding dimension**: All embeddings in a collection must have the same dimension.
