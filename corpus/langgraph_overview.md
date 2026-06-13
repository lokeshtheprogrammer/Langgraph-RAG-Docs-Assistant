# LangGraph Overview

LangGraph is a low-level orchestration framework and runtime for building, managing, and deploying long-running, stateful agents. It is designed to give developers precise control over agent orchestration, enabling durable execution, streaming, human-in-the-loop, and persistent state across agent loops.

## Core Abstractions
- **StateGraph**: The primary graph abstraction in LangGraph. Nodes represent operations/computations, and edges define execution control flow.
- **MessagesState**: A common prebuilt state schema containing a list of chat messages that automatically appends new model/user messages.
- **START and END**: Special nodes defining the entry point and exit point of graph execution.

## Installation
Install LangGraph using pip or uv:
```bash
# Using pip
pip install -U langgraph

# Using uv
uv add langgraph
```

## Basic Hello World Example
```python
from langgraph.graph import StateGraph, MessagesState, START, END

def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}

# Initialize graph with standard message state
graph = StateGraph(MessagesState)
graph.add_node(mock_llm)
graph.add_edge(START, "mock_llm")
graph.add_edge("mock_llm", END)
graph = graph.compile()

# Invoke the compiled graph
graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
```

## Core Benefits
1. **Persistence**: Build stateful agents that persist through failures and can run for extended periods, resuming from where they left off.
2. **Human-in-the-loop**: Incorporate human oversight by inspecting and modifying agent state at any point.
3. **Comprehensive Memory**: Support both short-term working memory for ongoing reasoning and long-term memory across sessions.
4. **LangSmith Integration**: Debug complex agent behavior with trace visualization, capturing state transitions and execution paths.
