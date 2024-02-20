from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import date

class UserCreateSchema(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    email: str
    joined_at: date
    is_activated: bool = False
    is_vip: bool = False
    is_staff: bool = False
    image: Optional[str]
      
    class Config:
        from_attributes = True  

class UserCreateOutSchema(BaseModel):
    id: UUID
    username: str
    first_name: str
    last_name: str
    email: str
    joined_at: date
    image: Optional[str]
      
    class Config:
        from_attributes = True  