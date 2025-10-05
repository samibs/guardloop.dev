"""Optimize agent chains based on task complexity."""

from enum import Enum
from typing import Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    CRITICAL = "critical"


class AgentChainOptimizer:
    """Select minimal agent chain for task."""

    # Task → Agent Chain Mapping
    TASK_AGENT_CHAINS = {
        # Simple tasks - single agent
        "fix_typo": ["standards_oracle"],
        "update_docs": ["documentation_codifier"],
        "format_code": ["standards_oracle"],
        # Medium tasks - focused chain
        "implement_function": ["cold_blooded_architect", "ruthless_coder", "ruthless_tester"],
        "add_tests": ["ruthless_tester"],
        "fix_bug": ["support_debug_hunter", "ruthless_tester"],
        "refactor": ["cold_blooded_architect", "ruthless_coder", "ruthless_tester"],
        # Complex tasks - extended chain
        "implement_feature": [
            "business_analyst",
            "cold_blooded_architect",
            "ruthless_coder",
            "ruthless_tester",
            "merciless_evaluator",
        ],
        "implement_auth": [
            "cold_blooded_architect",
            "secops_engineer",
            "ruthless_coder",
            "ruthless_tester",
            "merciless_evaluator",
        ],
        "database_design": [
            "cold_blooded_architect",
            "dba",
            "ruthless_coder",
            "ruthless_tester",
        ],
        # Critical tasks - full chain + compliance
        "build_auth_system": [
            "business_analyst",
            "cold_blooded_architect",
            "secops_engineer",
            "dba",
            "ruthless_coder",
            "ruthless_tester",
            "sre_ops",
            "standards_oracle",
            "merciless_evaluator",
        ],
        "implement_payment": [
            "business_analyst",
            "cold_blooded_architect",
            "secops_engineer",
            "dba",
            "ruthless_coder",
            "ruthless_tester",
            "standards_oracle",
            "sre_ops",
            "merciless_evaluator",
        ],
        "compliance_feature": [
            "business_analyst",
            "cold_blooded_architect",
            "secops_engineer",
            "ruthless_coder",
            "ruthless_tester",
            "standards_oracle",
            "merciless_evaluator",
            "documentation_codifier",
        ],
        # UI/UX tasks
        "implement_ui": [
            "ux_ui_designer",
            "ruthless_coder",
            "ruthless_tester",
        ],
        "improve_accessibility": [
            "ux_ui_designer",
            "ruthless_coder",
            "ruthless_tester",
        ],
        # API tasks
        "implement_api": [
            "cold_blooded_architect",
            "ruthless_coder",
            "ruthless_tester",
        ],
        "api_security": [
            "cold_blooded_architect",
            "secops_engineer",
            "ruthless_coder",
            "ruthless_tester",
        ],
    }

    # Agent name normalization mapping (old → new)
    AGENT_NAME_MAP = {
        "architect": "cold_blooded_architect",
        "coder": "ruthless_coder",
        "tester": "ruthless_tester",
        "debug_hunter": "support_debug_hunter",
        "secops": "secops_engineer",
        "sre": "sre_ops",
        "evaluator": "merciless_evaluator",
        "documentation": "documentation_codifier",
        "ux_designer": "ux_ui_designer",
    }

    def __init__(self):
        """Initialize chain optimizer"""
        logger.debug("AgentChainOptimizer initialized")

    def select_chain(
        self,
        task_type: str,
        mode: str = "standard",
        user_specified_agent: Optional[str] = None,
    ) -> List[str]:
        """Select optimal agent chain.

        Args:
            task_type: Type of task to perform
            mode: Operating mode (standard or strict)
            user_specified_agent: User-specified agent (optional)

        Returns:
            List of agent names to execute in order
        """
        # User explicitly chose an agent
        if user_specified_agent:
            # Normalize agent name
            normalized_agent = self._normalize_agent_name(user_specified_agent)
            logger.info(
                "Using user-specified agent",
                original=user_specified_agent,
                normalized=normalized_agent,
            )
            return [normalized_agent]

        # Get base chain for task
        chain = self.TASK_AGENT_CHAINS.get(
            task_type,
            ["cold_blooded_architect", "ruthless_coder", "ruthless_tester"],  # Default medium chain
        )

        # Strict mode: add compliance agents
        if mode == "strict":
            chain = self._add_strict_agents(chain, task_type)

        # Normalize all agent names
        chain = [self._normalize_agent_name(agent) for agent in chain]

        # Remove duplicates while preserving order
        seen = set()
        unique_chain = []
        for agent in chain:
            if agent not in seen:
                seen.add(agent)
                unique_chain.append(agent)

        logger.info(
            "Agent chain selected",
            task_type=task_type,
            mode=mode,
            chain_length=len(unique_chain),
            complexity=self.get_complexity(task_type).value,
        )

        return unique_chain

    def _add_strict_agents(self, chain: List[str], task_type: str) -> List[str]:
        """Add agents for strict mode.

        Args:
            chain: Base agent chain
            task_type: Task type

        Returns:
            Enhanced chain with strict mode agents
        """
        strict_chain = chain.copy()

        # Always add security check in strict mode
        if "secops_engineer" not in strict_chain and "secops" not in strict_chain:
            # Insert after architect, before coder
            insert_pos = next(
                (
                    i
                    for i, agent in enumerate(strict_chain)
                    if agent in ["ruthless_coder", "coder", "ruthless_tester", "tester"]
                ),
                len(strict_chain),
            )
            strict_chain.insert(insert_pos, "secops_engineer")

        # Always add standards check
        if "standards_oracle" not in strict_chain:
            strict_chain.append("standards_oracle")

        # Always add final evaluation
        if "merciless_evaluator" not in strict_chain and "evaluator" not in strict_chain:
            strict_chain.append("merciless_evaluator")

        logger.debug(
            "Strict mode agents added",
            original_length=len(chain),
            strict_length=len(strict_chain),
            added_agents=[a for a in strict_chain if a not in chain],
        )

        return strict_chain

    def get_complexity(self, task_type: str) -> TaskComplexity:
        """Determine task complexity.

        Args:
            task_type: Task type

        Returns:
            Task complexity level
        """
        chain_length = len(
            self.TASK_AGENT_CHAINS.get(
                task_type, ["cold_blooded_architect", "ruthless_coder", "ruthless_tester"]
            )
        )

        if chain_length <= 2:
            complexity = TaskComplexity.SIMPLE
        elif chain_length <= 5:
            complexity = TaskComplexity.MEDIUM
        elif chain_length <= 8:
            complexity = TaskComplexity.COMPLEX
        else:
            complexity = TaskComplexity.CRITICAL

        logger.debug(
            "Task complexity determined",
            task_type=task_type,
            chain_length=chain_length,
            complexity=complexity.value,
        )

        return complexity

    def _normalize_agent_name(self, agent_name: str) -> str:
        """Normalize agent name to standard format.

        Args:
            agent_name: Original agent name

        Returns:
            Normalized agent name
        """
        # Remove hyphens and underscores, convert to lowercase
        normalized = agent_name.lower().replace("-", "_")

        # Apply mapping if exists
        if normalized in self.AGENT_NAME_MAP:
            return self.AGENT_NAME_MAP[normalized]

        return normalized

    def get_task_types(self) -> List[str]:
        """Get all supported task types.

        Returns:
            List of task type names
        """
        return list(self.TASK_AGENT_CHAINS.keys())

    def estimate_execution_time(self, task_type: str, mode: str = "standard") -> float:
        """Estimate execution time in seconds.

        Args:
            task_type: Task type
            mode: Operating mode

        Returns:
            Estimated time in seconds
        """
        chain = self.select_chain(task_type, mode)
        chain_length = len(chain)

        # Rough estimate: 30 seconds per agent
        base_time = chain_length * 30

        # Add overhead for strict mode
        if mode == "strict":
            base_time *= 1.3

        return base_time
