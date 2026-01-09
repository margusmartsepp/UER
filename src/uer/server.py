"""UER MCP Server - Universal Expert Registry."""

import asyncio
import json
import logging
from collections.abc import Sequence
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from uer.llm.gateway import LLMGateway
from uer.models.llm import LLMCallRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("uer.server")

# Initialize MCP server
app = Server("uer")
gateway = LLMGateway()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    available = gateway.get_available_providers()

    return [
        Tool(
            name="llm_call",
            description=(
                "Call any LLM via LiteLLM unified interface. "
                f"Available providers: {', '.join(available) or 'none'}. "
                "Supports Anthropic (Claude), OpenAI (GPT), Google (Gemini), and 100+ more. "
                "Features: Structured output (response_format), Chain of Thought (thinking_level/thinking_budget), "
                "Tool use (tools) for web search, code execution, grounding, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "LiteLLM model identifier (e.g., 'gemini/gemini-3-flash-preview')",
                    },
                    "messages": {
                        "type": "array",
                        "description": "List of chat messages",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {
                                    "type": "string",
                                    "enum": ["system", "user", "assistant"],
                                },
                                "content": {"type": "string"},
                            },
                            "required": ["role", "content"],
                        },
                        "minItems": 1,
                    },
                    "temperature": {
                        "type": "number",
                        "default": 0.7,
                        "minimum": 0,
                        "maximum": 2,
                    },
                    "max_tokens": {
                        "type": "integer",
                        "default": 4096,
                        "minimum": 1,
                    },
                    "response_format": {
                        "type": "object",
                        "description": (
                            "Force structured JSON output. The calling LLM can generate schemas dynamically. "
                            "Format: {'type': 'json_schema', 'json_schema': {'name': '...', 'schema': {...}, 'strict': True}}"
                        ),
                    },
                    "thinking_level": {
                        "type": "string",
                        "enum": ["minimal", "low", "medium", "high"],
                        "description": "Gemini 3 reasoning level: 'high' for complex reasoning tasks, 'low' for simple ones",
                    },
                    "thinking_budget": {
                        "type": "integer",
                        "minimum": -1,
                        "maximum": 32768,
                        "description": "Gemini 2.5 thinking tokens (128-32768, or -1 for dynamic allocation)",
                    },
                    "tools": {
                        "type": "array",
                        "description": (
                            "List of tools the model can use. "
                            "Claude: [{'type': 'web_search_20250305'}] for web search, [{'type': 'bash_20250305'}] for code execution. "
                            "Gemini: [{'type': 'code_execution'}] or [{'type': 'google_search_retrieval'}]. "
                            "OpenAI: Standard function calling format."
                        ),
                        "items": {"type": "object"},
                    },
                },
                "required": ["model", "messages"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool invocation."""
    if name != "llm_call":
        raise ValueError(f"Unknown tool: {name}")

    try:
        # Validate input using Pydantic
        request = LLMCallRequest(**arguments)

        logger.info(
            f"Calling LLM: model={request.model}, messages={len(request.messages)}, "
            f"structured_output={request.response_format is not None}, "
            f"thinking={request.thinking_level or request.thinking_budget}, "
            f"tools={len(request.tools) if request.tools else 0}"
        )

        # Call LLM via gateway with all parameters
        response = await gateway.call(
            model=request.model,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format=request.response_format,
            thinking_level=request.thinking_level,
            thinking_budget=request.thinking_budget,
            tools=request.tools,
        )

        # Log result
        usage = response.get("usage", {})
        logger.info(
            f"LLM call successful: tokens={usage.get('total_tokens', 'unknown')}, "
            f"model={response.get('model', 'unknown')}"
        )

        # Return response as text content
        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except ValueError as e:
        # Validation error from Pydantic
        logger.error(f"Invalid input: {str(e)}")
        return [
            TextContent(type="text", text=json.dumps({"error": "Invalid input", "message": str(e)}))
        ]

    except RuntimeError as e:
        # Error from LLMGateway
        logger.error(f"LLM call failed: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "LLM call failed", "message": str(e)})
            )
        ]

    except Exception as e:
        # Unexpected error
        logger.exception(f"Unexpected error: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "Internal error", "message": str(e)})
            )
        ]


async def main() -> None:
    """Run the MCP server via stdio transport."""
    logger.info("Starting UER MCP server...")
    logger.info(f"Available providers: {gateway.get_available_providers()}")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
