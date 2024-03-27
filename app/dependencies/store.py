from fastapi import Depends, HTTPException, status
from crud.posts import crud_post
from dependencies.db import get_async_session
from models.users import Users
from dependencies.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.users import is_user_stuff


async def is_user_owner_or_stuff(
    post_id: str,
    user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> bool:

    if await is_user_stuff(user):
        return True

    if not user.is_activated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User isn't activated"
        )
    post = crud_post.get(db, id=post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post with this id dosen't exist",
        )

    if user.id != post.owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This user isn't owner of this post",
        )

    return True
