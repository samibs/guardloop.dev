"""Unit tests for the Debug Hunter agent"""

import pytest
from unittest.mock import MagicMock
from guardloop.agents.debug_hunter import DebugHunterAgent
from guardloop.agents.base import AgentContext
from guardloop.core.parser import ParsedResponse, CodeBlock

@pytest.fixture
def config():
    """Fixture for a mock config object."""
    return MagicMock()

@pytest.fixture
def agent(config):
    """Fixture for a DebugHunterAgent."""
    return DebugHunterAgent(config)

@pytest.mark.asyncio
async def test_evaluate_approved(agent):
    """Test a successful evaluation with all debug principles met."""
    raw_output = "The root cause was a null pointer. I've added a regression test and some logging."
    code_block = CodeBlock(language="python", content="assert result is not None\nlogger.info('Test')")
    parsed_response = ParsedResponse(code_blocks=[code_block])
    context = AgentContext(prompt="fix bug", mode="test", raw_output=raw_output, parsed_response=parsed_response)
    decision = await agent.evaluate(context)
    assert decision.approved is True
    assert decision.next_agent == "tester"
    assert "Bug fix is well-documented" in decision.reason

@pytest.mark.asyncio
async def test_evaluate_missing_root_cause(agent):
    """Test rejection when root cause analysis is missing."""
    raw_output = "Fixed the bug."
    code_block = CodeBlock(language="python", content="assert True")
    parsed_response = ParsedResponse(code_blocks=[code_block])
    context = AgentContext(prompt="fix bug", mode="test", raw_output=raw_output, parsed_response=parsed_response)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "root cause analysis" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_missing_regression_test(agent):
    """Test rejection when regression test is missing."""
    raw_output = "The root cause was a race condition."
    context = AgentContext(prompt="fix bug", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "regression test" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_missing_logging(agent):
    """Test rejection when debug logging is missing."""
    raw_output = "The root cause was an off-by-one error. Added a test."
    code_block = CodeBlock(language="python", content="assert 1 == 1")
    parsed_response = ParsedResponse(code_blocks=[code_block])
    context = AgentContext(prompt="fix bug", mode="test", raw_output=raw_output, parsed_response=parsed_response)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "logging" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_all_issues(agent):
    """Test rejection when all debug principles are missing."""
    raw_output = "I fixed it."
    context = AgentContext(prompt="fix bug", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert len(decision.suggestions) == 3
    assert "Found 3 issues" in decision.reason