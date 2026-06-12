# Pydantic v2 Documentation

Pydantic is the most widely used data validation library for Python. It is extremely fast and integrates seamlessly with modern IDEs and type checkers.

## Basic Model Definition
In Pydantic, data validation is defined using standard Python type hints via subclasses of `BaseModel`:

```python
from typing import Optional
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int
    name: str = "John Doe"
    signup_ts: Optional[datetime] = None
    friends: list[int] = []
```

## Validation and Serialization
Pydantic validates input data and converts types automatically (e.g. string "123" to integer 123):
```python
external_data = {
    "id": "123",
    "signup_ts": "2025-06-11 12:00",
    "friends": [1, 2, "3"]
}
user = User(**external_data)
print(user.id)  # outputs: 123 (as integer)
print(user.model_dump())  # serializes user data back into dict
```

## Field Customization
You can use `Field` to add validation constraints or metadata description properties:
```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    price: float = Field(..., gt=0.0, description="The price of the item")
```

## ConfigDict Settings
In Pydantic v2, configurations are defined inside the model using a class attribute named `model_config` with a `ConfigDict`:
```python
from pydantic import BaseModel, ConfigDict

class SettingsModel(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )
    username: str
```
