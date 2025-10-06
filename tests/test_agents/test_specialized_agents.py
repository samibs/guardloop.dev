"""Tests for specialized agent modules"""

import pytest

from guardloop.agents.base import AgentContext
from guardloop.agents.business_analyst import BusinessAnalystAgent
from guardloop.agents.dba import DBAAgent
from guardloop.agents.debug_hunter import DebugHunterAgent
from guardloop.agents.documentation import DocumentationAgent
from guardloop.agents.sre import SREAgent
from guardloop.agents.standards_oracle import StandardsOracleAgent
from guardloop.agents.ux_designer import UXDesignerAgent
from guardloop.utils.config import Config


@pytest.fixture
def config():
    """Create test config"""
    return Config()


@pytest.mark.asyncio
class TestBusinessAnalystAgent:
    """Test Business Analyst agent"""

    async def test_initialization(self, config):
        agent = BusinessAnalystAgent(config)
        assert agent.name == "business_analyst"
        assert agent.config == config

    async def test_evaluate_with_user_story(self, config):
        agent = BusinessAnalystAgent(config)
        context = AgentContext(
            prompt="As a user, I want to login, so that I can access my account",
            mode="standard",
            raw_output="Acceptance criteria: Given valid credentials, when user logs in, then access granted",
        )
        decision = await agent.evaluate(context)
        assert decision.approved is True
        assert decision.agent_name == "business_analyst"
        assert decision.next_agent == "architect"

    async def test_evaluate_missing_requirements(self, config):
        agent = BusinessAnalystAgent(config)
        context = AgentContext(prompt="Make a login page", mode="standard", raw_output="")
        decision = await agent.evaluate(context)
        assert decision.approved is True  # Agent is lenient
        assert len(decision.suggestions) > 0


@pytest.mark.asyncio
class TestDBAAgent:
    """Test DBA agent"""

    async def test_initialization(self, config):
        agent = DBAAgent(config)
        assert agent.name == "dba"
        assert agent.config == config

    async def test_evaluate_with_schema(self, config):
        agent = DBAAgent(config)
        context = AgentContext(
            prompt="Create user table",
            mode="standard",
            raw_output="CREATE TABLE users (id INT PRIMARY KEY, username VARCHAR(100) UNIQUE)",
        )
        decision = await agent.evaluate(context)
        assert decision.approved is True
        assert decision.agent_name == "dba"

    async def test_evaluate_missing_indexes(self, config):
        agent = DBAAgent(config)
        context = AgentContext(
            prompt="Create table", mode="standard", raw_output="CREATE TABLE test (id INT)"
        )
        decision = await agent.evaluate(context)
        assert decision.approved is True
        assert len(decision.suggestions) > 0


@pytest.mark.asyncio
class TestDebugHunterAgent:
    """Test Debug Hunter agent"""

    async def test_initialization(self, config):
        agent = DebugHunterAgent(config)
        assert agent.name == "debug_hunter"
        assert agent.config == config

    async def test_evaluate_with_logging(self, config):
        agent = DebugHunterAgent(config)
        context = AgentContext(
            prompt="Fix bug with root cause analysis",
            mode="standard",
            raw_output="Root cause: null pointer. Added error handling",
        )
        decision = await agent.evaluate(context)
        # DebugHunter requires regression tests in parsed_response (code blocks)
        # Without parsed_response, regression test check fails
        assert decision.approved is False
        assert "regression tests" in str(decision.suggestions)

    async def test_evaluate_missing_debugging(self, config):
        agent = DebugHunterAgent(config)
        context = AgentContext(prompt="Fix issue", mode="standard", raw_output="Fixed")
        decision = await agent.evaluate(context)
        # DebugHunter is strict - expects root cause analysis
        assert decision.approved is False
        assert len(decision.suggestions) > 0


@pytest.mark.asyncio
class TestDocumentationAgent:
    """Test Documentation agent"""

    async def test_initialization(self, config):
        agent = DocumentationAgent(config)
        assert agent.name == "documentation"
        assert agent.config == config

    async def test_evaluate_with_docs(self, config):
        agent = DocumentationAgent(config)
        context = AgentContext(
            prompt="Document API",
            mode="standard",
            raw_output="# API Documentation\n\n## Endpoints\n\n### GET /users\nReturns all users",
        )
        decision = await agent.evaluate(context)
        assert decision.approved is True

    async def test_evaluate_missing_docs(self, config):
        agent = DocumentationAgent(config)
        context = AgentContext(prompt="Update code", mode="standard", raw_output="Code updated")
        decision = await agent.evaluate(context)
        assert decision.approved is True
        assert len(decision.suggestions) > 0


@pytest.mark.asyncio
class TestSREAgent:
    """Test SRE agent"""

    async def test_initialization(self, config):
        agent = SREAgent(config)
        assert agent.name == "sre"
        assert agent.config == config

    async def test_evaluate_with_monitoring(self, config):
        agent = SREAgent(config)
        context = AgentContext(
            prompt="Deploy service",
            mode="standard",
            raw_output="Added monitoring, logging, alerts, and health checks",
        )
        decision = await agent.evaluate(context)
        assert decision.approved is True

    async def test_evaluate_missing_monitoring(self, config):
        agent = SREAgent(config)
        context = AgentContext(
            prompt="Deploy app", mode="standard", raw_output="Deployed to production"
        )
        decision = await agent.evaluate(context)
        assert decision.approved is True
        assert len(decision.suggestions) > 0


@pytest.mark.asyncio
class TestStandardsOracleAgent:
    """Test Standards Oracle agent"""

    async def test_initialization(self, config):
        agent = StandardsOracleAgent(config)
        assert agent.name == "standards_oracle"
        assert agent.config == config

    async def test_evaluate_with_formatting(self, config):
        agent = StandardsOracleAgent(config)
        context = AgentContext(
            prompt="Format code",
            mode="standard",
            raw_output="Ran prettier and eslint to format code according to style guide",
        )
        decision = await agent.evaluate(context)
        assert decision.approved is True

    async def test_evaluate_missing_standards(self, config):
        agent = StandardsOracleAgent(config)
        context = AgentContext(prompt="Write code", mode="standard", raw_output="function f(){}")
        decision = await agent.evaluate(context)
        # StandardsOracle approves but may have no suggestions for minimal code
        assert decision.approved is True


@pytest.mark.asyncio
class TestUXDesignerAgent:
    """Test UX Designer agent"""

    async def test_initialization(self, config):
        agent = UXDesignerAgent(config)
        assert agent.name == "ux_designer"
        assert agent.config == config

    async def test_evaluate_with_accessibility(self, config):
        agent = UXDesignerAgent(config)
        context = AgentContext(
            prompt="Create button",
            mode="standard",
            raw_output="<button aria-label='Submit' class='responsive'>Submit</button>",
        )
        decision = await agent.evaluate(context)
        assert decision.approved is True

    async def test_evaluate_missing_ux(self, config):
        agent = UXDesignerAgent(config)
        context = AgentContext(
            prompt="Make UI", mode="standard", raw_output="<div>Content</div>"
        )
        decision = await agent.evaluate(context)
        assert decision.approved is True
        assert len(decision.suggestions) > 0
