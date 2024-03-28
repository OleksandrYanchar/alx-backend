from crud.base import CRUDBase
from schemas.store import BugReportCreateSchema,BugCommentScheme
from models.store import BugReport, BugReportComment
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, select

class CRUDReports(CRUDBase[BugReport, BugReportCreateSchema, BugReportCreateSchema]):
    def __init__(self, model: BugReport):
        super().__init__(model)

    async def count_closed_bugs_by_admin_from_date(self, db: AsyncSession, start_date: datetime, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Counts how many bugs each admin closed since the given start date,
        optionally limiting the number of entries returned.

        :param db: The database session.
        :param start_date: The date from which to start counting.
        :param limit: The maximum number of admin entries to return. Returns all if None.
        :return: A dictionary with admin usernames as keys and the amount of closed bugs as values.
        """
        query = (
            db.query(
                self.model.closed_by,
                func.count(self.model.id).label('closed_count')
            )
            .filter(self.model.is_closed == True)
            .filter(self.model.time_stamp >= start_date)
            .group_by(self.model.closed_by)
            .order_by(desc('closed_count'))
        )

        if limit is not None:
            query = query.limit(limit)

        result = await db.execute(query)
        counts = {admin: count for admin, count in result}
        return counts

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
