# FastAPI Tutorial - Getting Started

FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints.

## Key Features
- **Fast**: Very high performance, on par with NodeJS and Go (thanks to Starlette and Pydantic).
- **Fast to code**: Increase the speed to develop features by about 200% to 300%.
- **Fewer bugs**: Reduce about 40% of developer induced errors.
- **Intuitive**: Great editor support. Completion everywhere. Less time debugging.
- **Easy**: Designed to be easy to use and learn. Less time reading documentation.
- **Short**: Minimize code duplication. Multiple features from each parameter declaration.
- **Robust**: Get production-ready code. With automatic interactive documentation.
- **Standards-based**: Based on (and fully compatible with) the open standards for APIs: OpenAPI and JSON Schema.

## Installation
Install FastAPI and Uvicorn (an ASGI server) using pip:
```bash
pip install fastapi uvicorn
```

## Basic Application Creation
Create a file named `main.py` with:
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
```

## Running the Application
Start the development server with:
```bash
uvicorn main:app --reload
```
The `--reload` flag enables auto-reloading of the server when files change.

## OpenAPI Documentation
FastAPI automatically generates interactive API documentation. You can access it at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
