"""Delegation tool for multi-agent orchestration."""

import logging
from typing import Any

from mcp.types import TextContent, Tool

from ..llm.gateway import LLMGateway
from ..orchestration.orchestrator import DelegationResult, SubagentOrchestrator
from ..storage.manager import StorageManager

logger = logging.getLogger(__name__)


class DelegateToolHandler:
    """Handler for the delegate tool."""

    def __init__(self, gateway: LLMGateway, storage: StorageManager):
        """Initialize delegate tool handler.

        Args:
            gateway: LLM gateway for model calls
            storage: Storage manager for context resolution
        """
        self.orchestrator = SubagentOrchestrator(gateway=gateway, storage=storage)
        logger.info("DelegateToolHandler initialized")

    def get_tool_definition(self) -> Tool:
        """Get the delegate tool definition for MCP.

        Returns:
            Tool definition
        """
        return Tool(
            name="delegate",
            description=(
                "Delegate a task to a subagent with a different model. "
                "Enables multi-agent orchestration with behavior monitoring. "
                "Based on Chen 2024 AgentVerse research on emergent behaviors. "
                "Supports context injection from S3 storage and result persistence."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": (
                            "Model to delegate to (e.g., 'gpt-4', 'claude-3-5-sonnet-20241022', "
                            "'gemini/gemini-2.0-flash-exp')"
                        ),
                    },
                    "task": {
                        "type": "string",
                        "description": "Task description for the subagent",
                    },
                    "messages": {
                        "type": "array",
                        "description": (
                            "Optional pre-built message list. If not provided, "
                            "will create from task description."
                        ),
                        "items": {"type": "object"},
                    },
                    "tools": {
                        "type": "array",
                        "description": "Optional list of tools available to the subagent",
                        "items": {"type": "object"},
                    },
                    "context_refs": {
                        "type": "array",
                        "description": (
                            "Optional list of S3/registry URIs to inject as context "
                            "(e.g., ['s3://uer-context/analysis.txt', 'registry://skills/financial'])"
                        ),
                        "items": {"type": "string"},
                    },
                    "store_result": {
                        "type": "string",
                        "description": (
                            "Optional URI to store the delegation result "
                            "(e.g., 's3://uer-context/result.txt')"
                        ),
                    },
                    "max_iterations": {
                        "type": "integer",
                        "description": "Maximum agentic loop iterations (default: 10)",
                        "default": 10,
                    },
                    "agent_id": {
                        "type": "string",
                        "description": (
                            "Optional identifier for behavior tracking "
                            "(auto-generated if not provided)"
                        ),
                    },
                },
                "required": ["model", "task"],
            },
        )

    async def handle(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle delegate tool call.

        Args:
            arguments: Tool arguments

        Returns:
            List of text content with delegation result
        """
        model = arguments["model"]
        task = arguments["task"]
        messages = arguments.get("messages")
        tools = arguments.get("tools")
        context_refs = arguments.get("context_refs")
        store_result = arguments.get("store_result")
        max_iterations = arguments.get("max_iterations", 10)
        agent_id = arguments.get("agent_id")

        logger.info(f"Handling delegate call to {model} for task: {task[:100]}")

        # Build messages if not provided
        if not messages:
            messages = [{"role": "user", "content": task}]

        # Delegate to subagent
        result: DelegationResult = await self.orchestrator.delegate(
            model=model,
            messages=messages,
            tools=tools,
            context_refs=context_refs,
            store_result=store_result,
            max_iterations=max_iterations,
            agent_id=agent_id,
        )

        # Format response
        if result.success:
            response_text = "✅ Delegation successful\n\n"
            response_text += f"**Model:** {result.model_used}\n"
            response_text += f"**Iterations:** {result.iterations}\n"
            response_text += f"**Tokens:** {result.tokens_used}\n"

            if result.stored_at:
                response_text += f"**Stored at:** {result.stored_at}\n"

            # Check for behavior logs
            behavior_logs = self.orchestrator.get_behavior_logs(
                agent_id=result.metadata.get("agent_id")
            )
            if behavior_logs:
                response_text += f"\n**Behaviors detected:** {len(behavior_logs)}\n"
                for log in behavior_logs:
                    response_text += f"- {log.behavior_type}: {log.description[:100]}\n"

            response_text += f"\n**Response:**\n{result.response}"

        else:
            response_text = "❌ Delegation failed\n\n"
            response_text += f"**Error:** {result.error}\n"
            response_text += f"**Iterations:** {result.iterations}\n"
            if result.tokens_used:
                response_text += f"**Tokens used:** {result.tokens_used}\n"

        return [TextContent(type="text", text=response_text)]

    def get_behavior_summary(self) -> str:
        """Get summary of all behavior logs.

        Returns:
            Formatted summary of behavior logs
        """
        logs = self.orchestrator.get_behavior_logs()

        if not logs:
            return "No behaviors logged yet."

        summary = f"**Behavior Summary ({len(logs)} total)**\n\n"

        # Count by type
        by_type: dict[str, int] = {}
        for log in logs:
            by_type[log.behavior_type] = by_type.get(log.behavior_type, 0) + 1

        summary += "**By Type:**\n"
        for behavior_type, count in sorted(by_type.items()):
            summary += f"- {behavior_type}: {count}\n"

        # Show recent logs
        summary += "\n**Recent Behaviors:**\n"
        for log in logs[-5:]:
            summary += (
                f"- [{log.severity}] {log.agent_id}: "
                f"{log.behavior_type} - {log.description[:80]}\n"
            )

        return summary
