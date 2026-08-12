from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vendor Onboarding Document Intelligence API"
    environment: str = "development"
    database_url: str = Field(
        default="sqlite+pysqlite:///./dev.db"
    )
    upload_dir: str = "uploads"
    storage_backend: str = "local"
    azure_storage_connection_string: str | None = None
    azure_storage_container: str | None = None
    document_intelligence_endpoint: str | None = None
    document_intelligence_api_key: str | None = None
    auth_required: bool = False
    entra_tenant_id: str | None = None
    entra_api_audience: str | None = None
    development_actor_id: str = "aria.han"
    development_actor_role: str = "admin"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def validate_production_configuration(self) -> None:
        if self.environment != "production":
            return
        missing: list[str] = []
        if self.database_url.startswith("sqlite"):
            missing.append("a managed PostgreSQL DATABASE_URL")
        if self.storage_backend != "azure_blob":
            missing.append("STORAGE_BACKEND=azure_blob")
        if not self.azure_storage_connection_string or not self.azure_storage_container:
            missing.append("Azure Blob Storage configuration")
        if not self.auth_required:
            missing.append("AUTH_REQUIRED=true")
        if not self.entra_tenant_id or not self.entra_api_audience:
            missing.append("ENTRA_TENANT_ID and ENTRA_API_AUDIENCE")
        if not self.allowed_cors_origins or any(
            "localhost" in origin or "127.0.0.1" in origin
            for origin in self.allowed_cors_origins
        ):
            missing.append("a non-localhost CORS_ORIGINS value")
        if missing:
            raise ValueError("Production configuration requires " + ", ".join(missing) + ".")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
