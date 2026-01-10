"""MCP server configuration models."""

import json
import os
from typing import Any

from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    name: str = Field(..., description="Unique name for the MCP server")
    command: str = Field(
        default="", description="Command to execute (e.g., 'npx', 'python') - required for stdio"
    )
    args: list[str] = Field(
        default_factory=list, description="Command arguments - for stdio transport"
    )
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    transport: str = Field(default="stdio", description="Transport type: stdio, sse, or http")
    url: str = Field(
        default="", description="HTTP/SSE endpoint URL - required for sse/http transports"
    )
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="HTTP headers for sse/http transports (e.g., Authorization)",
    )


class MCPConfig(BaseModel):
    """Configuration for all MCP servers."""

    servers: dict[str, MCPServerConfig] = Field(
        default_factory=dict, description="Map of server name to configuration"
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPConfig":
        """Create config from dictionary."""
        servers = {}
        for name, config in data.items():
            servers[name] = MCPServerConfig(name=name, **config)
        return cls(servers=servers)

    @classmethod
    def from_env(cls) -> "MCPConfig | None":
        """Load MCP configuration from UER_MCP_SERVERS environment variable.

        Expected format (JSON):
        {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"],
                "transport": "stdio"
            }
        }
        """
        env_config = os.environ.get("UER_MCP_SERVERS")
        if not env_config:
            return None

        try:
            data = json.loads(env_config)
            return cls.from_dict(data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid UER_MCP_SERVERS format: {e}") from e

    @classmethod
    def default(cls) -> "MCPConfig":
        """Create default configuration with common MCP servers for testing.

        Note: Filesystem server is disabled by default. Users should configure it
        with their desired allowed directories via environment variable or config file.
        """
        return cls(
            servers={
                # Filesystem disabled by default - needs explicit directory configuration
                # "filesystem": MCPServerConfig(
                #     name="filesystem",
                #     command="npx",
                #     args=[
                #         "-y",
                #         "@modelcontextprotocol/server-filesystem",
                #         "/path/to/allowed/dir",
                #     ],
                #     transport="stdio",
                # ),
                "memory": MCPServerConfig(
                    name="memory",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-memory"],
                    transport="stdio",
                    headers={},
                ),
                "fetch": MCPServerConfig(
                    name="fetch",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-fetch"],
                    transport="stdio",
                    headers={},
                ),
            }
        )
