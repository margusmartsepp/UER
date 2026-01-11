"""Configuration Guide - Help users securely configure LLM providers.

Detects MCP client location and provides instructions for setting environment
variables instead of storing API keys in config files.
"""

import platform
from pathlib import Path
from typing import Any


class ConfigGuide:
    """Guide for secure provider configuration."""

    @staticmethod
    def detect_mcp_client() -> dict[str, Any]:
        """Detect which MCP client is being used and its config location.

        Returns:
            Dictionary with client info and config locations
        """
        system = platform.system()
        home = Path.home()

        clients = []

        # Claude Desktop
        if system == "Darwin":  # macOS
            claude_config = (
                home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
            )
            if claude_config.exists():
                clients.append(
                    {
                        "name": "Claude Desktop",
                        "platform": "macOS",
                        "config_file": str(claude_config),
                        "detected": True,
                    }
                )
            else:
                clients.append(
                    {
                        "name": "Claude Desktop",
                        "platform": "macOS",
                        "config_file": str(claude_config),
                        "detected": False,
                    }
                )
        elif system == "Windows":
            claude_config = home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
            if claude_config.exists():
                clients.append(
                    {
                        "name": "Claude Desktop",
                        "platform": "Windows",
                        "config_file": str(claude_config),
                        "detected": True,
                    }
                )
            else:
                clients.append(
                    {
                        "name": "Claude Desktop",
                        "platform": "Windows",
                        "config_file": str(claude_config),
                        "detected": False,
                    }
                )

        # Cline (VS Code extension)
        if system == "Darwin":
            cline_config = (
                home
                / "Library"
                / "Application Support"
                / "Code"
                / "User"
                / "globalStorage"
                / "saoudrizwan.claude-dev"
                / "settings"
                / "cline_mcp_settings.json"
            )
        elif system == "Windows":
            cline_config = (
                home
                / "AppData"
                / "Roaming"
                / "Code"
                / "User"
                / "globalStorage"
                / "saoudrizwan.claude-dev"
                / "settings"
                / "cline_mcp_settings.json"
            )
        else:  # Linux
            cline_config = (
                home
                / ".config"
                / "Code"
                / "User"
                / "globalStorage"
                / "saoudrizwan.claude-dev"
                / "settings"
                / "cline_mcp_settings.json"
            )

        if cline_config.exists():
            clients.append(
                {
                    "name": "Cline (VS Code)",
                    "platform": system,
                    "config_file": str(cline_config),
                    "detected": True,
                }
            )
        else:
            clients.append(
                {
                    "name": "Cline (VS Code)",
                    "platform": system,
                    "config_file": str(cline_config),
                    "detected": False,
                }
            )

        # Windsurf
        if system == "Darwin":
            windsurf_config = (
                home
                / "Library"
                / "Application Support"
                / "Windsurf"
                / "User"
                / "globalStorage"
                / "windsurf.windsurf"
                / "settings"
                / "windsurf_mcp_settings.json"
            )
        elif system == "Windows":
            windsurf_config = (
                home
                / "AppData"
                / "Roaming"
                / "Windsurf"
                / "User"
                / "globalStorage"
                / "windsurf.windsurf"
                / "settings"
                / "windsurf_mcp_settings.json"
            )
        else:  # Linux
            windsurf_config = (
                home
                / ".config"
                / "Windsurf"
                / "User"
                / "globalStorage"
                / "windsurf.windsurf"
                / "settings"
                / "windsurf_mcp_settings.json"
            )

        if windsurf_config.exists():
            clients.append(
                {
                    "name": "Windsurf",
                    "platform": system,
                    "config_file": str(windsurf_config),
                    "detected": True,
                }
            )
        else:
            clients.append(
                {
                    "name": "Windsurf",
                    "platform": system,
                    "config_file": str(windsurf_config),
                    "detected": False,
                }
            )

        detected_clients = [c for c in clients if c["detected"]]

        return {
            "system": system,
            "detected_clients": detected_clients,
            "all_possible_clients": clients,
        }

    @staticmethod
    def get_env_var_instructions(provider: str, client_info: dict[str, Any]) -> dict[str, Any]:
        """Get instructions for setting environment variables for a provider.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            client_info: Client detection info from detect_mcp_client()

        Returns:
            Instructions for secure configuration
        """
        # Provider-specific environment variables
        provider_env_vars = {
            "openai": {
                "required": ["OPENAI_API_KEY"],
                "optional": ["OPENAI_API_BASE"],
                "description": "OpenAI API configuration",
            },
            "anthropic": {
                "required": ["ANTHROPIC_API_KEY"],
                "optional": [],
                "description": "Anthropic (Claude) API configuration",
            },
            "gemini": {
                "required": ["GEMINI_API_KEY"],
                "optional": ["GOOGLE_API_KEY"],
                "description": "Google Gemini API configuration",
            },
            "azure": {
                "required": ["AZURE_API_KEY", "AZURE_API_BASE"],
                "optional": ["AZURE_API_VERSION"],
                "description": "Azure OpenAI configuration",
            },
            "bedrock": {
                "required": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
                "optional": ["AWS_REGION_NAME"],
                "description": "AWS Bedrock configuration",
            },
            "cerebras": {
                "required": ["CEREBRAS_API_KEY"],
                "optional": [],
                "description": "Cerebras API configuration",
            },
            "groq": {
                "required": ["GROQ_API_KEY"],
                "optional": [],
                "description": "Groq API configuration",
            },
            "ollama": {
                "required": ["OLLAMA_API_BASE"],
                "optional": [],
                "description": "Ollama local server configuration",
            },
        }

        provider_info = provider_env_vars.get(
            provider,
            {
                "required": [],
                "optional": [],
                "description": f"{provider} configuration",
            },
        )

        detected_clients = client_info.get("detected_clients", [])

        instructions = {
            "provider": provider,
            "description": provider_info["description"],
            "required_env_vars": provider_info["required"],
            "optional_env_vars": provider_info["optional"],
            "security_note": (
                "⚠️ BEST PRACTICE: Use environment variables in MCP client config instead of sharing keys in chat. "
                "Chat logs can be leaked, accessed by monitoring systems, or used for training (depending on your provider's settings). "
                "Environment variables are more secure and convenient. "
                "You are responsible for managing your data sharing preferences with your LLM provider."
            ),
        }

        if detected_clients:
            client = detected_clients[0]
            instructions["detected_client"] = client["name"]
            instructions["config_file"] = client["config_file"]
            instructions["instructions"] = ConfigGuide._get_client_specific_instructions(
                client["name"], client["config_file"], provider, provider_info
            )
        else:
            instructions["detected_client"] = None
            instructions["instructions"] = (
                "No MCP client detected. If you're using an MCP client, "
                "add environment variables to the 'env' section of your MCP server configuration."
            )

        return instructions

    @staticmethod
    def _get_client_specific_instructions(
        client_name: str, config_file: str, provider: str, provider_info: dict[str, Any]
    ) -> str:
        """Generate client-specific instructions for setting environment variables."""
        env_vars = provider_info["required"] + provider_info["optional"]

        # Generate example env section
        env_example = "{\n"
        for var in provider_info["required"]:
            env_example += f'  "{var}": "your-{var.lower().replace("_", "-")}-here",\n'
        for var in provider_info["optional"]:
            env_example += f'  "{var}": "optional-{var.lower().replace("_", "-")}",\n'
        env_example = env_example.rstrip(",\n") + "\n}"

        instructions = f"""
To securely configure {provider} in {client_name}:

1. Open your MCP client configuration file:
   {config_file}

2. Find the UER MCP server entry in the "mcpServers" section

3. Add or update the "env" section with your API credentials:

   "uer": {{
     "command": "...",
     "args": [...],
     "env": {env_example}
   }}

4. Save the file and restart {client_name}

5. Your API keys will be securely stored in the config file (not in chat history)

IMPORTANT:
- Never paste your actual API keys in this chat
- The keys should only go in the config file
- This keeps your credentials secure and prevents exposure in training data
"""

        return instructions.strip()

    @staticmethod
    def get_full_guide(provider: str) -> dict[str, Any]:
        """Get complete configuration guide for a provider.

        Args:
            provider: Provider name

        Returns:
            Complete guide with detection, instructions, and examples
        """
        client_info = ConfigGuide.detect_mcp_client()
        env_instructions = ConfigGuide.get_env_var_instructions(provider, client_info)

        return {
            "provider": provider,
            "client_detection": client_info,
            "configuration_guide": env_instructions,
            "why_this_matters": {
                "security": (
                    "Chat logs can be leaked, accessed by monitoring systems, or used for training. "
                    "Environment variables in MCP client config files are never transmitted in conversations, "
                    "reducing the attack surface for credential exposure."
                ),
                "convenience": (
                    "Environment variables are loaded directly by the MCP server, making configuration "
                    "more convenient than typing keys in chat. This follows industry security best practices."
                ),
                "user_control": (
                    "Many LLM providers allow you to opt out of training data usage (check your provider's settings). "
                    "Some providers make this a premium feature. You are responsible for managing your data sharing preferences."
                ),
            },
        }
