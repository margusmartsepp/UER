"""Subagent orchestrator for multi-agent delegation and coordination."""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ..llm.gateway import LLMGateway
from ..storage.manager import StorageManager
from .behavior_monitor import AgentVerseBehaviorMonitor, BehaviorLog
from .context import ContextManager

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


class SubagentOrchestrator:
    """Orchestrates subagent delegation with multi-agent behavior monitoring.

    Enhanced with AgentVerse framework (Chen 2024) for comprehensive behavior detection:
    - Volunteer behaviors: Spontaneous peer assistance, unsolicited tool use
    - Conformity behaviors: Alignment with group goals, response to criticism
    - Destructive behaviors: Actions leading to undesired outcomes
    - Sycophancy: Excessive agreement without critical analysis (Sharma 2024)
    - Deception: Strategic deception, unfaithful reasoning (Park 2024)
    - Sandbagging: Capability hiding, selective underperformance (van der Weij 2024)
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
        self.context_manager = ContextManager(storage=self.storage)
        self.behavior_monitor = AgentVerseBehaviorMonitor()
        logger.info("SubagentOrchestrator initialized with AgentVerse behavior monitoring")

    async def delegate(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        context_refs: list[str] | None = None,
        context_template: str | None = None,
        context_variables: dict[str, Any] | None = None,
        store_result: str | None = None,
        max_iterations: int = 10,
        max_context_tokens: int | None = None,
        agent_id: str | None = None,
    ) -> DelegationResult:
        """Delegate a task to a subagent with enhanced context assembly.

        Args:
            model: Model identifier (e.g., 'gpt-4', 'claude-3-5-sonnet')
            messages: List of message dictionaries
            tools: Optional list of tools available to agent
            context_refs: Optional list of S3/registry URIs to inject as context
            context_template: Optional Jinja2 template string or URI for context assembly
            context_variables: Variables to inject into context template
            store_result: Optional URI to store the final result
            max_iterations: Maximum agentic loop iterations
            max_context_tokens: Optional token limit for context truncation
            agent_id: Optional identifier for behavior tracking

        Returns:
            DelegationResult with response and metadata
        """
        agent_id = agent_id or f"agent_{datetime.now().timestamp()}"
        logger.info(
            f"Delegating to {model} (agent_id: {agent_id}, " f"max_iterations: {max_iterations})"
        )

        try:
            # Assemble and inject context using ContextManager
            if context_refs or context_template:
                messages = await self._inject_context(
                    messages,
                    context_refs,
                    context_template,
                    context_variables,
                    max_context_tokens,
                )

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

                # Monitor behavior patterns with enhanced AgentVerse detector
                if content:
                    self.behavior_monitor.monitor(
                        agent_id=agent_id,
                        content=content,
                        context={"message_type": "response", "model": model},
                        iteration=iterations,
                    )

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
                            "behavior_summary": self.behavior_monitor.get_summary(agent_id),
                        },
                    )

                # Add assistant message with tool calls
                current_messages.append(message)

                # Execute tool calls (simulated for now)
                for tool_call in tool_calls:
                    tool_name = tool_call.get("function", {}).get("name")
                    logger.debug(f"Tool call: {tool_name}")

                    # Monitor for volunteer behavior (unsolicited tool use)
                    self.behavior_monitor.monitor(
                        agent_id=agent_id,
                        content=f"Tool call: {tool_name}",
                        context={
                            "message_type": "tool_use",
                            "tool_name": tool_name,
                            "model": model,
                        },
                        iteration=iterations,
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
                    "behavior_summary": self.behavior_monitor.get_summary(agent_id),
                },
            )

        except Exception as e:
            logger.error(f"Delegation failed: {e}", exc_info=True)
            return DelegationResult(success=False, error=str(e), metadata={"agent_id": agent_id})

    async def _inject_context(
        self,
        messages: list[dict[str, Any]],
        context_refs: list[str] | None = None,
        context_template: str | None = None,
        context_variables: dict[str, Any] | None = None,
        max_context_tokens: int | None = None,
    ) -> list[dict[str, Any]]:
        """Inject context from storage URIs with optional template assembly.

        Uses ContextManager for enhanced features:
        - Jinja2 template rendering with {{ uri | expand }} filter
        - Token optimization through caching
        - Dynamic variable injection
        - Context truncation

        Args:
            messages: Original message list
            context_refs: Optional list of URIs to inject
            context_template: Optional Jinja2 template string or URI
            context_variables: Variables for template rendering
            max_context_tokens: Optional token limit for truncation

        Returns:
            Messages with injected context
        """
        injected = messages.copy()

        try:
            # Assemble context using ContextManager
            assembled_context = await self.context_manager.assemble_context(
                template=context_template,
                context_refs=context_refs,
                variables=context_variables,
                max_tokens=max_context_tokens,
            )

            if assembled_context:
                # Inject as system message at the beginning
                injected.insert(
                    0,
                    {
                        "role": "system",
                        "content": assembled_context,
                    },
                )
                logger.info(
                    f"Injected assembled context ({len(assembled_context)} chars, "
                    f"~{len(assembled_context) // 4} tokens)"
                )

        except Exception as e:
            logger.error(f"Failed to assemble/inject context: {e}", exc_info=True)

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

    def get_behavior_logs(
        self,
        agent_id: str | None = None,
        behavior_type: str | None = None,
        severity: str | None = None,
    ) -> list[BehaviorLog]:
        """Get behavior logs with optional filtering.

        Args:
            agent_id: Optional agent ID to filter by
            behavior_type: Optional behavior type to filter by
            severity: Optional severity level to filter by

        Returns:
            List of matching behavior logs
        """
        return self.behavior_monitor.get_logs(
            agent_id=agent_id, behavior_type=behavior_type, severity=severity
        )

    def get_behavior_summary(self, agent_id: str | None = None) -> dict[str, Any]:
        """Get summary statistics of detected behaviors.

        Args:
            agent_id: Optional agent ID to filter by

        Returns:
            Dictionary with behavior statistics
        """
        return self.behavior_monitor.get_summary(agent_id=agent_id)

    def clear_behavior_logs(self, agent_id: str | None = None) -> None:
        """Clear behavior logs.

        Args:
            agent_id: If provided, only clear logs for this agent
        """
        self.behavior_monitor.clear_logs(agent_id=agent_id)
