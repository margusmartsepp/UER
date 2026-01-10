"""Message models for chat history and multi-agent communication."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """Represents a tool call made by an assistant."""

    id: str = Field(..., description="Unique identifier for the tool call")
    type: str = Field(default="function", description="Type of tool call")
    function: dict[str, Any] = Field(
        ..., description="Function details including name and arguments"
    )


class Message(BaseModel):
    """Represents a message in a chat conversation.

    Supports system, user, assistant, and tool roles for multi-agent orchestration.
    """

    role: Literal["system", "user", "assistant", "tool"] = Field(
        ..., description="Role of the message sender"
    )
    content: str | None = Field(default=None, description="Text content of the message")
    tool_calls: list[ToolCall] | None = Field(
        default=None, description="Tool calls made by assistant (assistant role only)"
    )
    tool_call_id: str | None = Field(
        default=None, description="ID of the tool call this responds to (tool role only)"
    )
    name: str | None = Field(
        default=None, description="Name of the tool or function (tool role only)"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary format for LLM APIs."""
        result: dict[str, Any] = {"role": self.role}

        if self.content is not None:
            result["content"] = self.content

        if self.tool_calls is not None:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": tc.function,
                }
                for tc in self.tool_calls
            ]

        if self.tool_call_id is not None:
            result["tool_call_id"] = self.tool_call_id

        if self.name is not None:
            result["name"] = self.name

        return result


class ContextReference(BaseModel):
    """Reference to stored context in S3 storage."""

    uri: str = Field(..., description="S3 URI or registry URI to context")
    description: str | None = Field(default=None, description="Optional description of the context")
    inject_as: Literal["system", "user"] = Field(
        default="system", description="How to inject the context into messages"
    )
