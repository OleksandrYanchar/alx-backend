from pydantic import BaseModel, Field
from typing import List, Generic, TypeVar, Optional

T = TypeVar('T')

class PaginationSchema(BaseModel, Generic[T]):
    items: List[T]
    total: int
    offset: int
    limit: int
