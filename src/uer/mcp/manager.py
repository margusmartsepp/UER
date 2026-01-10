"""MCP server connection manager using LiteLLM's MCP bridge."""

import asyncio
import logging
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from uer.mcp.config import MCPConfig, MCPServerConfig

logger = logging.getLogger(__name__)


class MCPManager:
    """Manages connections to external MCP servers using LiteLLM's MCP bridge."""

    def __init__(self, config: MCPConfig | None = None) -> None:
        """Initialize MCP manager with configuration."""
        self.config = config or MCPConfig.default()
        self._sessions: dict[str, ClientSession] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def connect(self, server_name: str) -> ClientSession:
        """Connect to an MCP server and return the session."""
        if server_name not in self.config.servers:
            raise ValueError(f"Unknown MCP server: {server_name}")

        # Return existing session if already connected
        if server_name in self._sessions:
            return self._sessions[server_name]

        # Ensure only one connection attempt at a time
        if server_name not in self._locks:
            self._locks[server_name] = asyncio.Lock()

        async with self._locks[server_name]:
            # Check again in case another coroutine connected while we waited
            if server_name in self._sessions:
                return self._sessions[server_name]

            server_config = self.config.servers[server_name]
            logger.info(f"Connecting to MCP server: {server_name}")

            try:
                session = await self._create_session(server_config)
                self._sessions[server_name] = session
                logger.info(f"Successfully connected to MCP server: {server_name}")
                return session
            except Exception as e:
                logger.error(f"Failed to connect to MCP server {server_name}: {e}")
                raise RuntimeError(f"Failed to connect to MCP server {server_name}: {e}") from e

    async def _create_session(self, config: MCPServerConfig) -> ClientSession:
        """Create a new MCP client session."""
        if config.transport != "stdio":
            raise NotImplementedError(f"Transport {config.transport} not yet supported")

        # Create server parameters
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env if config.env else None,
        )

        # Connect via stdio
        read, write = await stdio_client(server_params).__aenter__()
        session = ClientSession(read, write)
        await session.__aenter__()
        await session.initialize()

        return session

    async def list_tools(self, server_name: str) -> list[dict[str, Any]]:
        """List all tools available from an MCP server."""
        session = await self.connect(server_name)

        try:
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
        except Exception as e:
            logger.error(f"Failed to list tools from {server_name}: {e}")
            raise RuntimeError(f"Failed to list tools from {server_name}: {e}") from e

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        """Call a tool on an MCP server."""
        session = await self.connect(server_name)

        try:
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

        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {server_name}: {e}")
            raise RuntimeError(f"Failed to call tool {tool_name} on {server_name}: {e}") from e

    async def disconnect(self, server_name: str) -> None:
        """Disconnect from an MCP server."""
        if server_name in self._sessions:
            session = self._sessions[server_name]
            try:
                await session.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error disconnecting from {server_name}: {e}")
            finally:
                del self._sessions[server_name]

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        for server_name in list(self._sessions.keys()):
            await self.disconnect(server_name)

    def list_servers(self) -> list[str]:
        """List all configured MCP servers."""
        return list(self.config.servers.keys())

    def is_connected(self, server_name: str) -> bool:
        """Check if connected to an MCP server."""
        return server_name in self._sessions
