"""
MCP tools for UER.

Exposes storage, skills, and template functionality via MCP protocol.
"""

from .storage_tools import (
    storage_put,
    storage_get,
    storage_list,
    storage_delete,
    storage_exists,
)
from .skills_tools import (
    skill_create,
    skill_get,
    skill_list,
    skill_export,
    skill_to_prompt,
)
from .template_tools import (
    template_render,
    template_list,
    template_create,
    template_delete,
)

__all__ = [
    # Storage tools
    "storage_put",
    "storage_get",
    "storage_list",
    "storage_delete",
    "storage_exists",
    # Skills tools
    "skill_create",
    "skill_get",
    "skill_list",
    "skill_export",
    "skill_to_prompt",
    # Template tools
    "template_render",
    "template_list",
    "template_create",
    "template_delete",
]
