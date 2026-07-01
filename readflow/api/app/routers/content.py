from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.one_api_client import OneAPIClient, OneAPIError
from app.dependencies import get_db_session
from app.models.content import Chunk, ContentSource
from app.schemas.content import ContentUploadResponse, IndexResponse
from app.services.chunk_service import ChunkService
from app.services.pdf_service import PDFParseError, pdf_service
from app.services.vector_service import VectorService, VectorServiceError

router = APIRouter(prefix='/api/v1/content')

chunk_service = ChunkService(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
)
one_api_client = OneAPIClient(
    base_url=settings.one_api_url,
    api_key=settings.one_api_key,
)
vector_service = VectorService(milvus_uri=settings.milvus_uri)


@router.post('/upload', response_model=ContentUploadResponse)
async def upload_pdf(
    file: Annotated[UploadFile, File(description='PDF file to upload')],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ContentUploadResponse:
    if file.content_type not in ('application/pdf', 'application/octet-stream'):
        raise HTTPException(status_code=400, detail='File must be a PDF')

    file_bytes = await file.read()
    if len(file_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail='File too large (max 50MB)')

    try:
        parse_result = await pdf_service.parse_pdf(file_bytes, file.filename or 'unknown.pdf')
    except PDFParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    source = ContentSource(
        filename=parse_result.filename,
        source_type='pdf',
        page_count=parse_result.page_count,
        total_chars=parse_result.total_chars,
        extracted_text_preview=parse_result.extracted_text_preview,
        extracted_text=parse_result.extracted_text,
        status='parsed',
        file_size_bytes=len(file_bytes),
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    return ContentUploadResponse.model_validate(source)


@router.post('/{source_id}/index', response_model=IndexResponse)
async def index_content(
    source_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> IndexResponse:
    result = await db.execute(
        select(ContentSource).where(ContentSource.id == source_id)
    )
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail='Content source not found')

    if source.status != 'parsed':
        raise HTTPException(
            status_code=409,
            detail=f'Content source must be in "parsed" state, current: {source.status}',
        )

    try:
        chunks = chunk_service.chunk_text(source.extracted_text or '')
        if not chunks:
            source.status = 'indexed'
            await db.commit()
            return IndexResponse(
                source_id=source_id,
                status='indexed',
                chunk_count=0,
                message='No chunks generated from empty text',
            )

        embeddings = await one_api_client.embed(
            [chunk.text for chunk in chunks],
            model=settings.embedding_model,
        )
        vector_service.insert_chunks(source_id, chunks, embeddings)

        for chunk in chunks:
            db.add(
                Chunk(
                    source_id=source_id,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    token_count=chunk.token_count,
                )
            )

        source.status = 'indexed'
        await db.commit()

        return IndexResponse(
            source_id=source_id,
            status='indexed',
            chunk_count=len(chunks),
        )
    except OneAPIError as exc:
        await db.rollback()
        raise HTTPException(status_code=502, detail=f'Embedding failed: {exc}') from exc
    except VectorServiceError as exc:
        await db.rollback()
        raise HTTPException(status_code=502, detail=f'Vector storage failed: {exc}') from exc
    except Exception as exc:
        await db.rollback()
        source.status = 'failed'
        await db.commit()
        raise HTTPException(status_code=500, detail=f'Indexing failed: {exc}') from exc
