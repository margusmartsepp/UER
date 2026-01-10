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
from uer.mcp.config import MCPConfig
from uer.mcp.manager import MCPManager
from uer.models.llm import LLMCallRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("uer.server")

# Initialize MCP server
app = Server("uer")
gateway = LLMGateway()

# Load MCP config from environment or use default
mcp_config = MCPConfig.from_env() or MCPConfig.default()
mcp_manager = MCPManager(mcp_config)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    available = gateway.get_available_providers()

    mcp_servers = mcp_manager.list_servers()

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
        ),
        Tool(
            name="mcp_call",
            description=(
                "Call tools from external MCP servers. "
                f"Available servers: {', '.join(mcp_servers) or 'none'}. "
                "Use mcp_list_tools to discover available tools on each server first."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "server": {
                        "type": "string",
                        "description": f"MCP server name. Available: {', '.join(mcp_servers)}",
                    },
                    "tool": {
                        "type": "string",
                        "description": "Tool name to call on the MCP server",
                    },
                    "arguments": {
                        "type": "object",
                        "description": "Arguments to pass to the tool",
                        "default": {},
                    },
                },
                "required": ["server", "tool"],
            },
        ),
        Tool(
            name="mcp_list_tools",
            description=(
                "List all available tools from an MCP server. "
                f"Available servers: {', '.join(mcp_servers) or 'none'}. "
                "Returns tool names, descriptions, and input schemas."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "server": {
                        "type": "string",
                        "description": f"MCP server name. Available: {', '.join(mcp_servers)}",
                    }
                },
                "required": ["server"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool invocation."""
    if name == "llm_call":
        return await handle_llm_call(arguments)
    elif name == "mcp_call":
        return await handle_mcp_call(arguments)
    elif name == "mcp_list_tools":
        return await handle_mcp_list_tools(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_llm_call(arguments: Any) -> Sequence[TextContent]:
    """Handle llm_call tool invocation."""
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


async def handle_mcp_list_tools(arguments: Any) -> Sequence[TextContent]:
    """Handle mcp_list_tools tool invocation."""
    try:
        server = arguments.get("server")
        if not server:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "Missing required parameter", "message": "server is required"}
                    ),
                )
            ]

        logger.info(f"Listing tools from MCP server: {server}")
        tools = await mcp_manager.list_tools(server)

        logger.info(f"Found {len(tools)} tools on server {server}")
        return [
            TextContent(type="text", text=json.dumps({"server": server, "tools": tools}, indent=2))
        ]

    except RuntimeError as e:
        logger.error(f"MCP list_tools failed: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "MCP operation failed", "message": str(e)})
            )
        ]

    except Exception as e:
        logger.exception(f"Unexpected error in mcp_list_tools: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "Internal error", "message": str(e)})
            )
        ]


async def handle_mcp_call(arguments: Any) -> Sequence[TextContent]:
    """Handle mcp_call tool invocation."""
    try:
        server = arguments.get("server")
        tool = arguments.get("tool")
        tool_arguments = arguments.get("arguments", {})

        if not server or not tool:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": "Missing required parameters",
                            "message": "server and tool are required",
                        }
                    ),
                )
            ]

        logger.info(f"Calling tool {tool} on MCP server {server}")
        result = await mcp_manager.call_tool(server, tool, tool_arguments)

        logger.info(f"MCP tool call successful: {server}.{tool}")
        return [
            TextContent(
                type="text",
                text=json.dumps({"server": server, "tool": tool, "result": result}, indent=2),
            )
        ]

    except RuntimeError as e:
        logger.error(f"MCP call_tool failed: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "MCP operation failed", "message": str(e)})
            )
        ]

    except Exception as e:
        logger.exception(f"Unexpected error in mcp_call: {str(e)}")
        return [
            TextContent(
                type="text", text=json.dumps({"error": "Internal error", "message": str(e)})
            )
        ]


async def main() -> None:
    """Run the MCP server via stdio transport."""
    logger.info("Starting UER MCP server...")
    logger.info(f"Available LLM providers: {gateway.get_available_providers()}")
    logger.info(f"Available MCP servers: {mcp_manager.list_servers()}")

    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    finally:
        # Cleanup MCP connections
        logger.info("Shutting down MCP connections...")
        await mcp_manager.disconnect_all()


if __name__ == "__main__":
    asyncio.run(main())
