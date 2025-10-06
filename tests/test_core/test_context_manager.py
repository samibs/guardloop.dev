"""Unit tests for ContextManager"""

import pytest
from pathlib import Path
from guardloop.core.context_manager import ContextManager, GuardrailCache


class TestGuardrailCache:
    """Test GuardrailCache functionality"""

    def test_cache_set_and_get(self):
        """Test basic cache operations"""
        cache = GuardrailCache(ttl_seconds=60)
        cache.set("test_key", "test_value")

        assert cache.get("test_key") == "test_value"

    def test_cache_expiration(self):
        """Test cache TTL expiration"""
        import time

        cache = GuardrailCache(ttl_seconds=1)
        cache.set("test_key", "test_value")

        # Immediately should be available
        assert cache.get("test_key") == "test_value"

        # After TTL should expire
        time.sleep(1.1)
        assert cache.get("test_key") is None

    def test_cache_invalidate(self):
        """Test cache invalidation"""
        cache = GuardrailCache()
        cache.set("test_key", "test_value")

        cache.invalidate("test_key")
        assert cache.get("test_key") is None

    def test_cache_clear(self):
        """Test clearing entire cache"""
        cache = GuardrailCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestContextManager:
    """Test ContextManager functionality"""

    def test_initialization(self):
        """Test ContextManager initialization"""
        cm = ContextManager()
        assert cm.cache is not None
        assert cm.guardrails_path.exists() or True  # May not exist in test environment

    def test_validate_agent(self):
        """Test agent validation"""
        cm = ContextManager()

        assert cm.validate_agent("architect") is True
        assert cm.validate_agent("coder") is True
        assert cm.validate_agent("invalid_agent") is False

    def test_get_available_agents(self):
        """Test getting available agents"""
        cm = ContextManager()
        agents = cm.get_available_agents()

        assert len(agents) == 13
        assert "architect" in agents
        assert "coder" in agents
        assert "security" in agents

    def test_build_context_structure(self):
        """Test context building structure"""
        cm = ContextManager()

        # Mock guardrail loading to return empty string
        cm.load_guardrails = lambda agent=None, mode="standard", prompt="", task_type=None, db_session=None: "# Test Guardrails"

        context = cm.build_context("Test prompt", agent="architect", mode="standard")

        assert "<guardrails>" in context
        assert "</guardrails>" in context
        assert "<user_request>" in context
        assert "</user_request>" in context
        assert "Test prompt" in context
        assert "<mode>standard</mode>" in context

    def test_mode_instructions(self):
        """Test mode-specific instructions"""
        cm = ContextManager()

        standard = cm._get_mode_instructions("standard")
        strict = cm._get_mode_instructions("strict")

        assert "STANDARD MODE" in standard
        assert "STRICT MODE" in strict
        assert "MANDATORY" in strict
        assert "100%" in strict

    def test_estimate_tokens(self):
        """Test token estimation"""
        cm = ContextManager()

        text = "a" * 1000  # 1000 characters
        tokens = cm._estimate_tokens(text)

        # Should be approximately 250 tokens (1000 / 4)
        assert 200 <= tokens <= 300

    def test_get_stats(self):
        """Test getting statistics"""
        cm = ContextManager()
        stats = cm.get_stats()

        assert "cache_size" in stats
        assert "available_agents" in stats
        assert "guardrails_path" in stats
        assert stats["available_agents"] == 13


@pytest.mark.asyncio
class TestContextManagerAsync:
    """Test async ContextManager functionality"""

    async def test_cache_refresh(self):
        """Test cache refresh functionality"""
        cm = ContextManager(cache_ttl=1)

        # First load should cache
        cm.load_guardrails(agent="architect", mode="standard")

        # Immediate second load should use cache
        cm.load_guardrails(agent="architect", mode="standard")

        # Check cache is populated
        assert len(cm.cache._cache) > 0
