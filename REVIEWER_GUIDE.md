# Express Analytics AI/ML Engineer Intern Take-Home - Reviewer Guide (5-Minute Walkthrough)

Welcome, Reviewer! This guide is designed to help you verify all core features, bonus capabilities, and architectural components of this self-corrective RAG submission in **less than 5 minutes**.

---

### 🚀 Zero-Setup Review (Fastest)
This application is fully containerized and deployed on **Hugging Face Spaces**! You can test it immediately without running anything locally:
- **Live Streamlit App:** [RAG Documentation Assistant on Hugging Face Spaces](https://huggingface.co/spaces/lokeshtheprogrammer/Langgraph-RAG-Docs-Assistant)

---

## 🏗️ Architecture Overview

```text
User Query
    ↓
Query Analysis
    ↓
Hybrid Retrieval (BM25 + ChromaDB)
    ↓
Cross-Encoder Re-Ranking
    ↓
Document Grading
    ↓
Query Rewrite (Retry Loop)
    ↓
Web Search Fallback (if needed)
    ↓
Answer Generation
    ↓
Hallucination Check
    ↓
Response with Citations
```

---

## 📋 Assignment Coverage Table

| Assignment Requirement | Status |
|---|---|
| Query Analysis Node | ✅ |
| Retrieval Node | ✅ |
| Document Grading Node | ✅ |
| Generation Node | ✅ |
| Conditional Routing | ✅ |
| Document Ingestion | ✅ |
| Chunking Strategy | ✅ |
| Embeddings | ✅ |
| ChromaDB Vector Store | ✅ |
| FastAPI APIs | ✅ |

### Bonus & Advanced Features
| Feature | Status |
|---|---|
| Hallucination Check | ✅ |
| Conversation Memory | ✅ |
| Streamlit UI | ✅ |
| Web Search Fallback | ✅ |
| Hybrid Search (BM25 + Vector) | ✅ |
| Cross-Encoder Re-Ranking | ✅ |

---

## 🌟 Key Differentiators

* **Self-Corrective LangGraph Workflow:** Employs cycles to retry and self-heal when retrieval is irrelevant or hallucinated.
* **Query Rewrite Retry Loop:** Refines search queries dynamically.
* **Hallucination Grounding Validation:** Double-checks generated responses against context facts.
* **Web Search Fallback:** DDG fallback when database has zero relevant chunks.
* **Hybrid Search (BM25 + Vector):** High precision via reciprocal rank fusion.
* **Cross-Encoder Re-Ranking:** Candidates re-ordered using transformer cross-encoders.
* **Conversation Memory:** Session-based SQLite logs for contextual follow-up.
* **Retrieval Transparency Dashboard:** Cosine distance logging and debug traces.
* **Source Preview System:** 300-char context snippets in native Streamlit expanders.
* **Fully Deployed Demo:** Accessible instantly on Hugging Face Spaces.

---

## 💬 Direct Demo Queries (Copy-Paste)

* **FastAPI:** `What is FastAPI?`
* **Pydantic:** `What is BaseModel?`
* **LangGraph:** `What is a StateGraph?`
* **Uploaded Reference:** `List all API endpoints` (from `API_SPECIFICATION.md`)
* **Fallback (Web Search):** `What is Anthropic's Model Context Protocol (MCP)?`
* **Conversation Memory:** (First ask: `What is FastAPI?` then follow up with): `Who created it?`

---

## Prerequisites
Please ensure your Python version is **3.11+** and you have a valid **Google Gemini API Key** (or Groq API Key).

---

## Step 1: Clone and Start the Backend (1 Minute)

1. Open a terminal in the project root:
   ```powershell
   # 1. Activate the virtual environment
   .\venv\Scripts\activate  # On Windows PowerShell
   # OR: source venv/bin/activate on macOS/Linux

   # 2. Make sure dependencies are installed (including rank_bm25 and sentence-transformers)
   pip install -r requirements.txt
   ```
2. Set up your `.env` file in the root directory:
   ```ini
   LLM_PROVIDER=google
   LLM_MODEL=gemini-2.5-flash
   GEMINI_API_KEY=your_gemini_api_key_here
   CHROMA_PERSIST_DIR=./chroma_db
   SQLITE_DB_PATH=./data/app.db
   WEB_SEARCH_ENABLED=true
   WEB_SEARCH_PROVIDER=duckduckgo
   ```
3. Run the FastAPI backend:
   ```powershell
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   *Verify backend is active at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).*

---

## Step 2: Start the Streamlit UI (30 Seconds)

1. Open a **second terminal** in the project root:
   ```powershell
   .\venv\Scripts\activate
   streamlit run streamlit_app.py
   ```
2. Your browser should automatically open to [http://localhost:8501](http://localhost:8501).

---

## Step 3: Ingest a New Document & View Ingestion Checklist (1 Minute)

1. On the landing page or sidebar, upload a document (e.g. `API_SPECIFICATION.md` or any PDF/TXT file).
2. Observe the **auto-ingestion spinner** activate.
3. Upon success, look at the sidebar focus indicator. You will see a detailed **3-step ingestion checklist**:
   - `✓ File uploaded`
   - `✓ [N] chunks indexed`
   - `✓ Ready to query!`
4. In the document center dropdown, you will see your file listed. Click `🗑️` next to any file if you wish to test deletion.

---

## Step 4: Ask a Document-Specific Question (1 Minute)

1. Ask a question directly related to your uploaded file (e.g., if you uploaded `API_SPECIFICATION.md`, ask: *"What are the parameters for the POST /query endpoint?"*).
2. The UI will display a **green Focus Pill** showing that search is restricted only to your active file, preventing cross-document noise.
3. Look at the response:
   - Click the source expanders (e.g., `📄 API_SPECIFICATION.md #0`) under the response bubble.
   - Observe the **300-character source excerpt** previewing the exact context segment retrieved from the document database.

---

## Step 5: Verify the LangGraph Debug Trace (30 Seconds)

1. Expand the **◈ Retrieval trace** panel below the chatbot response.
2. Observe:
   - **Query Type:** (Conceptual, coding, conversational)
   - **Latency:** Execution time in milliseconds
   - **Grounding Progress Bar:** Groundedness score (verifying hallucination check evaluation)
   - **Retrieved & Graded Chunks:** Details of each retrieved chunk, showing its **ChromaDB distance score** and relevance grade.

---

## Step 6: Test Web Search Fallback (30 Seconds)

1. In the sidebar, click the `✕ Search All Documents` button to clear focus.
2. Ask a question outside the documentation corpus (e.g., *"Who won the last soccer world cup?"* or *"What is Anthropic's Model Context Protocol?"*).
3. Under the hood, LangGraph will:
   - Perform retrieval from the database (find 0 relevant chunks).
   - Attempt a query rewrite and re-retrieval up to max retries.
   - Automatically fall back to **Web Search via DuckDuckGo**.
   - Synthesize a comprehensive answer citing web URLs in the source expanders.

---

## Step 7: Test Conversation Memory (30 Seconds)

1. Ask: *"What is FastAPI?"*
2. Once answered, ask a follow-up question that relies on context: *"Who created it?"*
3. The RAG assistant will query SQLite conversation turns history, augment the query context, and correctly answer *"Sebastián Ramírez"* by resolving the pronoun "it".

---

Thank you for reviewing! For full details on database design, routing logic, or prompt templates, refer to [README.md](file:///c:/Users/aimpr/Downloads/RAG/README.md) or [REQUIREMENTS_MAPPING.md](file:///c:/Users/aimpr/Downloads/RAG/REQUIREMENTS_MAPPING.md).
