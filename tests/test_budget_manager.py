"""Tests for ContextBudgetManager"""

import pytest
from guardloop.core.budget_manager import ContextBudgetManager


class TestBudgetCalculation:
    """Test budget calculation logic"""

    @pytest.fixture
    def manager(self):
        """Create budget manager instance"""
        return ContextBudgetManager()

    def test_init(self, manager):
        """Test manager initialization"""
        assert manager is not None
        assert len(manager.MODEL_BUDGETS) > 0
        assert len(manager.COMPLEXITY_MULTIPLIERS) == 4
        assert len(manager.ALLOCATION_RATIOS) == 4

    def test_get_budget_claude_opus(self, manager):
        """Test budget calculation for Claude Opus"""
        budget = manager.get_budget("claude-opus-4", "simple")
        assert budget == 3000  # 10000 * 0.3

        budget = manager.get_budget("claude-opus-4", "medium")
        assert budget == 6000  # 10000 * 0.6

        budget = manager.get_budget("claude-opus-4", "complex")
        assert budget == 9000  # 10000 * 0.9

        budget = manager.get_budget("claude-opus-4", "critical")
        assert budget == 10000  # 10000 * 1.0

    def test_get_budget_claude_sonnet(self, manager):
        """Test budget calculation for Claude Sonnet"""
        budget = manager.get_budget("claude-sonnet-4", "simple")
        assert budget == 1800  # 6000 * 0.3

        budget = manager.get_budget("claude-sonnet-4", "medium")
        assert budget == 3600  # 6000 * 0.6

        budget = manager.get_budget("claude-sonnet-4", "complex")
        assert budget == 5400  # 6000 * 0.9

    def test_get_budget_gpt4(self, manager):
        """Test budget calculation for GPT-4"""
        budget = manager.get_budget("gpt-4", "simple")
        assert budget == 1200  # 4000 * 0.3

        budget = manager.get_budget("gpt-4", "critical")
        assert budget == 4000  # 4000 * 1.0

    def test_get_budget_unknown_model(self, manager):
        """Test budget calculation for unknown model uses default"""
        budget = manager.get_budget("unknown-model", "medium")
        assert budget == 3000  # 5000 (default) * 0.6

    def test_get_budget_unknown_complexity(self, manager):
        """Test unknown complexity uses medium (0.6) multiplier"""
        budget = manager.get_budget("claude-sonnet-4", "unknown")
        assert budget == 3600  # 6000 * 0.6 (default)


class TestBudgetAllocation:
    """Test budget allocation across categories"""

    @pytest.fixture
    def manager(self):
        """Create budget manager instance"""
        return ContextBudgetManager()

    def test_allocate_budget_basic(self, manager):
        """Test basic budget allocation"""
        allocation = manager.allocate_budget(1000)

        assert allocation["core"] == 300  # 30%
        assert allocation["agents"] == 400  # 40%
        assert allocation["specialized"] == 200  # 20%
        assert allocation["learned"] == 100  # 10%

        # Total should equal budget
        assert sum(allocation.values()) == 1000

    def test_allocate_budget_rounding(self, manager):
        """Test allocation handles rounding correctly"""
        allocation = manager.allocate_budget(1001)

        # Total should equal budget (remainder added to core)
        assert sum(allocation.values()) == 1001

        # Core should get the remainder
        expected_core = 300 + 1  # 30% + remainder
        assert allocation["core"] == expected_core

    def test_allocate_budget_large(self, manager):
        """Test allocation with large budget"""
        allocation = manager.allocate_budget(10000)

        assert allocation["core"] == 3000
        assert allocation["agents"] == 4000
        assert allocation["specialized"] == 2000
        assert allocation["learned"] == 1000
        assert sum(allocation.values()) == 10000

    def test_allocate_budget_small(self, manager):
        """Test allocation with small budget"""
        allocation = manager.allocate_budget(100)

        assert allocation["core"] == 30
        assert allocation["agents"] == 40
        assert allocation["specialized"] == 20
        assert allocation["learned"] == 10
        assert sum(allocation.values()) == 100


class TestModeAdjustment:
    """Test budget adjustment for different modes"""

    @pytest.fixture
    def manager(self):
        """Create budget manager instance"""
        return ContextBudgetManager()

    def test_adjust_for_standard_mode(self, manager):
        """Test standard mode doesn't change budget"""
        budget = manager.adjust_for_mode(1000, "standard")
        assert budget == 1000

    def test_adjust_for_strict_mode(self, manager):
        """Test strict mode increases budget by 30%"""
        budget = manager.adjust_for_mode(1000, "strict")
        assert budget == 1300  # 1000 * 1.3

    def test_adjust_for_unknown_mode(self, manager):
        """Test unknown mode uses standard (no adjustment)"""
        budget = manager.adjust_for_mode(1000, "unknown")
        assert budget == 1000


class TestModelNormalization:
    """Test model name normalization"""

    @pytest.fixture
    def manager(self):
        """Create budget manager instance"""
        return ContextBudgetManager()

    def test_normalize_claude_models(self, manager):
        """Test Claude model normalization"""
        assert manager._normalize_model_name("Claude-Opus-4") == "claude-opus-4"
        assert manager._normalize_model_name("claude-opus") == "claude-opus-4"
        assert manager._normalize_model_name("OPUS") == "claude-opus-4"

        assert manager._normalize_model_name("Claude-Sonnet-4") == "claude-sonnet-4"
        assert manager._normalize_model_name("sonnet") == "claude-sonnet-4"

        assert manager._normalize_model_name("Claude-Haiku") == "claude-haiku"
        assert manager._normalize_model_name("haiku") == "claude-haiku"

    def test_normalize_openai_models(self, manager):
        """Test OpenAI model normalization"""
        assert manager._normalize_model_name("GPT-4") == "gpt-4"
        assert manager._normalize_model_name("gpt-4-turbo") == "gpt-4-turbo"
        assert manager._normalize_model_name("gpt-4-1106-preview") == "gpt-4-turbo"
        assert manager._normalize_model_name("GPT-3.5-Turbo") == "gpt-3.5-turbo"
        assert manager._normalize_model_name("gpt-35-turbo") == "gpt-3.5-turbo"

    def test_normalize_google_models(self, manager):
        """Test Google model normalization"""
        assert manager._normalize_model_name("Gemini-Pro") == "gemini-pro"
        assert manager._normalize_model_name("gemini") == "gemini-pro"
        assert manager._normalize_model_name("Gemini-Ultra") == "gemini-ultra"

    def test_normalize_unknown_model(self, manager):
        """Test unknown model uses default"""
        assert manager._normalize_model_name("unknown-llm") == "default"


class TestUtilityMethods:
    """Test utility methods"""

    @pytest.fixture
    def manager(self):
        """Create budget manager instance"""
        return ContextBudgetManager()

    def test_get_model_info(self, manager):
        """Test get_model_info returns complete information"""
        info = manager.get_model_info("claude-sonnet-4")

        assert info["model"] == "claude-sonnet-4"
        assert info["normalized_name"] == "claude-sonnet-4"
        assert info["base_budget"] == 6000
        assert "complexity_budgets" in info
        assert info["complexity_budgets"]["simple"] == 1800
        assert info["complexity_budgets"]["critical"] == 6000

    def test_estimate_tokens(self, manager):
        """Test token estimation"""
        text = "a" * 400  # 400 characters
        tokens = manager.estimate_tokens(text, chars_per_token=4)
        assert tokens == 100  # 400 / 4

        tokens = manager.estimate_tokens(text, chars_per_token=5)
        assert tokens == 80  # 400 / 5

    def test_validate_allocation_valid(self, manager):
        """Test validation passes for valid allocation"""
        allocation = {"core": 300, "agents": 400, "specialized": 200, "learned": 100}
        is_valid = manager.validate_allocation(allocation, 1000)
        assert is_valid is True

    def test_validate_allocation_invalid(self, manager):
        """Test validation fails when allocation exceeds budget"""
        allocation = {"core": 600, "agents": 600, "specialized": 200, "learned": 100}
        is_valid = manager.validate_allocation(allocation, 1000)
        assert is_valid is False


class TestIntegration:
    """Test integration scenarios"""

    @pytest.fixture
    def manager(self):
        """Create budget manager instance"""
        return ContextBudgetManager()

    def test_full_workflow_simple_task(self, manager):
        """Test complete workflow for simple task"""
        # Calculate budget
        budget = manager.get_budget("claude-sonnet-4", "simple")
        assert budget == 1800

        # Allocate budget
        allocation = manager.allocate_budget(budget)
        assert sum(allocation.values()) == budget

        # Validate allocation
        is_valid = manager.validate_allocation(allocation, budget)
        assert is_valid is True

    def test_full_workflow_critical_strict(self, manager):
        """Test complete workflow for critical task in strict mode"""
        # Calculate budget
        budget = manager.get_budget("claude-opus-4", "critical")
        assert budget == 10000

        # Adjust for strict mode
        budget = manager.adjust_for_mode(budget, "strict")
        assert budget == 13000  # 10000 * 1.3

        # Allocate budget
        allocation = manager.allocate_budget(budget)
        assert sum(allocation.values()) == budget
        assert allocation["core"] == 3900  # 30% of 13000
        assert allocation["agents"] == 5200  # 40% of 13000
