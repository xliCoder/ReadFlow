import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.exceptions import ParseException, ReadFlowException
from app.models.base import Base, engine


@pytest.mark.asyncio
async def test_get_db_session_yields_async_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async for session in get_db_session():
        assert isinstance(session, AsyncSession)


def test_read_flow_exception_base():
    exc = ReadFlowException(status_code=500, detail='base error')
    assert exc.status_code == 500
    assert exc.detail == 'base error'


def test_parse_exception():
    exc = ParseException('bad pdf')
    assert exc.status_code == 422
    assert exc.detail == 'bad pdf'
    assert isinstance(exc, ReadFlowException)
