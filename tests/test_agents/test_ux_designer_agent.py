"""Unit tests for the UX Designer agent"""

import pytest
from unittest.mock import MagicMock
from guardloop.agents.ux_designer import UXDesignerAgent
from guardloop.agents.base import AgentContext
from guardloop.core.parser import ParsedResponse, CodeBlock

@pytest.fixture
def config():
    """Fixture for a mock config object."""
    return MagicMock()

@pytest.fixture
def agent(config):
    """Fixture for a UXDesignerAgent."""
    return UXDesignerAgent(config)

@pytest.mark.asyncio
async def test_evaluate_approved(agent):
    """Test a successful evaluation with all UX principles met."""
    raw_output = "This design is accessible (aria-label), responsive (@media), and has error and loading states."
    context = AgentContext(prompt="ux", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is True
    assert decision.next_agent == "coder"
    assert "User experience principles are well-considered" in decision.reason

@pytest.mark.asyncio
async def test_evaluate_missing_accessibility(agent):
    """Test rejection when accessibility is missing."""
    raw_output = "This design is responsive and has error/loading states."
    context = AgentContext(prompt="ux", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "accessibility" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_missing_responsive_design(agent):
    """Test rejection when responsive design is missing."""
    raw_output = "This design is accessible and has error/loading states."
    context = AgentContext(prompt="ux", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "responsive design" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_missing_error_states(agent):
    """Test rejection when error states are missing."""
    raw_output = "This design is accessible and responsive, with loading states."
    context = AgentContext(prompt="ux", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "error states" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_missing_loading_states(agent):
    """Test rejection when loading states are missing."""
    raw_output = "This design is accessible, responsive, and has error states."
    context = AgentContext(prompt="ux", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "loading states" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_all_issues(agent):
    """Test rejection when all UX principles are missing."""
    raw_output = "Here is a basic design."
    context = AgentContext(prompt="ux", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert len(decision.suggestions) == 4
    assert "Found 4 UX issues" in decision.reason

@pytest.mark.asyncio
async def test_evaluate_checks_code_blocks(agent):
    """Test that the agent checks code blocks as well as raw output."""
    code_block = CodeBlock(language="html", content='<div class="spinner"></div>')
    parsed_response = ParsedResponse(code_blocks=[code_block])
    raw_output = "Accessible, responsive, error states."
    context = AgentContext(prompt="ux", mode="test", raw_output=raw_output, parsed_response=parsed_response)
    decision = await agent.evaluate(context)
    assert decision.approved is True