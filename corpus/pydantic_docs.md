# Pydantic v2 — Complete Documentation Reference

Source: https://docs.pydantic.dev/latest/

---

## What is Pydantic?

Pydantic is the most widely used data validation library for Python. It uses Python type annotations to validate, serialize, and deserialize data. Pydantic v2, rewritten in Rust for performance, is 5–50x faster than Pydantic v1.

Pydantic is used by FastAPI, LangChain, HuggingFace, and thousands of production applications.

### Core capabilities

- **Data validation**: Validate data against type annotations at runtime.
- **Data serialization**: Convert models to/from JSON, dicts, and other formats.
- **Settings management**: Manage application configuration via environment variables.
- **JSON Schema generation**: Automatically generate JSON Schema from models.

---

## Installation

```bash
pip install pydantic
# For email validation
pip install "pydantic[email]"
# For settings management
pip install pydantic-settings
```

---

## BaseModel — Core Concept

The `BaseModel` class is the foundation of Pydantic:

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str
    age: int | None = None   # Optional field with default None
    is_active: bool = True   # Field with default value
```

### Creating instances

```python
user = User(id=1, name="Alice", email="alice@example.com")
print(user.id)       # 1
print(user.name)     # "Alice"
print(user.is_active) # True
```

### From dict

```python
data = {"id": "1", "name": "Alice", "email": "alice@example.com"}
user = User.model_validate(data)
# Pydantic coerces "1" (string) to 1 (int) automatically
```

### To dict / JSON

```python
user.model_dump()        # {"id": 1, "name": "Alice", ...}
user.model_dump_json()   # '{"id":1,"name":"Alice",...}'
```

---

## Field Validation

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, description="Price must be positive")
    quantity: int = Field(default=0, ge=0, le=10000)
    tags: list[str] = Field(default_factory=list)
```

### Field constraints

| Constraint | Applies to | Meaning |
|---|---|---|
| `gt` | numeric | greater than |
| `ge` | numeric | greater than or equal |
| `lt` | numeric | less than |
| `le` | numeric | less than or equal |
| `min_length` | str, list | minimum length |
| `max_length` | str, list | maximum length |
| `pattern` | str | regex pattern match |

---

## Types Supported

Pydantic supports a wide range of Python types:

### Primitive types
- `str`, `int`, `float`, `bool`, `bytes`
- `None` / `Optional[X]`
- `Literal["value1", "value2"]`

### Collection types
- `list[int]`, `tuple[str, int]`, `set[str]`
- `dict[str, Any]`, `frozenset[str]`

### Python standard library types
- `datetime`, `date`, `time`, `timedelta`
- `UUID`, `Decimal`, `Path`, `URL`
- `Enum`, `IntEnum`

### Pydantic-specific types
- `EmailStr` — validates email addresses
- `AnyUrl`, `HttpUrl` — validates URLs
- `FilePath`, `DirectoryPath` — validates filesystem paths
- `IPvAnyAddress` — validates IPv4/IPv6 addresses
- `Json` — parses JSON strings

---

## Validators

### Field validators

```python
from pydantic import BaseModel, field_validator

class User(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        assert v.isalnum(), "Username must be alphanumeric"
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
```

### Model validators

```python
from pydantic import model_validator

class UserWithConfirm(BaseModel):
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def check_passwords_match(self) -> "UserWithConfirm":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self
```

---

## Nested Models

```python
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    country: str

class Person(BaseModel):
    name: str
    address: Address   # Nested model

person = Person(
    name="Alice",
    address={"street": "123 Main St", "city": "Springfield", "country": "US"}
)
print(person.address.city)  # "Springfield"
```

---

## Serialization — Controlling Output

```python
from pydantic import BaseModel, field_serializer

class Event(BaseModel):
    name: str
    date: datetime

    @field_serializer("date")
    def serialize_date(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d")

# Exclude fields on export
user.model_dump(exclude={"password"})
user.model_dump(include={"name", "email"})

# Alias for JSON output
class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    first_name: str = Field(alias="firstName")
```

---

## Model Configuration

```python
from pydantic import BaseModel, ConfigDict

class StrictUser(BaseModel):
    model_config = ConfigDict(
        strict=True,           # No type coercion — "1" != 1
        frozen=True,           # Immutable instances
        extra="forbid",        # Reject unknown fields
        str_strip_whitespace=True,  # Strip whitespace from strings
        validate_default=True, # Validate default values too
    )
    id: int
    name: str
```

### Config options

| Option | Default | Description |
|---|---|---|
| `strict` | False | Disables coercion |
| `frozen` | False | Makes model immutable |
| `extra` | `"ignore"` | How to handle extra fields |
| `populate_by_name` | False | Allow both field name and alias |
| `str_strip_whitespace` | False | Strip whitespace from strings |
| `str_to_lower` | False | Lowercase all strings |
| `validate_assignment` | False | Validate on attribute assignment |

---

## JSON Schema Generation

Pydantic automatically generates JSON Schema from models:

```python
import json
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    quantity: int = 1

print(json.dumps(Item.model_json_schema(), indent=2))
```

Output:
```json
{
  "type": "object",
  "title": "Item",
  "properties": {
    "name": {"type": "string", "title": "Name"},
    "price": {"type": "number", "title": "Price"},
    "quantity": {"type": "integer", "title": "Quantity", "default": 1}
  },
  "required": ["name", "price"]
}
```

---

## Pydantic Settings — Configuration Management

`pydantic-settings` reads configuration from environment variables and `.env` files:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "My App"
    debug: bool = False
    database_url: str
    api_key: str
    max_connections: int = 10

settings = Settings()  # Reads from environment / .env
print(settings.database_url)
```

`.env` file:
```
DATABASE_URL=postgresql://user:pass@localhost/db
API_KEY=secret123
DEBUG=true
```

---

## Error Handling

Pydantic raises `ValidationError` with detailed messages:

```python
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    id: int
    name: str

try:
    user = User(id="not-an-int", name=123)
except ValidationError as e:
    print(e.error_count())    # 2
    print(e.errors())
    # [
    #   {"type": "int_parsing", "loc": ("id",), "msg": "Input should be a valid integer..."},
    #   ...
    # ]
```

---

## Pydantic v1 vs v2 Differences

| Feature | v1 | v2 |
|---|---|---|
| Performance | Baseline | 5–50x faster (Rust core) |
| `model_validate()` | `parse_obj()` | `model_validate()` |
| `model_dump()` | `.dict()` | `.model_dump()` |
| `model_dump_json()` | `.json()` | `.model_dump_json()` |
| Field validators | `@validator` | `@field_validator` |
| Model validators | `@root_validator` | `@model_validator` |
| Config | `class Config:` | `model_config = ConfigDict(...)` |
| Schema | `.schema()` | `.model_json_schema()` |

---

## Pydantic with FastAPI

FastAPI uses Pydantic for:
- **Request body validation**: JSON request bodies are validated as Pydantic models.
- **Response models**: Filter and validate response data.
- **Query parameters**: Validate and document query strings.
- **Settings**: Manage API configuration.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = False

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}
```

---

## TypeAdapter — Validate Without a Model

```python
from pydantic import TypeAdapter

# Validate a list of integers
ta = TypeAdapter(list[int])
result = ta.validate_python(["1", "2", "3"])
# [1, 2, 3]

# Validate arbitrary JSON
ta2 = TypeAdapter(dict[str, float])
result2 = ta2.validate_json('{"a": 1.5, "b": 2.7}')
```
