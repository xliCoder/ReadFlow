from fastapi import FastAPI

from app.config import settings
from app.routers.chat import router as chat_router
from app.routers.content import router as content_router

app = FastAPI(title=settings.app_name, version='0.1.0')
app.include_router(content_router)
app.include_router(chat_router)
