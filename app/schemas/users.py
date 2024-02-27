from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import date


class UserCreateSchema(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    email: str
    joined_at: date = Field(default=date.today, description="user registration date?")
      
    class Config:
        from_attributes = True  


class UserCreateOutSchema(BaseModel):
    id: UUID
    username: str
    first_name: str
    last_name: str
    email: str
    joined_at: date
      
    class Config:
        from_attributes = True  

        
class UserLoginSchema(BaseModel):
    username: str
    password: str

    class Config:
        from_attributes = True  


class UserPasswordChangechema(BaseModel):
    old_password: str
    new_password1: str
    new_password2: str

    class Config:
        from_attributes = True  
