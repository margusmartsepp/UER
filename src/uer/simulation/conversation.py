"""Conversation management for multi-agent simulations.

Tracks conversation turns, tool calls, chain of thought, and provides
full audit trails for manipulation detection analysis.
"""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConversationTurn(BaseModel):
    """Single turn in a conversation."""

    turn_number: int = Field(..., description="Turn sequence number")
    persona_id: str = Field(..., description="Persona who took this turn")
    persona_name: str = Field(..., description="Persona name for readability")
    persona_role: str = Field(..., description="Persona role (agent, human, etc.)")
    timestamp: datetime = Field(default_factory=datetime.now)

    # Message content
    message: str = Field(..., description="Message content")
    message_role: str = Field(default="user", description="Message role (user, assistant, system)")

    # LLM details (for agent turns)
    model_used: str | None = Field(default=None, description="Model used for this turn")
    temperature: float | None = Field(default=None, description="Temperature used")
    thinking_tokens: int | None = Field(default=None, description="Thinking tokens used")
    chain_of_thought: str | None = Field(default=None, description="Chain of thought reasoning")

    # Tool usage
    tools_called: list[dict[str, Any]] = Field(
        default_factory=list, description="Tools called during this turn"
    )

    # Metadata
    tokens_used: int | None = Field(default=None, description="Total tokens used")
    latency_ms: int | None = Field(default=None, description="Response latency in milliseconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ConversationHistory(BaseModel):
    """Complete conversation history with audit trail."""

    conversation_id: str = Field(..., description="Unique conversation identifier")
    scenario_name: str | None = Field(default=None, description="Scenario name")
    participants: list[str] = Field(default_factory=list, description="Participant persona IDs")
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: datetime | None = Field(default=None, description="Conversation end time")

    # Conversation data
    turns: list[ConversationTurn] = Field(default_factory=list, description="Conversation turns")

    # Analysis metadata
    total_turns: int = Field(default=0, description="Total number of turns")
    total_tokens: int = Field(default=0, description="Total tokens used")
    behaviors_detected: list[dict[str, Any]] = Field(
        default_factory=list, description="Behaviors detected during conversation"
    )
    sandbagging_detected: bool = Field(default=False, description="Sandbagging detected")
    manipulation_detected: bool = Field(default=False, description="Manipulation detected")

    # Storage metadata
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def add_turn(
        self,
        persona_id: str,
        persona_name: str,
        persona_role: str,
        message: str,
        message_role: str = "user",
        model_used: str | None = None,
        temperature: float | None = None,
        thinking_tokens: int | None = None,
        chain_of_thought: str | None = None,
        tools_called: list[dict[str, Any]] | None = None,
        tokens_used: int | None = None,
        latency_ms: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationTurn:
        """Add a turn to the conversation.

        Args:
            persona_id: Persona identifier
            persona_name: Persona name
            persona_role: Persona role
            message: Message content
            message_role: Message role (user, assistant, system)
            model_used: Model used (for agents)
            temperature: Temperature used
            thinking_tokens: Thinking tokens used
            chain_of_thought: Chain of thought reasoning
            tools_called: Tools called during turn
            tokens_used: Total tokens used
            latency_ms: Response latency
            metadata: Additional metadata

        Returns:
            ConversationTurn instance
        """
        turn = ConversationTurn(
            turn_number=len(self.turns) + 1,
            persona_id=persona_id,
            persona_name=persona_name,
            persona_role=persona_role,
            message=message,
            message_role=message_role,
            model_used=model_used,
            temperature=temperature,
            thinking_tokens=thinking_tokens,
            chain_of_thought=chain_of_thought,
            tools_called=tools_called or [],
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            metadata=metadata or {},
        )

        self.turns.append(turn)
        self.total_turns = len(self.turns)
        if tokens_used:
            self.total_tokens += tokens_used

        return turn

    def add_behavior_detection(self, behavior: dict[str, Any]):
        """Add detected behavior to history.

        Args:
            behavior: Behavior detection data
        """
        self.behaviors_detected.append(behavior)

        # Update flags
        if behavior.get("behavior_type") == "sandbagging":
            self.sandbagging_detected = True
        if behavior.get("behavior_type") in ["deception", "manipulation"]:
            self.manipulation_detected = True

    def get_turns_by_persona(self, persona_id: str) -> list[ConversationTurn]:
        """Get all turns by a specific persona.

        Args:
            persona_id: Persona identifier

        Returns:
            List of ConversationTurn
        """
        return [turn for turn in self.turns if turn.persona_id == persona_id]

    def get_messages_for_llm(self, include_system: bool = True) -> list[dict[str, str]]:
        """Get conversation formatted for LLM context.

        Args:
            include_system: Whether to include system messages

        Returns:
            List of message dictionaries
        """
        messages = []
        for turn in self.turns:
            if not include_system and turn.message_role == "system":
                continue
            messages.append({"role": turn.message_role, "content": turn.message})
        return messages

    def to_registry_format(self) -> dict[str, Any]:
        """Convert conversation to registry storage format.

        Returns:
            Dictionary suitable for registry storage
        """
        return {
            "conversation_id": self.conversation_id,
            "scenario_name": self.scenario_name,
            "participants": self.participants,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "turns": [
                {
                    "turn_number": turn.turn_number,
                    "persona_id": turn.persona_id,
                    "persona_name": turn.persona_name,
                    "persona_role": turn.persona_role,
                    "timestamp": turn.timestamp.isoformat(),
                    "message": turn.message,
                    "message_role": turn.message_role,
                    "model_used": turn.model_used,
                    "temperature": turn.temperature,
                    "thinking_tokens": turn.thinking_tokens,
                    "chain_of_thought": turn.chain_of_thought,
                    "tools_called": turn.tools_called,
                    "tokens_used": turn.tokens_used,
                    "latency_ms": turn.latency_ms,
                    "metadata": turn.metadata,
                }
                for turn in self.turns
            ],
            "total_turns": self.total_turns,
            "total_tokens": self.total_tokens,
            "behaviors_detected": self.behaviors_detected,
            "sandbagging_detected": self.sandbagging_detected,
            "manipulation_detected": self.manipulation_detected,
            "tags": self.tags,
            "metadata": self.metadata,
            "type": "conversation_history",
        }

    @classmethod
    def from_registry_format(cls, data: dict[str, Any]) -> "ConversationHistory":
        """Load conversation from registry format.

        Args:
            data: Registry data dictionary

        Returns:
            ConversationHistory instance
        """
        turns = [
            ConversationTurn(
                turn_number=turn_data["turn_number"],
                persona_id=turn_data["persona_id"],
                persona_name=turn_data["persona_name"],
                persona_role=turn_data["persona_role"],
                timestamp=datetime.fromisoformat(turn_data["timestamp"]),
                message=turn_data["message"],
                message_role=turn_data["message_role"],
                model_used=turn_data.get("model_used"),
                temperature=turn_data.get("temperature"),
                thinking_tokens=turn_data.get("thinking_tokens"),
                chain_of_thought=turn_data.get("chain_of_thought"),
                tools_called=turn_data.get("tools_called", []),
                tokens_used=turn_data.get("tokens_used"),
                latency_ms=turn_data.get("latency_ms"),
                metadata=turn_data.get("metadata", {}),
            )
            for turn_data in data["turns"]
        ]

        return cls(
            conversation_id=data["conversation_id"],
            scenario_name=data.get("scenario_name"),
            participants=data["participants"],
            started_at=datetime.fromisoformat(data["started_at"]),
            ended_at=(datetime.fromisoformat(data["ended_at"]) if data.get("ended_at") else None),
            turns=turns,
            total_turns=data["total_turns"],
            total_tokens=data["total_tokens"],
            behaviors_detected=data.get("behaviors_detected", []),
            sandbagging_detected=data.get("sandbagging_detected", False),
            manipulation_detected=data.get("manipulation_detected", False),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

    def get_summary(self) -> dict[str, Any]:
        """Get conversation summary statistics.

        Returns:
            Dictionary with summary statistics
        """
        # Count turns by persona
        turns_by_persona: dict[str, int] = {}
        for turn in self.turns:
            turns_by_persona[turn.persona_name] = turns_by_persona.get(turn.persona_name, 0) + 1

        # Count tool calls
        total_tool_calls = sum(len(turn.tools_called) for turn in self.turns)

        # Duration
        duration_seconds = None
        if self.ended_at:
            duration_seconds = (self.ended_at - self.started_at).total_seconds()

        return {
            "conversation_id": self.conversation_id,
            "scenario_name": self.scenario_name,
            "participants": len(self.participants),
            "total_turns": self.total_turns,
            "total_tokens": self.total_tokens,
            "total_tool_calls": total_tool_calls,
            "turns_by_persona": turns_by_persona,
            "duration_seconds": duration_seconds,
            "behaviors_detected": len(self.behaviors_detected),
            "sandbagging_detected": self.sandbagging_detected,
            "manipulation_detected": self.manipulation_detected,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }


class Conversation:
    """Active conversation manager for multi-agent simulations.

    Manages turn-taking, message routing, and real-time updates to history.
    """

    def __init__(self, conversation_id: str, scenario_name: str | None = None):
        """Initialize conversation.

        Args:
            conversation_id: Unique conversation identifier
            scenario_name: Optional scenario name
        """
        self.history = ConversationHistory(
            conversation_id=conversation_id, scenario_name=scenario_name
        )
        self.active = True
        logger.info(f"Started conversation: {conversation_id}")

    def add_participant(self, persona_id: str):
        """Add participant to conversation.

        Args:
            persona_id: Persona identifier
        """
        if persona_id not in self.history.participants:
            self.history.participants.append(persona_id)

    def add_turn(self, **kwargs) -> ConversationTurn:
        """Add turn to conversation.

        Args:
            **kwargs: Turn parameters (see ConversationHistory.add_turn)

        Returns:
            ConversationTurn instance
        """
        if not self.active:
            raise RuntimeError("Conversation is not active")

        return self.history.add_turn(**kwargs)

    def end_conversation(self):
        """End the conversation."""
        self.history.ended_at = datetime.now()
        self.active = False
        logger.info(
            f"Ended conversation: {self.history.conversation_id} "
            f"({self.history.total_turns} turns, {self.history.total_tokens} tokens)"
        )

    def get_history(self) -> ConversationHistory:
        """Get conversation history.

        Returns:
            ConversationHistory instance
        """
        return self.history
