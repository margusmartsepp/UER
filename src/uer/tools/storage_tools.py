"""
MCP tools for S3-compatible storage operations.

Exposes put, get, list, delete, and exists operations via MCP protocol.
"""

import json
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from ..storage import StorageManager, ObjectNotFoundError, BucketNotFoundError


# Global storage manager (will be initialized by server)
_storage: StorageManager | None = None


def init_storage(storage: StorageManager):
    """Initialize global storage manager."""
    global _storage
    _storage = storage


def get_storage() -> StorageManager:
    """Get global storage manager."""
    if _storage is None:
        raise RuntimeError("Storage not initialized. Call init_storage() first.")
    return _storage


# Tool: storage_put


def get_storage_put_tool() -> Tool:
    """Get storage_put tool definition."""
    return Tool(
        name="storage_put",
        description="""Store content at URI in S3-compatible storage.

Supports two URI schemes:
1. S3-native: s3://bucket-name/prefix/key
2. Registry alias: registry://type/key → s3://uer-{type}/key

Examples:
- storage_put("s3://uer-context/analysis/report.json", '{"result": "..."}', "application/json")
- storage_put("registry://context/report.json", '{"result": "..."}', "application/json")
- storage_put("registry://skills/my-skill/SKILL.md", skill_content, "text/markdown")
""",
        inputSchema={
            "type": "object",
            "properties": {
                "uri": {
                    "type": "string",
                    "description": "Storage URI (s3://bucket/key or registry://type/key)",
                },
                "content": {
                    "type": "string",
                    "description": "Content to store (string or JSON)",
                },
                "content_type": {
                    "type": "string",
                    "description": "MIME type (e.g., application/json, text/markdown)",
                    "default": "text/plain",
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional user metadata (key-value pairs)",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": ["uri", "content"],
        },
    )


async def storage_put(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Store content at URI.

    Args:
        arguments: Tool arguments with uri, content, content_type, metadata

    Returns:
        List of TextContent with result
    """
    storage = get_storage()

    uri = arguments["uri"]
    content = arguments["content"]
    content_type = arguments.get("content_type", "text/plain")
    metadata = arguments.get("metadata")

    try:
        # Store object
        result = await storage.put(uri, content, content_type, metadata)

        # Return metadata
        response = {
            "success": True,
            "uri": uri,
            "metadata": {
                "bucket": result.bucket,
                "key": result.key,
                "size": result.size,
                "content_type": result.content_type,
                "etag": result.etag,
            },
        }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        return [
            TextContent(
                type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2)
            )
        ]


# Tool: storage_get


def get_storage_get_tool() -> Tool:
    """Get storage_get tool definition."""
    return Tool(
        name="storage_get",
        description="""Retrieve content from URI in S3-compatible storage.

Supports both s3:// and registry:// URI schemes.

Examples:
- storage_get("s3://uer-context/analysis/report.json")
- storage_get("registry://context/report.json")
- storage_get("registry://skills/my-skill/SKILL.md")
""",
        inputSchema={
            "type": "object",
            "properties": {
                "uri": {
                    "type": "string",
                    "description": "Storage URI (s3://bucket/key or registry://type/key)",
                },
            },
            "required": ["uri"],
        },
    )


async def storage_get(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Retrieve content from URI.

    Args:
        arguments: Tool arguments with uri

    Returns:
        List of TextContent with content and metadata
    """
    storage = get_storage()
    uri = arguments["uri"]

    try:
        # Get object
        data, metadata = await storage.get(uri)
        content = data.decode("utf-8")

        # Return content and metadata
        response = {
            "success": True,
            "uri": uri,
            "content": content,
            "metadata": {
                "bucket": metadata.bucket,
                "key": metadata.key,
                "size": metadata.size,
                "content_type": metadata.content_type,
                "last_modified": metadata.last_modified.isoformat(),
            },
        }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except ObjectNotFoundError as e:
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": f"Object not found: {uri}"}, indent=2),
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2)
            )
        ]


# Tool: storage_list


def get_storage_list_tool() -> Tool:
    """Get storage_list tool definition."""
    return Tool(
        name="storage_list",
        description="""List objects under URI prefix in S3-compatible storage.

Supports both s3:// and registry:// URI schemes.
Use recursive=false to list only top-level (useful for listing skills/folders).

Examples:
- storage_list("s3://uer-context/analysis/") - List all analysis files
- storage_list("registry://skills/", false) - List all skills (non-recursive)
- storage_list("registry://skills/financial-analysis/") - List all files in a skill
""",
        inputSchema={
            "type": "object",
            "properties": {
                "uri": {
                    "type": "string",
                    "description": "Storage URI prefix (s3://bucket/prefix/ or registry://type/prefix/)",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "List recursively (default: true)",
                    "default": True,
                },
            },
            "required": ["uri"],
        },
    )


async def storage_list(arguments: dict[str, Any]) -> list[TextContent]:
    """
    List objects under URI prefix.

    Args:
        arguments: Tool arguments with uri, recursive

    Returns:
        List of TextContent with object list
    """
    storage = get_storage()
    uri = arguments["uri"]
    recursive = arguments.get("recursive", True)

    try:
        # List objects
        objects = await storage.list(uri, recursive)

        # Convert to response format
        response = {
            "success": True,
            "uri": uri,
            "count": len(objects),
            "objects": [
                {
                    "key": obj.key,
                    "size": obj.size,
                    "last_modified": obj.last_modified.isoformat(),
                }
                for obj in objects
            ],
        }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except BucketNotFoundError as e:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"success": False, "error": f"Bucket not found: {uri}"}, indent=2
                ),
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2)
            )
        ]


# Tool: storage_delete


def get_storage_delete_tool() -> Tool:
    """Get storage_delete tool definition."""
    return Tool(
        name="storage_delete",
        description="""Delete object at URI in S3-compatible storage.

Supports both s3:// and registry:// URI schemes.

Examples:
- storage_delete("s3://uer-context/old-report.json")
- storage_delete("registry://context/old-report.json")
""",
        inputSchema={
            "type": "object",
            "properties": {
                "uri": {
                    "type": "string",
                    "description": "Storage URI (s3://bucket/key or registry://type/key)",
                },
            },
            "required": ["uri"],
        },
    )


async def storage_delete(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Delete object at URI.

    Args:
        arguments: Tool arguments with uri

    Returns:
        List of TextContent with result
    """
    storage = get_storage()
    uri = arguments["uri"]

    try:
        # Delete object
        deleted = await storage.delete(uri)

        response = {"success": True, "uri": uri, "deleted": deleted}

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        return [
            TextContent(
                type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2)
            )
        ]


# Tool: storage_exists


def get_storage_exists_tool() -> Tool:
    """Get storage_exists tool definition."""
    return Tool(
        name="storage_exists",
        description="""Check if object exists at URI in S3-compatible storage.

Supports both s3:// and registry:// URI schemes.

Examples:
- storage_exists("s3://uer-context/report.json")
- storage_exists("registry://context/report.json")
""",
        inputSchema={
            "type": "object",
            "properties": {
                "uri": {
                    "type": "string",
                    "description": "Storage URI (s3://bucket/key or registry://type/key)",
                },
            },
            "required": ["uri"],
        },
    )


async def storage_exists(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Check if object exists at URI.

    Args:
        arguments: Tool arguments with uri

    Returns:
        List of TextContent with result
    """
    storage = get_storage()
    uri = arguments["uri"]

    try:
        # Check existence
        exists = await storage.exists(uri)

        response = {"success": True, "uri": uri, "exists": exists}

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        return [
            TextContent(
                type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2)
            )
        ]
