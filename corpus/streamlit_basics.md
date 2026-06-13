# Streamlit Basics for Python Applications

Streamlit is an open-source Python library that makes it easy to create and share beautiful, custom web apps for machine learning and data science. In just a few minutes you can build and deploy powerful data apps.

## Key Concepts
- **React-like state**: Whenever a user interacts with a widget, Streamlit reruns your entire Python script from top to bottom.
- **Session State**: Allows you to persist variables across reruns for the user's session using `st.session_state`.
- **Wired-up widgets**: Streamlit widgets (buttons, text inputs, sliders) return their value directly in the Python variable assignment.

## Basic API Reference
- `st.write()`: The swiss-army knife of Streamlit. Renders Markdown, charts, dataframes, and more.
- `st.title()`, `st.header()`, `st.subheader()`: Set heading levels.
- `st.sidebar`: Add components directly to the collapsible sidebar.
- `st.columns()`: Create horizontal layouts dynamically.
- `st.expander()`: Render collapsible details panels.

## State Management Example
```python
import streamlit as st

if "counter" not in st.session_state:
    st.session_state.counter = 0

if st.button("Increment Counter"):
    st.session_state.counter += 1

st.write(f"Count is: {st.session_state.counter}")
```

## Running a Streamlit App
Start the web server:
```bash
streamlit run app.py
```
By default, the server hosts the application locally at `http://localhost:8501`.
