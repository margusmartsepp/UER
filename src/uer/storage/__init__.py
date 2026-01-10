"""
S3-compatible storage layer for UER.

This module provides S3-native storage with support for:
- MinIO (local development)
- AWS S3 (cloud production)
- Azure Blob Storage (enterprise)
- NetApp StorageGRID (enterprise)

See docs/ADR-002-S3-Storage-Architecture.md for details.
"""

from .base import (
    StorageBackend,
    ObjectMetadata,
    Retention,
    RetentionMode,
    StorageError,
    ObjectNotFoundError,
    BucketNotFoundError,
)
from .manager import StorageManager

__all__ = [
    "StorageBackend",
    "ObjectMetadata",
    "Retention",
    "RetentionMode",
    "StorageError",
    "ObjectNotFoundError",
    "BucketNotFoundError",
    "StorageManager",
]
