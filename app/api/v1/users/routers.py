from fastapi import APIRouter
from api.v1.users.auth import router as user_router
 
router = APIRouter(
    prefix="/users",
    tags=["users"],
)


router.include_router(user_router) 
