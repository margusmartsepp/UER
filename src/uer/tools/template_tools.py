"""
MCP tools for Jinja2 template operations.

Exposes render, list, create, and delete operations for templates.
"""

import json
from typing import Any

from mcp.types import Tool, TextContent

from ..storage import StorageBackend
from ..storage.templates import TemplateManager


# Global template manager (will be initialized by server)
_templates: TemplateManager | None = None


def init_templates(backend: StorageBackend):
    """Initialize global template manager."""
    global _templates
    _templates = TemplateManager(backend)


def get_templates() -> TemplateManager:
    """Get global template manager."""
    if _templates is None:
        raise RuntimeError("Template manager not initialized. Call init_templates() first.")
    return _templates


# Tool: template_render


def get_template_render_tool() -> Tool:
    """Get template_render tool definition."""
    return Tool(
        name="template_render",
        description="""Render Jinja2 template with context expansion from S3.

Templates support custom filters:
- {{ uri | expand }}: Load content from S3 URI
- {{ key | s3 }}: Load content from templates bucket

Example:
template_render(
    "meeting-notes.md",
    {"meeting": {"title": "Sprint Planning", "date": "2026-01-10", "attendees": ["Alice", "Bob"]}}
)
""",
        inputSchema={
            "type": "object",
            "properties": {
                "template_key": {
                    "type": "string",
                    "description": "Template key in uer-templates bucket (e.g., 'meeting-notes.md')",
                },
                "context": {
                    "type": "object",
                    "description": "Context variables for template rendering",
                    "additionalProperties": True,
                },
            },
            "required": ["template_key", "context"],
        },
    )


async def template_render(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Render template with context.

    Args:
        arguments: Tool arguments with template_key, context

    Returns:
        List of TextContent with rendered template
    """
    templates = get_templates()

    template_key = arguments["template_key"]
    context = arguments["context"]

    try:
        # Render template
        rendered = await templates.render(template_key, context)

        response = {"success": True, "template": template_key, "rendered": rendered}

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        return [
            TextContent(
                type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2)
            )
        ]


# Tool: template_list


def get_template_list_tool() -> Tool:
    """Get template_list tool definition."""
    return Tool(
        name="template_list",
        description="""List available templates.

Returns all templates stored in uer-templates bucket.

Example:
template_list()
template_list(prefix="project-specs/")
""",
        inputSchema={
            "type": "object",
            "properties": {
                "prefix": {
                    "type": "string",
                    "description": "Optional prefix to filter by (e.g., 'project-specs/')",
                    "default": "",
                },
            },
        },
    )


async def template_list(arguments: dict[str, Any]) -> list[TextContent]:
    """
    List available templates.

    Args:
        arguments: Tool arguments with optional prefix

    Returns:
        List of TextContent with templates list
    """
    templates = get_templates()
    prefix = arguments.get("prefix", "")

    try:
        # List templates
        templates_list = await templates.list_templates(prefix)

        response = {"success": True, "count": len(templates_list), "templates": templates_list}

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        return [
            TextContent(
                type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2)
            )
        ]


# Tool: template_create


def get_template_create_tool() -> Tool:
    """Get template_create tool definition."""
    return Tool(
        name="template_create",
        description="""Create or update a template.

Templates are Jinja2 templates with custom filters for S3 content expansion.

Example:
template_create(
    "meeting-notes.md",
    "# Meeting: {{ meeting.title }}\\nDate: {{ meeting.date }}\\nAttendees: {% for a in meeting.attendees %}{{ a }}{% endfor %}",
    "text/markdown"
)
""",
        inputSchema={
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Template key (e.g., 'meeting-notes.md')",
                },
                "content": {
                    "type": "string",
                    "description": "Template content (Jinja2 format)",
                },
                "content_type": {
                    "type": "string",
                    "description": "MIME type (default: text/markdown)",
                    "default": "text/markdown",
                },
            },
            "required": ["key", "content"],
        },
    )


async def template_create(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Create or update template.

    Args:
        arguments: Tool arguments with key, content, content_type

    Returns:
        List of TextContent with result
    """
    templates = get_templates()

    key = arguments["key"]
    content = arguments["content"]
    content_type = arguments.get("content_type", "text/markdown")

    try:
        # Create template
        await templates.create_template(key, content, content_type)

        response = {
            "success": True,
            "template": key,
            "uri": f"s3://uer-templates/{key}",
            "note": "Template created successfully",
        }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        return [
            TextContent(
                type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2)
            )
        ]


# Tool: template_delete


def get_template_delete_tool() -> Tool:
    """Get template_delete tool definition."""
    return Tool(
        name="template_delete",
        description="""Delete a template.

Example:
template_delete("old-template.md")
""",
        inputSchema={
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Template key to delete",
                },
            },
            "required": ["key"],
        },
    )


async def template_delete(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Delete template.

    Args:
        arguments: Tool arguments with key

    Returns:
        List of TextContent with result
    """
    templates = get_templates()
    key = arguments["key"]

    try:
        # Delete template
        deleted = await templates.delete_template(key)

        response = {"success": True, "template": key, "deleted": deleted}

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        return [
            TextContent(
                type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2)
            )
        ]
