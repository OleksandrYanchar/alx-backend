from fastapi import APIRouter
from api.v1.store.posts import router as posts_router
from api.v1.store.categories import router as categories_router
from api.v1.store.stuff.reports import router as repors_router


router = APIRouter(
    prefix="/store",
    tags=["store"],
)

router.include_router(posts_router)
router.include_router(categories_router)
router.include_router(repors_router)
