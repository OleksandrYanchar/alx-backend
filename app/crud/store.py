from crud.base import CRUDBase
from schemas.store import BugReportCreateSchema
from models.store import BugReport


CRUDCategory = CRUDBase[BugReport, BugReportCreateSchema, BugReportCreateSchema]
crud_report = CRUDCategory(BugReport)
