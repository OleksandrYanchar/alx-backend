from fastapi import Depends, HTTPException, status
from models.users import Users
from dependencies.auth import get_current_user


async def is_user_activated(
    user: Users = Depends(get_current_user),
) -> bool:
    if user.is_activated:
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User isn't activated"
        )


async def is_user_stuff(
    user: Users = Depends(get_current_user),
) -> bool:
    if user.is_staff:
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User hasn't enough permissions",
        )

async def is_user_not_activated(user: Users = Depends(get_current_user)):
    if user.is_activated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is activated",
        )
    else:
        return True
