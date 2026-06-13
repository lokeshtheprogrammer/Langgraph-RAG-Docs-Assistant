# RAG Systems Best Practices

Retrieval-Augmented Generation (RAG) combines search retrieval with generative LLMs to answer questions using private data. Optimizing these systems requires balancing chunking, embedding quality, and validation.

## Chunking Strategies
- **Fixed-size chunking**: Splitting text into fixed character bounds. Easy but risks breaking words or sentences mid-thought.
- **Recursive chunking**: Splitting hierarchically by structural markers like paragraphs, sentences, and words. Preserves context coherence.
- **Semantic chunking**: Splitting based on semantic distance between sentences using embedding shifts. Highly precise but slow.

## Evaluation Metrics (Ragas Framework)
1. **Faithfulness / Groundedness**: Is the answer derived strictly from the retrieved context? Detects hallucinations.
2. **Answer Relevance**: Does the generated response directly address the user's question?
3. **Context Recall**: Did the retrieval node fetch all necessary document information to answer the question?
4. **Context Precision**: What fraction of the retrieved chunks are actually relevant to the user query?

## Advanced Ingestion Techniques
- **Metadata tagging**: Storing document attributes (author, date, heading) along with text chunks to enable metadata filtering during vector searches.
- **Query expansion**: Rewriting user queries to cover synonyms and abbreviations before querying the vector database.
