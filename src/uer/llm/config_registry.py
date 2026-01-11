"""Configuration Registry for LLM Provider Management.

Allows LLMs to read and update provider configurations without requiring
users to manually edit environment variables or config files.
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ConfigRegistry:
    """Registry for LLM provider configurations."""

    def __init__(self, config_file: Path | None = None) -> None:
        """Initialize configuration registry.

        Args:
            config_file: Path to config file. Defaults to ~/.uer/provider_config.json
        """
        self.config_file = config_file or Path.home() / ".uer" / "provider_config.json"
        self.config: dict[str, Any] = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from disk."""
        try:
            if self.config_file.exists():
                with open(self.config_file) as f:
                    return json.load(f)
        except Exception:
            pass

        # Default config structure
        return {
            "_metadata": {
                "version": "1.0",
                "created_at": datetime.now(UTC).isoformat(),
                "last_updated": datetime.now(UTC).isoformat(),
            },
            "providers": {},
        }

    def _save_config(self) -> None:
        """Save configuration to disk."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Update last_updated timestamp
            self.config["_metadata"]["last_updated"] = datetime.now(UTC).isoformat()

            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to save config: {e}") from e

    def get_all_providers(self) -> dict[str, Any]:
        """Get all provider configurations.

        Returns:
            Dictionary with metadata and provider configs
        """
        return {
            "metadata": self.config["_metadata"],
            "providers": self.config["providers"],
            "config_file": str(self.config_file),
        }

    def get_provider(self, provider_name: str) -> dict[str, Any] | None:
        """Get configuration for a specific provider.

        Args:
            provider_name: Provider name (e.g., 'openai', 'azure')

        Returns:
            Provider config or None if not found
        """
        return self.config["providers"].get(provider_name)

    def set_provider(
        self,
        provider_name: str,
        config: dict[str, Any],
        merge: bool = True,
    ) -> dict[str, Any]:
        """Set or update provider configuration.

        Args:
            provider_name: Provider name (e.g., 'openai', 'azure')
            config: Provider configuration dictionary
            merge: If True, merge with existing config. If False, replace.

        Returns:
            Updated provider configuration with security warnings if applicable
        """
        result = {}

        # Check for API keys in config (security risk)
        has_credentials = "credentials" in config
        has_api_keys = False
        if has_credentials:
            credential_keys = config["credentials"].keys()
            api_key_patterns = ["API_KEY", "SECRET", "PASSWORD", "TOKEN"]
            has_api_keys = any(
                any(pattern in key.upper() for pattern in api_key_patterns)
                for key in credential_keys
            )

        if merge and provider_name in self.config["providers"]:
            # Merge with existing config
            existing = self.config["providers"][provider_name]
            existing.update(config)
            self.config["providers"][provider_name] = existing
        else:
            # Replace or create new
            self.config["providers"][provider_name] = config

        # Add metadata
        self.config["providers"][provider_name]["_updated_at"] = datetime.now(
            UTC
        ).isoformat()

        # Add security warning if API keys detected
        if has_api_keys:
            self.config["providers"][provider_name]["_security_warning"] = (
                "API keys stored in config file. This poses a security risk if LLM chat "
                "data is used for training. Consider using environment variables instead."
            )

        self._save_config()

        result = self.config["providers"][provider_name].copy()

        # Add security warning to response
        if has_api_keys:
            result["_security_risk"] = {
                "level": "high",
                "issue": "API keys stored in plaintext config file",
                "risk": (
                    "Sharing credentials in chat conversations exposes them to multiple risks: "
                    "chat logs can be leaked, accessed by monitoring systems, or used for training (depending on provider settings). "
                    "Environment variables in MCP client config are more secure and never transmitted in conversations."
                ),
                "recommendation": "Use environment variables in MCP client config instead",
                "alternative_method": "Use llm_config_guide tool to get instructions for secure setup",
                "user_responsibility": "You are responsible for managing your data sharing preferences with your LLM provider",
            }

        return result

    def delete_provider(self, provider_name: str) -> bool:
        """Delete provider configuration.

        Args:
            provider_name: Provider name to delete

        Returns:
            True if deleted, False if not found
        """
        if provider_name in self.config["providers"]:
            del self.config["providers"][provider_name]
            self._save_config()
            return True
        return False

    def get_provider_credentials(self, provider_name: str) -> dict[str, str]:
        """Get provider credentials from config and environment.

        Checks both registry config and environment variables.
        Registry config takes precedence over environment.

        Args:
            provider_name: Provider name

        Returns:
            Dictionary of credential keys and values
        """
        credentials = {}

        # Get from environment first
        env_map = {
            "openai": ["OPENAI_API_KEY", "OPENAI_API_BASE"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
            "azure": ["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"],
            "bedrock": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION_NAME"],
            "vertex_ai": ["VERTEX_PROJECT", "VERTEX_LOCATION", "GOOGLE_APPLICATION_CREDENTIALS"],
            "cerebras": ["CEREBRAS_API_KEY"],
            "groq": ["GROQ_API_KEY"],
            "ollama": ["OLLAMA_API_BASE"],
        }

        if provider_name in env_map:
            for env_var in env_map[provider_name]:
                value = os.getenv(env_var)
                if value:
                    credentials[env_var] = value

        # Override with registry config
        provider_config = self.get_provider(provider_name)
        if provider_config and "credentials" in provider_config:
            credentials.update(provider_config["credentials"])

        return credentials

    def list_configured_providers(self) -> list[str]:
        """List all configured providers (from registry and environment).

        Returns:
            List of provider names that have credentials configured
        """
        configured = set()

        # Check registry
        for provider_name in self.config["providers"]:
            if "credentials" in self.config["providers"][provider_name]:
                configured.add(provider_name)

        # Check environment
        env_providers = {
            "openai": ["OPENAI_API_KEY", "OPENAI_API_BASE"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
            "azure": ["AZURE_API_KEY"],
            "bedrock": ["AWS_ACCESS_KEY_ID"],
            "vertex_ai": ["VERTEX_PROJECT"],
            "cerebras": ["CEREBRAS_API_KEY"],
            "groq": ["GROQ_API_KEY"],
            "ollama": ["OLLAMA_API_BASE"],
        }

        for provider, env_vars in env_providers.items():
            if any(os.getenv(var) for var in env_vars):
                configured.add(provider)

        return sorted(configured)

    def get_provider_instances(self, provider_name: str) -> list[dict[str, Any]]:
        """Get user's configured instances for a provider (e.g., Azure deployments).

        Args:
            provider_name: Provider name

        Returns:
            List of instance configurations
        """
        provider_config = self.get_provider(provider_name)
        if provider_config and "instances" in provider_config:
            return provider_config["instances"]
        return []

    def add_provider_instance(
        self,
        provider_name: str,
        instance_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Add a provider instance (e.g., Azure deployment, AWS endpoint).

        Args:
            provider_name: Provider name
            instance_config: Instance configuration

        Returns:
            Updated provider configuration
        """
        provider_config = self.get_provider(provider_name) or {}

        if "instances" not in provider_config:
            provider_config["instances"] = []

        # Add timestamp
        instance_config["_added_at"] = datetime.now(UTC).isoformat()

        provider_config["instances"].append(instance_config)

        return self.set_provider(provider_name, provider_config, merge=True)
