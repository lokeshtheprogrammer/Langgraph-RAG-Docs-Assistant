"""
RAG Technical Documentation Assistant - Streamlit UI
Interactive interface with retrieval debug panel for the self-corrective RAG pipeline.
"""

import streamlit as st
import requests
import uuid
import json
import time

# ─── Configuration ───────────────────────────────────────────────────────────
API_BASE = "http://127.0.0.1:8000"

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Documentation Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main theme */
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
    }
    
    /* Chat message styling */
    .user-msg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        font-size: 0.95rem;
    }
    .bot-msg {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #e0e0e0;
        padding: 14px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 85%;
        font-size: 0.95rem;
        backdrop-filter: blur(10px);
    }
    
    /* Debug panel */
    .debug-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }
    .debug-header {
        color: #667eea;
        font-weight: 600;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    
    /* Chunk cards */
    .chunk-card {
        background: rgba(102, 126, 234, 0.08);
        border-left: 3px solid #667eea;
        padding: 10px 14px;
        margin: 6px 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.82rem;
    }
    .chunk-relevant {
        border-left-color: #27ae60;
        background: rgba(39, 174, 96, 0.08);
    }
    .chunk-irrelevant {
        border-left-color: #e74c3c;
        background: rgba(231, 76, 60, 0.08);
    }
    
    /* Status badges */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-success { background: rgba(39, 174, 96, 0.2); color: #27ae60; }
    .badge-warning { background: rgba(230, 126, 34, 0.2); color: #e67e22; }
    .badge-error { background: rgba(231, 76, 60, 0.2); color: #e74c3c; }
    .badge-info { background: rgba(102, 126, 234, 0.2); color: #667eea; }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: rgba(15, 15, 35, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* Metric cards */
    .metric-row {
        display: flex;
        gap: 12px;
        margin: 8px 0;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 12px 16px;
        flex: 1;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-label {
        font-size: 0.72rem;
        color: rgba(255,255,255,0.5);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ──────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "debug_traces" not in st.session_state:
    st.session_state.debug_traces = []

# ─── Helper Functions ────────────────────────────────────────────────────────
def check_api_health():
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def query_rag(question: str, top_k: int = 5, max_retries: int = 2):
    payload = {
        "question": question,
        "session_id": st.session_state.session_id,
        "top_k": top_k,
        "max_retries": max_retries
    }
    try:
        r = requests.post(f"{API_BASE}/query", json=payload, timeout=120)
        if r.status_code == 200:
            return r.json()
        else:
            return {"error": f"API returned status {r.status_code}: {r.text}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to FastAPI backend. Is the server running on port 8000?"}
    except Exception as e:
        return {"error": str(e)}

def upload_document(file):
    try:
        files = {"file": (file.name, file.getvalue(), file.type or "application/octet-stream")}
        r = requests.post(f"{API_BASE}/ingest", files=files, timeout=60)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_documents():
    try:
        r = requests.get(f"{API_BASE}/documents", timeout=10)
        return r.json() if r.status_code == 200 else {"documents": []}
    except Exception:
        return {"documents": []}

def get_metrics():
    try:
        r = requests.get(f"{API_BASE}/metrics", timeout=10)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}

def submit_feedback(query_text, answer_text, rating):
    payload = {
        "query": query_text,
        "answer": answer_text,
        "rating": rating,
        "session_id": st.session_state.session_id
    }
    try:
        requests.post(f"{API_BASE}/feedback", json=payload, timeout=10)
    except Exception:
        pass

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 RAG Assistant")
    st.caption("Self-Corrective Documentation Copilot")
    
    # API Status
    api_up = check_api_health()
    if api_up:
        st.success("✅ API Connected", icon="🟢")
    else:
        st.error("❌ API Offline — Start FastAPI server first", icon="🔴")
    
    st.divider()
    
    # ─── Document Upload ─────────────────────────────────────────────────
    st.markdown("### 📄 Upload Document")
    uploaded_file = st.file_uploader(
        "Drop a file to ingest",
        type=["md", "txt", "pdf"],
        help="Supported formats: Markdown, Text, PDF"
    )
    if uploaded_file and st.button("⬆️ Ingest", use_container_width=True):
        with st.spinner("Ingesting document..."):
            result = upload_document(uploaded_file)
        if "error" in result:
            st.error(f"Failed: {result['error']}")
        else:
            status = result.get("status", "unknown")
            chunks = result.get("chunk_count", 0)
            if status == "indexed":
                st.success(f"✅ Indexed — {chunks} chunks created")
            elif result.get("duplicate"):
                st.warning("⚠️ Duplicate — already indexed")
            else:
                st.info(f"Status: {status}")
    
    st.divider()
    
    # ─── Corpus Browser ──────────────────────────────────────────────────
    st.markdown("### 📚 Indexed Corpus")
    docs_data = get_documents()
    docs_list = docs_data.get("documents", [])
    if docs_list:
        for doc in docs_list:
            fname = doc.get("filename", "unknown")
            chunks = doc.get("chunk_count", 0)
            status = doc.get("status", "unknown")
            st.markdown(f"📄 **{fname}** — `{chunks} chunks` · `{status}`")
    else:
        st.caption("No documents indexed yet.")
    
    st.divider()
    
    # ─── System Metrics ──────────────────────────────────────────────────
    st.markdown("### 📊 System Metrics")
    metrics = get_metrics()
    if metrics:
        col1, col2 = st.columns(2)
        col1.metric("Documents", metrics.get("total_documents", 0))
        col2.metric("Chunks", metrics.get("total_chunks", 0))
        col1.metric("Feedback 👍", metrics.get("feedback_positive", 0))
        col2.metric("Feedback 👎", metrics.get("feedback_negative", 0))
        st.metric("Avg Response", f"{metrics.get('average_response_time_ms', 0)}ms")
    else:
        st.caption("Metrics unavailable.")
    
    st.divider()
    
    # ─── Query Settings ──────────────────────────────────────────────────
    st.markdown("### ⚙️ Settings")
    top_k = st.slider("Top-K Chunks", 1, 20, 5)
    max_retries = st.slider("Max Retries", 0, 5, 2)
    show_debug = st.toggle("Show Debug Panel", value=True)
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.debug_traces = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

# ─── Main Chat Area ──────────────────────────────────────────────────────────
st.markdown("# 🤖 RAG Documentation Assistant")
st.caption("Ask questions about your indexed technical documentation. The system retrieves, grades, and generates grounded answers.")

# Display chat history
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(f'<div class="user-msg">💬 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-msg">{msg["content"]}</div>', unsafe_allow_html=True)
        
        # Show debug panel for this message
        if show_debug and i < len(st.session_state.debug_traces):
            trace = st.session_state.debug_traces[i]
            if trace:
                with st.expander(f"🔍 Retrieval Debug Trace", expanded=False):
                    st.markdown("Debug info displayed inline below.")

# Chat input
question = st.chat_input("Ask a question about your documentation...", disabled=not api_up)

if question:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})
    st.session_state.debug_traces.append(None)  # placeholder for user msg
    
    # Display user message
    st.markdown(f'<div class="user-msg">💬 {question}</div>', unsafe_allow_html=True)
    
    # Query the API
    with st.spinner("🔄 Analyzing query, retrieving context, grading relevance..."):
        result = query_rag(question, top_k=top_k, max_retries=max_retries)
    
    if "error" in result:
        answer = f"⚠️ Error: {result['error']}"
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.debug_traces.append(None)
        st.markdown(f'<div class="bot-msg">{answer}</div>', unsafe_allow_html=True)
    else:
        answer = result.get("answer", "No response generated.")
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.debug_traces.append(result)
        
        # Display answer
        st.markdown(f'<div class="bot-msg">{answer}</div>', unsafe_allow_html=True)
        
        # Sources
        sources = result.get("sources", [])
        if sources:
            st.markdown("**📎 Sources:**")
            for src in sources:
                st.markdown(f"- `{src['source_file']}` (chunk #{src['chunk_index']})")
        
        # Feedback buttons
        col1, col2, col3 = st.columns([1, 1, 6])
        with col1:
            if st.button("👍", key=f"pos_{len(st.session_state.messages)}", help="Helpful"):
                submit_feedback(question, answer, "positive")
                st.toast("✅ Thanks for the feedback!", icon="👍")
        with col2:
            if st.button("👎", key=f"neg_{len(st.session_state.messages)}", help="Not helpful"):
                submit_feedback(question, answer, "negative")
                st.toast("📝 Feedback recorded", icon="👎")
        
        # Debug Panel
        if show_debug:
            st.divider()
            st.markdown("### 🔍 Retrieval Debug Panel")
            
            # ── Flow Summary ──
            is_fallback = result.get("is_fallback", False)
            retry_count = result.get("retry_count", 0)
            response_time = result.get("response_time_ms", 0)
            halluc_score = result.get("hallucination_score")
            query_type = result.get("query_type", "unknown")
            rewritten = result.get("rewritten_query", question)
            
            # Status row
            cols = st.columns(5)
            cols[0].markdown(f"**Query Type**<br/>`{query_type}`", unsafe_allow_html=True)
            cols[1].markdown(f"**Retries**<br/>`{retry_count}`", unsafe_allow_html=True)
            cols[2].markdown(f"**Fallback**<br/>{'🔴 Yes' if is_fallback else '🟢 No'}", unsafe_allow_html=True)
            cols[3].markdown(f"**Grounding**<br/>`{halluc_score:.2f}`" if halluc_score is not None else "**Grounding**<br/>`N/A`", unsafe_allow_html=True)
            cols[4].markdown(f"**Latency**<br/>`{response_time}ms`", unsafe_allow_html=True)
            
            # ── Execution Flow ──
            st.markdown("#### 📋 Execution Flow")
            
            flow_col1, flow_col2 = st.columns([1, 1])
            
            with flow_col1:
                st.markdown(f"""
<div class="debug-card">
<div class="debug-header">❓ Original Question</div>
<div>{question}</div>
</div>
""", unsafe_allow_html=True)
                
                if rewritten != question:
                    st.markdown(f"""
<div class="debug-card">
<div class="debug-header">🔄 Rewritten Query</div>
<div>{rewritten}</div>
</div>
""", unsafe_allow_html=True)
            
            with flow_col2:
                st.markdown(f"""
<div class="debug-card">
<div class="debug-header">✨ Final Answer</div>
<div>{answer[:300]}{'...' if len(answer) > 300 else ''}</div>
</div>
""", unsafe_allow_html=True)
            
            # ── Retrieved Chunks ──
            retrieved = result.get("retrieved_chunks", [])
            if retrieved:
                st.markdown(f"#### 📚 Retrieved Chunks ({len(retrieved)})")
                for idx, chunk in enumerate(retrieved):
                    st.markdown(f"""
<div class="chunk-card">
<strong>Chunk #{chunk.get('chunk_index', idx)}</strong> from <code>{chunk.get('source_file', 'unknown')}</code><br/>
<span style="color: rgba(255,255,255,0.7);">{chunk.get('content', '')[:200]}...</span>
</div>
""", unsafe_allow_html=True)
            
            # ── Graded Chunks ──
            graded = result.get("graded_chunks", [])
            if graded:
                relevant_count = sum(1 for c in graded if c.get("grade") == "relevant")
                irrelevant_count = len(graded) - relevant_count
                
                st.markdown(f"#### ⚖️ Document Grading — {relevant_count} relevant, {irrelevant_count} irrelevant")
                for chunk in graded:
                    grade = chunk.get("grade", "unknown")
                    css_class = "chunk-relevant" if grade == "relevant" else "chunk-irrelevant"
                    icon = "✅" if grade == "relevant" else "❌"
                    st.markdown(f"""
<div class="chunk-card {css_class}">
{icon} <strong>{grade.upper()}</strong> — Chunk #{chunk.get('chunk_index', '?')} from <code>{chunk.get('source_file', 'unknown')}</code><br/>
<span style="color: rgba(255,255,255,0.6);">{chunk.get('content', '')[:150]}...</span>
</div>
""", unsafe_allow_html=True)
            
            # ── Hallucination Check ──
            if halluc_score is not None:
                st.markdown("#### 🛡️ Hallucination Check")
                score_pct = halluc_score * 100
                if halluc_score >= 0.8:
                    st.progress(halluc_score, text=f"Grounding Score: {score_pct:.0f}% ✅ Well-grounded")
                elif halluc_score >= 0.5:
                    st.progress(halluc_score, text=f"Grounding Score: {score_pct:.0f}% ⚠️ Partially grounded")
                else:
                    st.progress(halluc_score, text=f"Grounding Score: {score_pct:.0f}% ❌ Poorly grounded")
    
    st.rerun()

# ─── Empty State ─────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px; color: rgba(255,255,255,0.4);">
        <div style="font-size: 4rem; margin-bottom: 16px;">🤖</div>
        <div style="font-size: 1.2rem; margin-bottom: 8px;">Ask me anything about your documentation</div>
        <div style="font-size: 0.85rem;">
            Try: <em>"What is FastAPI?"</em> · <em>"Explain LangGraph concepts"</em> · <em>"How does Pydantic v2 work?"</em>
        </div>
    </div>
    """, unsafe_allow_html=True)
