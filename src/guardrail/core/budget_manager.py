"""Dynamic context budget management for optimal token allocation."""

from typing import Dict
import structlog

logger = structlog.get_logger(__name__)


class ContextBudgetManager:
    """Manage context size based on task complexity and LLM model capabilities."""

    # Model → Max Context Tokens
    MODEL_BUDGETS = {
        # Claude models
        "claude-opus-4": 10000,
        "claude-sonnet-4": 6000,
        "claude-haiku": 4000,
        # OpenAI models
        "gpt-4": 4000,
        "gpt-4-turbo": 8000,
        "gpt-3.5-turbo": 2000,
        # Google models
        "gemini-pro": 5000,
        "gemini-ultra": 8000,
        # Generic defaults
        "default": 5000,
    }

    # Task Complexity → Budget Multiplier
    COMPLEXITY_MULTIPLIERS = {
        "simple": 0.3,  # 30% of model budget (typo fixes, docs)
        "medium": 0.6,  # 60% of model budget (functions, refactors)
        "complex": 0.9,  # 90% of model budget (features, auth)
        "critical": 1.0,  # 100% of model budget (security, payments)
    }

    # Budget Allocation Ratios
    ALLOCATION_RATIOS = {
        "core": 0.3,  # 30% for core guardrails (always applicable)
        "agents": 0.4,  # 40% for agent-specific rules
        "specialized": 0.2,  # 20% for task-specific guardrails
        "learned": 0.1,  # 10% for dynamic learned rules
    }

    def __init__(self):
        """Initialize budget manager."""
        logger.debug("ContextBudgetManager initialized")

    def get_budget(self, model: str, task_complexity: str) -> int:
        """Calculate optimal budget for model and task complexity.

        Args:
            model: LLM model name
            task_complexity: Task complexity level (simple/medium/complex/critical)

        Returns:
            Optimal token budget for the task
        """
        # Normalize model name (handle variations)
        model_key = self._normalize_model_name(model)

        # Get base model budget
        base_budget = self.MODEL_BUDGETS.get(model_key, self.MODEL_BUDGETS["default"])

        # Apply complexity multiplier
        multiplier = self.COMPLEXITY_MULTIPLIERS.get(task_complexity, 0.6)

        # Calculate final budget
        budget = int(base_budget * multiplier)

        logger.info(
            "Budget calculated",
            model=model,
            model_key=model_key,
            task_complexity=task_complexity,
            base_budget=base_budget,
            multiplier=multiplier,
            final_budget=budget,
        )

        return budget

    def allocate_budget(self, total_budget: int) -> Dict[str, int]:
        """Allocate total budget across guardrail categories.

        Args:
            total_budget: Total token budget to allocate

        Returns:
            Dictionary mapping category to allocated tokens
        """
        allocation = {
            "core": int(total_budget * self.ALLOCATION_RATIOS["core"]),
            "agents": int(total_budget * self.ALLOCATION_RATIOS["agents"]),
            "specialized": int(total_budget * self.ALLOCATION_RATIOS["specialized"]),
            "learned": int(total_budget * self.ALLOCATION_RATIOS["learned"]),
        }

        # Ensure total matches (handle rounding)
        allocated_total = sum(allocation.values())
        if allocated_total < total_budget:
            # Add remainder to core (most important)
            allocation["core"] += total_budget - allocated_total

        logger.debug(
            "Budget allocated",
            total_budget=total_budget,
            allocation=allocation,
            allocated_total=sum(allocation.values()),
        )

        return allocation

    def adjust_for_mode(self, budget: int, mode: str) -> int:
        """Adjust budget based on operating mode.

        Args:
            budget: Base budget
            mode: Operating mode (standard or strict)

        Returns:
            Adjusted budget
        """
        if mode == "strict":
            # Increase budget by 30% for strict mode (more validation)
            adjusted = int(budget * 1.3)
            logger.debug(
                "Budget adjusted for strict mode",
                original=budget,
                adjusted=adjusted,
                increase_pct=30,
            )
            return adjusted
        else:
            return budget

    def _normalize_model_name(self, model: str) -> str:
        """Normalize model name to match budget keys.

        Args:
            model: Original model name

        Returns:
            Normalized model name
        """
        model_lower = model.lower()

        # Claude models
        if "opus" in model_lower:
            return "claude-opus-4"
        elif "sonnet" in model_lower:
            return "claude-sonnet-4"
        elif "haiku" in model_lower:
            return "claude-haiku"

        # OpenAI models
        elif "gpt-4-turbo" in model_lower or "gpt-4-1106" in model_lower:
            return "gpt-4-turbo"
        elif "gpt-4" in model_lower:
            return "gpt-4"
        elif "gpt-3.5" in model_lower or "gpt-35" in model_lower:
            return "gpt-3.5-turbo"

        # Google models
        elif "gemini-ultra" in model_lower:
            return "gemini-ultra"
        elif "gemini" in model_lower:
            return "gemini-pro"

        # Default
        else:
            logger.warning(
                "Unknown model, using default budget", model=model, default="default"
            )
            return "default"

    def get_model_info(self, model: str) -> Dict[str, any]:
        """Get model budget information.

        Args:
            model: Model name

        Returns:
            Dictionary with model budget info
        """
        normalized = self._normalize_model_name(model)
        base_budget = self.MODEL_BUDGETS.get(normalized, self.MODEL_BUDGETS["default"])

        return {
            "model": model,
            "normalized_name": normalized,
            "base_budget": base_budget,
            "complexity_budgets": {
                complexity: int(base_budget * multiplier)
                for complexity, multiplier in self.COMPLEXITY_MULTIPLIERS.items()
            },
        }

    def estimate_tokens(self, text: str, chars_per_token: int = 4) -> int:
        """Estimate token count from text.

        Args:
            text: Input text
            chars_per_token: Average characters per token (default: 4)

        Returns:
            Estimated token count
        """
        return len(text) // chars_per_token

    def validate_allocation(
        self, allocation: Dict[str, int], total_budget: int
    ) -> bool:
        """Validate that allocation doesn't exceed budget.

        Args:
            allocation: Allocation dictionary
            total_budget: Total available budget

        Returns:
            True if allocation is valid
        """
        allocated_total = sum(allocation.values())

        if allocated_total > total_budget:
            logger.warning(
                "Allocation exceeds budget",
                allocated=allocated_total,
                budget=total_budget,
                excess=allocated_total - total_budget,
            )
            return False

        return True
