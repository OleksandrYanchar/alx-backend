from fastapi import APIRouter
from api.v1.users.routers import router as user_router
from api.v1.store.routers import router as store_router
from api.v1.store.admin import router as admin_router

router = APIRouter(
    prefix="/v1",
    tags=["v1"],
)


router.include_router(user_router)
router.include_router(store_router)
router.include_router(admin_router)