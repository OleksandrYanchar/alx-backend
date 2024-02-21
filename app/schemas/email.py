from pydantic import BaseModel
from typing import List

class EmailSchema(BaseModel):
    email: List[str]
    
class EmailVerificationSchema(BaseModel):
    username : str
    is_active: bool 