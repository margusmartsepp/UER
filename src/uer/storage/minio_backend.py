"""
MinIO backend for S3-compatible storage.

Local development storage using MinIO Docker container.
"""

import io
import os
from datetime import datetime

from minio import Minio
from minio.commonconfig import COMPLIANCE as MINIO_COMPLIANCE
from minio.commonconfig import GOVERNANCE as MINIO_GOVERNANCE
from minio.error import S3Error
from minio.retention import Retention as MinioRetention

from .base import (
    BucketNotFoundError,
    ObjectMetadata,
    ObjectNotFoundError,
    Retention,
    RetentionMode,
    StorageError,
)


class MinIOBackend:
    """
    MinIO S3-compatible storage backend.

    Uses MinIO Python SDK for local S3-compatible storage.
    Perfect for development and testing.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        secure: bool | None = None,
    ):
        """
        Initialize MinIO backend from environment variables.

        Environment variables:
            MINIO_ENDPOINT: MinIO server endpoint (default: localhost:9000)
            MINIO_ACCESS_KEY: Access key (default: minioadmin)
            MINIO_SECRET_KEY: Secret key (default: minioadmin)
            MINIO_SECURE: Use HTTPS (default: false)
        """
        self.endpoint = endpoint or os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = access_key or os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = secret_key or os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.secure = (
            secure if secure is not None else os.getenv("MINIO_SECURE", "false").lower() == "true"
        )

        self.client = Minio(
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )

        # Track if buckets have been initialized
        self._buckets_initialized = False
        self.default_buckets = ["uer-context", "uer-skills", "uer-templates"]

    def _ensure_default_buckets(self):
        """Create default buckets if they don't exist (lazy initialization)."""
        if self._buckets_initialized:
            return

        for bucket in self.default_buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
            except S3Error as e:
                # Ignore if bucket already exists (race condition)
                if e.code != "BucketAlreadyOwnedByYou":
                    raise StorageError(f"Failed to create bucket {bucket}: {e}")

        self._buckets_initialized = True

    async def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> ObjectMetadata:
        """Store object in MinIO."""
        try:
            # Lazy initialization of default buckets
            self._ensure_default_buckets()

            # Ensure bucket exists
            if not self.client.bucket_exists(bucket):
                raise BucketNotFoundError(bucket)

            # Upload object
            result = self.client.put_object(
                bucket_name=bucket,
                object_name=key,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type,
                metadata=metadata or {},
            )

            return ObjectMetadata(
                bucket=bucket,
                key=key,
                size=len(data),
                content_type=content_type,
                last_modified=datetime.utcnow(),
                etag=result.etag,
                version_id=result.version_id,
                metadata=metadata or {},
            )

        except S3Error as e:
            if e.code == "NoSuchBucket":
                raise BucketNotFoundError(bucket)
            raise StorageError(f"Failed to put object s3://{bucket}/{key}: {e}")

    async def get_object(self, bucket: str, key: str) -> tuple[bytes, ObjectMetadata]:
        """Retrieve object from MinIO."""
        try:
            # Lazy initialization of default buckets
            self._ensure_default_buckets()

            # Get object data
            response = self.client.get_object(bucket, key)
            data = response.read()
            response.close()
            response.release_conn()

            # Get object metadata
            stat = self.client.stat_object(bucket, key)

            metadata = ObjectMetadata(
                bucket=bucket,
                key=key,
                size=stat.size,
                content_type=stat.content_type or "application/octet-stream",
                last_modified=stat.last_modified,
                etag=stat.etag,
                version_id=stat.version_id,
                metadata=stat.metadata or {},
            )

            return data, metadata

        except S3Error as e:
            if e.code == "NoSuchKey":
                raise ObjectNotFoundError(bucket, key)
            elif e.code == "NoSuchBucket":
                raise BucketNotFoundError(bucket)
            raise StorageError(f"Failed to get object s3://{bucket}/{key}: {e}")

    async def delete_object(self, bucket: str, key: str) -> bool:
        """Delete object from MinIO."""
        try:
            # Check if object exists first
            exists = await self.object_exists(bucket, key)
            if not exists:
                return False

            self.client.remove_object(bucket, key)
            return True

        except S3Error as e:
            if e.code == "NoSuchBucket":
                raise BucketNotFoundError(bucket)
            raise StorageError(f"Failed to delete object s3://{bucket}/{key}: {e}")

    async def list_objects(
        self, bucket: str, prefix: str = "", recursive: bool = True
    ) -> list[ObjectMetadata]:
        """List objects in bucket with optional prefix filter."""
        try:
            # Lazy initialization of default buckets
            self._ensure_default_buckets()

            # Ensure bucket exists
            if not self.client.bucket_exists(bucket):
                raise BucketNotFoundError(bucket)

            objects = []
            for obj in self.client.list_objects(bucket, prefix=prefix, recursive=recursive):
                objects.append(
                    ObjectMetadata(
                        bucket=bucket,
                        key=obj.object_name,
                        size=obj.size,
                        content_type="",  # Not available in list_objects
                        last_modified=obj.last_modified,
                        etag=obj.etag,
                        version_id=obj.version_id,
                        metadata={},  # Not available in list_objects
                    )
                )

            return objects

        except S3Error as e:
            if e.code == "NoSuchBucket":
                raise BucketNotFoundError(bucket)
            raise StorageError(f"Failed to list objects in bucket {bucket}: {e}")

    async def object_exists(self, bucket: str, key: str) -> bool:
        """Check if object exists in MinIO."""
        try:
            self.client.stat_object(bucket, key)
            return True
        except S3Error as e:
            if e.code in ("NoSuchKey", "NoSuchBucket"):
                return False
            raise StorageError(f"Failed to check object existence s3://{bucket}/{key}: {e}")

    async def set_object_retention(self, bucket: str, key: str, retention: Retention) -> None:
        """
        Set WORM retention on object.

        Requires bucket created with object_lock=True.
        """
        try:
            # Convert UER retention to MinIO retention
            mode = (
                MINIO_COMPLIANCE if retention.mode == RetentionMode.COMPLIANCE else MINIO_GOVERNANCE
            )
            minio_retention = MinioRetention(mode, retention.retain_until_date)

            self.client.set_object_retention(bucket, key, minio_retention)

        except S3Error as e:
            if e.code == "NoSuchKey":
                raise ObjectNotFoundError(bucket, key)
            elif e.code == "NoSuchBucket":
                raise BucketNotFoundError(bucket)
            elif e.code == "InvalidBucketState":
                raise StorageError(
                    f"Bucket {bucket} does not have object locking enabled. "
                    "Create bucket with object_lock=True to use retention."
                )
            raise StorageError(f"Failed to set retention on s3://{bucket}/{key}: {e}")

    async def get_object_retention(self, bucket: str, key: str) -> Retention | None:
        """Get retention settings for object."""
        try:
            minio_retention = self.client.get_object_retention(bucket, key)

            if not minio_retention:
                return None

            # Convert MinIO retention to UER retention
            mode = (
                RetentionMode.COMPLIANCE
                if minio_retention.mode == MINIO_COMPLIANCE
                else RetentionMode.GOVERNANCE
            )

            return Retention(mode=mode, retain_until_date=minio_retention.retain_until_date)

        except S3Error as e:
            if e.code == "NoSuchKey":
                raise ObjectNotFoundError(bucket, key)
            elif e.code == "NoSuchBucket":
                raise BucketNotFoundError(bucket)
            elif e.code == "NoSuchObjectLockConfiguration":
                return None  # No retention set
            raise StorageError(f"Failed to get retention for s3://{bucket}/{key}: {e}")
