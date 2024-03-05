import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from schemas.users import UserDataSchema


class PostCreateInSchema(BaseModel):
    title: str
    category: str
    subcategory: str
    price: float
    description: Optional[str] = None

    class Config:
        from_attributes = True  # Assuming you are using this model with SQLAlchemy

class PostInfoSchema(BaseModel):
    id: uuid.UUID
    owner: UserDataSchema
    slug:str
    title: str
    category: str
    subcategory: str
    price: float
    description: Optional[str] = None
    is_vip: bool
    created_at: datetime
    updated_at: Optional[datetime] = None 

    class Config:
        from_attributes = True 


class PostUpdateSchema(BaseModel):

    title: str
    slug:str
    category: str
    subcategory: str
    price: float
    description: Optional[str] = None
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Post updating time"
    )

    class Config:
        from_attributes = True  # Assuming you are using this model with SQLAlchemy



