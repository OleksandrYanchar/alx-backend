from pydantic import BaseModel
from schemas.users import UserDataSchema


class BugReportCreateSchema(BaseModel):
    title: str
    body: str

    class Config:
        from_attributes = True


class BugReportInfoSchema(BaseModel):
    user: UserDataSchema
    title: str
    body: str
    is_closed: bool

    class Config:
        from_attributes = True
