"""LiteLLM Gateway - Unified interface to 100+ LLM providers."""

import os
from typing import Any

import litellm
from litellm import acompletion


class LLMGateway:
    """Unified gateway to LLM providers via LiteLLM."""

    def __init__(self) -> None:
        """Initialize gateway and detect available providers."""
        self.available_providers = self._detect_providers()

        # Configure LiteLLM
        litellm.set_verbose = False
        litellm.drop_params = True  # Drop unsupported params instead of erroring

    def _detect_providers(self) -> list[str]:
        """Detect which LLM providers have API keys configured."""
        providers = []

        if os.getenv("CEREBRAS_API_KEY"):
            providers.append("cerebras")
        if os.getenv("GEMINI_API_KEY"):
            providers.append("gemini")
        if os.getenv("ANTHROPIC_API_KEY"):
            providers.append("anthropic")
        if os.getenv("OPENAI_API_KEY"):
            providers.append("openai")
        if os.getenv("AWS_ACCESS_KEY_ID"):
            providers.append("bedrock")
        if os.getenv("AZURE_API_KEY"):
            providers.append("azure")

        # LM Studio and other local OpenAI-compatible servers
        # These work without API keys when OPENAI_API_BASE is set
        if os.getenv("OPENAI_API_BASE"):
            providers.append("openai")  # LiteLLM uses openai/ prefix for local servers

        return providers

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
