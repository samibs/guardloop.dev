"""Unit tests for the Business Analyst agent"""

import pytest
from unittest.mock import MagicMock
from guardloop.agents.business_analyst import BusinessAnalystAgent
from guardloop.agents.base import AgentContext

@pytest.fixture
def config():
    """Fixture for a mock config object."""
    return MagicMock()

@pytest.fixture
def agent(config):
    """Fixture for a BusinessAnalystAgent."""
    return BusinessAnalystAgent(config)

@pytest.mark.asyncio
async def test_evaluate_approved(agent):
    """Test a successful evaluation with a well-formed prompt."""
    prompt = "As a user, I want to see my profile picture, so that I can personalize my account. Given I am logged in, when I navigate to my profile, then I should see my picture. This will increase user engagement."
    context = AgentContext(prompt=prompt, mode="test", raw_output="")
    decision = await agent.evaluate(context)
    assert decision.approved is True
    assert decision.next_agent == "architect"
    assert "Business requirements are clear" in decision.reason

@pytest.mark.asyncio
async def test_evaluate_generic_prompt(agent):
    """Test that a generic prompt is rejected."""
    prompt = "build a website"
    context = AgentContext(prompt=prompt, mode="test")
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert decision.next_agent is None
    assert "Prompt is too generic" in decision.suggestions[0]
    assert "Found 4 issues" in decision.reason

@pytest.mark.asyncio
async def test_evaluate_missing_user_story(agent):
    """Test rejection when the user story format is missing."""
    prompt = "I need a new login page. It should have a username and password field. This will help users log in."
    context = AgentContext(prompt=prompt, mode="test", raw_output="")
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "Use user story format" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_missing_acceptance_criteria(agent):
    """Test rejection when acceptance criteria are missing."""
    prompt = "As a user, I want a dashboard, so that I can see my stats. This will provide value."
    context = AgentContext(prompt=prompt, mode="test", raw_output="")
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "Define clear acceptance criteria" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_missing_business_value(agent):
    """Test rejection when business value is not clarified."""
    prompt = "As a user, I want a button. Given I am on the page, when I click the button, then something happens."
    context = AgentContext(prompt=prompt, mode="test", raw_output="")
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "Clarify the business value" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_multiple_issues(agent):
    """Test that multiple issues are caught and reported."""
    prompt = "Make a login system."
    context = AgentContext(prompt=prompt, mode="test", raw_output="")
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert len(decision.suggestions) == 4
    assert "Found 4 issues" in decision.reason