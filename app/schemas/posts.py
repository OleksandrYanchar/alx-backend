import uuid
from pydantic import BaseModel, validator, Field
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
        from_attributes = True


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
    
    title: Optional[str]= None
    slug:Optional[str]= None
    category: Optional[str]= None
    subcategory: Optional[str]= None
    price: Optional[float]= None
    description: Optional[str] = None
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Post updating time"
    )

    @validator('price')
    def validate_price(cls, value):
        if value < 0:
            raise ValueError("price can't be negative")
        return value

    class Config:
        from_attributes = True  # Assuming you are using this model with SQLAlchemy



