# FastAPI — Complete Documentation Reference

Source: https://fastapi.tiangolo.com/

---

## What is FastAPI?

FastAPI is a modern, high-performance web framework for building APIs with Python 3.8+, based on standard Python type hints. It was created by Sebastián Ramírez and is one of the fastest Python frameworks available, on par with NodeJS and Go (thanks to Starlette and Pydantic).

FastAPI is used in production at companies like Microsoft, Uber, Netflix, and NASA.

### Key Characteristics

- **Fast to run**: Very high performance, on par with NodeJS and Go.
- **Fast to code**: Increases development speed by 200–300%.
- **Fewer bugs**: Reduces developer-induced errors by ~40%.
- **Intuitive**: Great editor support with autocompletion everywhere.
- **Easy**: Designed to be easy to use and learn.
- **Short**: Minimize code duplication.
- **Robust**: Get production-ready code with automatic interactive documentation.
- **Standards-based**: Based on (and fully compatible with) the open standards OpenAPI and JSON Schema.

---

## Installation

```bash
pip install fastapi
pip install "uvicorn[standard]"  # ASGI server to run FastAPI
```

---

## First Steps — Hello World

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

Run with:

```bash
uvicorn main:app --reload
```

Visit: `http://127.0.0.1:8000/` — returns JSON response.
Visit: `http://127.0.0.1:8000/docs` — Swagger UI auto-generated docs.
Visit: `http://127.0.0.1:8000/redoc` — ReDoc auto-generated docs.

---

## Path Parameters

FastAPI uses Python type hints to declare path parameters:

```python
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

FastAPI automatically:
- Validates that `item_id` is an integer.
- Returns a clear error if validation fails.
- Documents the parameter in OpenAPI schema.

### Predefined values with Enum

```python
from enum import Enum

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    return {"model_name": model_name}
```

---

## Query Parameters

Parameters not in the path become query parameters:

```python
fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}]

@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
```

- URL: `/items/?skip=0&limit=10`
- Optional parameters with defaults: `limit: int = 10`
- Optional parameters without value: `q: str | None = None`

---

## Request Body

Use Pydantic models to declare request bodies:

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

@app.post("/items/")
async def create_item(item: Item):
    return item
```

FastAPI will:
- Read the request body as JSON.
- Convert it to the `Item` model.
- Validate the data.
- Provide the data in the function parameter `item`.
- Generate JSON Schema documentation.

---

## Response Model

Control what is returned to the client:

```python
class ItemOut(BaseModel):
    name: str
    price: float

@app.post("/items/", response_model=ItemOut)
async def create_item(item: Item):
    return item
```

This filters the output to only include fields declared in `ItemOut`, even if the input model has more fields.

---

## HTTP Methods

FastAPI supports all HTTP methods:

```python
@app.get("/items/")       # GET
@app.post("/items/")      # POST
@app.put("/items/{id}")   # PUT
@app.delete("/items/{id}")# DELETE
@app.patch("/items/{id}") # PATCH
@app.options("/items/")   # OPTIONS
@app.head("/items/")      # HEAD
```

---

## Status Codes

```python
from fastapi import status

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    return item
```

Common status codes:
- `200` — OK (default for GET)
- `201` — Created (for POST)
- `204` — No Content (for DELETE)
- `400` — Bad Request
- `401` — Unauthorized
- `403` — Forbidden
- `404` — Not Found
- `422` — Unprocessable Entity (validation errors)
- `500` — Internal Server Error

---

## Request Headers and Cookies

```python
from fastapi import Header, Cookie

@app.get("/items/")
async def read_items(user_agent: str | None = Header(default=None)):
    return {"User-Agent": user_agent}

@app.get("/cookie/")
async def read_cookie(ads_id: str | None = Cookie(default=None)):
    return {"ads_id": ads_id}
```

---

## Form Data and File Uploads

```python
from fastapi import Form, File, UploadFile

@app.post("/login/")
async def login(username: str = Form(), password: str = Form()):
    return {"username": username}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}
```

---

## Dependencies Injection

FastAPI has a powerful dependency injection system:

```python
from fastapi import Depends

async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: dict = Depends(common_parameters)):
    return commons
```

### Class-based dependencies

```python
class CommonQueryParams:
    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit

@app.get("/items/")
async def read_items(commons: CommonQueryParams = Depends()):
    return {"q": commons.q, "skip": commons.skip}
```

### Dependency with yield (for database sessions)

```python
async def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()

@app.get("/items/")
async def read_items(db: Session = Depends(get_db)):
    return db.query(Item).all()
```

---

## Security and Authentication

### OAuth2 with Password Bearer

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # validate user, return JWT
    return {"access_token": "...", "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    return {"token": token}
```

### API Key Header

```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

@app.get("/secure/")
async def secure_endpoint(api_key: str = Depends(api_key_header)):
    return {"api_key": api_key}
```

---

## Middleware

Middleware runs before and after each request:

```python
from fastapi.middleware.cors import CORSMiddleware
import time

@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Background Tasks

```python
from fastapi import BackgroundTasks

def write_notification(email: str, message: str = ""):
    with open("log.txt", mode="a") as f:
        f.write(f"notification for {email}: {message}\n")

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_notification, email, message="some notification")
    return {"message": "Notification sent in the background"}
```

---

## Exception Handling

```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.requests import Request

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": items[item_id]}

# Custom exception handler
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"message": str(exc)})
```

---

## Routers — Organizing Large Applications

```python
# routers/items.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/items/")
async def read_items():
    return [{"item_id": "Foo"}]

# main.py
from fastapi import FastAPI
from .routers import items

app = FastAPI()
app.include_router(items.router, prefix="/api/v1", tags=["items"])
```

---

## FastAPI vs Flask vs Django

| Feature | FastAPI | Flask | Django |
|---|---|---|---|
| Performance | Very high (ASGI) | Medium (WSGI) | Medium (WSGI) |
| Async support | Native | Limited | Limited |
| Data validation | Built-in (Pydantic) | Manual | Forms/Serializers |
| Auto docs | Yes (Swagger + ReDoc) | No | No |
| Type hints | Full support | Partial | Partial |
| ORM | Any | Any | Django ORM |
| Learning curve | Low | Very Low | High |
| Best for | APIs, microservices | Simple apps | Full-stack web |

---

## FastAPI with Databases

### SQLAlchemy (sync)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Async with asyncpg / SQLAlchemy async

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"
engine = create_async_engine(DATABASE_URL)
```

---

## Testing FastAPI

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
```

---

## Deployment

### With Uvicorn

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### With Gunicorn + Uvicorn workers

```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## FastAPI Dependencies — Common Use Cases

1. **Database sessions** — yield pattern with cleanup
2. **Authentication** — OAuth2, JWT, API keys
3. **Rate limiting** — count requests per user
4. **Caching** — Redis-based response caching
5. **Feature flags** — conditionally enable endpoints
6. **Audit logging** — log all API access
7. **Pagination** — standard skip/limit across all endpoints
