from datetime import date, timedelta
import logging
from pathlib import Path
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from services.email import report_email_sender
from crud.posts import crud_post
from crud.users import crud_user
from dependencies.db import get_async_session
from schemas.admin import DailyReportScheme
from utils.admin import calculate_percentage_change, generate_report_file
from configs.general import admins_emails


async def generate_report(
    db: AsyncSession = Depends(get_async_session),
) -> DailyReportScheme:

    try:
        today = date.today()
        yesterday = today - timedelta(days=1)

        users, total_users = await crud_user.get_multi_filtered(db)
        users_before_today = await crud_user.get_total_before(db, "joined_at", today)
        users_before_yesterday = await crud_user.get_total_before(
            db, "joined_at", yesterday
        )

        vips, total_vips = await crud_user.get_multi_filtered(db, is_vip=True)
        vips_before_today = await crud_user.get_total_before(db, "viped_at", today)
        vips_before_yesterday = await crud_user.get_total_before(
            db, "viped_at", yesterday
        )

        posts, total_posts = await crud_post.get_multi_filtered(db)
        posts_before_today = await crud_post.get_total_before(db, "created_at", today)
        posts_before_yesterday = await crud_post.get_total_before(
            db, "created_at", yesterday
        )

        new_users = total_users - users_before_today
        new_posts = total_posts - posts_before_today
        new_vips = total_vips - vips_before_today

        new_users_yesterday = total_users - users_before_yesterday
        new_posts_yesterday = total_posts - posts_before_yesterday
        new_vips_yesterday = total_vips - vips_before_yesterday

        activated, total_activated = await crud_user.get_multi_filtered(
            db, is_activated=True
        )

        users_change = await calculate_percentage_change(new_users, new_users_yesterday)
        posts_change = await calculate_percentage_change(new_posts, new_posts_yesterday)
        vips_change = await calculate_percentage_change(new_vips, new_vips_yesterday)

        posts_average_price = await crud_post.get_average_price(db)

        report_data: dict = {
            "total_users": total_users,
            "total_activated": total_activated,
            "total_posts": total_posts,
            "total_vips": total_vips,
            "new_users": new_users,
            "new_posts": new_posts,
            "new_vips": new_vips,
            "users_change": users_change,
            "posts_change": posts_change,
            "vips_change": vips_change,
            "posts_average_price": posts_average_price,
        }

        report_path = await generate_report_file(report_data)

        # Extract just the file name from the full path
        report_file_name = Path(report_path).name

        print(admins_emails)
        # Now pass the file name of the report
        await report_email_sender.send_email(admins_emails, None, report_file_name)

        return DailyReportScheme(**report_data)

    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="An error occurred")
