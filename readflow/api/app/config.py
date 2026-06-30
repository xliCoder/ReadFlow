from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    app_name: str = 'ReadFlow API'
    debug: bool = False
    secret_key: str = 'dev-secret-change-me'

    database_url: PostgresDsn | str = 'sqlite+aiosqlite:///:memory:'
    redis_url: RedisDsn | str = 'redis://localhost:6379/0'
    rabbitmq_url: str = 'amqp://readflow:changeme@localhost:5672/'
    milvus_uri: str = 'http://localhost:19530'
    one_api_url: str = 'http://localhost:3000'

    max_upload_size_bytes: int = 50 * 1024 * 1024  # 50 MB


settings = Settings()
