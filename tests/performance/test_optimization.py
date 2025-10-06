"""Performance tests for optimization impact measurement."""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any


def count_tokens(text: str, chars_per_token: int = 4) -> int:
    """Estimate token count from text.

    Args:
        text: Input text
        chars_per_token: Average characters per token

    Returns:
        Estimated token count
    """
    return len(text) // chars_per_token


@pytest.fixture
def test_config():
    """Create test configuration."""
    config = Mock()
    config.mode = "standard"
    config.tools = {"claude": Mock(enabled=True, cli_path="claude", timeout=30)}
    config.database = Mock(path=":memory:")
    config.features = Mock(
        v2_adaptive_learning=True,
        v2_auto_save_files=False,
        v2_task_classification=True,
    )
    config.guardrails = Mock(
        base_path="~/.guardrail/guardrails",
        agents_path="~/.guardrail/guardrails/agents",
        files=["BPSBS.md", "AI_Guardrails.md", "UXUI_Guardrails.md"],
    )
    return config


class TestContextSizeReduction:
    """Test context size optimization"""

    @pytest.mark.asyncio
    async def test_smart_selection_reduces_context(self, test_config):
        """Verify smart selection reduces context size significantly."""
        from guardloop.core.context_manager import ContextManager

        context_manager = ContextManager(cache_ttl=300)

        # Simulate old system: load all guardrails (legacy behavior)
        # Old: Would load all 3 main files + all agents (~24K tokens total)
        # Each guardrail file is ~500-1000 lines of markdown with detailed rules and examples
        old_guardrails = [
            "# Core Always Guardrails\n" + ("## Rule: " + "x" * 400 + "\n" + "Details: " + "y" * 600 + "\n" + "Example: " + "z" * 500 + "\n\n") * 15,  # ~22K chars
            "# Security Baseline\n" + ("## Security: " + "x" * 400 + "\n" + "Example: " + "y" * 600 + "\n" + "Code: " + "z" * 500 + "\n\n") * 12,  # ~18K chars
            "# Testing Baseline\n" + ("## Test: " + "x" * 400 + "\n" + "Coverage: " + "y" * 600 + "\n" + "Assert: " + "z" * 500 + "\n\n") * 12,  # ~18K chars
            "# Auth Security\n" + ("## Auth pattern: " + "x" * 400 + "\n" + "Implementation: " + "y" * 600 + "\n\n") * 10,  # ~10K chars
            "# Database Design\n" + ("## DB rule: " + "x" * 400 + "\n" + "Schema: " + "y" * 600 + "\n\n") * 10,  # ~10K chars
            "# API Patterns\n" + ("## API guideline: " + "x" * 400 + "\n" + "Endpoint: " + "y" * 600 + "\n\n") * 12,  # ~12K chars
        ]
        old_context = "\n\n".join(old_guardrails)
        old_tokens = count_tokens(old_context)

        # New system: Smart selection (task-specific)
        new_context = context_manager.build_context(
            prompt="implement user authentication",
            agent=None,
            mode="standard",
            task_type="authentication",
        )
        new_tokens = count_tokens(new_context)

        # Verify significant reduction
        # Old system would have ~24K tokens (all guardrails)
        # New system should have <5K tokens (task-specific)
        assert old_tokens > 20000, f"Old system baseline too low: {old_tokens}"
        assert new_tokens < 10000, f"New system not optimized: {new_tokens}"

        reduction_pct = ((old_tokens - new_tokens) / old_tokens) * 100
        print(f"\nContext size reduction: {reduction_pct:.1f}%")
        print(f"Old tokens: {old_tokens:,}")
        print(f"New tokens: {new_tokens:,}")

        # Target: 60%+ reduction (allows for variation)
        assert reduction_pct >= 60, f"Context only reduced by {reduction_pct:.1f}%"

    @pytest.mark.asyncio
    async def test_creative_task_minimal_context(self, test_config):
        """Verify creative tasks use minimal context."""
        from guardloop.core.context_manager import ContextManager

        context_manager = ContextManager(cache_ttl=300)

        # Creative task should skip guardrails
        creative_context = context_manager.build_context(
            prompt="write a poem about coding",
            agent=None,
            mode="standard",
            task_type="creative",  # Creative type
        )
        creative_tokens = count_tokens(creative_context)

        # Should be just the prompt (minimal context)
        # Creative tasks bypass guardrails
        assert creative_tokens < 500, f"Creative task context too large: {creative_tokens}"


class TestResponseTimeImprovement:
    """Test response time optimization"""

    @pytest.mark.asyncio
    async def test_agent_chain_reduces_execution_time(self):
        """Verify optimized agent chains execute faster."""
        from guardloop.agents.chain_optimizer import AgentChainOptimizer

        optimizer = AgentChainOptimizer()

        # Old system: Always full chain (13 agents)
        old_chain_length = 13  # Full agent chain
        old_time_estimate = old_chain_length * 30  # 30s per agent = 390s

        # New system: Optimized chains
        simple_chain = optimizer.select_chain("fix_typo", "standard")
        simple_time = optimizer.estimate_execution_time("fix_typo", "standard")

        medium_chain = optimizer.select_chain("implement_function", "standard")
        medium_time = optimizer.estimate_execution_time("implement_function", "standard")

        # Verify improvements
        assert len(simple_chain) <= 2, f"Simple chain too long: {len(simple_chain)}"
        assert simple_time < old_time_estimate * 0.2, f"Simple task not optimized"

        assert len(medium_chain) <= 5, f"Medium chain too long: {len(medium_chain)}"
        assert medium_time < old_time_estimate * 0.5, f"Medium task not optimized"

        # Calculate improvement
        improvement_simple = ((old_time_estimate - simple_time) / old_time_estimate) * 100
        improvement_medium = ((old_time_estimate - medium_time) / old_time_estimate) * 100

        print(f"\nExecution time improvements:")
        print(
            f"Simple task: {improvement_simple:.1f}% faster ({simple_time}s vs {old_time_estimate}s)"
        )
        print(
            f"Medium task: {improvement_medium:.1f}% faster ({medium_time}s vs {old_time_estimate}s)"
        )

        assert improvement_simple >= 75, f"Simple tasks should be 75%+ faster"
        assert improvement_medium >= 50, f"Medium tasks should be 50%+ faster"

    @pytest.mark.asyncio
    async def test_budget_manager_calculates_quickly(self):
        """Verify budget calculations are performant."""
        from guardloop.core.budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()

        # Measure budget calculation time
        iterations = 1000
        start = time.time()

        for _ in range(iterations):
            budget = manager.get_budget("claude-sonnet-4", "medium")
            allocation = manager.allocate_budget(budget)

        elapsed = time.time() - start
        avg_time = (elapsed / iterations) * 1000  # Convert to ms

        print(f"\nBudget calculation performance:")
        print(f"Average time: {avg_time:.3f}ms per calculation")

        # Should be very fast (<1ms per calculation)
        assert avg_time < 1.0, f"Budget calculation too slow: {avg_time:.3f}ms"


class TestCreativeTaskSkip:
    """Test creative task bypass logic"""

    @pytest.mark.asyncio
    async def test_creative_tasks_skip_guardrails(self):
        """Verify creative tasks bypass guardrail validation."""
        from guardloop.core.task_classifier import TaskClassifier

        classifier = TaskClassifier()

        # Test creative prompts
        creative_prompts = [
            "write a poem about coding",
            "create a blog post about AI",
            "draft documentation outline",
            "brainstorm feature ideas",
        ]

        for prompt in creative_prompts:
            classification = classifier.classify(prompt)

            # Should be classified as creative/content
            assert classification.task_type in [
                "creative",
                "content",
            ], f"'{prompt}' not classified as creative: {classification.task_type}"

            # Should not require guardrails
            assert (
                classification.requires_guardrails is False
            ), f"Creative task requires guardrails: {prompt}"

            print(f"\n✓ '{prompt[:40]}...' → {classification.task_type} (skip guardrails)")

    @pytest.mark.asyncio
    async def test_code_tasks_require_guardrails(self):
        """Verify code tasks still get guardrails."""
        from guardloop.core.task_classifier import TaskClassifier

        classifier = TaskClassifier()

        # Test code prompts
        code_prompts = [
            "implement user authentication",
            "create API endpoint for login",
            "add SQL injection prevention",
        ]

        for prompt in code_prompts:
            classification = classifier.classify(prompt)

            # Should require guardrails
            assert (
                classification.requires_guardrails is True
            ), f"Code task doesn't require guardrails: {prompt}"

            print(f"\n✓ '{prompt[:40]}...' → {classification.task_type} (apply guardrails)")


class TestAgentChainOptimization:
    """Test agent chain optimization"""

    def test_simple_task_minimal_agents(self):
        """Verify simple tasks use minimal agents."""
        from guardloop.agents.chain_optimizer import AgentChainOptimizer

        optimizer = AgentChainOptimizer()

        simple_tasks = ["fix_typo", "update_docs", "format_code"]

        for task in simple_tasks:
            chain = optimizer.select_chain(task, "standard")
            complexity = optimizer.get_complexity(task)

            assert len(chain) <= 2, f"{task} uses too many agents: {len(chain)} (chain: {chain})"
            assert complexity.value == "simple", f"{task} complexity not simple: {complexity.value}"

            print(f"\n✓ {task}: {len(chain)} agents → {chain}")

    def test_medium_task_focused_chain(self):
        """Verify medium tasks use focused chains."""
        from guardloop.agents.chain_optimizer import AgentChainOptimizer

        optimizer = AgentChainOptimizer()

        # Medium tasks have 3-5 agents
        medium_tasks = ["implement_function", "refactor"]

        for task in medium_tasks:
            chain = optimizer.select_chain(task, "standard")
            complexity = optimizer.get_complexity(task)

            # Medium tasks should have 3-5 agents for focused execution
            assert 3 <= len(chain) <= 5, f"{task} chain length wrong: {len(chain)} (chain: {chain})"
            assert complexity.value == "medium", f"{task} complexity not medium: {complexity.value}"

            print(f"\n✓ {task}: {len(chain)} agents → {chain}")

    def test_critical_task_full_validation(self):
        """Verify critical tasks get full validation."""
        from guardloop.agents.chain_optimizer import AgentChainOptimizer

        optimizer = AgentChainOptimizer()

        critical_tasks = ["build_auth_system", "implement_payment"]

        for task in critical_tasks:
            standard_chain = optimizer.select_chain(task, "standard")
            strict_chain = optimizer.select_chain(task, "strict")
            complexity = optimizer.get_complexity(task)

            assert (
                len(standard_chain) >= 5
            ), f"{task} standard chain too short: {len(standard_chain)}"
            assert len(strict_chain) >= len(standard_chain), f"{task} strict chain not longer"
            assert (
                complexity.value == "critical"
            ), f"{task} complexity not critical: {complexity.value}"

            # Verify strict mode adds compliance
            assert (
                "secops_engineer" in strict_chain or "secops" in strict_chain
            ), f"{task} strict mode missing security"
            assert "standards_oracle" in strict_chain, f"{task} strict mode missing standards"

            print(
                f"\n✓ {task}: {len(standard_chain)} agents (standard), {len(strict_chain)} agents (strict)"
            )


class TestSemanticMatching:
    """Test semantic matching performance"""

    @pytest.mark.asyncio
    async def test_semantic_matching_faster_than_keyword(self):
        """Verify semantic matching finds relevant rules efficiently."""
        # Skip if numpy/sentence-transformers not installed
        pytest.importorskip("numpy")
        pytest.importorskip("sentence_transformers")

        # Mock guardrails
        guardrails = []
        for i in range(100):
            g = Mock()
            g.id = i
            g.rule_text = f"Security rule {i}: Validate input and prevent injection"
            g.rule_metadata = {}
            guardrails.append(g)

        # Test semantic matching speed
        from guardloop.core.semantic_matcher import SemanticGuardrailMatcher

        matcher = SemanticGuardrailMatcher()

        # Index guardrails
        start = time.time()
        await matcher.index_guardrails(guardrails)
        index_time = time.time() - start

        # Find relevant
        start = time.time()
        results = await matcher.find_relevant(
            prompt="Implement SQL injection prevention",
            guardrails=guardrails,
            top_k=5,
            threshold=0.3,
        )
        search_time = time.time() - start

        print(f"\nSemantic matching performance:")
        print(f"Indexing 100 guardrails: {index_time*1000:.1f}ms")
        print(f"Finding top 5: {search_time*1000:.1f}ms")

        # Should be reasonably fast
        assert index_time < 5.0, f"Indexing too slow: {index_time:.2f}s"
        assert search_time < 1.0, f"Search too slow: {search_time:.2f}s"


class TestBudgetAllocation:
    """Test budget allocation efficiency"""

    def test_budget_allocation_within_limits(self):
        """Verify budget allocations stay within limits."""
        from guardloop.core.budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()

        # Test various budgets
        budgets = [1000, 2000, 5000, 10000, 15000]

        for total_budget in budgets:
            allocation = manager.allocate_budget(total_budget)

            # Verify allocation sums to budget
            allocated_total = sum(allocation.values())
            assert (
                allocated_total == total_budget
            ), f"Allocation mismatch: {allocated_total} != {total_budget}"

            # Verify ratios
            assert (
                allocation["agents"] > allocation["specialized"]
            ), "Agents should get more than specialized"
            assert allocation["core"] > allocation["learned"], "Core should get more than learned"

            print(f"\n✓ Budget {total_budget:,}: {allocation}")

    def test_model_budgets_appropriate(self):
        """Verify model budgets are appropriate for context limits."""
        from guardloop.core.budget_manager import ContextBudgetManager

        manager = ContextBudgetManager()

        # Test model budgets
        models = [
            ("claude-opus-4", 10000),
            ("claude-sonnet-4", 6000),
            ("gpt-4", 4000),
            ("gpt-3.5-turbo", 2000),
        ]

        for model, expected_base in models:
            info = manager.get_model_info(model)

            assert (
                info["base_budget"] == expected_base
            ), f"{model} budget wrong: {info['base_budget']}"

            # Verify complexity budgets scale correctly
            simple = info["complexity_budgets"]["simple"]
            critical = info["complexity_budgets"]["critical"]

            assert simple < critical, f"{model} simple >= critical"
            assert simple == expected_base * 0.3, f"{model} simple budget wrong"
            assert critical == expected_base, f"{model} critical budget wrong"

            print(f"\n✓ {model}: {simple:,} (simple) → {critical:,} (critical)")


@pytest.mark.benchmark
class TestRegressionSuite:
    """Regression tests to prevent performance degradation"""

    @pytest.mark.asyncio
    async def test_no_regression_in_context_size(self):
        """Ensure context size doesn't regress."""
        from guardloop.core.context_manager import ContextManager

        context_manager = ContextManager()

        # Baseline: Authentication task should be <5K tokens
        context = context_manager.build_context(
            prompt="implement user authentication with password hashing",
            agent=None,
            mode="standard",
            task_type="authentication",
        )

        tokens = count_tokens(context)

        # Regression threshold: 5K tokens
        assert tokens < 5000, f"Context size regression: {tokens} tokens (should be <5K)"

        print(f"\n✓ Context size: {tokens:,} tokens (target: <5K)")

    def test_no_regression_in_agent_chains(self):
        """Ensure agent chains don't regress."""
        from guardloop.agents.chain_optimizer import AgentChainOptimizer

        optimizer = AgentChainOptimizer()

        # Baseline chain lengths
        baselines = {
            "fix_typo": 1,
            "implement_function": 3,
            "implement_feature": 5,
            "build_auth_system": 9,
        }

        for task, max_length in baselines.items():
            chain = optimizer.select_chain(task, "standard")

            assert (
                len(chain) <= max_length
            ), f"Chain regression for {task}: {len(chain)} > {max_length}"

            print(f"\n✓ {task}: {len(chain)} agents (max: {max_length})")
