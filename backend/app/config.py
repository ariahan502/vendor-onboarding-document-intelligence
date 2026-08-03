from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vendor Onboarding Document Intelligence API"
    environment: str = "development"
    database_url: str = Field(
        default="sqlite+pysqlite:///./dev.db"
    )
    upload_dir: str = "uploads"
    document_intelligence_endpoint: str | None = None
    document_intelligence_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
