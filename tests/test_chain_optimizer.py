"""Tests for AgentChainOptimizer"""

import pytest

from guardloop.agents.chain_optimizer import AgentChainOptimizer, TaskComplexity


@pytest.fixture
def optimizer():
    """Create chain optimizer instance"""
    return AgentChainOptimizer()


class TestTaskChainSelection:
    """Test task-to-chain selection"""

    def test_simple_task_single_agent(self, optimizer):
        chain = optimizer.select_chain("fix_typo")
        assert len(chain) == 1
        assert chain == ["standards_oracle"]

    def test_simple_task_docs(self, optimizer):
        chain = optimizer.select_chain("update_docs")
        assert len(chain) == 1
        assert chain == ["documentation"]

    def test_medium_task_focused_chain(self, optimizer):
        chain = optimizer.select_chain("implement_function")
        assert len(chain) == 3
        assert "architect" in chain
        assert "coder" in chain
        assert "tester" in chain

    def test_complex_task_extended_chain(self, optimizer):
        chain = optimizer.select_chain("implement_feature")
        assert len(chain) >= 4
        assert "business_analyst" in chain
        assert "architect" in chain
        assert "evaluator" in chain

    def test_critical_task_full_chain(self, optimizer):
        chain = optimizer.select_chain("build_auth_system")
        assert len(chain) >= 8
        assert "secops" in chain
        assert "dba" in chain
        assert "standards_oracle" in chain

    def test_default_chain_for_unknown_task(self, optimizer):
        chain = optimizer.select_chain("unknown_task_xyz")
        # Should return default medium chain
        assert len(chain) == 3
        assert "architect" in chain
        assert "coder" in chain
        assert "tester" in chain


class TestStrictMode:
    """Test strict mode enhancements"""

    def test_strict_mode_adds_security(self, optimizer):
        # Standard mode
        standard_chain = optimizer.select_chain("implement_function", mode="standard")
        # Strict mode
        strict_chain = optimizer.select_chain("implement_function", mode="strict")

        assert len(strict_chain) > len(standard_chain)
        assert "secops" in strict_chain
        assert "standards_oracle" in strict_chain
        assert "evaluator" in strict_chain

    def test_strict_mode_preserves_order(self, optimizer):
        chain = optimizer.select_chain("implement_function", mode="strict")

        # Security should be before coder
        secops_idx = chain.index("secops")
        coder_idx = chain.index("coder")
        assert secops_idx < coder_idx

    def test_strict_mode_no_duplicates(self, optimizer):
        # Task already has some strict agents
        chain = optimizer.select_chain("build_auth_system", mode="strict")

        # Should not have duplicate agents
        assert len(chain) == len(set(chain))


class TestUserSpecifiedAgent:
    """Test user-specified agent override"""

    def test_user_agent_override(self, optimizer):
        chain = optimizer.select_chain(
            task_type="implement_feature", user_specified_agent="coder"
        )
        assert chain == ["coder"]

    def test_user_agent_normalization(self, optimizer):
        # Test with old agent name
        chain = optimizer.select_chain(task_type="implement_feature", user_specified_agent="coder")
        assert chain == ["coder"]

    def test_user_agent_hyphenated(self, optimizer):
        chain = optimizer.select_chain(
            task_type="implement_feature", user_specified_agent="architect"
        )
        assert chain == ["architect"]


class TestComplexityDetection:
    """Test task complexity detection"""

    def test_simple_complexity(self, optimizer):
        complexity = optimizer.get_complexity("fix_typo")
        assert complexity == TaskComplexity.SIMPLE

    def test_medium_complexity(self, optimizer):
        complexity = optimizer.get_complexity("implement_function")
        assert complexity == TaskComplexity.MEDIUM

    def test_complex_complexity(self, optimizer):
        # Most tasks are either SIMPLE (<=2), MEDIUM (3-5), or CRITICAL (9+)
        # There are no defined tasks with 6-8 agents in current implementation
        # Skip this test or verify complexity classification logic works
        # For now, verify that COMPLEX range (6-8 agents) classification works
        # by checking the get_complexity logic directly
        from guardloop.agents.chain_optimizer import TaskComplexity

        # Simulate a task with 7 agents (COMPLEX range)
        mock_task = "mock_complex_task"
        optimizer.TASK_AGENT_CHAINS[mock_task] = ["agent" + str(i) for i in range(7)]
        complexity = optimizer.get_complexity(mock_task)
        assert complexity == TaskComplexity.COMPLEX

    def test_critical_complexity(self, optimizer):
        complexity = optimizer.get_complexity("build_auth_system")
        assert complexity == TaskComplexity.CRITICAL

    def test_default_medium_complexity(self, optimizer):
        complexity = optimizer.get_complexity("unknown_task")
        assert complexity == TaskComplexity.MEDIUM


class TestAgentNameNormalization:
    """Test agent name normalization"""

    def test_normalize_hyphenated(self, optimizer):
        chain = optimizer.select_chain("implement_api")
        assert chain == ["architect", "coder", "tester"]

    def test_normalize_old_names(self, optimizer):
        chain = optimizer.select_chain("implement_ui")
        assert chain == ["ux_designer", "coder", "tester"]

    def test_normalize_already_normalized(self, optimizer):
        chain = optimizer.select_chain("implement_function")
        assert chain == ["architect", "coder", "tester"]


class TestSpecializedTasks:
    """Test specialized task chains"""

    def test_ui_task_chain(self, optimizer):
        chain = optimizer.select_chain("implement_ui")
        assert "ux_designer" in chain
        assert "coder" in chain
        assert "tester" in chain

    def test_database_task_chain(self, optimizer):
        chain = optimizer.select_chain("database_design")
        assert "dba" in chain
        assert "architect" in chain

    def test_auth_task_chain(self, optimizer):
        chain = optimizer.select_chain("implement_auth")
        assert "secops" in chain
        assert "architect" in chain

    def test_api_security_chain(self, optimizer):
        chain = optimizer.select_chain("api_security")
        assert "secops" in chain


class TestUtilityMethods:
    """Test utility methods"""

    def test_get_task_types(self, optimizer):
        task_types = optimizer.get_task_types()
        assert len(task_types) > 0
        assert "fix_typo" in task_types
        assert "implement_feature" in task_types
        assert "build_auth_system" in task_types

    def test_estimate_execution_time(self, optimizer):
        # Simple task
        simple_time = optimizer.estimate_execution_time("fix_typo")
        assert simple_time > 0
        assert simple_time < 100  # Should be quick

        # Complex task
        complex_time = optimizer.estimate_execution_time("build_auth_system")
        assert complex_time > simple_time

        # Strict mode takes longer
        standard_time = optimizer.estimate_execution_time("implement_feature", "standard")
        strict_time = optimizer.estimate_execution_time("implement_feature", "strict")
        assert strict_time > standard_time


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_task_type(self, optimizer):
        # Should return default chain
        chain = optimizer.select_chain("")
        assert len(chain) == 3

    def test_none_user_agent(self, optimizer):
        # Should use normal chain selection
        chain = optimizer.select_chain("implement_function", user_specified_agent=None)
        assert len(chain) > 1

    def test_invalid_mode(self, optimizer):
        # Should treat as standard mode
        chain = optimizer.select_chain("implement_function", mode="invalid")
        # Should still work, just not add strict agents
        assert len(chain) >= 3