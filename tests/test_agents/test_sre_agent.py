"""Unit tests for the SRE agent"""

import pytest
from unittest.mock import MagicMock
from guardloop.agents.sre import SREAgent
from guardloop.agents.base import AgentContext
from guardloop.core.parser import ParsedResponse, CodeBlock

@pytest.fixture
def config():
    """Fixture for a mock config object."""
    return MagicMock()

@pytest.fixture
def agent(config):
    """Fixture for a SREAgent."""
    return SREAgent(config)

@pytest.mark.asyncio
async def test_evaluate_approved(agent):
    """Test a successful evaluation with all SRE principles met."""
    raw_output = "We will use prometheus for monitoring, a circuit breaker for recovery, and a Dockerfile for deployment."
    context = AgentContext(prompt="test", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is True
    assert decision.next_agent == "evaluator"
    assert "SRE principles" in decision.reason

@pytest.mark.asyncio
async def test_evaluate_missing_monitoring(agent):
    """Test rejection when monitoring is missing."""
    raw_output = "We have a circuit breaker and a Dockerfile."
    context = AgentContext(prompt="test", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "monitoring" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_missing_error_recovery(agent):
    """Test rejection when error recovery is missing."""
    raw_output = "We have prometheus and a Dockerfile."
    context = AgentContext(prompt="test", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "error recovery" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_missing_deployment_config(agent):
    """Test rejection when deployment config is missing."""
    raw_output = "We have prometheus and a circuit breaker."
    context = AgentContext(prompt="test", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "deployment" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_all_issues(agent):
    """Test rejection when all SRE principles are missing."""
    raw_output = "Here is some code."
    context = AgentContext(prompt="test", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert len(decision.suggestions) == 3
    assert "Found 3 SRE issues" in decision.reason

@pytest.mark.asyncio
async def test_evaluate_checks_code_blocks(agent):
    """Test that the agent checks code blocks as well as raw output."""
    code_block = CodeBlock(language="yaml", content="kind: Deployment")
    parsed_response = ParsedResponse(code_blocks=[code_block])
    context = AgentContext(prompt="test", mode="test", raw_output="monitoring and recovery", parsed_response=parsed_response)
    decision = await agent.evaluate(context)
    assert decision.approved is True