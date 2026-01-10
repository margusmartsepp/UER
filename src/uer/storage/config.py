"""
Storage configuration with support for optional/disabled backends.

Supports three deployment scenarios:
1. Docker MinIO (default for development)
2. Custom S3-compatible storage (production)
3. Disabled storage (LLM/MCP features only)
"""

import os


class StorageConfig:
    """Storage backend configuration."""

    def __init__(self):
        """Initialize storage configuration from environment."""
        # Check if storage is explicitly disabled
        self.enabled = os.getenv("STORAGE_ENABLED", "true").lower() in ("true", "1", "yes")

        # Backend type: minio, s3, or disabled
        self.backend_type = os.getenv("STORAGE_BACKEND", "minio").lower()

        # MinIO/S3 configuration
        self.endpoint = os.getenv("MINIO_ENDPOINT", os.getenv("S3_ENDPOINT", "localhost:9000"))
        self.access_key = os.getenv("MINIO_ACCESS_KEY", os.getenv("S3_ACCESS_KEY", "minioadmin"))
        self.secret_key = os.getenv("MINIO_SECRET_KEY", os.getenv("S3_SECRET_KEY", "minioadmin"))
        self.secure = os.getenv("MINIO_SECURE", os.getenv("S3_SECURE", "false")).lower() in (
            "true",
            "1",
            "yes",
        )
        self.region = os.getenv("S3_REGION", "us-east-1")

        # Default buckets to create
        self.default_buckets = ["uer-context", "uer-skills", "uer-templates"]

    def is_available(self) -> bool:
        """Check if storage backend is available and enabled."""
        if not self.enabled:
            return False

        # Storage is considered available if explicitly enabled
        # Actual connection will be tested lazily on first use
        return True

    def get_display_info(self) -> dict:
        """Get human-readable configuration info."""
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "Storage features are disabled. Set STORAGE_ENABLED=true to enable.",
            }

        return {
            "status": "enabled",
            "backend": self.backend_type,
            "endpoint": self.endpoint,
            "secure": self.secure,
            "buckets": self.default_buckets,
        }


# Global storage configuration
storage_config = StorageConfig()
