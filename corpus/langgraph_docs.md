# LangGraph — Complete Documentation Reference

Source: https://langchain-ai.github.io/langgraph/

---

## What is LangGraph?

LangGraph is a low-level framework for building stateful, multi-actor applications with LLMs. It extends LangChain by adding support for stateful, cyclic computation — essential for building agents with loops, retries, and branching logic.

LangGraph is used by companies including Klarna, Uber, JP Morgan, and LinkedIn for production agent systems.

### Core design goals

- **Stateful**: Maintain state across multiple LLM calls.
- **Cyclic**: Support loops and retries (unlike simple DAGs).
- **Multi-actor**: Coordinate multiple agents or sub-graphs.
- **Controllable**: Fine-grained control over agent behavior.
- **Streaming**: Native support for token streaming.
- **Persistence**: Built-in checkpointing and memory.

---

## Installation

```bash
pip install langgraph
pip install langchain-openai  # or langchain-google-genai, etc.
```

---

## Core Concepts

### StateGraph

`StateGraph` is the primary graph type in LangGraph. It maintains a `State` dict that is passed between nodes and updated at each step.

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]  # Messages accumulate
    question: str
    answer: str | None
```

### Nodes

Nodes are Python functions (sync or async) that receive the current `State` and return a partial update:

```python
def my_node(state: AgentState) -> dict:
    # Do something with state
    return {"answer": "computed result"}  # Partial update to state
```

### Edges

Edges define the flow between nodes:

```python
# Simple edge: always go from A to B
graph.add_edge("node_a", "node_b")

# Conditional edge: choose next node based on state
graph.add_conditional_edges(
    "node_a",
    route_function,   # Returns the name of the next node
    {
        "path_1": "node_b",
        "path_2": "node_c",
        "end": END
    }
)
```

---

## Building a Simple Graph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    input: str
    output: str

def process(state: State) -> dict:
    return {"output": f"Processed: {state['input']}"}

def check(state: State) -> str:
    if "error" in state["output"]:
        return "retry"
    return "done"

# Build the graph
graph_builder = StateGraph(State)
graph_builder.add_node("process", process)
graph_builder.set_entry_point("process")
graph_builder.add_conditional_edges("process", check, {
    "retry": "process",
    "done": END
})

graph = graph_builder.compile()

# Invoke
result = graph.invoke({"input": "hello", "output": ""})
```

---

## State Management

### TypedDict State

```python
from typing import TypedDict, Annotated
import operator

class RAGState(TypedDict):
    question: str                          # Simple field — last write wins
    documents: list[str]                   # Simple field — last write wins
    messages: Annotated[list, operator.add] # Reducer — messages accumulate
    retry_count: int
    generation: str | None
```

### Annotated fields with reducers

When multiple nodes update the same field, use `Annotated` to define a reducer:
- `Annotated[list, operator.add]` — appends new items to the list
- `Annotated[int, max]` — keeps the maximum value
- Custom reducer functions for complex merge logic

---

## Conditional Edges and Routing

```python
def grade_documents(state: RAGState) -> str:
    """Route based on document quality."""
    relevant = [d for d in state["documents"] if d["grade"] == "relevant"]
    
    if not relevant:
        return "rewrite"     # No relevant docs — rewrite query
    elif len(relevant) >= 3:
        return "generate"    # Enough context — generate answer
    else:
        return "web_search"  # Some context — augment with web search

graph.add_conditional_edges(
    "grade_documents",
    grade_documents,
    {
        "rewrite": "rewrite_query",
        "generate": "generate",
        "web_search": "web_search"
    }
)
```

---

## Checkpointing and Persistence

LangGraph supports persistent state via checkpointers:

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver

# In-memory (for testing)
memory = MemorySaver()

# SQLite (persistent)
with SqliteSaver.from_conn_string("./checkpoints.db") as checkpointer:
    graph = graph_builder.compile(checkpointer=checkpointer)

# Invoke with a thread_id (enables persistence and resumability)
config = {"configurable": {"thread_id": "user-123"}}
result = graph.invoke({"question": "What is RAG?"}, config=config)
```

---

## Streaming

```python
# Stream individual node outputs
for chunk in graph.stream({"question": "What is FastAPI?"}, config=config):
    for node_name, node_output in chunk.items():
        print(f"Node: {node_name}")
        print(f"Output: {node_output}")

# Stream LLM tokens (requires astream_events)
async for event in graph.astream_events({"question": "..."}, version="v2"):
    if event["event"] == "on_chat_model_stream":
        print(event["data"]["chunk"].content, end="", flush=True)
```

---

## Human-in-the-Loop

LangGraph supports pausing execution for human approval:

```python
from langgraph.graph import StateGraph, END, interrupt

def human_approval(state: State) -> dict:
    # Pause and wait for human input
    decision = interrupt("Do you approve this action? (yes/no)")
    return {"approved": decision == "yes"}

graph_builder.add_node("human_approval", human_approval)
```

---

## Multi-Agent Systems

LangGraph supports multiple agents collaborating:

```python
from langgraph.graph import StateGraph

# Each agent is a node in the parent graph
def researcher_agent(state):
    # Agent 1: searches for information
    ...

def writer_agent(state):
    # Agent 2: writes based on research
    ...

def supervisor(state) -> str:
    # Decides which agent to call next
    ...

main_graph = StateGraph(State)
main_graph.add_node("researcher", researcher_agent)
main_graph.add_node("writer", writer_agent)
main_graph.add_conditional_edges("supervisor", supervisor, {...})
```

---

## Prebuilt Agents

LangGraph includes prebuilt agent architectures:

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

@tool
def search(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

llm = ChatOpenAI(model="gpt-4o")
agent = create_react_agent(llm, tools=[search])

result = agent.invoke({"messages": [("user", "What is the weather in Paris?")]})
```

---

## RAG with LangGraph — Corrective RAG Pattern

```python
from langgraph.graph import StateGraph, END

# Nodes
graph.add_node("retrieve", retrieve_documents)
graph.add_node("grade_documents", grade_documents)
graph.add_node("generate", generate_answer)
graph.add_node("rewrite_query", rewrite_query)
graph.add_node("web_search", web_search)

# Edges
graph.set_entry_point("retrieve")
graph.add_edge("retrieve", "grade_documents")
graph.add_conditional_edges(
    "grade_documents",
    decide_next_step,
    {
        "generate": "generate",
        "rewrite": "rewrite_query",
        "web_search": "web_search",
    }
)
graph.add_edge("rewrite_query", "retrieve")   # Loop back
graph.add_edge("web_search", "generate")
graph.add_edge("generate", END)
```

---

## LangGraph vs Traditional LangChain Chains

| Feature | LangChain Chains | LangGraph |
|---|---|---|
| Execution flow | Linear DAG | Cyclic graph |
| State management | Limited | Full TypedDict state |
| Loops/retries | Not supported | Native |
| Branching | Limited | Conditional edges |
| Human-in-loop | Not supported | Built-in interrupt |
| Streaming | Partial | Full token streaming |
| Persistence | External | Built-in checkpointing |
| Debugging | Limited | LangSmith integration |

---

## LangGraph Key Components Summary

| Component | Description |
|---|---|
| `StateGraph` | Main graph class with state management |
| `TypedDict` | Define the state schema |
| `Annotated` | Add reducers for accumulating state fields |
| `add_node()` | Register a node function |
| `add_edge()` | Define deterministic transitions |
| `add_conditional_edges()` | Define dynamic routing |
| `set_entry_point()` | Set the starting node |
| `compile()` | Build the executable graph |
| `invoke()` | Run graph synchronously |
| `ainvoke()` | Run graph asynchronously |
| `stream()` | Stream node outputs |
| `MemorySaver` | In-memory checkpointing |
| `SqliteSaver` | SQLite-based persistence |
| `END` | Special node indicating graph completion |
| `interrupt()` | Pause for human-in-the-loop |
