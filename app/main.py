import uvicorn
from fastapi import FastAPI
from fastapi.responses import UJSONResponse
from api.v1.routers import router as v1_router
from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from configs.general import STATIC_FILES_PATH, setup_logger
from configs.db import REDIS_URL
from redis import asyncio as aioredis

router = APIRouter(
    prefix="/api",
    tags=["api"],
)

router.include_router(v1_router)


app = FastAPI(
    title="FastAPI Starter Project",
    description="FastAPI Starter Project",
    version="1.0",
    docs_url="/api/docs/",
    redoc_url="/api/redoc/",
    openapi_url="/api/openapi.json",
    default_response_class=UJSONResponse,
)


app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    app.mount("/static", StaticFiles(directory=STATIC_FILES_PATH))
except Exception:
    STATIC_FILES_PATH = "../{STATIC_FILES_PATH}"
    app.mount("/static", StaticFiles(directory=f"{STATIC_FILES_PATH}"))


setup_logger(STATIC_FILES_PATH)


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)


@app.on_event("startup")
async def startup_event():
    redis = aioredis.from_url(REDIS_URL, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
