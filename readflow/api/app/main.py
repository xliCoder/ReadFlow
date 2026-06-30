from fastapi import FastAPI

from app.config import settings
from app.routers.content import router as content_router

app = FastAPI(title=settings.app_name, version='0.1.0')
app.include_router(content_router)
