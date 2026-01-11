"""Storage integration for behavior monitoring with historical tracking.

Enables persistent storage of behavior logs, metrics aggregation, and trend detection
for multi-agent safety monitoring based on hackathon research priorities.
"""

import json
import logging
from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from ..storage.manager import StorageManager
from .behavior_monitor import BehaviorLog

logger = logging.getLogger(__name__)


class BehaviorMetrics(BaseModel):
    """Aggregated behavior metrics for a time period."""

    period_start: datetime = Field(..., description="Start of metrics period")
    period_end: datetime = Field(..., description="End of metrics period")
    total_behaviors: int = Field(default=0, description="Total behaviors detected")
    by_category: dict[str, int] = Field(
        default_factory=dict, description="Count by behavior category"
    )
    by_severity: dict[str, int] = Field(default_factory=dict, description="Count by severity")
    by_pattern: dict[str, int] = Field(default_factory=dict, description="Count by pattern name")
    by_agent: dict[str, int] = Field(default_factory=dict, description="Count by agent ID")
    critical_count: int = Field(default=0, description="Critical behaviors")
    warning_count: int = Field(default=0, description="Warning behaviors")
    unique_agents: int = Field(default=0, description="Number of unique agents")
    most_common_pattern: str | None = Field(default=None, description="Most common pattern")
    most_active_agent: str | None = Field(default=None, description="Most active agent")


class BehaviorTrend(BaseModel):
    """Trend analysis for behavior patterns over time."""

    pattern_name: str = Field(..., description="Pattern being tracked")
    time_series: list[tuple[datetime, int]] = Field(
        default_factory=list, description="Time series data (timestamp, count)"
    )
    trend_direction: str = Field(
        default="stable", description="Trend direction (increasing, decreasing, stable)"
    )
    change_percentage: float = Field(default=0.0, description="Percentage change over period")
    average_per_day: float = Field(default=0.0, description="Average occurrences per day")


class BehaviorStorage:
    """Manages persistent storage of behavior logs and metrics.

    Storage structure:
    - s3://uer-behavior/logs/{date}/{agent_id}/{timestamp}.json - Individual logs
    - s3://uer-behavior/metrics/daily/{date}.json - Daily aggregated metrics
    - s3://uer-behavior/metrics/weekly/{week}.json - Weekly aggregated metrics
    - s3://uer-behavior/metrics/monthly/{month}.json - Monthly aggregated metrics
    - s3://uer-behavior/trends/{pattern_name}.json - Trend data per pattern
    """

    def __init__(self, storage: StorageManager | None = None):
        """Initialize behavior storage.

        Args:
            storage: Storage manager (creates new if None)
        """
        self.storage = storage or StorageManager()
        self.bucket = "uer-behavior"
        logger.info("BehaviorStorage initialized")

    async def store_log(self, log: BehaviorLog) -> str:
        """Store a single behavior log.

        Args:
            log: BehaviorLog to store

        Returns:
            URI where log was stored
        """
        if not self.storage.is_available():
            logger.warning("Storage not available, cannot store behavior log")
            return ""

        try:
            # Generate storage key: logs/{date}/{agent_id}/{timestamp}.json
            date_str = log.timestamp.strftime("%Y-%m-%d")
            timestamp_str = log.timestamp.strftime("%Y%m%d_%H%M%S_%f")
            key = f"logs/{date_str}/{log.agent_id}/{timestamp_str}.json"

            # Store log as JSON
            content = log.model_dump_json(indent=2)
            uri = f"s3://{self.bucket}/{key}"

            await self.storage.put(
                uri,
                content.encode("utf-8"),
                content_type="application/json",
                metadata={
                    "type": "behavior_log",
                    "agent_id": log.agent_id,
                    "behavior_type": log.behavior_type,
                    "severity": log.severity,
                    "timestamp": log.timestamp.isoformat(),
                },
            )

            logger.debug(f"Stored behavior log at {uri}")
            return uri

        except Exception as e:
            logger.error(f"Failed to store behavior log: {e}", exc_info=True)
            return ""

    async def store_logs_batch(self, logs: list[BehaviorLog]) -> list[str]:
        """Store multiple behavior logs in batch.

        Args:
            logs: List of BehaviorLog to store

        Returns:
            List of URIs where logs were stored
        """
        uris = []
        for log in logs:
            uri = await self.store_log(log)
            if uri:
                uris.append(uri)

        logger.info(f"Stored {len(uris)} behavior logs in batch")
        return uris

    async def get_logs_by_date(
        self, date: datetime, agent_id: str | None = None
    ) -> list[BehaviorLog]:
        """Retrieve behavior logs for a specific date.

        Args:
            date: Date to retrieve logs for
            agent_id: Optional agent ID to filter by

        Returns:
            List of BehaviorLog for the date
        """
        if not self.storage.is_available():
            logger.warning("Storage not available, cannot retrieve logs")
            return []

        try:
            date_str = date.strftime("%Y-%m-%d")
            prefix = f"logs/{date_str}/"
            if agent_id:
                prefix = f"logs/{date_str}/{agent_id}/"

            # List all log files for the date
            objects = await self.storage.list(f"s3://{self.bucket}/{prefix}")

            # Load and parse each log
            logs = []
            for obj_key in objects:
                try:
                    uri = f"s3://{self.bucket}/{obj_key}"
                    content, _ = await self.storage.get(uri)
                    log_data = json.loads(content.decode("utf-8"))
                    log = BehaviorLog.model_validate(log_data)
                    logs.append(log)
                except Exception as e:
                    logger.warning(f"Failed to parse log {obj_key}: {e}")

            logger.info(f"Retrieved {len(logs)} logs for {date_str}")
            return logs

        except Exception as e:
            logger.error(f"Failed to retrieve logs for {date}: {e}", exc_info=True)
            return []

    async def get_logs_by_range(
        self, start_date: datetime, end_date: datetime, agent_id: str | None = None
    ) -> list[BehaviorLog]:
        """Retrieve behavior logs for a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            agent_id: Optional agent ID to filter by

        Returns:
            List of BehaviorLog in the range
        """
        all_logs = []
        current_date = start_date

        while current_date <= end_date:
            logs = await self.get_logs_by_date(current_date, agent_id)
            all_logs.extend(logs)
            current_date += timedelta(days=1)

        logger.info(f"Retrieved {len(all_logs)} logs from {start_date.date()} to {end_date.date()}")
        return all_logs

    async def aggregate_metrics(
        self, logs: list[BehaviorLog], period_start: datetime, period_end: datetime
    ) -> BehaviorMetrics:
        """Aggregate behavior metrics from logs.

        Args:
            logs: List of BehaviorLog to aggregate
            period_start: Start of metrics period
            period_end: End of metrics period

        Returns:
            BehaviorMetrics with aggregated data
        """
        metrics = BehaviorMetrics(period_start=period_start, period_end=period_end)

        if not logs:
            return metrics

        # Count by category, severity, pattern, agent
        by_category: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_pattern: dict[str, int] = {}
        by_agent: dict[str, int] = {}

        for log in logs:
            # Category
            by_category[log.behavior_type] = by_category.get(log.behavior_type, 0) + 1

            # Severity
            by_severity[log.severity] = by_severity.get(log.severity, 0) + 1

            # Pattern
            if log.pattern_name:
                by_pattern[log.pattern_name] = by_pattern.get(log.pattern_name, 0) + 1

            # Agent
            by_agent[log.agent_id] = by_agent.get(log.agent_id, 0) + 1

        metrics.total_behaviors = len(logs)
        metrics.by_category = by_category
        metrics.by_severity = by_severity
        metrics.by_pattern = by_pattern
        metrics.by_agent = by_agent
        metrics.critical_count = by_severity.get("critical", 0)
        metrics.warning_count = by_severity.get("warning", 0)
        metrics.unique_agents = len(by_agent)

        # Find most common pattern and most active agent
        if by_pattern:
            metrics.most_common_pattern = max(by_pattern, key=by_pattern.get)
        if by_agent:
            metrics.most_active_agent = max(by_agent, key=by_agent.get)

        return metrics

    async def store_metrics(self, metrics: BehaviorMetrics, period_type: str = "daily") -> str:
        """Store aggregated metrics.

        Args:
            metrics: BehaviorMetrics to store
            period_type: Type of period (daily, weekly, monthly)

        Returns:
            URI where metrics were stored
        """
        if not self.storage.is_available():
            logger.warning("Storage not available, cannot store metrics")
            return ""

        try:
            # Generate storage key based on period type
            if period_type == "daily":
                date_str = metrics.period_start.strftime("%Y-%m-%d")
                key = f"metrics/daily/{date_str}.json"
            elif period_type == "weekly":
                week_str = metrics.period_start.strftime("%Y-W%W")
                key = f"metrics/weekly/{week_str}.json"
            elif period_type == "monthly":
                month_str = metrics.period_start.strftime("%Y-%m")
                key = f"metrics/monthly/{month_str}.json"
            else:
                raise ValueError(f"Invalid period_type: {period_type}")

            uri = f"s3://{self.bucket}/{key}"
            content = metrics.model_dump_json(indent=2)

            await self.storage.put(
                uri,
                content.encode("utf-8"),
                content_type="application/json",
                metadata={
                    "type": "behavior_metrics",
                    "period_type": period_type,
                    "period_start": metrics.period_start.isoformat(),
                    "period_end": metrics.period_end.isoformat(),
                },
            )

            logger.info(f"Stored {period_type} metrics at {uri}")
            return uri

        except Exception as e:
            logger.error(f"Failed to store metrics: {e}", exc_info=True)
            return ""

    async def get_metrics(
        self, date: datetime, period_type: str = "daily"
    ) -> BehaviorMetrics | None:
        """Retrieve aggregated metrics for a period.

        Args:
            date: Date within the period
            period_type: Type of period (daily, weekly, monthly)

        Returns:
            BehaviorMetrics if found, None otherwise
        """
        if not self.storage.is_available():
            logger.warning("Storage not available, cannot retrieve metrics")
            return None

        try:
            # Generate storage key
            if period_type == "daily":
                date_str = date.strftime("%Y-%m-%d")
                key = f"metrics/daily/{date_str}.json"
            elif period_type == "weekly":
                week_str = date.strftime("%Y-W%W")
                key = f"metrics/weekly/{week_str}.json"
            elif period_type == "monthly":
                month_str = date.strftime("%Y-%m")
                key = f"metrics/monthly/{month_str}.json"
            else:
                raise ValueError(f"Invalid period_type: {period_type}")

            uri = f"s3://{self.bucket}/{key}"
            content, _ = await self.storage.get(uri)
            metrics_data = json.loads(content.decode("utf-8"))
            metrics = BehaviorMetrics.model_validate(metrics_data)

            logger.debug(f"Retrieved {period_type} metrics from {uri}")
            return metrics

        except Exception as e:
            logger.debug(f"No metrics found for {date} ({period_type}): {e}")
            return None

    async def compute_trend(
        self, pattern_name: str, start_date: datetime, end_date: datetime
    ) -> BehaviorTrend:
        """Compute trend for a specific behavior pattern over time.

        Args:
            pattern_name: Pattern to analyze
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            BehaviorTrend with trend analysis
        """
        trend = BehaviorTrend(pattern_name=pattern_name)

        # Get daily metrics for the period
        current_date = start_date
        time_series: list[tuple[datetime, int]] = []

        while current_date <= end_date:
            metrics = await self.get_metrics(current_date, "daily")
            count = 0
            if metrics and metrics.by_pattern:
                count = metrics.by_pattern.get(pattern_name, 0)

            time_series.append((current_date, count))
            current_date += timedelta(days=1)

        trend.time_series = time_series

        # Calculate trend statistics
        if len(time_series) >= 2:
            counts = [count for _, count in time_series]
            total_days = len(time_series)

            # Average per day
            trend.average_per_day = sum(counts) / total_days

            # Trend direction (compare first half to second half)
            mid_point = total_days // 2
            first_half_avg = sum(counts[:mid_point]) / mid_point if mid_point > 0 else 0
            second_half_avg = sum(counts[mid_point:]) / (total_days - mid_point)

            if second_half_avg > first_half_avg * 1.1:  # 10% threshold
                trend.trend_direction = "increasing"
                if first_half_avg > 0:
                    trend.change_percentage = (
                        (second_half_avg - first_half_avg) / first_half_avg * 100
                    )
            elif second_half_avg < first_half_avg * 0.9:  # 10% threshold
                trend.trend_direction = "decreasing"
                if first_half_avg > 0:
                    trend.change_percentage = (
                        (second_half_avg - first_half_avg) / first_half_avg * 100
                    )
            else:
                trend.trend_direction = "stable"

        logger.info(
            f"Computed trend for {pattern_name}: {trend.trend_direction} "
            f"({trend.change_percentage:.1f}% change)"
        )
        return trend

    async def store_trend(self, trend: BehaviorTrend) -> str:
        """Store trend analysis.

        Args:
            trend: BehaviorTrend to store

        Returns:
            URI where trend was stored
        """
        if not self.storage.is_available():
            logger.warning("Storage not available, cannot store trend")
            return ""

        try:
            key = f"trends/{trend.pattern_name}.json"
            uri = f"s3://{self.bucket}/{key}"
            content = trend.model_dump_json(indent=2)

            await self.storage.put(
                uri,
                content.encode("utf-8"),
                content_type="application/json",
                metadata={
                    "type": "behavior_trend",
                    "pattern_name": trend.pattern_name,
                    "trend_direction": trend.trend_direction,
                },
            )

            logger.info(f"Stored trend for {trend.pattern_name} at {uri}")
            return uri

        except Exception as e:
            logger.error(f"Failed to store trend: {e}", exc_info=True)
            return ""

    async def get_all_trends(self) -> list[BehaviorTrend]:
        """Retrieve all stored trends.

        Returns:
            List of BehaviorTrend
        """
        if not self.storage.is_available():
            logger.warning("Storage not available, cannot retrieve trends")
            return []

        try:
            # List all trend files
            objects = await self.storage.list(f"s3://{self.bucket}/trends/")

            trends = []
            for obj_key in objects:
                try:
                    uri = f"s3://{self.bucket}/{obj_key}"
                    content, _ = await self.storage.get(uri)
                    trend_data = json.loads(content.decode("utf-8"))
                    trend = BehaviorTrend.model_validate(trend_data)
                    trends.append(trend)
                except Exception as e:
                    logger.warning(f"Failed to parse trend {obj_key}: {e}")

            logger.info(f"Retrieved {len(trends)} trends")
            return trends

        except Exception as e:
            logger.error(f"Failed to retrieve trends: {e}", exc_info=True)
            return []
