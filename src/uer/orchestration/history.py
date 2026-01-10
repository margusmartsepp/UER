"""Chat history builder for multi-agent conversations."""

import logging
from typing import Any

from ..models.message import ContextReference, Message, ToolCall

logger = logging.getLogger(__name__)


class ChatHistoryBuilder:
    """Builds chat history for LLM conversations with support for context injection.

    Supports system, user, assistant, and tool messages for multi-agent orchestration.
    Can inject context from S3 storage URIs.
    """

    def __init__(self):
        """Initialize empty chat history."""
        self.messages: list[Message] = []
        self.context_refs: list[ContextReference] = []

    def add_system(self, content: str) -> "ChatHistoryBuilder":
        """Add a system message.

        Args:
            content: System message content (instructions, context, etc.)

        Returns:
            Self for method chaining
        """
        self.messages.append(Message(role="system", content=content))
        logger.debug(f"Added system message ({len(content)} chars)")
        return self

    def add_user(self, content: str) -> "ChatHistoryBuilder":
        """Add a user message.

        Args:
            content: User message content

        Returns:
            Self for method chaining
        """
        self.messages.append(Message(role="user", content=content))
        logger.debug(f"Added user message ({len(content)} chars)")
        return self

    def add_assistant(
        self, content: str | None = None, tool_calls: list[dict[str, Any]] | None = None
    ) -> "ChatHistoryBuilder":
        """Add an assistant message.

        Args:
            content: Assistant response content (optional if tool_calls provided)
            tool_calls: List of tool calls made by assistant

        Returns:
            Self for method chaining
        """
        parsed_tool_calls = None
        if tool_calls:
            parsed_tool_calls = [
                ToolCall(
                    id=tc.get("id", ""),
                    type=tc.get("type", "function"),
                    function=tc.get("function", {}),
                )
                for tc in tool_calls
            ]

        self.messages.append(
            Message(role="assistant", content=content, tool_calls=parsed_tool_calls)
        )
        logger.debug(
            f"Added assistant message (content: {len(content or '')} chars, "
            f"tool_calls: {len(tool_calls or [])})"
        )
        return self

    def add_tool_result(
        self, tool_call_id: str, result: str, name: str | None = None
    ) -> "ChatHistoryBuilder":
        """Add a tool result message.

        Args:
            tool_call_id: ID of the tool call this responds to
            result: Result content from tool execution
            name: Optional name of the tool

        Returns:
            Self for method chaining
        """
        self.messages.append(
            Message(role="tool", content=result, tool_call_id=tool_call_id, name=name)
        )
        logger.debug(f"Added tool result for call {tool_call_id} ({len(result)} chars)")
        return self

    def add_context_ref(
        self,
        uri: str,
        description: str | None = None,
        inject_as: str = "system",
    ) -> "ChatHistoryBuilder":
        """Add a context reference to be resolved later.

        Args:
            uri: S3 URI or registry URI to context
            description: Optional description of the context
            inject_as: How to inject context ('system' or 'user')

        Returns:
            Self for method chaining
        """
        self.context_refs.append(
            ContextReference(uri=uri, description=description, inject_as=inject_as)
        )
        logger.debug(f"Added context reference: {uri} (inject as {inject_as})")
        return self

    def build(self) -> list[dict[str, Any]]:
        """Build the final message list for LLM API.

        Returns:
            List of message dictionaries ready for LLM API
        """
        result = [msg.to_dict() for msg in self.messages]
        logger.info(f"Built chat history with {len(result)} messages")
        return result

    def get_messages(self) -> list[Message]:
        """Get the raw message list.

        Returns:
            List of Message objects
        """
        return self.messages

    def clear(self) -> "ChatHistoryBuilder":
        """Clear all messages and context references.

        Returns:
            Self for method chaining
        """
        self.messages.clear()
        self.context_refs.clear()
        logger.debug("Cleared chat history")
        return self

    def message_count(self) -> int:
        """Get the number of messages in the history.

        Returns:
            Number of messages
        """
        return len(self.messages)

    def estimate_tokens(self) -> int:
        """Estimate token count (rough approximation).

        Uses simple heuristic: ~4 characters per token.

        Returns:
            Estimated token count
        """
        total_chars = sum(len(msg.content or "") for msg in self.messages)
        estimated_tokens = total_chars // 4
        logger.debug(f"Estimated tokens: {estimated_tokens} ({total_chars} chars)")
        return estimated_tokens
