from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ContentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    source_id: str = Field(validation_alias='id')
    filename: str
    source_type: str = 'pdf'
    page_count: int | None
    total_chars: int | None
    extracted_text_preview: str | None
    status: str
    file_size_bytes: int | None = None
    created_at: datetime | None = None


class ContentParseResult(BaseModel):
    source_id: str = ''
    filename: str
    source_type: str = 'pdf'
    page_count: int
    total_chars: int
    extracted_text_preview: str
    status: str = 'parsed'
    message: str = ''
    file_size_bytes: int | None = None
