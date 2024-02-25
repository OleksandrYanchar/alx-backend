import uvicorn
from fastapi import FastAPI
from fastapi.responses import UJSONResponse
from api.v1.routers import router as v1_router
from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

from configs.general import STATIC_FILES_PATH

app = FastAPI(
    title="FastAPI Starter Project",
    description="FastAPI Starter Project",
    version="1.0",
    docs_url="/api/docs/",
    redoc_url="/api/redoc/",
    openapi_url="/api/openapi.json",
    default_response_class=UJSONResponse,
)
router = APIRouter(
    prefix="/api",
    tags=["api"],
)
router.include_router(v1_router)    

app.include_router(router)

app.mount('/static', StaticFiles(directory=STATIC_FILES_PATH))

if __name__ == "__main__":
        uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)
