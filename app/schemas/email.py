from pydantic import BaseModel

class ForgotPasswordEmailSchema(BaseModel): 
    identifier: str
    