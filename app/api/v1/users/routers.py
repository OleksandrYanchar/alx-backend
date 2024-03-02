from fastapi import APIRouter
from api.v1.users.auth import router as auth_router
from api.v1.users.profile import router as profiles_router

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

router.include_router(auth_router)
router.include_router(profiles_router)
