"""Behavior analysis dashboard with statistics, reporting, and visualization.

Provides comprehensive analysis tools for multi-agent safety monitoring based on
hackathon research priorities. Aggregates behavior statistics, generates reports,
and creates visualizations for pattern analysis across agents.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from .behavior_storage import BehaviorStorage

logger = logging.getLogger(__name__)


class AgentProfile(BaseModel):
    """Profile of an agent's behavior patterns."""

    agent_id: str = Field(..., description="Agent identifier")
    total_behaviors: int = Field(default=0, description="Total behaviors detected")
    by_category: dict[str, int] = Field(default_factory=dict, description="Behaviors by category")
    by_severity: dict[str, int] = Field(default_factory=dict, description="Behaviors by severity")
    critical_count: int = Field(default=0, description="Critical behaviors")
    warning_count: int = Field(default=0, description="Warning behaviors")
    most_common_pattern: str | None = Field(default=None, description="Most common pattern")
    risk_score: float = Field(default=0.0, description="Risk score (0-100)")
    first_seen: datetime | None = Field(default=None, description="First behavior timestamp")
    last_seen: datetime | None = Field(default=None, description="Last behavior timestamp")


class ComparisonReport(BaseModel):
    """Comparison report between multiple agents."""

    agents: list[str] = Field(default_factory=list, description="Agent IDs compared")
    period_start: datetime = Field(..., description="Start of comparison period")
    period_end: datetime = Field(..., description="End of comparison period")
    safest_agent: str | None = Field(default=None, description="Agent with lowest risk score")
    riskiest_agent: str | None = Field(default=None, description="Agent with highest risk score")
    total_behaviors: int = Field(default=0, description="Total behaviors across all agents")
    critical_behaviors: int = Field(default=0, description="Total critical behaviors")
    common_patterns: list[tuple[str, int]] = Field(
        default_factory=list, description="Most common patterns (pattern, count)"
    )
    category_distribution: dict[str, int] = Field(
        default_factory=dict, description="Distribution by category"
    )


class SafetyReport(BaseModel):
    """Comprehensive safety report for a time period."""

    period_start: datetime = Field(..., description="Start of report period")
    period_end: datetime = Field(..., description="End of report period")
    total_agents: int = Field(default=0, description="Number of unique agents")
    total_behaviors: int = Field(default=0, description="Total behaviors detected")
    critical_count: int = Field(default=0, description="Critical behaviors")
    warning_count: int = Field(default=0, description="Warning behaviors")
    info_count: int = Field(default=0, description="Info behaviors")
    by_category: dict[str, int] = Field(default_factory=dict, description="Behaviors by category")
    top_patterns: list[tuple[str, int]] = Field(
        default_factory=list, description="Top 10 patterns (pattern, count)"
    )
    high_risk_agents: list[str] = Field(
        default_factory=list, description="Agents with risk score > 70"
    )
    trends: dict[str, str] = Field(default_factory=dict, description="Trend direction by category")
    recommendations: list[str] = Field(default_factory=list, description="Safety recommendations")


class BehaviorAnalyzer:
    """Analyzes behavior patterns and generates reports.

    Provides comprehensive analysis capabilities:
    - Agent profiling and risk scoring
    - Multi-agent comparisons
    - Safety reports with recommendations
    - Trend analysis and visualization
    - Pattern aggregation across agents
    """

    def __init__(self, storage: BehaviorStorage):
        """Initialize behavior analyzer.

        Args:
            storage: BehaviorStorage for accessing historical data
        """
        self.storage = storage
        logger.info("BehaviorAnalyzer initialized")

    async def create_agent_profile(
        self, agent_id: str, start_date: datetime, end_date: datetime
    ) -> AgentProfile:
        """Create detailed profile for an agent.

        Args:
            agent_id: Agent identifier
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            AgentProfile with behavior statistics and risk score
        """
        # Get logs for agent in date range
        logs = await self.storage.get_logs_by_range(start_date, end_date, agent_id)

        profile = AgentProfile(agent_id=agent_id)

        if not logs:
            return profile

        # Aggregate statistics
        by_category: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_pattern: dict[str, int] = {}

        for log in logs:
            by_category[log.behavior_type] = by_category.get(log.behavior_type, 0) + 1
            by_severity[log.severity] = by_severity.get(log.severity, 0) + 1
            if log.pattern_name:
                by_pattern[log.pattern_name] = by_pattern.get(log.pattern_name, 0) + 1

        profile.total_behaviors = len(logs)
        profile.by_category = by_category
        profile.by_severity = by_severity
        profile.critical_count = by_severity.get("critical", 0)
        profile.warning_count = by_severity.get("warning", 0)

        # Find most common pattern
        if by_pattern:
            profile.most_common_pattern = max(by_pattern, key=by_pattern.get)

        # Calculate risk score (0-100)
        # Critical behaviors: 10 points each
        # Warning behaviors: 5 points each
        # Destructive category: 2x multiplier
        # Deception category: 2x multiplier
        risk_score = 0.0
        risk_score += profile.critical_count * 10
        risk_score += profile.warning_count * 5

        # Category multipliers
        if "destructive" in by_category:
            risk_score += by_category["destructive"] * 5
        if "deception" in by_category:
            risk_score += by_category["deception"] * 5

        # Cap at 100
        profile.risk_score = min(risk_score, 100.0)

        # Timestamps
        profile.first_seen = min(log.timestamp for log in logs)
        profile.last_seen = max(log.timestamp for log in logs)

        logger.info(
            f"Created profile for {agent_id}: {profile.total_behaviors} behaviors, "
            f"risk score {profile.risk_score:.1f}"
        )
        return profile

    async def compare_agents(
        self, agent_ids: list[str], start_date: datetime, end_date: datetime
    ) -> ComparisonReport:
        """Compare behavior patterns across multiple agents.

        Args:
            agent_ids: List of agent IDs to compare
            start_date: Start of comparison period
            end_date: End of comparison period

        Returns:
            ComparisonReport with comparative analysis
        """
        report = ComparisonReport(agents=agent_ids, period_start=start_date, period_end=end_date)

        # Create profiles for all agents
        profiles: dict[str, AgentProfile] = {}
        for agent_id in agent_ids:
            profile = await self.create_agent_profile(agent_id, start_date, end_date)
            profiles[agent_id] = profile

        # Find safest and riskiest
        if profiles:
            safest = min(profiles.items(), key=lambda x: x[1].risk_score)
            riskiest = max(profiles.items(), key=lambda x: x[1].risk_score)
            report.safest_agent = safest[0]
            report.riskiest_agent = riskiest[0]

        # Aggregate totals
        all_category_counts: dict[str, int] = {}
        all_pattern_counts: dict[str, int] = {}
        total_critical = 0

        for profile in profiles.values():
            report.total_behaviors += profile.total_behaviors
            total_critical += profile.critical_count

            for category, count in profile.by_category.items():
                all_category_counts[category] = all_category_counts.get(category, 0) + count

            # Get patterns from logs
            logs = await self.storage.get_logs_by_range(start_date, end_date, profile.agent_id)
            for log in logs:
                if log.pattern_name:
                    all_pattern_counts[log.pattern_name] = (
                        all_pattern_counts.get(log.pattern_name, 0) + 1
                    )

        report.critical_behaviors = total_critical
        report.category_distribution = all_category_counts

        # Top 10 common patterns
        if all_pattern_counts:
            sorted_patterns = sorted(all_pattern_counts.items(), key=lambda x: x[1], reverse=True)
            report.common_patterns = sorted_patterns[:10]

        logger.info(
            f"Compared {len(agent_ids)} agents: safest={report.safest_agent}, "
            f"riskiest={report.riskiest_agent}"
        )
        return report

    async def generate_safety_report(
        self, start_date: datetime, end_date: datetime
    ) -> SafetyReport:
        """Generate comprehensive safety report for a period.

        Args:
            start_date: Start of report period
            end_date: End of report period

        Returns:
            SafetyReport with analysis and recommendations
        """
        report = SafetyReport(period_start=start_date, period_end=end_date)

        # Get all logs for period
        logs = await self.storage.get_logs_by_range(start_date, end_date)

        if not logs:
            report.recommendations.append("No behavior data available for this period.")
            return report

        # Aggregate statistics
        unique_agents = set()
        by_category: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_pattern: dict[str, int] = {}
        agent_risk_scores: dict[str, float] = {}

        for log in logs:
            unique_agents.add(log.agent_id)
            by_category[log.behavior_type] = by_category.get(log.behavior_type, 0) + 1
            by_severity[log.severity] = by_severity.get(log.severity, 0) + 1
            if log.pattern_name:
                by_pattern[log.pattern_name] = by_pattern.get(log.pattern_name, 0) + 1

        report.total_agents = len(unique_agents)
        report.total_behaviors = len(logs)
        report.critical_count = by_severity.get("critical", 0)
        report.warning_count = by_severity.get("warning", 0)
        report.info_count = by_severity.get("info", 0)
        report.by_category = by_category

        # Top 10 patterns
        if by_pattern:
            sorted_patterns = sorted(by_pattern.items(), key=lambda x: x[1], reverse=True)
            report.top_patterns = sorted_patterns[:10]

        # Calculate risk scores for all agents
        for agent_id in unique_agents:
            profile = await self.create_agent_profile(agent_id, start_date, end_date)
            agent_risk_scores[agent_id] = profile.risk_score
            if profile.risk_score > 70:
                report.high_risk_agents.append(agent_id)

        # Analyze trends
        for category in by_category:
            # Get trend for this category (simplified - check last 7 days)
            trend_start = end_date - timedelta(days=7)
            if trend_start >= start_date:
                # Compare first half vs second half
                mid_date = start_date + (end_date - start_date) / 2
                first_half = await self.storage.get_logs_by_range(start_date, mid_date)
                second_half = await self.storage.get_logs_by_range(mid_date, end_date)

                first_count = sum(1 for log in first_half if log.behavior_type == category)
                second_count = sum(1 for log in second_half if log.behavior_type == category)

                if second_count > first_count * 1.1:
                    report.trends[category] = "increasing"
                elif second_count < first_count * 0.9:
                    report.trends[category] = "decreasing"
                else:
                    report.trends[category] = "stable"

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report, agent_risk_scores)

        logger.info(
            f"Generated safety report: {report.total_behaviors} behaviors, "
            f"{report.critical_count} critical, {len(report.high_risk_agents)} high-risk agents"
        )
        return report

    def _generate_recommendations(
        self, report: SafetyReport, agent_risk_scores: dict[str, float]
    ) -> list[str]:
        """Generate safety recommendations based on report data.

        Args:
            report: SafetyReport with statistics
            agent_risk_scores: Risk scores by agent

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Critical behavior threshold
        if report.critical_count > 10:
            recommendations.append(
                f"⚠️ HIGH ALERT: {report.critical_count} critical behaviors detected. "
                "Immediate review recommended."
            )
        elif report.critical_count > 0:
            recommendations.append(
                f"⚠️ {report.critical_count} critical behaviors detected. Review recommended."
            )

        # High-risk agents
        if report.high_risk_agents:
            recommendations.append(
                f"🔴 {len(report.high_risk_agents)} high-risk agents identified: "
                f"{', '.join(report.high_risk_agents[:5])}. Consider additional monitoring."
            )

        # Destructive behaviors
        if "destructive" in report.by_category and report.by_category["destructive"] > 5:
            recommendations.append(
                f"⚠️ {report.by_category['destructive']} destructive behaviors detected. "
                "Review security measures and access controls."
            )

        # Deception patterns
        if "deception" in report.by_category and report.by_category["deception"] > 0:
            recommendations.append(
                f"🔍 {report.by_category['deception']} deception behaviors detected. "
                "Implement unfaithful reasoning detection (Park 2024)."
            )

        # Sandbagging
        if "sandbagging" in report.by_category and report.by_category["sandbagging"] > 3:
            recommendations.append(
                f"📉 {report.by_category['sandbagging']} sandbagging behaviors detected. "
                "Apply multi-method detection (van der Weij 2024)."
            )

        # Sycophancy
        if "sycophancy" in report.by_category and report.by_category["sycophancy"] > 5:
            recommendations.append(
                f"🤝 {report.by_category['sycophancy']} sycophancy behaviors detected. "
                "Modify preference data collection (Sharma 2024)."
            )

        # Increasing trends
        increasing_categories = [
            cat for cat, trend in report.trends.items() if trend == "increasing"
        ]
        if increasing_categories:
            recommendations.append(
                f"📈 Increasing trends detected in: {', '.join(increasing_categories)}. "
                "Monitor closely for escalation."
            )

        # Overall assessment
        if report.critical_count == 0 and report.warning_count < 10:
            recommendations.append(
                "✅ Overall safety metrics are within acceptable ranges. "
                "Continue routine monitoring."
            )

        # No data
        if report.total_behaviors == 0:
            recommendations.append("ℹ️ No behavior data available. Ensure monitoring is active.")

        return recommendations

    async def create_visualization_data(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Create data structure for visualization.

        Args:
            start_date: Start of visualization period
            end_date: End of visualization period

        Returns:
            Dictionary with visualization data (time series, distributions, etc.)
        """
        viz_data: dict[str, Any] = {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "time_series": {},
            "category_distribution": {},
            "severity_distribution": {},
            "agent_comparison": {},
            "pattern_heatmap": {},
        }

        # Get all logs
        logs = await self.storage.get_logs_by_range(start_date, end_date)

        if not logs:
            return viz_data

        # Time series data (daily counts)
        daily_counts: dict[str, dict[str, int]] = {}
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            daily_logs = [log for log in logs if log.timestamp.date() == current_date.date()]

            daily_counts[date_str] = {
                "total": len(daily_logs),
                "critical": sum(1 for log in daily_logs if log.severity == "critical"),
                "warning": sum(1 for log in daily_logs if log.severity == "warning"),
                "info": sum(1 for log in daily_logs if log.severity == "info"),
            }

            current_date += timedelta(days=1)

        viz_data["time_series"] = daily_counts

        # Category distribution
        category_counts: dict[str, int] = {}
        for log in logs:
            category_counts[log.behavior_type] = category_counts.get(log.behavior_type, 0) + 1
        viz_data["category_distribution"] = category_counts

        # Severity distribution
        severity_counts: dict[str, int] = {}
        for log in logs:
            severity_counts[log.severity] = severity_counts.get(log.severity, 0) + 1
        viz_data["severity_distribution"] = severity_counts

        # Agent comparison (top 10 agents by behavior count)
        agent_counts: dict[str, int] = {}
        for log in logs:
            agent_counts[log.agent_id] = agent_counts.get(log.agent_id, 0) + 1

        sorted_agents = sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)
        viz_data["agent_comparison"] = dict(sorted_agents[:10])

        # Pattern heatmap (pattern x day)
        pattern_by_day: dict[str, dict[str, int]] = {}
        for log in logs:
            if log.pattern_name:
                date_str = log.timestamp.strftime("%Y-%m-%d")
                if log.pattern_name not in pattern_by_day:
                    pattern_by_day[log.pattern_name] = {}
                pattern_by_day[log.pattern_name][date_str] = (
                    pattern_by_day[log.pattern_name].get(date_str, 0) + 1
                )

        viz_data["pattern_heatmap"] = pattern_by_day

        logger.info(f"Created visualization data for {len(logs)} behaviors")
        return viz_data

    async def export_report_markdown(self, report: SafetyReport) -> str:
        """Export safety report as Markdown.

        Args:
            report: SafetyReport to export

        Returns:
            Markdown-formatted report
        """
        md = f"""# Multi-Agent Safety Report

**Period:** {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}

## Executive Summary

- **Total Agents:** {report.total_agents}
- **Total Behaviors:** {report.total_behaviors}
- **Critical Behaviors:** {report.critical_count} 🔴
- **Warning Behaviors:** {report.warning_count} ⚠️
- **Info Behaviors:** {report.info_count} ℹ️

## Behavior Categories

"""
        for category, count in sorted(report.by_category.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / report.total_behaviors * 100) if report.total_behaviors > 0 else 0
            md += f"- **{category.title()}:** {count} ({percentage:.1f}%)\n"

        md += "\n## Top Patterns\n\n"
        for i, (pattern, count) in enumerate(report.top_patterns[:10], 1):
            md += f"{i}. **{pattern}:** {count} occurrences\n"

        if report.high_risk_agents:
            md += f"\n## High-Risk Agents ({len(report.high_risk_agents)})\n\n"
            for agent in report.high_risk_agents[:10]:
                md += f"- `{agent}`\n"

        if report.trends:
            md += "\n## Trends\n\n"
            for category, trend in report.trends.items():
                emoji = "📈" if trend == "increasing" else "📉" if trend == "decreasing" else "➡️"
                md += f"- **{category.title()}:** {emoji} {trend}\n"

        md += "\n## Recommendations\n\n"
        for i, rec in enumerate(report.recommendations, 1):
            md += f"{i}. {rec}\n"

        md += f"\n---\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

        return md

    async def export_report_json(self, report: SafetyReport) -> str:
        """Export safety report as JSON.

        Args:
            report: SafetyReport to export

        Returns:
            JSON-formatted report
        """
        return report.model_dump_json(indent=2)
