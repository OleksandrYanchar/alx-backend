from datetime import datetime
import logging
from fastapi_cache.decorator import cache
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import Response

from models.store import BugReportComment
from dependencies.users import is_user_stuff
from schemas.pagination import PaginationSchema
from crud.users import crud_user
from schemas.users import UserDataSchema
from schemas.store import BugCommentInfoScheme, BugCommentScheme, BugReportCreateSchema, BugReportInfoSchema
from dependencies.db import get_async_session
from dependencies.auth import get_current_user
from models.users import Users
from crud.store import crud_report, crud_comments

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
)


@router.post("/create")
async def ceate_report(
    report_data: BugReportCreateSchema,
    user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> dict:

    try:
        is_vip = True if user.is_vip else False
        time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        user_name = user.username

        report_obj = report_data.dict()

        report_obj.update(
            {
                "user": user.id,
                "body": f"from: {user_name} at: {time} problem:{report_data.body} ",
                "is_vip": is_vip,
            }
        )

        print(report_data)

        await crud_report.create(db, obj_in=report_obj)

        return {"detail": "report was successfuly sent"}

    except HTTPException as e:
        raise e

    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during bug report creating",
        )


@cache(expire=60)
@router.get(
    "/all",
    dependencies=[Depends(is_user_stuff)],
    response_model=PaginationSchema[BugReportInfoSchema],
)
async def get_reports(
    request: Request,
    response: Response,
    offset: int = Query(default=0),
    limit: int = Query(default=2),
    db: AsyncSession = Depends(get_async_session),
) -> PaginationSchema[BugReportInfoSchema]:

    try:
        reports_list = []
        reports, total = await crud_report.get_multi_filtered(
            db,
            limit=limit,
            offset=offset,
            is_activated=False,
            activated_field_name="is_closed",
        )
        for report in reports:
            report_data = report.dict()
            user = await crud_user.get(db, id=report.user)
            report_data.update({"user": UserDataSchema(**user.dict()).dict()})
            reports_list.append(BugReportInfoSchema(**report_data))

        return PaginationSchema[BugReportInfoSchema](
            total=total,
            items=reports_list,
            offset=offset,
            limit=limit,
        )

    except HTTPException as e:
        raise e

    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during bug report fetching",
        )


@router.put(
    "/close/{id}",
    dependencies=[Depends(is_user_stuff)],
)
async def close_report(id: int, db: AsyncSession = Depends(get_async_session)) -> dict:
    try:
        report = await crud_report.update(db, id=id, obj_in={"is_closed": True})
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        return {"detail": f"report id: {id} was closed"}

    except HTTPException as e:
        raise e

    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during closing report",
        )


@cache(expire=60)
@router.get(
    "/id/{report_id}",
    dependencies=[Depends(is_user_stuff)],
    response_model=BugReportInfoSchema,
)
async def get_report_by_id(
    request: Request,
    response: Response,
    report_id: int,  # Correctly capture the path parameter
    db: AsyncSession = Depends(get_async_session),
) -> BugReportInfoSchema:

    try:
        # Ensure you use the correct variable name to fetch the report
        report = await crud_report.get(db, id=report_id)

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        report_data = report.dict()

        # Assuming crud_user.get is an async function; if not, you need to adjust it
        user = await crud_user.get(db, id=report.user)

        # This assumes UserDataSchema can be initialized directly from user object
        # Adjust according to your actual schema and data retrieval methods
        report_data.update({"user": UserDataSchema(**user.dict()).dict()})

        return report_data

    except HTTPException as e:
        raise e

    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during getting report",
        )




@router.post("/{bug_id}/create-comment", response_model=BugCommentInfoScheme, dependencies=[Depends(is_user_stuff)])
async def add_comment_to_bug(bug_id: int, comment_data: BugCommentScheme, user: Users = Depends(get_current_user), db: AsyncSession = Depends(get_async_session)):
    # Ensure the bug exists
    try:
        bug = await crud_report.get(db, id=bug_id)
        if not bug:
            raise HTTPException(status_code=404, detail="Bug not found")
        
        # Use 'user_id' that matches the model attribute
        comment = await crud_comments.create(db, obj_in={
            'bug_report_id': bug_id,
            'body': comment_data.body,
            'user_id': user.id  # Ensure this is a UUID that matches your User model's ID field
        })
        
        # Assuming you'll adjust BugCommentInfoScheme and response construction accordingly
        return BugCommentInfoScheme(time_stamp=comment.time_stamp, author=user.username, body=comment.body)

    
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during email verification",
        )

@router.get("/{bug_report_id}/comments/", response_model=PaginationSchema[BugCommentInfoScheme])
async def read_comments_for_bug(
    bug_report_id: int,
    db: AsyncSession = Depends(get_async_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=1000)
):
    comments, total = await crud_comments.get_comments_for_bug_paginated(db, bug_report_id=bug_report_id, offset=offset, limit=limit)
    
    # The following assumes you have a method to get the user's name from the user_id.
    # You may need to adjust this part based on how your User model and relationships are set up.
    comments_info = [BugCommentInfoScheme(time_stamp=comment.time_stamp, author="Author Name", body=comment.body) for comment in comments]

    return PaginationSchema[BugCommentInfoScheme](
        items=comments_info,
        total=total,
        offset=offset,
        limit=limit,
        detail="ok"
    )