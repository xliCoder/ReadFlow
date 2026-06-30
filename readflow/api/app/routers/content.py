from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db_session
from app.models.content import ContentSource
from app.schemas.content import ContentUploadResponse
from app.services.pdf_service import PDFParseError, pdf_service

router = APIRouter(prefix='/api/v1/content')


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
        status='parsed',
        file_size_bytes=len(file_bytes),
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    return ContentUploadResponse.model_validate(source)
