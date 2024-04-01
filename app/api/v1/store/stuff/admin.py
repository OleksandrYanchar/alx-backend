from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from crud.users import crud_user
from crud.store import crud_report
from services.admin import generate_report
from schemas.admin import DailyReportScheme,  AdminBugsClosedCountSchema
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

@router.get("/closed-bugs/count", response_model=dict)
async def admin_bug_counts(db: AsyncSession = Depends(get_async_session)):
    # Fetch all admins. This assumes you have a function to fetch all users who are admins.
    all_admins = await crud_user.get_multi(db, is_staff=True)
    
    # Initialize result with all admins set to 0 bugs closed
    result = {admin.username: 0 for admin in all_admins}
    
    # Fetch counts of closed bugs by admins who have closed bugs
    closed_bugs_by_admin = await crud_report.get_closed_bugs_count_by_admin(db)
    
    # Update result with actual counts for admins who have closed bugs
    for admin_id, count in closed_bugs_by_admin:
        user = await crud_user.get(db, id=admin_id)
        # Check if user is not None before trying to access attributes
        if user is not None:
            username = user.username
            result[username] = count
        # No need for else, as all users are already initialized with 0

    return result
