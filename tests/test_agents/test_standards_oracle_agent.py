"""Unit tests for the Standards Oracle agent"""

import pytest
from unittest.mock import MagicMock
from guardloop.agents.standards_oracle import StandardsOracleAgent
from guardloop.agents.base import AgentContext
from guardloop.core.parser import ParsedResponse, CodeBlock

@pytest.fixture
def config():
    """Fixture for a mock config object."""
    return MagicMock()

@pytest.fixture
def agent(config):
    """Fixture for a StandardsOracleAgent."""
    return StandardsOracleAgent(config)

@pytest.mark.asyncio
async def test_evaluate_approved(agent):
    """Test a successful evaluation with good standards."""
    code_block = CodeBlock(language="python", content="my_variable = 1")
    parsed_response = ParsedResponse(code_blocks=[code_block])
    context = AgentContext(prompt="code", mode="test", parsed_response=parsed_response)
    decision = await agent.evaluate(context)
    assert decision.approved is True
    assert decision.next_agent == "evaluator"
    assert "Code adheres" in decision.reason

@pytest.mark.asyncio
async def test_evaluate_bad_naming_python(agent):
    """Test rejection for bad naming conventions in Python."""
    code_block = CodeBlock(language="python", content="myVar = 1")
    parsed_response = ParsedResponse(code_blocks=[code_block])
    context = AgentContext(prompt="code", mode="test", parsed_response=parsed_response)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "naming conventions" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_bad_naming_js(agent):
    """Test rejection for bad naming conventions in JavaScript."""
    code_block = CodeBlock(language="javascript", content="my_var = 1;")
    parsed_response = ParsedResponse(code_blocks=[code_block])
    context = AgentContext(prompt="code", mode="test", parsed_response=parsed_response)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "naming conventions" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_inconsistent_style(agent):
    """Test rejection for inconsistent indentation."""
    code_block = CodeBlock(language="python", content="def my_func():\n\tprint('hello')\n    print('world')")
    parsed_response = ParsedResponse(code_blocks=[code_block])
    context = AgentContext(prompt="code", mode="test", parsed_response=parsed_response)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "consistent code style" in decision.suggestions[0]

@pytest.mark.asyncio
async def test_evaluate_long_function(agent):
    """Test rejection for a long function violating SRP."""
    long_code = "\n".join([f"print({i})" for i in range(100)])
    code_block = CodeBlock(language="python", content=long_code)
    parsed_response = ParsedResponse(code_blocks=[code_block])
    context = AgentContext(prompt="code", mode="test", parsed_response=parsed_response)
    decision = await agent.evaluate(context)
    assert decision.approved is False
    assert "SOLID principles" in decision.suggestions[0]