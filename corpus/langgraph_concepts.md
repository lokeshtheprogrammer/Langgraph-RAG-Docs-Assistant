# LangGraph Concepts and Architecture

LangGraph is a library for building stateful, multi-actor applications with LLMs, built on top of LangChain. It extends the LangChain Expression Language (LCEL) to support loops, cycles, and complex agentic workflows.

## Key Concepts

### 1. State
Every LangGraph application runs on top of a central State database/schema. The state is represented as a subclass of `TypedDict` or a Pydantic model. Each node in the graph receives the current state and returns a dictionary with updates to apply to the state.
```python
from typing import TypedDict, List

class AgentState(TypedDict):
    messages: List[dict]
    retry_count: int
```

### 2. Nodes
Nodes in LangGraph are python functions (usually asynchronous) that accept the graph state and return an update dictionary.
```python
async def my_node(state: AgentState) -> dict:
    # Perform operations (e.g. call LLM)
    return {"retry_count": state["retry_count"] + 1}
```

### 3. Edges
Edges connect nodes in the graph to define execution flows:
- **Normal Edges**: Direct transitions between nodes.
- **Conditional Edges**: Dynamic routing decisions based on a function of the state.

## Creating a StateGraph
To compile a graph:
```python
from langgraph.graph import StateGraph, END

# Define graph on state
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", my_node)

# Set entry point
workflow.set_entry_point("agent")

# Add edges
workflow.add_edge("agent", END)

# Compile graph
app = workflow.compile()
```
The compiled graph implements the standard Runnable interface, supporting `.invoke()`, `.stream()`, and `.ainvoke()`.
