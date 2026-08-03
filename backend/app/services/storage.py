"""Document storage boundary: local files for development, Azure Blob for production."""

from dataclasses import dataclass
from pathlib import Path

from app.config import settings


class StorageConfigurationError(RuntimeError):
    pass


class DocumentStorage:
    def write_bytes(self, key: str, contents: bytes) -> None:
        raise NotImplementedError

    def read_bytes(self, key: str) -> bytes:
        raise NotImplementedError

    def healthcheck(self) -> None:
        raise NotImplementedError


@dataclass
class LocalDocumentStorage(DocumentStorage):
    root: Path

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root.resolve() not in path.parents:
            raise StorageConfigurationError("Document storage key escaped the configured root.")
        return path

    def write_bytes(self, key: str, contents: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)

    def read_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def healthcheck(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.root.is_dir():
            raise StorageConfigurationError("Local upload directory is unavailable.")


class AzureBlobDocumentStorage(DocumentStorage):
    def __init__(self, connection_string: str, container: str) -> None:
        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError as exc:
            raise StorageConfigurationError(
                "azure-storage-blob must be installed for Azure Blob Storage."
            ) from exc
        self.container = BlobServiceClient.from_connection_string(
            connection_string
        ).get_container_client(container)

    def write_bytes(self, key: str, contents: bytes) -> None:
        self.container.upload_blob(name=key, data=contents, overwrite=True)

    def read_bytes(self, key: str) -> bytes:
        return self.container.download_blob(key).readall()

    def healthcheck(self) -> None:
        self.container.get_container_properties()


def build_document_key(package_id: str, document_id: str, file_name: str) -> str:
    return f"packages/{package_id}/{document_id}_{file_name}"


def legacy_local_document_key(package_id: str, document_id: str, file_name: str) -> str:
    """Read documents written before storage_key was introduced."""
    return f"{package_id}/{document_id}_{file_name}"


def get_document_storage() -> DocumentStorage:
    if settings.storage_backend == "local":
        return LocalDocumentStorage(Path(settings.upload_dir).resolve())
    if settings.storage_backend == "azure_blob":
        if not settings.azure_storage_connection_string or not settings.azure_storage_container:
            raise StorageConfigurationError(
                "Azure Blob Storage requires AZURE_STORAGE_CONNECTION_STRING and AZURE_STORAGE_CONTAINER."
            )
        return AzureBlobDocumentStorage(
            settings.azure_storage_connection_string, settings.azure_storage_container
        )
    raise StorageConfigurationError(f"Unsupported storage backend: {settings.storage_backend}")
