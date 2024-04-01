from datetime import datetime, date
from typing import Dict, List
from pydantic import BaseModel
from schemas.users import UserDataSchema


class BugReportCreateSchema(BaseModel):
    title: str
    body: str

    class Config:
        from_attributes = True


class BugReportInfoSchema(BaseModel):
    id: int
    user: UserDataSchema
    title: str
    body: str
    is_closed: bool

    class Config:
        from_attributes = True


class BugCommentScheme(BaseModel):
    body: str


class BugCommentInfoScheme(BaseModel):
    time_stamp: datetime
    author: str
    body: str

