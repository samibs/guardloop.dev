"""The ACE adapter."""

from typing import List

from guardloop.ace.models import Action, Goal, Plan


class ACEAdapter:
    """The ACE adapter."""

    def __init__(self):
        """Initialize the ACE adapter."""
        pass

    def get_goals(self) -> List[Goal]:
        """Get the ACE's goals."""
        return []

    def get_plan(self, goal: Goal) -> Plan:
        """Get the ACE's plan for a goal."""
        return Plan(goal=goal)

    def get_next_action(self, plan: Plan) -> Action:
        """Get the ACE's next action."""
        return Action(name="finish")