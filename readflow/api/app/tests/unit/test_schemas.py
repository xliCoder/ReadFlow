import pytest
from pydantic import ValidationError

from app.schemas.content import ContentUploadResponse


class FakeSource:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_upload_response_valid():
    data = {
        'source_id': '550e8400-e29b-41d4-a716-446655440000',
        'filename': 'test.pdf',
        'source_type': 'pdf',
        'page_count': 3,
        'total_chars': 1234,
        'extracted_text_preview': 'preview',
        'status': 'parsed',
        'file_size_bytes': 5678,
    }
    response = ContentUploadResponse(**data)
    assert response.source_id == data['source_id']
    assert response.filename == 'test.pdf'
    assert response.status == 'parsed'


def test_upload_response_from_orm():
    source = FakeSource(
        id='550e8400-e29b-41d4-a716-446655440000',
        filename='orm.pdf',
        source_type='pdf',
        page_count=1,
        total_chars=100,
        extracted_text_preview='hello',
        status='parsed',
        file_size_bytes=200,
    )
    response = ContentUploadResponse.model_validate(source)
    assert response.source_id == source.id
    assert response.filename == source.filename


def test_upload_response_missing_required():
    with pytest.raises(ValidationError):
        ContentUploadResponse(filename='missing_id.pdf')


def test_upload_response_defaults():
    response = ContentUploadResponse(
        source_id='550e8400-e29b-41d4-a716-446655440000',
        filename='test.pdf',
        source_type='pdf',
        page_count=1,
        total_chars=10,
        extracted_text_preview='x',
        status='parsed',
        file_size_bytes=1,
    )
    assert response.source_type == 'pdf'
