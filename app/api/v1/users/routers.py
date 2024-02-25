from fastapi import APIRouter
from api.v1.users.auth import router as auth_router

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

router.include_router(auth_router)
