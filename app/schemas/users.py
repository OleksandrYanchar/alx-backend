from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
import uuid
from schemas.tokens import TokenSchema


class UserCreateInSchema(BaseModel):
    id: uuid.UUID =  Field(
        default_factory=uuid.uuid4, description="user id")
    username: str
    password: str
    first_name: str
    last_name: Optional[str] = None
    email: str
    # Use default_factory=date.today to ensure the current date is used as default
    joined_at: date = Field(
        default_factory=date.today, description="User registration date"
    )

    class Config:
        from_attributes = True  # Assuming you are using this model with SQLAlchemy


class UserCreateOutSchema(BaseModel):
    id: uuid.UUID
    first_name: str
    email: str

    tokens: TokenSchema


class UserLoginSchema(BaseModel):
    username: str
    password: str

    class Config:
        from_attributes = True


class UserPasswordChangeSchema(BaseModel):
    old_password: str
    new_password1: str
    new_password2: str

    class Config:
        from_attributes = True


class UserPasswordResetSchema(BaseModel):
    new_password1: str
    new_password2: str

    class Config:
        from_attributes = True
        
class UserDataSchema(BaseModel):
    username: str
    joined_at: date
    first_name : str
    email : str
    is_vip: bool
