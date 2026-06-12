# AI_ENGINEERING.md — AI Engineering Document
## RAG-Based Technical Documentation Assistant

**Version:** 1.0.0
**Date:** 2025-06-11

---

## RAG Strategy

This system implements **Corrective RAG (CRAG)** — a variant of standard RAG that adds a self-correction loop. The core insight is that naive RAG trusts whatever the vector store returns; CRAG validates retrieved documents and discards irrelevant ones before generation.

**Pipeline summary:**
1. Query is rewritten/expanded for better vector search coverage
2. Top-K chunks retrieved via cosine similarity
3. Each chunk independently graded by an LLM
4. Irrelevant chunks discarded
5. If no relevant chunks remain, query is rewritten and retrieval retried (max N times)
6. Generation is performed only on the validated, relevant subset

**Why CRAG over standard RAG?**

Standard RAG would generate an answer even when the retrieved chunks are completely irrelevant to the query. This causes hallucinations. CRAG's grading step acts as a quality gate. The tradeoff is additional LLM calls for grading — approximately K calls per retrieval cycle (where K = top_k, default 5).

---

## Embedding Strategy

**Primary model:** `sentence-transformers/all-MiniLM-L6-v2`

- Vector dimension: 384
- Max sequence length: 256 tokens
- Runs locally (no API dependency)
- Trained on 1B+ sentence pairs for semantic similarity
- Average benchmark: 68.1 SBERT average on STS tasks

**Secondary model (configurable):** `text-embedding-3-small` (OpenAI)

- Vector dimension: 1536
- Significantly better on domain-specific vocabulary
- Cost: ~$0.02 per 1M tokens (negligible for prototype)

**Consistency requirement:** The embedding model used at ingestion time MUST match the model used at query time. A model fingerprint is stored in ChromaDB collection metadata and validated at startup.

```python
# Validate embedding consistency
def validate_embedding_model(collection, expected_model: str):
    stored_model = collection.metadata.get("embedding_model")
    if stored_model and stored_model != expected_model:
        raise RuntimeError(
            f"Embedding model mismatch: collection uses '{stored_model}', "
            f"but config specifies '{expected_model}'. "
            "Re-ingest documents or update configuration."
        )
```

---

## Chunking Strategy

### Chosen Strategy: Recursive Character Text Splitter

**Implementation:**

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=64,
    separators=["\n\n", "\n", "```", ".", " ", ""],
    length_function=len,
    is_separator_regex=False,
)
```

### Why Recursive Character Text Splitter?

The `RecursiveCharacterTextSplitter` attempts to split on semantically meaningful boundaries in order: double newlines (paragraph breaks), single newlines, code fences, sentences, words, characters. This ensures chunks respect natural document structure rather than cutting mid-sentence or mid-code-block.

**Alternative considered:** `MarkdownHeaderTextSplitter` — splits on # headers, which is semantically ideal for markdown docs. However, it requires clean markdown formatting and produces variable-length chunks.

**Recommendation:** Use `MarkdownHeaderTextSplitter` as a pre-pass on markdown documents, then apply `RecursiveCharacterTextSplitter` as a secondary splitter for chunks that exceed the size limit.

```python
# Hybrid approach for .md files
from langchain_text_splitters import MarkdownHeaderTextSplitter

headers_to_split_on = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]
md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
header_splits = md_splitter.split_text(doc)

# Then apply size-based splitting if needed
chunks = splitter.split_documents(header_splits)
```

---

## Chunk Size Justification

**Chosen chunk size: 512 characters (approximately 128-150 tokens)**

| Chunk Size | Pros | Cons |
|-----------|------|------|
| 256 chars | Very precise retrieval; less noise per chunk | Context too narrow; may lose surrounding explanation |
| 512 chars | Good balance; typically one code snippet or one paragraph | — |
| 1024 chars | More context per chunk | Retrieval less precise; embedding diluted by irrelevant content |
| 2048 chars | Very high context | Exceeds many embedding model max lengths; poor retrieval precision |

Technical documentation typically contains dense paragraphs (explaining a concept) or code blocks (showing usage). A 512-character window covers one of these units cleanly.

**Empirical guidance:** For RAG on technical docs, chunks between 400-600 characters tend to perform best on precision metrics. (Source: Pinecone and LlamaIndex benchmarks on documentation corpora.)

---

## Overlap Justification

**Chosen overlap: 64 characters (approximately 16 tokens)**

Overlap ensures that concepts that span chunk boundaries are captured. Without overlap, a sentence split across two chunks would be semantically incomplete in both. 64 characters (~1-2 sentences) is sufficient to capture boundary context without significantly increasing storage or retrieval noise.

Too much overlap (e.g., 50% of chunk size) causes redundant chunks and inflates the corpus size proportionally. 64/512 = 12.5% overlap is a widely accepted default.

---

## Metadata Design

Every chunk is stored with the following metadata in the vector store:

```python
chunk_metadata = {
    "document_id": "doc_001",          # Unique ID assigned at ingestion
    "source_file": "langchain_docs.md", # Original filename
    "source_url": "https://...",        # If ingested from URL
    "chunk_index": 3,                   # 0-based position in document
    "total_chunks": 47,                 # Total chunks from this document
    "char_count": 487,                  # Length of this chunk
    "ingestion_timestamp": "2025-06-11T10:00:00Z",
    "embedding_model": "all-MiniLM-L6-v2",
    # Optional, for markdown:
    "section_header": "## Installation", # From MarkdownHeaderTextSplitter
    "section_level": 2,
}
```

Metadata is used for:
- Citation generation (source_file, chunk_index)
- Document listing (document_id, source_file)
- Filtering by document (document_id)
- Debugging (ingestion_timestamp, embedding_model)

---

## Retrieval Strategy

**Method:** Dense vector retrieval (semantic search) using cosine similarity.

**Top-K:** 5 (configurable). Rationale: 5 chunks provides enough context for generation while keeping grading cost manageable (5 LLM calls per retrieval).

**Future enhancement — Hybrid Search:**

Combine dense retrieval (semantic) with sparse retrieval (BM25/keyword) via Reciprocal Rank Fusion:

```python
# Hybrid retrieval (future)
dense_results = vector_store.similarity_search(query, k=10)
sparse_results = bm25_index.search(query, k=10)
fused = reciprocal_rank_fusion([dense_results, sparse_results], k=5)
```

This is particularly valuable for technical documentation where users may search for exact function names (`get_completion`) that semantic search might not rank highly.

---

## Re-Ranking Strategy

**MVP:** Not implemented (cost/complexity tradeoff for prototype).

**Recommended for production:** Cross-encoder re-ranking with `cross-encoder/ms-marco-MiniLM-L-6-v2`.

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query: str, chunks: List[str], top_n: int = 3) -> List[str]:
    pairs = [(query, chunk) for chunk in chunks]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
    return [chunk for chunk, score in ranked[:top_n]]
```

Cross-encoders consider the query and document jointly, producing much higher precision than bi-encoder similarity alone.

---

## Citation Strategy

Citations are generated at two levels:

**1. Source-level citations (always present):**
```
[Source: langchain_docs.md]
```

**2. Chunk-level citations (more precise):**
```
[Source: langchain_docs.md, chunk 3]
```

**Implementation in generation prompt:**

The generation prompt explicitly instructs the LLM to add `[Source: <filename>]` after each factual claim. The relevant chunks are prefixed with their source identifier before being injected into the prompt context, providing the LLM with the grounding needed to produce accurate citations.

**Post-processing validation (future):**

After generation, verify that every cited source actually exists in `state["sources"]`. If the LLM invents a source filename, flag it.

```python
def validate_citations(answer: str, valid_sources: List[str]) -> bool:
    import re
    cited = re.findall(r'\[Source: ([^\]]+)\]', answer)
    return all(cite.split(",")[0].strip() in valid_sources for cite in cited)
```

---

## Hallucination Prevention

Multiple layers of defense:

| Layer | Technique |
|-------|-----------|
| Retrieval | Only generate from validated, relevant chunks (not raw retrieval) |
| Prompt design | Explicit instruction: "Answer based ONLY on the provided context" |
| Citation enforcement | LLM instructed to cite sources for every claim |
| Grading filter | Irrelevant chunks never reach the generation step |
| Hallucination check (bonus) | Post-generation verification of factual support |
| Fallback response | When context is insufficient, return explicit "I don't know" |

The most important prevention is the grading filter — ensuring the generation LLM only sees content that has been validated as relevant.

---

## Grounding Strategy

**Context injection pattern:**

```
[Source: langchain_docs.md, chunk 3]
<chunk content>

---

[Source: fastapi_docs.md, chunk 11]
<chunk content>
```

This pattern provides the LLM with both the content and the source attribution inline, enabling accurate citation generation without post-hoc source lookup.

**Temperature:** Set to 0.0 (or near-zero) for grading and citation tasks. Higher temperature (0.3-0.7) acceptable for generation to improve fluency.

---

## Evaluation Metrics

### RAGAS Framework (Recommended)

[RAGAS](https://github.com/explodinggradients/ragas) provides automated RAG evaluation:

| Metric | Definition | Target |
|--------|-----------|--------|
| **Faithfulness** | Fraction of answer claims supported by context | ≥ 0.85 |
| **Answer Relevancy** | Semantic similarity of answer to question | ≥ 0.80 |
| **Context Precision** | Fraction of retrieved chunks that are relevant | ≥ 0.70 |
| **Context Recall** | Fraction of ground-truth facts present in retrieved context | ≥ 0.75 |

### Manual Evaluation Protocol

For each test question:
1. Is the answer factually correct? (0/1)
2. Is every claim grounded in the provided context? (0/1)
3. Are the citations accurate (pointing to real source)? (0/1)
4. Is the answer complete (covers all aspects of the question)? (0/1)

---

## LLM Selection Comparison

### Comparison Matrix

| Provider | Model | Speed | Quality | Cost | Free Tier | Best For |
|---------|-------|-------|---------|------|-----------|---------|
| **Groq** | Llama3-8b-8192 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Free | Generous | Grading, prototyping |
| **Groq** | Llama3-70b-8192 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Free | Generous | Generation |
| **OpenAI** | GPT-4o-mini | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ~$0.15/1M | PAYG | Best quality/cost |
| **OpenAI** | GPT-4o | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ~$5/1M | PAYG | Premium quality |
| **Anthropic** | Claude 3 Haiku | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ~$0.25/1M | PAYG | Instruction following |
| **Anthropic** | Claude 3.5 Sonnet | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ~$3/1M | PAYG | Best reasoning |
| **Google** | Gemini 1.5 Flash | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Free tier | Generous | Long context |
| **Google** | Gemini 1.5 Pro | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | PAYG | Limited | 1M token context |

### Detailed Provider Analysis

#### Groq
- **Strengths:** Fastest inference available (LPU hardware). Llama3-8b is excellent for structured JSON tasks like grading. Free tier covers prototype usage entirely. Zero latency means grading 5 chunks costs <2 seconds total.
- **Weaknesses:** Models are open-source Llama/Mixtral — slightly weaker instruction following than GPT-4o for complex generation tasks. Rate limits on free tier.
- **Best use case:** Document grading node (structured JSON, low complexity). Query rewriting.

#### OpenAI
- **Strengths:** GPT-4o-mini has the best quality/cost ratio of any available model. Excellent JSON mode support (`response_format={"type": "json_object"}`). Reliable function calling. Strong instruction following.
- **Weaknesses:** Costs money (though minimal). Requires internet access. Usage policies.
- **Best use case:** Generation node where answer quality is paramount.

#### Anthropic (Claude)
- **Strengths:** Best instruction-following behavior. Claude 3.5 Sonnet produces the most fluent, accurate technical answers. Excellent at following "only use the provided context" constraints (critical for hallucination prevention).
- **Weaknesses:** Higher cost than GPT-4o-mini. No JSON mode (relies on prompt engineering).
- **Best use case:** Generation node when hallucination prevention is most critical.

#### Google Gemini
- **Strengths:** Gemini 1.5 Flash has a generous free tier and 1M token context window. Good at processing long documents.
- **Weaknesses:** Slightly weaker than GPT-4o-mini on structured output tasks. API less mature.
- **Best use case:** Processing entire documents in a single context (future long-context RAG variant).

---

## Final Recommendation

**For this assignment:**

> **Primary:** Groq with `llama3-70b-8192` for both grading and generation.
>
> **Rationale:** Zero cost, generous free tier, fast enough for prototype latency requirements, sufficiently accurate for a 3-5 document corpus. This removes any barrier to running the system.

**For production:**

> **Grading:** Groq `llama3-8b-8192` (fast, cheap, structured output)
> **Generation:** OpenAI `gpt-4o-mini` (best quality/cost for end-user-facing answers)

**Configuration to support both:**

```python
# .env
GRADING_LLM_PROVIDER=groq
GRADING_LLM_MODEL=llama3-8b-8192
GENERATION_LLM_PROVIDER=openai
GENERATION_LLM_MODEL=gpt-4o-mini
```

This dual-model approach optimizes cost (cheap model for high-volume grading) and quality (better model for low-volume generation).