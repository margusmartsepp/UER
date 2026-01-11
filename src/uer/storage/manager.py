"""
Storage manager with URI parsing and convenience methods.

Handles URI parsing and provides a clean interface for storage operations.
"""

from .base import ObjectMetadata, Retention, StorageBackend, StorageError
from .config import storage_config


def parse_uri(uri: str) -> tuple[str, str]:
    """
    Parse URI into (bucket, key).

    Supports two URI schemes:
    1. S3-native: s3://bucket-name/prefix/key
    2. Registry alias: registry://type/key → s3://uer-{type}/key

    Args:
        uri: URI to parse

    Returns:
        Tuple of (bucket, key)

    Raises:
        ValueError: If URI format is invalid

    Examples:
        >>> parse_uri("s3://uer-context/analysis/report.json")
        ('uer-context', 'analysis/report.json')

        >>> parse_uri("registry://context/analysis/report.json")
        ('uer-context', 'analysis/report.json')

        >>> parse_uri("registry://skills/financial-analysis/SKILL.md")
        ('uer-skills', 'financial-analysis/SKILL.md')
    """
    if uri.startswith("registry://"):
        # registry://type/key → s3://uer-{type}/key
        path = uri.replace("registry://", "")
        if "/" not in path:
            raise ValueError(f"Invalid registry URI (missing key): {uri}")

        type_name, key = path.split("/", 1)
        bucket = f"uer-{type_name}"
        return bucket, key

    elif uri.startswith("s3://"):
        # s3://bucket/key
        path = uri.replace("s3://", "")
        if "/" not in path:
            raise ValueError(f"Invalid S3 URI (missing key): {uri}")

        bucket, key = path.split("/", 1)
        return bucket, key

    else:
        raise ValueError(f"Invalid URI scheme. Must start with 's3://' or 'registry://': {uri}")


class StorageManager:
    """
    High-level storage manager with URI parsing and convenience methods.

    Wraps a StorageBackend and provides a clean interface for storage operations.
    """

    def __init__(self, backend: StorageBackend | None = None):
        """
        Initialize storage manager.

        Args:
            backend: Storage backend to use (default: MinIOBackend from environment)
        """
        self.backend: StorageBackend | None = backend
        self._backend_initialized = False

    def _ensure_backend(self) -> StorageBackend:
        """Ensure storage backend is initialized (lazy initialization)."""
        if self.backend is not None:
            return self.backend

        if self._backend_initialized:
            raise StorageError(
                "Storage backend is not available. "
                "If you're not using Docker/MinIO, add STORAGE_ENABLED=false to your env config. "
                "Otherwise, start MinIO with 'docker-compose up -d' or configure custom storage credentials."
            )

        self._backend_initialized = True

        # Check if storage is enabled
        if not storage_config.is_available():
            raise StorageError(
                "Storage is disabled. Enable with STORAGE_ENABLED=true and configure credentials."
            )

        # Create backend based on configuration
        backend_type = storage_config.backend_type

        if backend_type == "minio":
            from .minio_backend import MinIOBackend

            self.backend = MinIOBackend(
                endpoint=storage_config.endpoint,
                access_key=storage_config.access_key,
                secret_key=storage_config.secret_key,
                secure=storage_config.secure,
            )
            return self.backend
        elif backend_type == "s3":
            # Future: AWS S3 backend
            raise NotImplementedError("S3 backend not yet implemented")
        elif backend_type == "azure":
            # Future: Azure Blob backend
            raise NotImplementedError("Azure backend not yet implemented")
        else:
            raise ValueError(f"Unknown storage backend: {backend_type}")

    def is_available(self) -> bool:
        """Check if storage backend is available."""
        return storage_config.is_available()

    async def put(
        self,
        uri: str,
        data: bytes | str,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> ObjectMetadata:
        """
        Store object at URI.

        Args:
            uri: Storage URI (s3://... or registry://...)
            data: Object data (bytes or string)
            content_type: MIME type
            metadata: Optional user metadata

        Returns:
            ObjectMetadata

        Example:
            >>> meta = await storage.put(
            ...     "registry://context/report.json",
            ...     json.dumps(data),
            ...     content_type="application/json"
            ... )
        """
        backend = self._ensure_backend()
        bucket, key = parse_uri(uri)

        # Convert string to bytes if needed
        if isinstance(data, str):
            data = data.encode("utf-8")

        return await backend.put_object(bucket, key, data, content_type, metadata)

    async def get(self, uri: str) -> tuple[bytes, ObjectMetadata]:
        """
        Retrieve object from URI.

        Args:
            uri: Storage URI (s3://... or registry://...)

        Returns:
            Tuple of (data, metadata)

        Example:
            >>> data, meta = await storage.get("registry://context/report.json")
            >>> content = data.decode('utf-8')
        """
        backend = self._ensure_backend()
        bucket, key = parse_uri(uri)
        return await backend.get_object(bucket, key)

    async def get_text(self, uri: str) -> str:
        """
        Retrieve object as text.

        Args:
            uri: Storage URI

        Returns:
            Object content as string

        Example:
            >>> text = await storage.get_text("registry://templates/meeting-notes.md")
        """
        data, _ = await self.get(uri)
        return data.decode("utf-8")

    async def get_json(self, uri: str) -> dict:
        """
        Retrieve object as JSON.

        Args:
            uri: Storage URI

        Returns:
            Parsed JSON object

        Example:
            >>> data = await storage.get_json("registry://context/report.json")
        """
        import json

        text = await self.get_text(uri)
        return json.loads(text)

    async def delete(self, uri: str) -> bool:
        """
        Delete object at URI.

        Args:
            uri: Storage URI

        Returns:
            True if deleted, False if didn't exist

        Example:
            >>> deleted = await storage.delete("registry://context/old-report.json")
        """
        backend = self._ensure_backend()
        bucket, key = parse_uri(uri)
        return await backend.delete_object(bucket, key)

    async def list(self, uri: str, recursive: bool = True) -> list[ObjectMetadata]:
        """
        List objects under URI prefix.

        Args:
            uri: Storage URI prefix (e.g., "registry://skills/")
            recursive: List recursively or only top-level

        Returns:
            List of ObjectMetadata

        Example:
            >>> # List all skills (non-recursive)
            >>> skills = await storage.list("registry://skills/", recursive=False)

            >>> # List all files in a skill (recursive)
            >>> files = await storage.list("registry://skills/financial-analysis/")
        """
        backend = self._ensure_backend()
        bucket, prefix = parse_uri(uri)
        return await backend.list_objects(bucket, prefix, recursive)

    async def exists(self, uri: str) -> bool:
        """
        Check if object exists at URI.

        Args:
            uri: Storage URI

        Returns:
            True if exists, False otherwise

        Example:
            >>> exists = await storage.exists("registry://context/report.json")
        """
        backend = self._ensure_backend()
        bucket, key = parse_uri(uri)
        return await backend.object_exists(bucket, key)

    async def set_retention(self, uri: str, retention: Retention) -> None:
        """
        Set WORM retention on object (MinIO/S3 only).

        Args:
            uri: Storage URI
            retention: Retention configuration

        Example:
            >>> from datetime import datetime, timedelta
            >>> retention = Retention(
            ...     mode=RetentionMode.COMPLIANCE,
            ...     retain_until_date=datetime.now() + timedelta(days=2555)
            ... )
            >>> await storage.set_retention("registry://audit/log.json", retention)
        """
        backend = self._ensure_backend()
        bucket, key = parse_uri(uri)
        await backend.set_object_retention(bucket, key, retention)

    async def get_retention(self, uri: str) -> Retention | None:
        """
        Get retention settings for object (MinIO/S3 only).

        Args:
            uri: Storage URI

        Returns:
            Retention configuration or None

        Example:
            >>> retention = await storage.get_retention("registry://audit/log.json")
            >>> if retention:
            ...     print(f"Locked until {retention.retain_until_date}")
        """
        backend = self._ensure_backend()
        bucket, key = parse_uri(uri)
        return await backend.get_object_retention(bucket, key)
