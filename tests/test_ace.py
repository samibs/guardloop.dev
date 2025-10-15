"""Tests for the ACE integration."""

import pytest

from guardloop.ace.adapter import ACEAdapter
from guardloop.ace.models import Goal
from guardloop.agents.orchestrator import OrchestratorAgent
from guardloop.utils.config import get_config


class TestACEIntegration:
    """Tests for the ACE integration."""

    def test_ace_adapter_get_goals(self):
        """Test that the ACE adapter can get goals."""
        adapter = ACEAdapter()
        goals = adapter.get_goals()
        assert goals == []

    def test_ace_adapter_get_plan(self):
        """Test that the ACE adapter can get a plan."""
        adapter = ACEAdapter()
        goal = Goal(description="Test goal")
        plan = adapter.get_plan(goal)
        assert plan.goal == goal
        assert plan.steps == []

    def test_ace_adapter_get_next_action(self):
        """Test that the ACE adapter can get the next action."""
        adapter = ACEAdapter()
        goal = Goal(description="Test goal")
        plan = adapter.get_plan(goal)
        action = adapter.get_next_action(plan)
        assert action.name == "finish"

    @pytest.mark.asyncio
    async def test_orchestrator_run_ace(self):
        """Test that the orchestrator can run the ACE lifecycle."""
        config = get_config()
        orchestrator = OrchestratorAgent(config)
        decision = await orchestrator.run_ace(None)
        assert decision.approved
        assert "No goals for ACE to accomplish" in decision.reason