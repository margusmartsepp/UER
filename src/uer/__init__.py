"""
UER - Universal Expert Registry.

An MCP server providing universal LLM access via LiteLLM.
"""

__version__ = "0.1.0"

# Export main components for programmatic use
from uer.llm.gateway import LLMGateway
from uer.models.llm import LLMCallRequest, LLMCallResponse

__all__ = [
    "LLMGateway",
    "LLMCallRequest",
    "LLMCallResponse",
]
