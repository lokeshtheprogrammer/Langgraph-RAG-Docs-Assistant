# LangChain Tools and Custom Tool Creation

Tools are interfaces that an agent, chain, or LLM can use to interact with the world. They combine a function description (schema) with a python execution handler.

## Decator Syntax (`@tool`)
The easiest way to define a custom tool is to use the `@tool` decorator on a Python function:
```python
from langchain.tools import tool

@tool
def calculate_multiply(a: int, b: int) -> int:
    """Multiply two integers together."""
    return a * b
```
Pydantic uses the function parameters type hints and the docstring description to generate the tool schema presented to the LLM.

## Inheriting from BaseTool
For more complex tools requiring customization, inherit from the `BaseTool` class:
```python
from typing import Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

class ToolInputSchema(BaseModel):
    query: str = Field(..., description="Query parameter")

class CustomSearchTool(BaseTool):
    name: str = "custom_search"
    description: str = "Use this tool to search database records"
    args_schema: Type[BaseModel] = ToolInputSchema
    
    def _run(self, query: str) -> str:
        # Synchronous execution logic
        return f"Results for query: {query}"
        
    async def _arun(self, query: str) -> str:
        # Asynchronous execution logic
        return f"Async results for: {query}"
```
Tools must always define a descriptive name and docstring description to allow the LLM to identify when to call them.
