"""Pydantic models for LLM call requests and responses."""

from typing import Any, Literal

from pydantic import BaseModel, Field, validator


class LLMCallRequest(BaseModel):
    """Request for llm_call tool with validation."""

    model: str = Field(
        ..., description="LiteLLM model identifier (e.g., 'gemini/gemini-3-flash-preview')"
    )
    messages: list[dict[str, str]] = Field(
        ..., min_length=1, description="List of chat messages with 'role' and 'content' keys"
    )
    temperature: float | None = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int | None = Field(default=4096, ge=1, description="Maximum tokens to generate")

    # Structured Output Support
    response_format: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Force structured JSON output matching a schema. "
            "Format: {'type': 'json_schema', 'json_schema': {'name': '...', 'schema': {...}, 'strict': True}}. "
            "The calling LLM can generate schemas dynamically based on the task."
        ),
    )

    # Chain of Thought Support (Gemini-specific)
    thinking_level: Literal["minimal", "low", "medium", "high"] | None = Field(
        default=None,
        description=(
            "Gemini 3 reasoning level. Use 'high' for complex tasks requiring deep reasoning, "
            "'low' for simple tasks. Defaults to 'high' if not specified."
        ),
    )
    thinking_budget: int | None = Field(
        default=None,
        ge=-1,
        le=32768,
        description=(
            "Gemini 2.5 thinking tokens budget (128-32768, or -1 for dynamic). "
            "Use -1 for automatic complexity-based allocation."
        ),
    )

    @validator("model")
    def validate_model_format(cls, v: str) -> str:
        """Ensure model is in 'provider/model' format."""
        if "/" not in v:
            raise ValueError(f"Model must be in format 'provider/model', got '{v}'")
        return v

    @validator("messages")
    def validate_messages(cls, v: list[dict[str, str]]) -> list[dict[str, str]]:
        """Ensure messages have required fields."""
        for msg in v:
            if "role" not in msg:
                raise ValueError("Each message must have 'role' field")
            if "content" not in msg:
                raise ValueError("Each message must have 'content' field")
        return v

    @validator("response_format")
    def validate_response_format(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Validate response_format structure."""
        if v is not None:
            if "type" not in v:
                raise ValueError("response_format must have 'type' field")
            if v["type"] == "json_schema" and "json_schema" not in v:
                raise ValueError("json_schema response_format must have 'json_schema' field")
        return v


class LLMCallResponse(BaseModel):
    """Response from llm_call tool."""

    model: str
    choices: list[dict[str, Any]]
    usage: dict[str, int] | None = None

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "examples": [
                {
                    "model": "gemini/gemini-3-flash-preview",
                    "choices": [
                        {"message": {"role": "assistant", "content": "Hello! How can I help you?"}}
                    ],
                    "usage": {"total_tokens": 25},
                }
            ]
        }
