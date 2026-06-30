import asyncio
from io import BytesIO

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from reportlab.pdfgen import canvas
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.dependencies import get_db_session
from app.main import app as main_app
from app.models.base import Base


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='session')
async def test_engine():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:', echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session) -> AsyncClient:
    async def _override_get_db():
        yield db_session

    main_app.dependency_overrides[get_db_session] = _override_get_db
    transport = ASGITransport(app=main_app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        yield ac
    main_app.dependency_overrides.clear()


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 700, 'Hello, ReadFlow!')
    c.showPage()
    c.drawString(100, 700, 'Second page content.')
    c.showPage()
    c.save()
    return buffer.getvalue()


@pytest.fixture
def corrupted_pdf_bytes() -> bytes:
    return b"this is not a pdf file"
