"""Pydantic models for the ACE lifecycle."""

from typing import List, Optional

from pydantic import BaseModel, Field


class Goal(BaseModel):
    """An ACE's goal."""

    description: str = Field(description="The goal's description.")
    sub_goals: List["Goal"] = Field(default_factory=list, description="A list of sub-goals.")


class Plan(BaseModel):
    """An ACE's plan to achieve a goal."""

    goal: Goal = Field(description="The goal this plan is for.")
    steps: List[str] = Field(default_factory=list, description="The steps in the plan.")


class Action(BaseModel):
    """An action an ACE can take."""

    name: str = Field(description="The action's name.")
    args: Optional[dict] = Field(default=None, description="The action's arguments.")