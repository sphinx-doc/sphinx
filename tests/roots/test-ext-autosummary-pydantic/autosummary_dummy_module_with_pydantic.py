__all__ = [
    "MyModel",
]

from pydantic import BaseModel


class MyModel(BaseModel):
    attr: str
