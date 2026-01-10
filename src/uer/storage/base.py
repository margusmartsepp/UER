"""
Base storage protocols and models for S3-compatible storage.

Defines the interface that all storage backends must implement.
"""

from abc import abstractmethod
from datetime import datetime
from enum import Enum
from typing import Protocol
from pydantic import BaseModel, Field


class RetentionMode(str, Enum):
    """WORM retention modes for compliance."""

    GOVERNANCE = "GOVERNANCE"  # Can be overridden by privileged users
    COMPLIANCE = "COMPLIANCE"  # Cannot be overridden during retention period


class Retention(BaseModel):
    """Object retention configuration for WORM compliance."""

    mode: RetentionMode
    retain_until_date: datetime

    class Config:
        use_enum_values = True


class ObjectMetadata(BaseModel):
    """Metadata for a stored object."""

    bucket: str
    key: str
    size: int
    content_type: str
    last_modified: datetime
    etag: str
    version_id: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# Storage Exceptions


class StorageError(Exception):
    """Base exception for storage errors."""

    pass


class ObjectNotFoundError(StorageError):
    """Object not found in storage."""

    def __init__(self, bucket: str, key: str):
        self.bucket = bucket
        self.key = key
        super().__init__(f"Object not found: s3://{bucket}/{key}")


class BucketNotFoundError(StorageError):
    """Bucket not found in storage."""

    def __init__(self, bucket: str):
        self.bucket = bucket
        super().__init__(f"Bucket not found: {bucket}")


class StorageBackend(Protocol):
    """
    S3-compatible storage interface.

    All storage backends (MinIO, S3, Azure, NetApp) must implement this protocol.
    """

    @abstractmethod
    async def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> ObjectMetadata:
        """
        Store object in S3-compatible storage.

        Args:
            bucket: Bucket name (e.g., "uer-context")
            key: Object key (e.g., "analysis/report.json")
            data: Object data as bytes
            content_type: MIME type (default: "application/octet-stream")
            metadata: Optional user metadata (key-value pairs)

        Returns:
            ObjectMetadata with storage details

        Raises:
            BucketNotFoundError: If bucket doesn't exist
            StorageError: On storage failure

        Example:
            >>> metadata = await storage.put_object(
            ...     bucket="uer-context",
            ...     key="analysis/report.json",
            ...     data=json.dumps(data).encode(),
            ...     content_type="application/json"
            ... )
        """
        ...

    @abstractmethod
    async def get_object(self, bucket: str, key: str) -> tuple[bytes, ObjectMetadata]:
        """
        Retrieve object from S3-compatible storage.

        Args:
            bucket: Bucket name
            key: Object key

        Returns:
            Tuple of (data, metadata)

        Raises:
            ObjectNotFoundError: If object doesn't exist
            BucketNotFoundError: If bucket doesn't exist
            StorageError: On storage failure

        Example:
            >>> data, metadata = await storage.get_object("uer-context", "report.json")
            >>> content = data.decode('utf-8')
        """
        ...

    @abstractmethod
    async def delete_object(self, bucket: str, key: str) -> bool:
        """
        Delete object from S3-compatible storage.

        Args:
            bucket: Bucket name
            key: Object key

        Returns:
            True if object was deleted, False if it didn't exist

        Raises:
            BucketNotFoundError: If bucket doesn't exist
            StorageError: On storage failure

        Example:
            >>> deleted = await storage.delete_object("uer-context", "old-report.json")
        """
        ...

    @abstractmethod
    async def list_objects(
        self, bucket: str, prefix: str = "", recursive: bool = True
    ) -> list[ObjectMetadata]:
        """
        List objects in bucket with optional prefix filter.

        Args:
            bucket: Bucket name
            prefix: Optional prefix to filter by (e.g., "analysis/")
            recursive: If True, list all objects recursively. If False, list only "top-level"

        Returns:
            List of ObjectMetadata for matching objects

        Raises:
            BucketNotFoundError: If bucket doesn't exist
            StorageError: On storage failure

        Example:
            >>> # List all skills
            >>> skills = await storage.list_objects("uer-skills", prefix="", recursive=False)
            >>> # List all files in a skill
            >>> files = await storage.list_objects("uer-skills", prefix="financial-analysis/")
        """
        ...

    @abstractmethod
    async def object_exists(self, bucket: str, key: str) -> bool:
        """
        Check if object exists in storage.

        Args:
            bucket: Bucket name
            key: Object key

        Returns:
            True if object exists, False otherwise

        Raises:
            BucketNotFoundError: If bucket doesn't exist
            StorageError: On storage failure

        Example:
            >>> exists = await storage.object_exists("uer-context", "report.json")
        """
        ...

    # Optional: WORM/compliance features

    async def set_object_retention(
        self, bucket: str, key: str, retention: Retention
    ) -> None:
        """
        Set WORM retention on object (MinIO/S3 only).

        Requires bucket created with object_lock=True.

        Args:
            bucket: Bucket name
            key: Object key
            retention: Retention configuration

        Raises:
            NotImplementedError: If backend doesn't support retention
            BucketNotFoundError: If bucket doesn't exist
            ObjectNotFoundError: If object doesn't exist
            StorageError: On storage failure

        Example:
            >>> retention = Retention(
            ...     mode=RetentionMode.COMPLIANCE,
            ...     retain_until_date=datetime.now() + timedelta(days=2555)  # 7 years
            ... )
            >>> await storage.set_object_retention("uer-audit", "log.json", retention)
        """
        raise NotImplementedError("This backend does not support object retention")

    async def get_object_retention(self, bucket: str, key: str) -> Retention | None:
        """
        Get retention settings for object (MinIO/S3 only).

        Args:
            bucket: Bucket name
            key: Object key

        Returns:
            Retention configuration or None if no retention set

        Raises:
            NotImplementedError: If backend doesn't support retention
            BucketNotFoundError: If bucket doesn't exist
            ObjectNotFoundError: If object doesn't exist
            StorageError: On storage failure

        Example:
            >>> retention = await storage.get_object_retention("uer-audit", "log.json")
            >>> if retention:
            ...     print(f"Locked until {retention.retain_until_date}")
        """
        raise NotImplementedError("This backend does not support object retention")
