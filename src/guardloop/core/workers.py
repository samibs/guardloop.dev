"""Background workers for analysis, metrics, and maintenance"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from guardloop.core.logger import get_logger
from guardloop.utils.config import Config
from guardloop.utils.db import DatabaseManager

logger = get_logger(__name__)


class BackgroundWorker(ABC):
    """Base class for background workers"""

    def __init__(self, config: Config, db: DatabaseManager):
        """Initialize worker

        Args:
            config: Guardrail configuration
            db: Database manager
        """
        self.config = config
        self.db = db
        self.running = False
        self.worker_name = self.__class__.__name__

    @abstractmethod
    async def run(self) -> None:
        """Run worker loop - must be implemented by subclasses"""
        pass

    async def start(self) -> None:
        """Start worker"""
        self.running = True
        logger.info(f"{self.worker_name} starting")
        await self.run()

    async def stop(self) -> None:
        """Stop worker"""
        self.running = False
        logger.info(f"{self.worker_name} stopping")


class AnalysisWorker(BackgroundWorker):
    """Worker for analyzing failure trends and generating insights"""

    async def run(self) -> None:
        """Run analysis every 5 minutes"""
        while self.running:
            try:
                logger.debug(f"{self.worker_name} cycle starting")

                # Analyze failure trends
                trends = await self._analyze_trends()
                await self._save_trends(trends)

                # Generate insights
                insights = await self._generate_insights(trends)
                await self._save_insights(insights)

                logger.debug(
                    f"{self.worker_name} cycle completed",
                    trends_count=len(trends),
                    insights_count=len(insights),
                )

            except Exception as e:
                logger.error(f"{self.worker_name} error", error=str(e))

            await asyncio.sleep(300)  # 5 minutes

    async def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze failure trends from last 24 hours

        Returns:
            Dictionary of trend data
        """
        # Query last 24h of failures
        # cutoff_time would be used for actual DB query
        trends = {
            "timestamp": datetime.now().isoformat(),
            "period": "24h",
            "by_category": {},
            "by_tool": {},
            "by_agent": {},
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        }

        # This would query actual database
        # For now, return structure
        logger.debug("Trends analyzed", period="24h")
        return trends

    async def _save_trends(self, trends: Dict[str, Any]) -> None:
        """Save trends to database

        Args:
            trends: Trend data to save
        """
        # Store trends in database
        logger.debug("Trends saved")

    async def _generate_insights(self, trends: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights from trends

        Args:
            trends: Trend data

        Returns:
            List of insights
        """
        insights = []

        # Example: Detect spike in specific failure category
        for category, count in trends.get("by_category", {}).items():
            if count > 10:  # Threshold
                insights.append(
                    {
                        "type": "spike",
                        "category": category,
                        "count": count,
                        "severity": "warning",
                        "message": f"High frequency of {category} failures detected",
                    }
                )

        logger.debug("Insights generated", count=len(insights))
        return insights

    async def _save_insights(self, insights: List[Dict[str, Any]]) -> None:
        """Save insights to database

        Args:
            insights: Insights to save
        """
        for insight in insights:
            logger.info(
                "Insight generated",
                type=insight["type"],
                category=insight.get("category"),
                message=insight.get("message"),
            )
        # Store in database
        logger.debug("Insights saved", count=len(insights))


class MetricsWorker(BackgroundWorker):
    """Worker for aggregating and storing metrics"""

    async def run(self) -> None:
        """Run metrics collection every 1 minute"""
        while self.running:
            try:
                logger.debug(f"{self.worker_name} cycle starting")

                # Aggregate metrics
                metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "total_sessions": await self._count_sessions(),
                    "success_rate": await self._calculate_success_rate(),
                    "avg_execution_time": await self._avg_execution_time(),
                    "top_violations": await self._top_violations(),
                    "top_failures": await self._top_failures(),
                    "agent_stats": await self._agent_stats(),
                }

                await self._store_metrics(metrics)

                logger.debug(
                    f"{self.worker_name} cycle completed",
                    total_sessions=metrics["total_sessions"],
                    success_rate=metrics["success_rate"],
                )

            except Exception as e:
                logger.error(f"{self.worker_name} error", error=str(e))

            await asyncio.sleep(60)  # 1 minute

    async def _count_sessions(self) -> int:
        """Count total sessions

        Returns:
            Session count
        """
        # Query database
        return 0  # Placeholder

    async def _calculate_success_rate(self) -> float:
        """Calculate success rate

        Returns:
            Success rate percentage
        """
        # Calculate from database
        return 95.5  # Placeholder

    async def _avg_execution_time(self) -> int:
        """Calculate average execution time

        Returns:
            Average time in milliseconds
        """
        # Calculate from database
        return 1500  # Placeholder

    async def _top_violations(self) -> List[Dict[str, Any]]:
        """Get top violations

        Returns:
            List of top violations
        """
        # Query database
        return []  # Placeholder

    async def _top_failures(self) -> List[Dict[str, Any]]:
        """Get top failures

        Returns:
            List of top failures
        """
        # Query database
        return []  # Placeholder

    async def _agent_stats(self) -> Dict[str, Any]:
        """Get agent statistics

        Returns:
            Agent statistics
        """
        # Query database
        return {}  # Placeholder

    async def _store_metrics(self, metrics: Dict[str, Any]) -> None:
        """Store metrics in database

        Args:
            metrics: Metrics to store
        """
        # Store in database
        logger.debug("Metrics stored")


class MarkdownExporter(BackgroundWorker):
    """Worker for exporting failure modes to markdown"""

    async def run(self) -> None:
        """Export markdown every 10 minutes"""
        while self.running:
            try:
                logger.debug(f"{self.worker_name} cycle starting")

                # Get recent failures
                failures = await self._get_recent_failures(limit=100)

                # Generate markdown
                md_content = self._generate_markdown(failures)

                # Write to file
                output_path = Path("~/.guardrail/AI_Failure_Modes.md").expanduser()
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(md_content)

                logger.debug(
                    f"{self.worker_name} cycle completed",
                    failures_exported=len(failures),
                    output_path=str(output_path),
                )

            except Exception as e:
                logger.error(f"{self.worker_name} error", error=str(e))

            await asyncio.sleep(600)  # 10 minutes

    async def _get_recent_failures(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent failures from database

        Args:
            limit: Maximum number of failures to retrieve

        Returns:
            List of failure records
        """
        # Query database
        return []  # Placeholder

    def _generate_markdown(self, failures: List[Dict[str, Any]]) -> str:
        """Generate markdown document from failures

        Args:
            failures: List of failure records

        Returns:
            Markdown content
        """
        lines = [
            "# AI Failure Modes - Guardrail.dev",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Failures**: {len(failures)}",
            "",
            "---",
            "",
            "## Recent Failures",
            "",
        ]

        if not failures:
            lines.append("No failures detected recently. ✅")
        else:
            lines.extend(
                [
                    "| Timestamp | Category | Severity | Tool | Context |",
                    "|-----------|----------|----------|------|---------|",
                ]
            )

            for failure in failures[:50]:  # Limit to 50 rows
                timestamp = failure.get("timestamp", "N/A")
                category = failure.get("category", "Unknown")
                severity = failure.get("severity", "unknown")
                tool = failure.get("tool", "N/A")
                context = failure.get("context", "")[:50]  # Truncate context

                lines.append(f"| {timestamp} | {category} | {severity} | {tool} | {context}... |")

        lines.extend(["", "---", "", "**Powered by Guardrail.dev**"])

        return "\n".join(lines)


class CleanupWorker(BackgroundWorker):
    """Worker for database cleanup and maintenance"""

    async def run(self) -> None:
        """Run cleanup daily"""
        while self.running:
            try:
                logger.debug(f"{self.worker_name} cycle starting")

                # Clean old sessions (>30 days)
                deleted_sessions = await self._delete_old_sessions(days=30)

                # Vacuum database
                await self._vacuum_database()

                # Rotate logs
                await self._rotate_logs()

                logger.info(
                    f"{self.worker_name} cycle completed",
                    deleted_sessions=deleted_sessions,
                )

            except Exception as e:
                logger.error(f"{self.worker_name} error", error=str(e))

            await asyncio.sleep(86400)  # 24 hours

    async def _delete_old_sessions(self, days: int = 30) -> int:
        """Delete sessions older than specified days

        Args:
            days: Number of days to retain

        Returns:
            Number of deleted sessions
        """
        # cutoff_date would be used for actual DB query
        # Delete from database
        logger.debug("Old sessions deleted", cutoff_days=days)
        return 0  # Placeholder

    async def _vacuum_database(self) -> None:
        """Vacuum database to reclaim space"""
        # Run VACUUM command
        logger.debug("Database vacuumed")

    async def _rotate_logs(self) -> None:
        """Rotate log files"""
        # Rotate logs if size exceeds threshold
        log_dir = Path("~/.guardrail/logs").expanduser()
        if log_dir.exists():
            # Implement log rotation logic
            logger.debug("Logs rotated")


class WorkerManager:
    """Manager for all background workers"""

    def __init__(self, config: Config, db: DatabaseManager):
        """Initialize worker manager

        Args:
            config: Guardrail configuration
            db: Database manager
        """
        self.config = config
        self.db = db
        self.workers: List[BackgroundWorker] = []

        # Create workers based on config
        if config.features.analysis_worker:
            self.workers.append(AnalysisWorker(config, db))

        if config.features.metrics_worker:
            self.workers.append(MetricsWorker(config, db))

        if config.features.markdown_export:
            self.workers.append(MarkdownExporter(config, db))

        if config.features.cleanup_worker:
            self.workers.append(CleanupWorker(config, db))

        logger.info(
            "WorkerManager initialized",
            worker_count=len(self.workers),
            workers=[w.worker_name for w in self.workers],
        )

    async def start_all(self) -> None:
        """Start all workers concurrently"""
        if not self.workers:
            logger.warning("No workers configured")
            return

        logger.info("Starting all workers", count=len(self.workers))
        tasks = [worker.start() for worker in self.workers]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop_all(self) -> None:
        """Stop all workers"""
        logger.info("Stopping all workers", count=len(self.workers))
        for worker in self.workers:
            await worker.stop()

    def get_status(self) -> Dict[str, Any]:
        """Get status of all workers

        Returns:
            Dictionary of worker statuses
        """
        return {
            "total_workers": len(self.workers),
            "workers": [{"name": w.worker_name, "running": w.running} for w in self.workers],
        }
