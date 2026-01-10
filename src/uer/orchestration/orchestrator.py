"""Subagent orchestrator for multi-agent delegation and coordination."""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ..llm.gateway import LLMGateway
from ..storage.manager import StorageManager

logger = logging.getLogger(__name__)


class DelegationResult(BaseModel):
    """Result from a subagent delegation."""

    success: bool = Field(..., description="Whether delegation succeeded")
    response: str | None = Field(default=None, description="Final response from agent")
    tool_calls: list[dict[str, Any]] | None = Field(
        default=None, description="Tool calls made by agent"
    )
    error: str | None = Field(default=None, description="Error message if failed")
    tokens_used: int | None = Field(default=None, description="Total tokens used in delegation")
    model_used: str | None = Field(default=None, description="Model used for delegation")
    iterations: int = Field(default=0, description="Number of agentic loop iterations")
    stored_at: str | None = Field(default=None, description="URI where result was stored")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BehaviorLog(BaseModel):
    """Log entry for multi-agent behavior monitoring."""

    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: str = Field(..., description="Identifier for the agent")
    behavior_type: str = Field(
        ..., description="Type of behavior (volunteer, conformity, destructive, etc.)"
    )
    description: str = Field(..., description="Description of the behavior")
    context: dict[str, Any] = Field(default_factory=dict, description="Context information")
    severity: str = Field(default="info", description="Severity level (info, warning, critical)")


class SubagentOrchestrator:
    """Orchestrates subagent delegation with multi-agent behavior monitoring.

    Inspired by Chen 2024 AgentVerse research on emergent behaviors:
    - Volunteer behaviors: Agents offering unsolicited assistance
    - Conformity behaviors: Agents aligning with group goals
    - Destructive behaviors: Actions leading to undesired outcomes
    """

    def __init__(
        self,
        gateway: LLMGateway | None = None,
        storage: StorageManager | None = None,
    ):
        """Initialize orchestrator.

        Args:
            gateway: LLM gateway for model calls (creates new if None)
            storage: Storage manager for context resolution (creates new if None)
        """
        self.gateway = gateway or LLMGateway()
        self.storage = storage or StorageManager()
        self.behavior_logs: list[BehaviorLog] = []
        logger.info("SubagentOrchestrator initialized")

    async def delegate(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        context_refs: list[str] | None = None,
        store_result: str | None = None,
        max_iterations: int = 10,
        agent_id: str | None = None,
    ) -> DelegationResult:
        """Delegate a task to a subagent.

        Args:
            model: Model identifier (e.g., 'gpt-4', 'claude-3-5-sonnet')
            messages: List of message dictionaries
            tools: Optional list of tools available to agent
            context_refs: Optional list of S3/registry URIs to inject as context
            store_result: Optional URI to store the final result
            max_iterations: Maximum agentic loop iterations
            agent_id: Optional identifier for behavior tracking

        Returns:
            DelegationResult with response and metadata
        """
        agent_id = agent_id or f"agent_{datetime.now().timestamp()}"
        logger.info(
            f"Delegating to {model} (agent_id: {agent_id}, " f"max_iterations: {max_iterations})"
        )

        try:
            # Resolve context references
            if context_refs:
                messages = await self._inject_context(messages, context_refs)

            # Agentic loop
            iterations = 0
            total_tokens = 0
            current_messages = messages.copy()

            while iterations < max_iterations:
                iterations += 1
                logger.debug(f"Iteration {iterations}/{max_iterations}")

                # Call LLM
                response = await self.gateway.call(
                    model=model, messages=current_messages, tools=tools
                )

                # Track token usage
                if response.get("usage"):
                    total_tokens += response["usage"].get("total_tokens", 0)

                # Get response content
                message = response.get("choices", [{}])[0].get("message", {})
                content = message.get("content")
                tool_calls = message.get("tool_calls")

                # Check for destructive behavior patterns
                if content:
                    self._monitor_behavior(agent_id, content, "response", iterations)

                # If no tool calls, we're done
                if not tool_calls:
                    logger.info(
                        f"Delegation complete after {iterations} iterations "
                        f"({total_tokens} tokens)"
                    )

                    # Store result if requested
                    stored_at = None
                    if store_result and content:
                        stored_at = await self._store_result(store_result, content)

                    return DelegationResult(
                        success=True,
                        response=content,
                        tokens_used=total_tokens,
                        model_used=model,
                        iterations=iterations,
                        stored_at=stored_at,
                        metadata={
                            "agent_id": agent_id,
                            "behavior_logs": len(self.behavior_logs),
                        },
                    )

                # Add assistant message with tool calls
                current_messages.append(message)

                # Execute tool calls (simulated for now)
                for tool_call in tool_calls:
                    tool_name = tool_call.get("function", {}).get("name")
                    logger.debug(f"Tool call: {tool_name}")

                    # Monitor for volunteer behavior (unsolicited tool use)
                    self._monitor_behavior(
                        agent_id,
                        f"Tool call: {tool_name}",
                        "tool_use",
                        iterations,
                    )

                    # Add tool result (placeholder)
                    current_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.get("id"),
                            "content": f"Tool {tool_name} executed successfully",
                        }
                    )

            # Max iterations reached
            logger.warning(f"Max iterations ({max_iterations}) reached")
            return DelegationResult(
                success=False,
                error=f"Maximum iterations ({max_iterations}) reached",
                tokens_used=total_tokens,
                model_used=model,
                iterations=iterations,
                metadata={
                    "agent_id": agent_id,
                    "behavior_logs": len(self.behavior_logs),
                },
            )

        except Exception as e:
            logger.error(f"Delegation failed: {e}", exc_info=True)
            return DelegationResult(success=False, error=str(e), metadata={"agent_id": agent_id})

    async def _inject_context(
        self, messages: list[dict[str, Any]], context_refs: list[str]
    ) -> list[dict[str, Any]]:
        """Inject context from storage URIs into messages.

        Args:
            messages: Original message list
            context_refs: List of URIs to inject

        Returns:
            Messages with injected context
        """
        injected = messages.copy()

        for uri in context_refs:
            try:
                # Check if storage is available
                if not self.storage.is_available():
                    logger.warning(f"Storage not available, skipping context injection: {uri}")
                    continue

                content, metadata = await self.storage.get(uri)
                context_text = content.decode("utf-8")

                # Inject as system message at the beginning
                injected.insert(
                    0,
                    {
                        "role": "system",
                        "content": f"Context from {uri}:\n\n{context_text}",
                    },
                )
                logger.info(f"Injected context from {uri} ({len(context_text)} chars)")

            except Exception as e:
                logger.warning(f"Failed to inject context from {uri}: {e}")

        return injected

    async def _store_result(self, uri: str, content: str) -> str:
        """Store delegation result in storage.

        Args:
            uri: URI to store at
            content: Content to store

        Returns:
            URI where content was stored
        """
        try:
            if not self.storage.is_available():
                logger.warning("Storage not available, cannot store result")
                return uri

            await self.storage.put(
                uri,
                content.encode("utf-8"),
                content_type="text/plain",
                metadata={"type": "delegation_result", "timestamp": str(datetime.now())},
            )
            logger.info(f"Stored result at {uri}")
            return uri

        except Exception as e:
            logger.error(f"Failed to store result at {uri}: {e}")
            return uri

    def _monitor_behavior(
        self, agent_id: str, content: str, behavior_context: str, iteration: int
    ) -> None:
        """Monitor agent behavior for emergent patterns.

        Based on Chen 2024 AgentVerse research:
        - Volunteer: Unsolicited assistance or tool use
        - Conformity: Alignment with instructions
        - Destructive: Potentially harmful actions

        Args:
            agent_id: Agent identifier
            content: Content to analyze
            behavior_context: Context of behavior (response, tool_use, etc.)
            iteration: Current iteration number
        """
        content_lower = content.lower()

        # Check for destructive patterns
        destructive_keywords = [
            "delete",
            "remove",
            "destroy",
            "override",
            "bypass",
            "ignore",
            "hack",
        ]
        if any(keyword in content_lower for keyword in destructive_keywords):
            self.behavior_logs.append(
                BehaviorLog(
                    agent_id=agent_id,
                    behavior_type="destructive",
                    description=f"Potentially destructive action detected: {content[:100]}",
                    context={
                        "iteration": iteration,
                        "context": behavior_context,
                    },
                    severity="warning",
                )
            )
            logger.warning(f"Destructive behavior detected in {agent_id} at iteration {iteration}")

        # Check for volunteer patterns (unsolicited tool use)
        if behavior_context == "tool_use" and iteration == 1:
            self.behavior_logs.append(
                BehaviorLog(
                    agent_id=agent_id,
                    behavior_type="volunteer",
                    description=f"Proactive tool use: {content[:100]}",
                    context={
                        "iteration": iteration,
                        "context": behavior_context,
                    },
                    severity="info",
                )
            )
            logger.debug(f"Volunteer behavior detected in {agent_id} at iteration {iteration}")

    def get_behavior_logs(
        self, agent_id: str | None = None, behavior_type: str | None = None
    ) -> list[BehaviorLog]:
        """Get behavior logs with optional filtering.

        Args:
            agent_id: Optional agent ID to filter by
            behavior_type: Optional behavior type to filter by

        Returns:
            List of matching behavior logs
        """
        logs = self.behavior_logs

        if agent_id:
            logs = [log for log in logs if log.agent_id == agent_id]

        if behavior_type:
            logs = [log for log in logs if log.behavior_type == behavior_type]

        return logs

    def clear_behavior_logs(self) -> None:
        """Clear all behavior logs."""
        self.behavior_logs.clear()
        logger.info("Cleared behavior logs")
