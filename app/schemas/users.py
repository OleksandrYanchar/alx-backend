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