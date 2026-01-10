"""MCP server configuration models."""

from typing import Any

from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    name: str = Field(..., description="Unique name for the MCP server")
    command: str = Field(..., description="Command to execute (e.g., 'npx', 'python')")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    transport: str = Field(default="stdio", description="Transport type (stdio, sse, http)")


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
    def default(cls) -> "MCPConfig":
        """Create default configuration with common MCP servers for testing."""
        return cls(
            servers={
                "filesystem": MCPServerConfig(
                    name="filesystem",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "."],
                    transport="stdio",
                ),
                "memory": MCPServerConfig(
                    name="memory",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-memory"],
                    transport="stdio",
                ),
                "fetch": MCPServerConfig(
                    name="fetch",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-fetch"],
                    transport="stdio",
                ),
            }
        )
