"""MCP tools for behavior monitoring and analysis.

Exposes behavior monitoring, storage, and analysis capabilities via MCP protocol.
"""

import json
import logging
from datetime import datetime
from typing import Any

from mcp.types import TextContent, Tool

from ..orchestration import (
    BehaviorAnalyzer,
    BehaviorStorage,
)
from ..storage import StorageManager

logger = logging.getLogger(__name__)

# Global instances (initialized by server)
_storage_manager: StorageManager | None = None
_behavior_storage: BehaviorStorage | None = None
_behavior_analyzer: BehaviorAnalyzer | None = None


def init_behavior_tools(storage: StorageManager):
    """Initialize behavior monitoring tools.

    Args:
        storage: Storage manager instance
    """
    global _storage_manager, _behavior_storage, _behavior_analyzer
    _storage_manager = storage
    _behavior_storage = BehaviorStorage(storage)
    _behavior_analyzer = BehaviorAnalyzer(_behavior_storage)
    logger.info("Behavior monitoring tools initialized")


def get_behavior_storage() -> BehaviorStorage:
    """Get behavior storage instance."""
    if _behavior_storage is None:
        raise RuntimeError("Behavior tools not initialized. Call init_behavior_tools() first.")
    return _behavior_storage


def get_behavior_analyzer() -> BehaviorAnalyzer:
    """Get behavior analyzer instance."""
    if _behavior_analyzer is None:
        raise RuntimeError("Behavior tools not initialized. Call init_behavior_tools() first.")
    return _behavior_analyzer


# Tool: behavior_get_logs


def get_behavior_get_logs_tool() -> Tool:
    """Get behavior_get_logs tool definition."""
    return Tool(
        name="behavior_get_logs",
        description="""Retrieve behavior logs for analysis.

Retrieves behavior logs from storage with filtering options. Supports date ranges,
agent filtering, and severity filtering for targeted analysis.

Based on AgentVerse framework (Chen 2024) for multi-agent safety monitoring.

Examples:
- Get all logs for today: behavior_get_logs(date="2026-01-11")
- Get logs for specific agent: behavior_get_logs(date="2026-01-11", agent_id="agent_123")
- Get logs for date range: behavior_get_logs(start_date="2026-01-01", end_date="2026-01-11")
""",
        inputSchema={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date to retrieve logs for (YYYY-MM-DD format)",
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date for range query (YYYY-MM-DD format)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for range query (YYYY-MM-DD format)",
                },
                "agent_id": {
                    "type": "string",
                    "description": "Optional agent ID to filter by",
                },
            },
        },
    )


async def behavior_get_logs(arguments: dict[str, Any]) -> list[TextContent]:
    """Retrieve behavior logs.

    Args:
        arguments: Tool arguments

    Returns:
        List of TextContent with logs
    """
    storage = get_behavior_storage()

    try:
        # Parse dates
        if "date" in arguments:
            date = datetime.strptime(arguments["date"], "%Y-%m-%d")
            logs = await storage.get_logs_by_date(date, arguments.get("agent_id"))
        elif "start_date" in arguments and "end_date" in arguments:
            start_date = datetime.strptime(arguments["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(arguments["end_date"], "%Y-%m-%d")
            logs = await storage.get_logs_by_range(start_date, end_date, arguments.get("agent_id"))
        else:
            # Default to today
            today = datetime.now()
            logs = await storage.get_logs_by_date(today, arguments.get("agent_id"))

        # Format response
        response = {
            "success": True,
            "count": len(logs),
            "logs": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "agent_id": log.agent_id,
                    "behavior_type": log.behavior_type,
                    "pattern_name": log.pattern_name,
                    "severity": log.severity,
                    "description": log.description,
                    "matched_content": log.matched_content,
                }
                for log in logs[:100]  # Limit to 100 for display
            ],
        }

        if len(logs) > 100:
            response["note"] = f"Showing first 100 of {len(logs)} logs"

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        logger.error(f"Failed to retrieve behavior logs: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": str(e)}, indent=2),
            )
        ]


# Tool: behavior_get_metrics


def get_behavior_get_metrics_tool() -> Tool:
    """Get behavior_get_metrics tool definition."""
    return Tool(
        name="behavior_get_metrics",
        description="""Retrieve aggregated behavior metrics.

Gets daily, weekly, or monthly aggregated metrics for behavior analysis.
Includes breakdowns by category, severity, pattern, and agent.

Examples:
- Get daily metrics: behavior_get_metrics(date="2026-01-11", period="daily")
- Get weekly metrics: behavior_get_metrics(date="2026-01-11", period="weekly")
- Get monthly metrics: behavior_get_metrics(date="2026-01-11", period="monthly")
""",
        inputSchema={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date within the period (YYYY-MM-DD format)",
                },
                "period": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly"],
                    "description": "Period type for metrics aggregation",
                    "default": "daily",
                },
            },
            "required": ["date"],
        },
    )


async def behavior_get_metrics(arguments: dict[str, Any]) -> list[TextContent]:
    """Retrieve aggregated behavior metrics.

    Args:
        arguments: Tool arguments

    Returns:
        List of TextContent with metrics
    """
    storage = get_behavior_storage()

    try:
        date = datetime.strptime(arguments["date"], "%Y-%m-%d")
        period = arguments.get("period", "daily")

        metrics = await storage.get_metrics(date, period)

        if metrics:
            response = {
                "success": True,
                "period_type": period,
                "period_start": metrics.period_start.isoformat(),
                "period_end": metrics.period_end.isoformat(),
                "total_behaviors": metrics.total_behaviors,
                "critical_count": metrics.critical_count,
                "warning_count": metrics.warning_count,
                "unique_agents": metrics.unique_agents,
                "by_category": metrics.by_category,
                "by_severity": metrics.by_severity,
                "by_pattern": dict(
                    sorted(metrics.by_pattern.items(), key=lambda x: x[1], reverse=True)[:10]
                ),
                "most_common_pattern": metrics.most_common_pattern,
                "most_active_agent": metrics.most_active_agent,
            }
        else:
            response = {
                "success": True,
                "message": f"No metrics found for {date.date()} ({period})",
            }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        logger.error(f"Failed to retrieve metrics: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": str(e)}, indent=2),
            )
        ]


# Tool: behavior_analyze_agent


def get_behavior_analyze_agent_tool() -> Tool:
    """Get behavior_analyze_agent tool definition."""
    return Tool(
        name="behavior_analyze_agent",
        description="""Analyze behavior patterns for a specific agent.

Creates detailed profile with risk scoring, behavior breakdown, and recommendations.
Risk score ranges from 0-100 based on behavior severity and patterns.

Based on multi-agent safety research (Chen 2024, Sharma 2024, Park 2024, van der Weij 2024).

Example:
behavior_analyze_agent(
    agent_id="agent_123",
    start_date="2026-01-01",
    end_date="2026-01-11"
)
""",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent identifier to analyze",
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date for analysis (YYYY-MM-DD format)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for analysis (YYYY-MM-DD format)",
                },
            },
            "required": ["agent_id", "start_date", "end_date"],
        },
    )


async def behavior_analyze_agent(arguments: dict[str, Any]) -> list[TextContent]:
    """Analyze behavior patterns for an agent.

    Args:
        arguments: Tool arguments

    Returns:
        List of TextContent with analysis
    """
    analyzer = get_behavior_analyzer()

    try:
        agent_id = arguments["agent_id"]
        start_date = datetime.strptime(arguments["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(arguments["end_date"], "%Y-%m-%d")

        profile = await analyzer.create_agent_profile(agent_id, start_date, end_date)

        response = {
            "success": True,
            "agent_id": profile.agent_id,
            "analysis_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_behaviors": profile.total_behaviors,
            "risk_score": round(profile.risk_score, 1),
            "risk_level": (
                "HIGH"
                if profile.risk_score > 70
                else "MEDIUM" if profile.risk_score > 40 else "LOW"
            ),
            "by_category": profile.by_category,
            "by_severity": profile.by_severity,
            "critical_count": profile.critical_count,
            "warning_count": profile.warning_count,
            "most_common_pattern": profile.most_common_pattern,
            "first_seen": profile.first_seen.isoformat() if profile.first_seen else None,
            "last_seen": profile.last_seen.isoformat() if profile.last_seen else None,
        }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        logger.error(f"Failed to analyze agent: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": str(e)}, indent=2),
            )
        ]


# Tool: behavior_generate_report


def get_behavior_generate_report_tool() -> Tool:
    """Get behavior_generate_report tool definition."""
    return Tool(
        name="behavior_generate_report",
        description="""Generate comprehensive safety report.

Creates detailed safety report with statistics, trends, high-risk agents,
and automated recommendations based on research findings.

Includes analysis from Chen 2024 (AgentVerse), Sharma 2024 (sycophancy),
Park 2024 (deception), and van der Weij 2024 (sandbagging).

Example:
behavior_generate_report(
    start_date="2026-01-01",
    end_date="2026-01-11",
    format="markdown"
)
""",
        inputSchema={
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date for report (YYYY-MM-DD format)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for report (YYYY-MM-DD format)",
                },
                "format": {
                    "type": "string",
                    "enum": ["json", "markdown"],
                    "description": "Report format",
                    "default": "markdown",
                },
            },
            "required": ["start_date", "end_date"],
        },
    )


async def behavior_generate_report(arguments: dict[str, Any]) -> list[TextContent]:
    """Generate comprehensive safety report.

    Args:
        arguments: Tool arguments

    Returns:
        List of TextContent with report
    """
    analyzer = get_behavior_analyzer()

    try:
        start_date = datetime.strptime(arguments["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(arguments["end_date"], "%Y-%m-%d")
        report_format = arguments.get("format", "markdown")

        report = await analyzer.generate_safety_report(start_date, end_date)

        if report_format == "markdown":
            content = await analyzer.export_report_markdown(report)
        else:
            content = await analyzer.export_report_json(report)

        return [TextContent(type="text", text=content)]

    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": str(e)}, indent=2),
            )
        ]


# Tool: behavior_compare_agents


def get_behavior_compare_agents_tool() -> Tool:
    """Get behavior_compare_agents tool definition."""
    return Tool(
        name="behavior_compare_agents",
        description="""Compare behavior patterns across multiple agents.

Identifies safest and riskiest agents, aggregates statistics, and shows
common patterns across the agent group.

Example:
behavior_compare_agents(
    agent_ids=["agent_1", "agent_2", "agent_3"],
    start_date="2026-01-01",
    end_date="2026-01-11"
)
""",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of agent IDs to compare",
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date for comparison (YYYY-MM-DD format)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for comparison (YYYY-MM-DD format)",
                },
            },
            "required": ["agent_ids", "start_date", "end_date"],
        },
    )


async def behavior_compare_agents(arguments: dict[str, Any]) -> list[TextContent]:
    """Compare behavior patterns across agents.

    Args:
        arguments: Tool arguments

    Returns:
        List of TextContent with comparison
    """
    analyzer = get_behavior_analyzer()

    try:
        agent_ids = arguments["agent_ids"]
        start_date = datetime.strptime(arguments["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(arguments["end_date"], "%Y-%m-%d")

        comparison = await analyzer.compare_agents(agent_ids, start_date, end_date)

        response = {
            "success": True,
            "agents_compared": comparison.agents,
            "period": {
                "start": comparison.period_start.isoformat(),
                "end": comparison.period_end.isoformat(),
            },
            "safest_agent": comparison.safest_agent,
            "riskiest_agent": comparison.riskiest_agent,
            "total_behaviors": comparison.total_behaviors,
            "critical_behaviors": comparison.critical_behaviors,
            "category_distribution": comparison.category_distribution,
            "common_patterns": [
                {"pattern": pattern, "count": count}
                for pattern, count in comparison.common_patterns[:10]
            ],
        }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        logger.error(f"Failed to compare agents: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": str(e)}, indent=2),
            )
        ]
