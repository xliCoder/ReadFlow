from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.one_api_client import OneAPIClient, OneAPIError
from app.dependencies import get_db_session
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService
from app.services.context_builder import ContextBuilder
from app.services.vector_service import VectorService, VectorServiceError

router = APIRouter(prefix='/api/v1/chat')

context_builder = ContextBuilder(
    one_api_client=OneAPIClient(
        base_url=settings.one_api_url,
        api_key=settings.one_api_key,
    ),
    vector_service=VectorService(milvus_uri=settings.milvus_uri),
)
chat_service = ChatService(
    one_api_client=OneAPIClient(
        base_url=settings.one_api_url,
        api_key=settings.one_api_key,
    ),
    context_builder=context_builder,
)


async def _stream_response(source_id: str, question: str):
    try:
        async for event in chat_service.stream_chat(source_id, question):
            yield event
    except OneAPIError as exc:
        yield f'event: error\ndata: {{"detail": "Chat model failed: {exc}"}}\n\n'
    except Exception as exc:
        yield f'event: error\ndata: {{"detail": "Chat failed: {exc}"}}\n\n'


@router.post('')
async def chat(
    request: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    del db  # reserved for future user-scoped retrieval
    try:
        await context_builder.build(request.source_id, request.question, request.top_k)
    except OneAPIError as exc:
        raise HTTPException(status_code=502, detail=f'Embedding failed: {exc}') from exc
    except VectorServiceError as exc:
        raise HTTPException(status_code=502, detail=f'Retrieval failed: {exc}') from exc

    return StreamingResponse(
        _stream_response(request.source_id, request.question),
        media_type='text/event-stream',
    )
