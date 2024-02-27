from pydantic import BaseModel
from typing import List


class EmailSchema(BaseModel):
    email: List[str]
    subject: str
    body: str

class EmailVerificationSchema(BaseModel):
    username: str
    is_active: bool
