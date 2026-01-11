"""
MCP tools for Claude Skills operations.

Exposes create, get, list, export, and to_prompt operations for skills.
"""

import json
from typing import Any

from mcp.types import Tool, TextContent

from ..storage import StorageBackend, StorageManager
from ..storage.skills import SkillsManager


# Global storage manager and skills manager (will be initialized by server)
_storage_manager: StorageManager | None = None
_skills: SkillsManager | None = None


def init_skills_manager(storage_manager: StorageManager):
    """Initialize global skills manager with storage manager."""
    global _storage_manager
    _storage_manager = storage_manager


def get_skills() -> SkillsManager:
    """Get global skills manager, creating it lazily on first use."""
    global _skills
    if _skills is None:
        if _storage_manager is None:
            raise RuntimeError("Skills manager not initialized. Call init_skills_manager() first.")
        # Create backend and skills manager lazily on first use
        backend = _storage_manager._ensure_backend()
        _skills = SkillsManager(backend)
    return _skills


# Tool: skill_create


def get_skill_create_tool() -> Tool:
    """Get skill_create tool definition."""
    return Tool(
        name="skill_create",
        description="""Create Claude Skill in storage.

Skills are stored in Claude Skills API format (SKILL.md + optional resource files).
Can be used with Claude Skills API or converted to system prompts for other LLMs.

The skill will be stored at: s3://uer-skills/{name}/

Example:
skill_create(
    "financial-analysis",
    "Financial Analysis",
    "---\\nname: financial-analysis\\ndescription: Analyze financial reports\\n---\\n\\n# Financial Analysis\\n\\nThis skill analyzes financial reports...",
    {"scripts/analyze.py": "def analyze_report(data):\\n    ..."}
)
""",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Skill identifier (slug, e.g., 'financial-analysis')",
                },
                "display_title": {
                    "type": "string",
                    "description": "Human-readable title (e.g., 'Financial Analysis')",
                },
                "skill_md": {
                    "type": "string",
                    "description": "SKILL.md content with YAML frontmatter",
                },
                "files": {
                    "type": "object",
                    "description": "Optional additional files (e.g., {'scripts/analyze.py': 'content'})",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": ["name", "display_title", "skill_md"],
        },
    )


async def skill_create(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Create skill in storage.

    Args:
        arguments: Tool arguments with name, display_title, skill_md, files

    Returns:
        List of TextContent with result
    """
    skills = get_skills()

    name = arguments["name"]
    display_title = arguments["display_title"]
    skill_md = arguments["skill_md"]
    additional_files = arguments.get("files", {})

    try:
        # Combine SKILL.md with additional files
        files = {"SKILL.md": skill_md}
        files.update(additional_files)

        # Create skill
        metadata = await skills.create_skill(name, display_title, files)

        response = {
            "success": True,
            "skill": {
                "name": metadata.name,
                "display_title": metadata.display_title,
                "file_count": metadata.file_count,
                "created_at": metadata.created_at.isoformat(),
            },
            "uri": f"s3://uer-skills/{name}/",
        }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        return [
            TextContent(
                type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2)
            )
        ]


# Tool: skill_get


def get_skill_get_tool() -> Tool:
    """Get skill_get tool definition."""
    return Tool(
        name="skill_get",
        description="""Retrieve complete skill with all files.

Returns the skill with all associated files (SKILL.md, scripts, examples, etc.).

Example:
skill_get("financial-analysis")
""",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Skill identifier",
                },
            },
            "required": ["name"],
        },
    )


async def skill_get(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Retrieve complete skill.

    Args:
        arguments: Tool arguments with name

    Returns:
        List of TextContent with skill data
    """
    skills = get_skills()
    name = arguments["name"]

    try:
        # Get skill
        skill = await skills.get_skill(name)

        response = {
            "success": True,
            "skill": {
                "name": skill.name,
                "display_title": skill.display_title,
                "files": skill.files,
                "metadata": {
                    "created_at": skill.metadata.created_at.isoformat(),
                    "updated_at": skill.metadata.updated_at.isoformat(),
                    "file_count": skill.metadata.file_count,
                },
            },
        }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        return [
            TextContent(
                type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2)
            )
        ]


# Tool: skill_list


def get_skill_list_tool() -> Tool:
    """Get skill_list tool definition."""
    return Tool(
        name="skill_list",
        description="""List all available skills.

Returns metadata for all skills stored in the registry.

Example:
skill_list()
""",
        inputSchema={"type": "object", "properties": {}},
    )


async def skill_list(arguments: dict[str, Any]) -> list[TextContent]:
    """
    List all skills.

    Args:
        arguments: Tool arguments (none required)

    Returns:
        List of TextContent with skills list
    """
    skills = get_skills()

    try:
        # List skills
        skills_list = await skills.list_skills()

        response = {
            "success": True,
            "count": len(skills_list),
            "skills": [
                {
                    "name": skill.name,
                    "display_title": skill.display_title,
                    "description": skill.description or "",
                    "file_count": skill.file_count,
                }
                for skill in skills_list
            ],
        }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        return [
            TextContent(
                type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2)
            )
        ]


# Tool: skill_export


def get_skill_export_tool() -> Tool:
    """Get skill_export tool definition."""
    return Tool(
        name="skill_export",
        description="""Export skill for Claude Skills API.

Returns skill in format suitable for POST /v1/skills endpoint.
Use this when you want to register the skill with Claude Skills API.

Example:
skill_export("financial-analysis")
""",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Skill identifier",
                },
            },
            "required": ["name"],
        },
    )


async def skill_export(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Export skill for Claude API.

    Args:
        arguments: Tool arguments with name

    Returns:
        List of TextContent with export data
    """
    skills = get_skills()
    name = arguments["name"]

    try:
        # Export skill
        export_data = await skills.export_for_api(name)

        # Convert files to base64 for JSON serialization
        files_info = []
        for file_data in export_data["files"]:
            files_info.append(
                {
                    "filename": file_data["filename"],
                    "size": len(file_data["content"]),
                    "preview": file_data["content"][:200].decode("utf-8", errors="ignore")
                    + "...",
                }
            )

        response = {
            "success": True,
            "display_title": export_data["display_title"],
            "files": files_info,
            "note": "Use this with Claude Skills API: client.beta.skills.create(display_title=..., files=..., betas=['skills-2025-10-02'])",
        }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        return [
            TextContent(
                type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2)
            )
        ]


# Tool: skill_to_prompt


def get_skill_to_prompt_tool() -> Tool:
    """Get skill_to_prompt tool definition."""
    return Tool(
        name="skill_to_prompt",
        description="""Convert skill to system prompt for non-Claude LLMs.

Parses the skill and creates a system prompt that can be used with GPT, Gemini, or other LLMs.
This allows using Claude Skills with any LLM via LiteLLM.

Example:
skill_to_prompt("financial-analysis")
""",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Skill identifier",
                },
            },
            "required": ["name"],
        },
    )


async def skill_to_prompt(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Convert skill to system prompt.

    Args:
        arguments: Tool arguments with name

    Returns:
        List of TextContent with system prompt
    """
    skills = get_skills()
    name = arguments["name"]

    try:
        # Convert to system prompt
        system_prompt = await skills.to_system_prompt(name)

        response = {
            "success": True,
            "skill": name,
            "system_prompt": system_prompt,
            "note": "Use this as system message when calling non-Claude LLMs with llm_call tool",
        }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        return [
            TextContent(
                type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2)
            )
        ]
