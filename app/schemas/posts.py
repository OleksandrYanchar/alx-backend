from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid


class PostCreateInSchema(BaseModel):
    id: uuid.UUID =  Field(
        default_factory=uuid.uuid4, description="post id")
    title: str
    category: str
    subcategory: str
    price: float
    description: Optional[str] = None
    created_at: datetime = Field(
        default_factory=datetime.now, description="Post creating time"
    )

    class Config:
        from_attributes = True  # Assuming you are using this model with SQLAlchemy

class PostCreateOutSchema(BaseModel):
    owner: uuid.UUID
    title: str
    category: str
    subcategory: str
    price: float
    description: Optional[str] = None
    is_vip: bool
    created_at: datetime
    updated_at: datetime 

    class Config:
        from_attributes = True 


class PostUpdateSchema(BaseModel):

    title: str
    category: str
    subcategory: str
    price: float
    description: Optional[str] = None
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Post updating time"
    )

    class Config:
        from_attributes = True  # Assuming you are using this model with SQLAlchemy



