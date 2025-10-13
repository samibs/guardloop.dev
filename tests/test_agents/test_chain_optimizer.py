"""Unit tests for the Agent Chain Optimizer"""

import pytest
from guardloop.agents.chain_optimizer import AgentChainOptimizer, TaskComplexity

@pytest.fixture
def optimizer():
    """Fixture for an AgentChainOptimizer."""
    return AgentChainOptimizer()

def test_select_simple_chain(optimizer):
    """Test selection of a simple agent chain."""
    chain = optimizer.select_chain("fix_typo")
    assert chain == ["standards_oracle"]

def test_select_complex_chain(optimizer):
    """Test selection of a complex agent chain."""
    chain = optimizer.select_chain("implement_feature")
    assert chain == ["business_analyst", "architect", "coder", "tester", "evaluator"]

def test_select_default_chain(optimizer):
    """Test that a default chain is returned for an unknown task type."""
    chain = optimizer.select_chain("unknown_task")
    assert chain == ["architect", "coder", "tester"]

def test_strict_mode(optimizer):
    """Test that strict mode adds compliance agents."""
    chain = optimizer.select_chain("implement_function", mode="strict")
    assert "secops" in chain
    assert "standards_oracle" in chain
    assert "evaluator" in chain

def test_user_specified_agent(optimizer):
    """Test that a user-specified agent overrides the chain."""
    chain = optimizer.select_chain("implement_feature", user_specified_agent="tester")
    assert chain == ["tester"]

def test_get_complexity(optimizer):
    """Test complexity calculation."""
    assert optimizer.get_complexity("fix_typo") == TaskComplexity.SIMPLE
    assert optimizer.get_complexity("implement_function") == TaskComplexity.MEDIUM
    assert optimizer.get_complexity("implement_feature") == TaskComplexity.COMPLEX
    assert optimizer.get_complexity("build_auth_system") == TaskComplexity.CRITICAL
