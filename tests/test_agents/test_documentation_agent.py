"""Unit tests for the Documentation agent"""

import pytest
from unittest.mock import MagicMock
from guardloop.agents.documentation import DocumentationAgent
from guardloop.agents.base import AgentContext
from guardloop.core.parser import ParsedResponse, CodeBlock

@pytest.fixture
def config():
    """Fixture for a mock config object."""
    return MagicMock()

@pytest.fixture
def agent(config):
    """Fixture for a DocumentationAgent."""
    return DocumentationAgent(config)

@pytest.mark.asyncio
async def test_evaluate_approved(agent):
    """Test a successful evaluation with all documentation principles met."""
    raw_output = "This is a README. Here is an example of how to use the API. The function `foo` is documented below."
    code_block = CodeBlock(language="python", content='"""Args:"""')
    parsed_response = ParsedResponse(code_blocks=[code_block])
    context = AgentContext(prompt="doc", mode="test", raw_output=raw_output, parsed_response=parsed_response)
    decision = await agent.evaluate(context)
    assert decision.approved is True
    assert decision.next_agent == "evaluator"
    assert "Documentation is comprehensive" in decision.reason

@pytest.mark.asyncio
async def test_evaluate_missing_readme(agent):
    """Test rejection when README is missing."""
    raw_output = "Here is the API and an example."
    context = AgentContext(prompt="doc", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "README.md" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_missing_api_docs(agent):
    """Test rejection when API docs are missing."""
    raw_output = "This is a README and an example."
    context = AgentContext(prompt="doc", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "API documentation" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_missing_examples(agent):
    """Test rejection when examples are missing."""
    raw_output = "This is a README. The API is documented in the code."
    code_block = CodeBlock(language="python", content='"""Args:"""')
    parsed_response = ParsedResponse(code_blocks=[code_block])
    context = AgentContext(prompt="doc", mode="test", raw_output=raw_output, parsed_response=parsed_response)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "code examples" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_all_issues(agent):
    """Test rejection when all documentation principles are missing."""
    raw_output = "Here is some code."
    context = AgentContext(prompt="doc", mode="test", raw_output=raw_output)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert len(decision.suggestions) == 3
    assert "Found 3 documentation issues" in decision.reason