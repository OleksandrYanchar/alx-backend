from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.admin import generate_report
from schemas.admin import DailyReportScheme
from schemas.store import BugReportInfoSchema
from dependencies.users import is_user_stuff
from dependencies.db import get_async_session


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get(
    "/daily-report",
    response_model=DailyReportScheme,
    dependencies=[Depends(is_user_stuff)],
)
async def send_report(
    db: AsyncSession = Depends(get_async_session),
) -> DailyReportScheme:

    return await generate_report(db)

@router.get(
    "/bugs-report",
    response_model=BugReportInfoSchema,
    dependencies=[Depends(is_user_stuff)],
)
async def send_report(
    db: AsyncSession = Depends(get_async_session),
) -> BugReportInfoSchema:

    return await generate_report(db)
