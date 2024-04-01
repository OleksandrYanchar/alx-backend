from models.users import Users
from schemas.admin import AdminBugsClosedCountSchema
from crud.users import crud_user
from crud.base import CRUDBase
from schemas.store import BugReportCreateSchema,BugCommentScheme
from models.store import BugReport, BugReportComment
from typing import Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, select



class CRUDReports(CRUDBase[BugReport, BugReportCreateSchema, BugReportCreateSchema]):
    def __init__(self, model: BugReport):
        super().__init__(model)

    async def get_closed_bugs_count_by_admin(self, db: AsyncSession):
        # Query to count bugs closed by each admin
        query = select(self._model.closed_by_id, func.count().label('bugs_closed')).where(self._model.is_closed == True).group_by(self._model.closed_by_id)
        result = await db.execute(query)
        closed_bugs_by_admin = result.all()
        return closed_bugs_by_admin


class CRUDComments(CRUDBase[BugReportComment, BugCommentScheme, BugCommentScheme]):
    async def get_comments_for_bug_paginated(self, db: AsyncSession, *, bug_report_id: int,
                                             offset: int = 0, limit: int = 100
    ) -> Tuple[List[BugReportComment], int]:
        comments_query = select(BugReportComment).where(BugReportComment.bug_report_id == bug_report_id).order_by(desc(BugReportComment.time_stamp)).offset(offset).limit(limit)
        result = await db.execute(comments_query)
        comments = result.scalars().all()
        
        total_count_query = select(func.count()).select_from(select(BugReportComment).where(BugReportComment.bug_report_id == bug_report_id).subquery())
        total_count_result = await db.execute(total_count_query)
        total = total_count_result.scalar_one()

        return comments, total

crud_comments = CRUDComments(BugReportComment)

crud_report = CRUDReports(BugReport)
