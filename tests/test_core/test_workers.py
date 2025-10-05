"""Unit tests for background workers"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
from datetime import datetime

from guardloop.core.workers import (
    BackgroundWorker,
    AnalysisWorker,
    MetricsWorker,
    MarkdownExporter,
    CleanupWorker,
    WorkerManager,
)
from guardloop.utils.config import Config


class TestBackgroundWorker:
    """Test BackgroundWorker base class"""

    class TestWorker(BackgroundWorker):
        """Test worker implementation"""

        async def run(self):
            """Test run method"""
            while self.running:
                await asyncio.sleep(0.1)

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return Config()

    @pytest.fixture
    def db(self):
        """Create mock database"""
        return MagicMock()

    @pytest.fixture
    def worker(self, config, db):
        """Create test worker"""
        return self.TestWorker(config, db)

    def test_initialization(self, worker, config, db):
        """Test worker initialization"""
        assert worker.config == config
        assert worker.db == db
        assert worker.running is False
        assert worker.worker_name == "TestWorker"

    @pytest.mark.asyncio
    async def test_start_stop(self, worker):
        """Test starting and stopping worker"""
        # Start worker
        task = asyncio.create_task(worker.start())

        # Give it time to start
        await asyncio.sleep(0.05)
        assert worker.running is True

        # Stop worker
        await worker.stop()
        assert worker.running is False

        # Wait for task to complete
        await asyncio.sleep(0.15)
        task.cancel()


class TestAnalysisWorker:
    """Test AnalysisWorker"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return Config()

    @pytest.fixture
    def db(self):
        """Create mock database"""
        return MagicMock()

    @pytest.fixture
    def worker(self, config, db):
        """Create analysis worker"""
        return AnalysisWorker(config, db)

    def test_initialization(self, worker):
        """Test worker initialization"""
        assert worker.worker_name == "AnalysisWorker"

    @pytest.mark.asyncio
    async def test_analyze_trends(self, worker):
        """Test trend analysis"""
        trends = await worker._analyze_trends()

        assert "timestamp" in trends
        assert "period" in trends
        assert "by_category" in trends
        assert "by_tool" in trends
        assert "by_agent" in trends
        assert "by_severity" in trends
        assert trends["period"] == "24h"

    @pytest.mark.asyncio
    async def test_generate_insights(self, worker):
        """Test insight generation"""
        trends = {
            "by_category": {
                "JWT/Auth": 15,  # Above threshold
                "Type Errors": 5,  # Below threshold
            }
        }

        insights = await worker._generate_insights(trends)

        # Should generate insight for JWT/Auth
        assert len(insights) > 0
        jwt_insight = next(
            (i for i in insights if i.get("category") == "JWT/Auth"), None
        )
        assert jwt_insight is not None
        assert jwt_insight["type"] == "spike"
        assert jwt_insight["count"] == 15

    @pytest.mark.asyncio
    async def test_save_trends(self, worker):
        """Test saving trends"""
        trends = {"test": "data"}
        await worker._save_trends(trends)
        # Should complete without error

    @pytest.mark.asyncio
    async def test_save_insights(self, worker):
        """Test saving insights"""
        insights = [{"type": "test", "message": "Test insight"}]
        await worker._save_insights(insights)
        # Should complete without error


class TestMetricsWorker:
    """Test MetricsWorker"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return Config()

    @pytest.fixture
    def db(self):
        """Create mock database"""
        return MagicMock()

    @pytest.fixture
    def worker(self, config, db):
        """Create metrics worker"""
        return MetricsWorker(config, db)

    def test_initialization(self, worker):
        """Test worker initialization"""
        assert worker.worker_name == "MetricsWorker"

    @pytest.mark.asyncio
    async def test_count_sessions(self, worker):
        """Test session counting"""
        count = await worker._count_sessions()
        assert isinstance(count, int)

    @pytest.mark.asyncio
    async def test_calculate_success_rate(self, worker):
        """Test success rate calculation"""
        rate = await worker._calculate_success_rate()
        assert isinstance(rate, float)
        assert 0 <= rate <= 100

    @pytest.mark.asyncio
    async def test_avg_execution_time(self, worker):
        """Test average execution time calculation"""
        avg_time = await worker._avg_execution_time()
        assert isinstance(avg_time, int)

    @pytest.mark.asyncio
    async def test_top_violations(self, worker):
        """Test getting top violations"""
        violations = await worker._top_violations()
        assert isinstance(violations, list)

    @pytest.mark.asyncio
    async def test_top_failures(self, worker):
        """Test getting top failures"""
        failures = await worker._top_failures()
        assert isinstance(failures, list)

    @pytest.mark.asyncio
    async def test_agent_stats(self, worker):
        """Test getting agent statistics"""
        stats = await worker._agent_stats()
        assert isinstance(stats, dict)

    @pytest.mark.asyncio
    async def test_store_metrics(self, worker):
        """Test storing metrics"""
        metrics = {
            "total_sessions": 100,
            "success_rate": 95.5,
        }
        await worker._store_metrics(metrics)
        # Should complete without error


class TestMarkdownExporter:
    """Test MarkdownExporter"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return Config()

    @pytest.fixture
    def db(self):
        """Create mock database"""
        return MagicMock()

    @pytest.fixture
    def worker(self, config, db):
        """Create markdown exporter"""
        return MarkdownExporter(config, db)

    def test_initialization(self, worker):
        """Test worker initialization"""
        assert worker.worker_name == "MarkdownExporter"

    @pytest.mark.asyncio
    async def test_get_recent_failures(self, worker):
        """Test getting recent failures"""
        failures = await worker._get_recent_failures(limit=50)
        assert isinstance(failures, list)

    def test_generate_markdown_empty(self, worker):
        """Test generating markdown with no failures"""
        md = worker._generate_markdown([])

        assert "AI Failure Modes" in md
        assert "No failures detected" in md
        assert "✅" in md

    def test_generate_markdown_with_failures(self, worker):
        """Test generating markdown with failures"""
        failures = [
            {
                "timestamp": "2025-10-04 10:00:00",
                "category": "JWT/Auth",
                "severity": "high",
                "tool": "claude",
                "context": "Token expired during authentication process",
            },
            {
                "timestamp": "2025-10-04 10:05:00",
                "category": "Type Errors",
                "severity": "medium",
                "tool": "gemini",
                "context": "Cannot read property of undefined",
            },
        ]

        md = worker._generate_markdown(failures)

        assert "AI Failure Modes" in md
        assert "**Total Failures**: 2" in md
        assert "JWT/Auth" in md
        assert "Type Errors" in md
        assert "| Timestamp | Category | Severity | Tool | Context |" in md

    def test_generate_markdown_truncates_context(self, worker):
        """Test that long context is truncated"""
        failures = [
            {
                "timestamp": "2025-10-04 10:00:00",
                "category": "Test",
                "severity": "low",
                "tool": "claude",
                "context": "A" * 100,  # 100 character context
            }
        ]

        md = worker._generate_markdown(failures)

        # Should truncate to 50 chars
        assert "A" * 50 in md
        assert "A" * 51 not in md


class TestCleanupWorker:
    """Test CleanupWorker"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return Config()

    @pytest.fixture
    def db(self):
        """Create mock database"""
        return MagicMock()

    @pytest.fixture
    def worker(self, config, db):
        """Create cleanup worker"""
        return CleanupWorker(config, db)

    def test_initialization(self, worker):
        """Test worker initialization"""
        assert worker.worker_name == "CleanupWorker"

    @pytest.mark.asyncio
    async def test_delete_old_sessions(self, worker):
        """Test deleting old sessions"""
        deleted = await worker._delete_old_sessions(days=30)
        assert isinstance(deleted, int)
        assert deleted >= 0

    @pytest.mark.asyncio
    async def test_vacuum_database(self, worker):
        """Test database vacuum"""
        await worker._vacuum_database()
        # Should complete without error

    @pytest.mark.asyncio
    async def test_rotate_logs(self, worker):
        """Test log rotation"""
        await worker._rotate_logs()
        # Should complete without error


class TestWorkerManager:
    """Test WorkerManager"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return Config()

    @pytest.fixture
    def db(self):
        """Create mock database"""
        return MagicMock()

    @pytest.fixture
    def manager(self, config, db):
        """Create worker manager"""
        return WorkerManager(config, db)

    def test_initialization(self, manager, config):
        """Test manager initialization"""
        assert manager.config == config
        # Should create workers based on config
        assert len(manager.workers) > 0

    def test_initialization_with_all_workers(self, config, db):
        """Test initialization with all workers enabled"""
        config.features.analysis_worker = True
        config.features.metrics_worker = True
        config.features.markdown_export = True
        config.features.cleanup_worker = True

        manager = WorkerManager(config, db)

        assert len(manager.workers) == 4
        worker_names = [w.worker_name for w in manager.workers]
        assert "AnalysisWorker" in worker_names
        assert "MetricsWorker" in worker_names
        assert "MarkdownExporter" in worker_names
        assert "CleanupWorker" in worker_names

    def test_initialization_with_no_workers(self, db):
        """Test initialization with all workers disabled"""
        config = Config()
        config.features.analysis_worker = False
        config.features.metrics_worker = False
        config.features.markdown_export = False
        config.features.cleanup_worker = False

        manager = WorkerManager(config, db)

        assert len(manager.workers) == 0

    @pytest.mark.asyncio
    async def test_start_all_no_workers(self, db):
        """Test starting with no workers"""
        config = Config()
        config.features.analysis_worker = False
        config.features.metrics_worker = False
        config.features.markdown_export = False
        config.features.cleanup_worker = False

        manager = WorkerManager(config, db)
        await manager.start_all()
        # Should complete without error

    @pytest.mark.asyncio
    async def test_stop_all(self, manager):
        """Test stopping all workers"""
        # Mock workers
        for worker in manager.workers:
            worker.stop = AsyncMock()

        await manager.stop_all()

        # All workers should be stopped
        for worker in manager.workers:
            worker.stop.assert_called_once()

    def test_get_status(self, manager):
        """Test getting manager status"""
        status = manager.get_status()

        assert "total_workers" in status
        assert "workers" in status
        assert isinstance(status["workers"], list)
        assert status["total_workers"] == len(manager.workers)

        if manager.workers:
            first_worker_status = status["workers"][0]
            assert "name" in first_worker_status
            assert "running" in first_worker_status
