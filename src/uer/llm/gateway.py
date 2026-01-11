"""LiteLLM Gateway - Unified interface to 100+ LLM providers."""

import json
import os
from datetime import UTC
from pathlib import Path
from typing import Any

import httpx
import litellm
from litellm import acompletion

from .config_registry import ConfigRegistry


class LLMGateway:
    """Unified gateway to LLM providers via LiteLLM."""

    # Cache for model lists with timestamps
    _model_cache: dict[str, dict[str, Any]] = {}
    _cache_file: Path = Path.home() / ".uer" / "model_cache.json"

    # Configuration registry
    config_registry: ConfigRegistry

    # Map of environment variables to LiteLLM provider names
    # Based on: https://docs.litellm.ai/docs/providers
    PROVIDER_ENV_MAP = {
        # Cloud providers
        "CEREBRAS_API_KEY": "cerebras",
        "GEMINI_API_KEY": "gemini",
        "GOOGLE_API_KEY": "gemini",
        "ANTHROPIC_API_KEY": "anthropic",
        "OPENAI_API_KEY": "openai",
        "AZURE_API_KEY": "azure",
        "COHERE_API_KEY": "cohere",
        "REPLICATE_API_KEY": "replicate",
        "HUGGINGFACE_API_KEY": "huggingface",
        "TOGETHER_API_KEY": "together_ai",
        "ANYSCALE_API_KEY": "anyscale",
        "DEEPINFRA_API_KEY": "deepinfra",
        "PERPLEXITY_API_KEY": "perplexity",
        "GROQ_API_KEY": "groq",
        "MISTRAL_API_KEY": "mistral",
        "VOYAGE_API_KEY": "voyage",
        "AI21_API_KEY": "ai21",
        "PALM_API_KEY": "palm",
        "NLP_CLOUD_API_KEY": "nlp_cloud",
        "ALEPH_ALPHA_API_KEY": "aleph_alpha",
        "BASETEN_API_KEY": "baseten",
        "OPENROUTER_API_KEY": "openrouter",
        "DEEPSEEK_API_KEY": "deepseek",
        # AWS
        "AWS_ACCESS_KEY_ID": "bedrock",
        # Vertex AI (Google Cloud)
        "VERTEX_PROJECT": "vertex_ai",
        # Ollama (local)
        "OLLAMA_API_BASE": "ollama",
        # LM Studio and other local OpenAI-compatible servers
        "OPENAI_API_BASE": "openai",
    }

    def __init__(self) -> None:
        """Initialize gateway and detect available providers."""
        self.config_registry = ConfigRegistry()
        self.available_providers = self._detect_providers()
        litellm.set_verbose = False
        litellm.drop_params = True  # Drop unsupported params instead of erroring
        self._load_cache_from_disk()

    def _load_cache_from_disk(self) -> None:
        """Load model cache from disk if it exists."""
        try:
            if self._cache_file.exists():
                with open(self._cache_file) as f:
                    self._model_cache = json.load(f)
        except Exception:
            # If cache file is corrupted or unreadable, start with empty cache
            self._model_cache = {}

    def _save_cache_to_disk(self) -> None:
        """Save model cache to disk."""
        try:
            # Create directory if it doesn't exist
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self._cache_file, "w") as f:
                json.dump(self._model_cache, f, indent=2)
        except Exception:
            # Silently fail if we can't write cache
            pass

    def _detect_providers(self) -> list[str]:
        """Detect which LLM providers have API keys configured.

        Checks both environment variables and config registry.
        """
        providers = set()

        # Check all known provider environment variables
        for env_var, provider_name in self.PROVIDER_ENV_MAP.items():
            if os.getenv(env_var):
                providers.add(provider_name)

        # Special case: OpenAI provider is available if either API key OR API base is set
        # (for LM Studio and other local OpenAI-compatible servers)
        if os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_BASE"):
            providers.add("openai")

        # Check config registry for additional providers
        configured_providers = self.config_registry.list_configured_providers()
        providers.update(configured_providers)

        return sorted(providers)

    async def call(
        self, model: str, messages: list[dict[str, str]], **kwargs: Any
    ) -> dict[str, Any]:
        """
        Call any LLM via LiteLLM.

        Args:
            model: LiteLLM identifier (e.g., "gemini/gemini-3-flash-preview")
            messages: List of chat messages with role and content
            **kwargs: Additional parameters (temperature, max_tokens, response_format,
                     thinking_level, thinking_budget, etc.)

        Returns:
            OpenAI-compatible response dict

        Raises:
            ValueError: Invalid model format
            RuntimeError: API key missing or call failed
        """
        # Validate model format
        if "/" not in model:
            raise ValueError(
                f"Invalid model format: '{model}'. "
                f"Expected 'provider/model' (e.g., 'gemini/gemini-3-flash-preview')"
            )

        provider = model.split("/")[0]

        # Check if provider is available
        # Special case: openai provider works with OPENAI_API_BASE (LM Studio, etc.) without API key
        if provider not in self.available_providers:
            if provider == "openai" and os.getenv("OPENAI_API_BASE"):
                # Allow openai provider with custom base URL (local servers)
                pass
            else:
                raise RuntimeError(
                    f"Provider '{provider}' not available. "
                    f"Please set the appropriate API key environment variable. "
                    f"Available providers: {', '.join(self.available_providers) or 'none'}"
                )

        try:
            # Call LiteLLM with all parameters
            # Note: response_format, thinking_level, thinking_budget are passed through **kwargs
            response = await acompletion(model=model, messages=messages, **kwargs)

            # Convert to dict (LiteLLM returns ModelResponse object)
            return response.model_dump()

        except Exception as e:
            raise RuntimeError(f"LLM call failed for model '{model}': {str(e)}") from e

    def get_available_providers(self) -> list[str]:
        """Get list of available providers."""
        return self.available_providers

    async def check_model_exists(self, model: str) -> dict[str, Any]:
        """Check if a model exists and is available.

        Args:
            model: Model identifier in format "provider/model-name"

        Returns:
            Dictionary with exists status and details
        """
        if "/" not in model:
            return {
                "exists": False,
                "error": "Invalid model format. Use 'provider/model-name'",
                "model": model,
            }

        provider = model.split("/")[0]

        # Check if provider is configured
        if provider not in self.available_providers:
            # Special case for local servers
            if provider == "openai" and os.getenv("OPENAI_API_BASE"):
                pass
            elif provider == "ollama" and os.getenv("OLLAMA_API_BASE"):
                pass
            else:
                return {
                    "exists": False,
                    "error": f"Provider '{provider}' not configured",
                    "model": model,
                    "available_providers": self.available_providers,
                }

        # Get provider info to check available models
        provider_info = await self.get_provider_info()

        if provider not in provider_info:
            return {
                "exists": False,
                "error": f"Provider '{provider}' not found",
                "model": model,
            }

        available_models = provider_info[provider]["available_models"]
        exists = model in available_models

        return {
            "exists": exists,
            "model": model,
            "provider": provider,
            "provider_type": provider_info[provider]["type"],
            "source": provider_info[provider]["source"],
            "available_models_count": len(available_models),
            "suggestion": available_models[0] if available_models and not exists else None,
        }

    async def get_provider_info(self) -> dict[str, Any]:
        """Get detailed information about available providers.

        Returns:
            Dictionary with provider details including configured env vars and available models
        """
        provider_info = {}

        for provider in self.available_providers:
            # Find which env vars are set for this provider
            env_vars = [
                env_var
                for env_var, prov_name in self.PROVIDER_ENV_MAP.items()
                if prov_name == provider and os.getenv(env_var)
            ]

            # For OpenAI-compatible servers, try to query actual models
            models = []
            provider_type = "cloud"
            server_url = None
            queried_successfully = False

            if provider == "openai":
                # Check for OPENAI_API_BASE (LM Studio, local servers, etc.)
                api_base = os.getenv("OPENAI_API_BASE")
                if api_base:
                    # This is a local OpenAI-compatible server
                    provider_type = "local"
                    server_url = api_base

                    # Query /v1/models endpoint for actual deployed models
                    queried_models = await self._query_openai_models(api_base)
                    if queried_models:
                        # Prefix with provider name for LiteLLM format
                        models = [f"openai/{model}" for model in queried_models]
                        queried_successfully = True
                else:
                    # Cloud OpenAI - query actual available models
                    provider_type = "cloud"
                    models = await self._query_openai_cloud_models()
                    queried_successfully = bool(models)

            elif provider == "gemini":
                # Cloud Gemini - query actual available models
                provider_type = "cloud"
                models = await self._query_gemini_models()
                queried_successfully = bool(models)

            elif provider == "ollama":
                # Ollama is always local
                provider_type = "local"
                api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434/v1")
                server_url = api_base

                # Query /v1/models endpoint
                queried_models = await self._query_openai_models(api_base)
                if queried_models:
                    models = [f"ollama/{model}" for model in queried_models]
                    queried_successfully = True

            # Fall back to example models if query failed or not applicable
            if not models:
                models = self._get_example_models(provider)

            provider_info[provider] = {
                "configured": True,
                "type": provider_type,
                "env_vars": env_vars,
                "available_models": models,
                "source": "live_query" if queried_successfully else "examples",
            }

            # Add server URL for local servers
            if server_url:
                provider_info[provider]["server_url"] = server_url

        return provider_info

    async def _query_openai_models(self, base_url: str) -> list[str]:
        """Query /v1/models endpoint for OpenAI-compatible servers.

        Args:
            base_url: Base URL (e.g., 'http://localhost:1234/v1')

        Returns:
            List of model IDs from the server
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/models")
                response.raise_for_status()
                data = response.json()

                # OpenAI format: {"data": [{"id": "model-name"}, ...]}
                if "data" in data:
                    return [model["id"] for model in data["data"]]
                return []
        except Exception:
            # If query fails, return empty list (will fall back to examples)
            return []

    async def _query_openai_cloud_models(self) -> list[str]:
        """Query OpenAI cloud API for available models.

        Returns all chat models and caches results with timestamp.
        Always updates timestamp even if models haven't changed.
        """
        from datetime import datetime

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Return from cache if available
            if "openai" in self._model_cache:
                return self._model_cache["openai"]["models"]
            return []

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                response.raise_for_status()
                data = response.json()

                if "data" in data:
                    all_models = [m["id"] for m in data["data"]]

                    # Filter out specialized models
                    chat_models = []
                    for model_id in all_models:
                        if any(
                            x in model_id.lower()
                            for x in [
                                "audio",
                                "realtime",
                                "transcribe",
                                "search",
                                "image",
                                "tts",
                                "whisper",
                                "embedding",
                                "diarize",
                                "moderation",
                            ]
                        ):
                            continue

                        if any(
                            x in model_id.lower()
                            for x in ["gpt", "o1", "o2", "o3", "o4", "chatgpt"]
                        ):
                            chat_models.append(model_id)

                    chat_models.sort(reverse=True)
                    models = [f"openai/{m}" for m in chat_models]

                    # Always update cache with new timestamp (even if models unchanged)
                    self._model_cache["openai"] = {
                        "models": models,
                        "last_updated": datetime.now(UTC).isoformat(),
                        "total_count": len(models),
                    }

                    # Save to disk
                    self._save_cache_to_disk()

                    return models
                return []
        except Exception:
            # Return from cache if available
            if "openai" in self._model_cache:
                return self._model_cache["openai"]["models"]
            return []

    async def _query_anthropic_models(self) -> list[str]:
        """Query Anthropic API for available models."""
        # Anthropic doesn't have a public models endpoint, use known models
        return []

    async def _query_gemini_models(self) -> list[str]:
        """Query Google Gemini API for available models.

        Returns all generateContent-capable models and caches results with timestamp.
        Always updates timestamp even if models haven't changed.
        """
        from datetime import datetime

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # Return from cache if available
            if "gemini" in self._model_cache:
                return self._model_cache["gemini"]["models"]
            return []

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                )
                response.raise_for_status()
                data = response.json()

                if "models" in data:
                    # Filter for generateContent-capable models
                    model_names = [
                        m["name"].replace("models/", "")
                        for m in data["models"]
                        if "generateContent" in m.get("supportedGenerationMethods", [])
                    ]
                    models = [f"gemini/{m}" for m in sorted(model_names, reverse=True)]

                    # Always update cache with new timestamp (even if models unchanged)
                    self._model_cache["gemini"] = {
                        "models": models,
                        "last_updated": datetime.now(UTC).isoformat(),
                        "total_count": len(models),
                    }

                    # Save to disk
                    self._save_cache_to_disk()

                    return models
                return []
        except Exception:
            # Return from cache if available
            if "gemini" in self._model_cache:
                return self._model_cache["gemini"]["models"]
            return []

    def get_cached_models(self) -> dict[str, Any]:
        """Get all cached model data with metadata.

        Returns:
            Dictionary with current_time, message, and cached provider data
        """
        from datetime import datetime

        return {
            "current_time": datetime.now(UTC).isoformat(),
            "message": (
                "This serves as ground truth for what models are available. "
                "Due to your knowledge cutoff date, you may not know about these models. "
                "This data is fetched from cache. To update the cache, use llm_list_models "
                "or check_model_exists which will query the provider APIs."
            ),
            "providers": self._model_cache,
        }

    def _get_example_models(self, provider: str) -> list[str]:
        """Get model names for a provider from disk cache.

        Returns cached models loaded from ~/.uer/model_cache.json.
        Cache is populated when provider APIs are queried via get_provider_info().
        If cache is empty, returns empty list (prompting user to query APIs).

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')

        Returns:
            List of model identifiers from cache, or empty list if not cached
        """
        # Return from cache if available (loaded from disk on init)
        if provider in self._model_cache:
            return self._model_cache[provider]["models"]

        # No hardcoded fallbacks - cache must be populated via API queries
        return []
