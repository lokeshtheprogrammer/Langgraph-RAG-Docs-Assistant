# Streamlit — Complete Documentation Reference

Source: https://docs.streamlit.io/

---

## What is Streamlit?

Streamlit is an open-source Python framework for building interactive data apps and ML demos with minimal code. You write Python and Streamlit automatically builds a web UI — no HTML, CSS, or JavaScript required.

Streamlit is widely used for:
- Machine learning model demos
- Data dashboards
- LLM and RAG application UIs
- Internal analytics tools
- Rapid prototyping

---

## Installation

```bash
pip install streamlit
streamlit hello   # Verify installation
```

Run your app:

```bash
streamlit run app.py
```

---

## How Streamlit Works

Streamlit re-runs your entire Python script from top to bottom every time:
1. The user interacts with a widget.
2. The script completes and the UI is updated.

This "rerun model" is simple but requires understanding of:
- **Caching**: To avoid re-running expensive computations.
- **Session state**: To persist values across reruns.

---

## Basic UI Elements

### Text display

```python
import streamlit as st

st.title("My App")                          # Large heading
st.header("Section Header")                 # Medium heading
st.subheader("Subsection")                  # Small heading
st.text("Fixed-width monospace text")        # Plain text
st.markdown("**Bold**, *Italic*, `code`")   # Markdown rendering
st.caption("Small greyed-out text")         # Caption
st.code("print('hello')", language="python") # Code block
st.latex(r"E = mc^2")                        # LaTeX math
```

### Data display

```python
import pandas as pd

df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
st.dataframe(df)             # Interactive table
st.table(df)                 # Static table
st.json({"key": "value"})   # JSON viewer
st.metric("Temperature", "25°C", delta="2°C")  # Metric card
```

---

## Input Widgets

```python
# Text input
name = st.text_input("Your name", placeholder="Enter name...")
message = st.text_area("Message", height=150)

# Number input
age = st.number_input("Age", min_value=0, max_value=120, value=25)

# Slider
value = st.slider("Pick a number", 0, 100, 50)
range_val = st.slider("Range", 0.0, 1.0, (0.2, 0.8))

# Selectbox (dropdown)
option = st.selectbox("Chose provider", ["Gemini", "Groq", "OpenAI"])

# Multi-select
options = st.multiselect("Select tags", ["Python", "AI", "API", "RAG"])

# Radio buttons
choice = st.radio("Mode", ["Fast", "Balanced", "Thorough"])

# Checkbox
agreed = st.checkbox("I agree to the terms")

# Toggle
dark_mode = st.toggle("Dark mode")

# Button
if st.button("Submit"):
    st.success("Submitted!")

# Date/time
date = st.date_input("Pick a date")
time = st.time_input("Pick a time")

# File upload
uploaded = st.file_uploader("Upload a file", type=["pdf", "txt", "md"])
if uploaded:
    content = uploaded.read().decode("utf-8")
```

---

## Layout

### Columns

```python
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Users", "1,234")
with col2:
    st.metric("Revenue", "$5,678")
with col3:
    st.metric("Requests", "9,012")
```

### Sidebar

```python
with st.sidebar:
    st.header("Settings")
    model = st.selectbox("Model", ["gemini-2.5-flash", "llama-3.3-70b"])
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2)
    st.divider()
    st.caption("App v1.0")
```

### Expander

```python
with st.expander("Advanced settings"):
    debug_mode = st.checkbox("Debug mode")
    verbose = st.checkbox("Verbose logging")
```

### Tabs

```python
tab1, tab2, tab3 = st.tabs(["Results", "Debug", "History"])
with tab1:
    st.write("Query results here")
with tab2:
    st.json(debug_info)
with tab3:
    st.dataframe(history_df)
```

### Containers

```python
with st.container():
    st.header("Container contents")
    st.write("Grouped content")
```

---

## Session State

Session state persists values across script reruns:

```python
# Initialize
if "counter" not in st.session_state:
    st.session_state.counter = 0
if "history" not in st.session_state:
    st.session_state.history = []

# Read and write
st.session_state.counter += 1
st.session_state.history.append({"query": "...", "answer": "..."})

# Display
st.write(f"Count: {st.session_state.counter}")
```

---

## Chat Interface — Building Chat Apps

Streamlit has first-class chat UI support:

```python
import streamlit as st

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render existing messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Ask a question..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate and display response
    with st.chat_message("assistant"):
        response = call_your_llm(prompt)
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
```

### Streaming responses

```python
with st.chat_message("assistant"):
    response_placeholder = st.empty()
    full_response = ""
    
    for chunk in llm.stream(prompt):
        full_response += chunk
        response_placeholder.markdown(full_response + "▌")  # Typing cursor
    
    response_placeholder.markdown(full_response)
```

---

## Caching

Caching prevents re-running expensive functions on every rerun:

### `@st.cache_data` — for data and serializable outputs

```python
@st.cache_data
def load_large_dataset():
    return pd.read_csv("huge_file.csv")  # Only loaded once

@st.cache_data(ttl=3600)  # Cache expires after 1 hour
def fetch_from_api(endpoint: str):
    return requests.get(endpoint).json()
```

### `@st.cache_resource` — for connections and models

```python
@st.cache_resource
def get_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")  # Loaded once, shared

@st.cache_resource
def get_chromadb_client():
    return chromadb.PersistentClient(path="./chroma_db")
```

---

## Status and Progress

```python
# Spinner
with st.spinner("Processing your query..."):
    result = slow_function()

# Progress bar
progress_bar = st.progress(0)
for i in range(100):
    do_work()
    progress_bar.progress(i + 1)
progress_bar.empty()

# Status messages
st.success("Query completed successfully!")
st.error("An error occurred.")
st.warning("Warning: Rate limit approaching.")
st.info("Using server API key.")

# Toast notification
st.toast("Query complete!", icon="✅")
```

---

## Forms

Forms group widgets and submit them together (avoiding per-widget reruns):

```python
with st.form("query_form"):
    question = st.text_input("Your question")
    provider = st.selectbox("Provider", ["Gemini", "Groq"])
    submitted = st.form_submit_button("Ask")

if submitted:
    process_query(question, provider)
```

---

## Charts and Visualization

```python
import pandas as pd
import numpy as np

df = pd.DataFrame(np.random.randn(20, 3), columns=["A", "B", "C"])

st.line_chart(df)          # Line chart
st.bar_chart(df)           # Bar chart
st.area_chart(df)          # Area chart
st.scatter_chart(df)       # Scatter chart

# Matplotlib
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.hist(df["A"], bins=20)
st.pyplot(fig)

# Plotly
import plotly.express as px
fig = px.scatter(df, x="A", y="B", color="C")
st.plotly_chart(fig)
```

---

## Theming

Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1E90FF"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#1A1F2E"
textColor = "#FAFAFA"
font = "sans serif"
```

---

## Multipage Apps

Create a `pages/` directory with numbered Python files:

```
app.py              # Main page
pages/
  1_🏠_Home.py
  2_📊_Analytics.py
  3_⚙️_Settings.py
```

---

## Deployment

### Streamlit Community Cloud (free)

1. Push code to GitHub.
2. Go to share.streamlit.io.
3. Connect your repo and deploy.
4. Set secrets in the platform dashboard.

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Secrets management

```toml
# .streamlit/secrets.toml (never commit this)
GEMINI_API_KEY = "..."
GROQ_API_KEY = "..."
DATABASE_URL = "..."
```

```python
# Access in code
api_key = st.secrets["GEMINI_API_KEY"]
```

---

## Streamlit vs Gradio vs Panel

| Feature | Streamlit | Gradio | Panel |
|---|---|---|---|
| Learning curve | Very low | Very low | Medium |
| Chat UI | Native | Native | Manual |
| Layout control | Medium | Limited | High |
| Custom CSS/JS | Limited | Limited | Full |
| Best for | Dashboards, LLM apps | ML demos | Complex dashboards |
| Community | Large | Large | Medium |
