from pydantic import BaseModel
from typing import List, Generic, TypeVar

T = TypeVar("T")


class PaginationSchema(BaseModel, Generic[T]):
    items: List[T]
    total: int
    offset: int
    limit: int
    detail: str = "ok"
