"""MCP server connection manager using native MCP SDK."""

import asyncio
import logging
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

from uer.mcp.config import MCPConfig

logger = logging.getLogger(__name__)


class MCPManager:
    """Manages connections to external MCP servers.

    Note: Connections are created fresh for each request to avoid async context issues.
    """

    def __init__(self, config: MCPConfig | None = None) -> None:
        """Initialize MCP manager with configuration."""
        self.config = config or MCPConfig.default()
        self._locks: dict[str, asyncio.Lock] = {}

    async def _with_connection(self, server_name: str, operation: Any) -> Any:
        """Execute an operation with a fresh MCP connection.

        This creates a new connection for each operation to avoid async context issues.
        Supports stdio, sse, and http transports.
        """
        if server_name not in self.config.servers:
            raise ValueError(f"Unknown MCP server: {server_name}")

        server_config = self.config.servers[server_name]
        logger.info(f"Connecting to MCP server: {server_name} via {server_config.transport}")

        try:
            if server_config.transport == "stdio":
                # Validate stdio requirements
                if not server_config.command:
                    raise ValueError(f"Server {server_name}: command required for stdio transport")

                # Create server parameters
                server_params = StdioServerParameters(
                    command=server_config.command,
                    args=server_config.args,
                    env=server_config.env if server_config.env else None,
                )

                # Use stdio client
                async with (
                    stdio_client(server_params) as (read, write),
                    ClientSession(read, write) as session,
                ):
                    await session.initialize()
                    logger.info(f"Connected to MCP server: {server_name}")
                    result = await operation(session)
                    return result

            elif server_config.transport in ("sse", "http"):
                # Validate SSE/HTTP requirements
                if not server_config.url:
                    transport = server_config.transport
                    raise ValueError(
                        f"Server {server_name}: url required for {transport} transport"
                    )

                # Use SSE client for HTTP/SSE transport with headers
                async with (
                    sse_client(server_config.url, headers=server_config.headers or None) as (
                        read,
                        write,
                    ),
                    ClientSession(read, write) as session,
                ):
                    await session.initialize()
                    logger.info(f"Connected to MCP server: {server_name}")
                    result = await operation(session)
                    return result

            else:
                raise NotImplementedError(f"Transport {server_config.transport} not supported")

        except Exception as e:
            logger.exception(f"MCP operation failed on {server_name}: {e}")
            error_msg = str(e)
            if server_config.transport in ("sse", "http") and "huggingface" in server_name.lower():
                if "405" in str(e) or "Method Not Allowed" in str(e):
                    hf_help = (
                        " | The ?login OAuth flow doesn't work with SSE client. "
                        "Use token-based auth instead: url='https://huggingface.co/mcp' with "
                        "headers={'Authorization': 'Bearer <token>'}. "
                        "Get token from: https://huggingface.co/settings/tokens"
                    )
                else:
                    hf_help = (
                        " | For Hugging Face MCP: Use url='https://huggingface.co/mcp' with "
                        "headers={'Authorization': 'Bearer <token>'}. "
                        "Get token from: https://huggingface.co/settings/tokens"
                    )
                error_msg += hf_help
            raise RuntimeError(f"MCP operation failed on {server_name}: {error_msg}") from e

    async def list_tools(self, server_name: str) -> list[dict[str, Any]]:
        """List all tools available from an MCP server."""

        async def operation(session: ClientSession) -> list[dict[str, Any]]:
            result = await session.list_tools()
            tools = []
            for tool in result.tools:
                tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description or "",
                        "inputSchema": tool.inputSchema,
                    }
                )
            return tools

        return await self._with_connection(server_name, operation)

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        """Call a tool on an MCP server."""

        async def operation(session: ClientSession) -> Any:
            logger.info(f"Calling tool {tool_name} on server {server_name}")
            result = await session.call_tool(tool_name, arguments or {})

            # Extract content from result
            if hasattr(result, "content") and result.content:
                # Return first content item's text if available
                if len(result.content) > 0:
                    first_content = result.content[0]
                    if hasattr(first_content, "text"):
                        return first_content.text
                    return str(first_content)
                return result.content

            return str(result)

        return await self._with_connection(server_name, operation)

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers.

        Note: With fresh connections per request, this is a no-op.
        Connections are automatically cleaned up by context managers.
        """
        logger.info("MCP connections use auto-cleanup (no persistent connections)")

    def list_servers(self) -> list[str]:
        """List all configured MCP servers."""
        return list(self.config.servers.keys())

    def is_connected(self, server_name: str) -> bool:
        """Check if connected to an MCP server.

        Note: Always returns False since connections are not persistent.
        """
        return False
