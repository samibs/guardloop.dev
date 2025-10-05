#!/usr/bin/env python3
"""Benchmark script for measuring optimization impact."""

import time
import statistics
from typing import Dict, List, Tuple
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def count_tokens(text: str) -> int:
    """Estimate token count."""
    return len(text) // 4


def benchmark_context_size() -> Dict[str, float]:
    """Benchmark context size reduction."""
    from guardloop.core.context_manager import ContextManager

    context_manager = ContextManager()

    results = {}

    # Test different task types
    test_cases = [
        ("authentication", "implement user authentication with MFA"),
        ("database", "create database schema for user management"),
        ("api", "implement REST API endpoint for login"),
        ("creative", "write a poem about coding"),
    ]

    for task_type, prompt in test_cases:
        context = context_manager.build_context(
            prompt=prompt, agent=None, mode="standard", task_type=task_type
        )

        tokens = count_tokens(context)
        results[task_type] = tokens

        print(f"  {task_type:15s}: {tokens:6,} tokens")

    return results


def benchmark_agent_chains() -> Dict[str, int]:
    """Benchmark agent chain optimization."""
    from guardloop.agents.chain_optimizer import AgentChainOptimizer

    optimizer = AgentChainOptimizer()

    results = {}

    test_tasks = [
        "fix_typo",
        "update_docs",
        "implement_function",
        "fix_bug",
        "implement_feature",
        "database_design",
        "build_auth_system",
    ]

    for task in test_tasks:
        chain = optimizer.select_chain(task, "standard")
        complexity = optimizer.get_complexity(task)
        exec_time = optimizer.estimate_execution_time(task, "standard")

        results[task] = len(chain)

        print(
            f"  {task:20s}: {len(chain)} agents, {complexity.value:8s}, ~{exec_time}s"
        )

    return results


def benchmark_semantic_matching() -> Dict[str, float]:
    """Benchmark semantic matching performance."""
    from guardloop.core.semantic_matcher import SemanticGuardrailMatcher
    from unittest.mock import Mock

    matcher = SemanticGuardrailMatcher()

    # Create mock guardrails
    guardrails = []
    for i in range(50):
        g = Mock()
        g.id = i
        g.rule_text = f"Security rule {i}: Validate and sanitize user input"
        guardrails.append(g)

    results = {}

    # Measure indexing time
    import asyncio

    start = time.time()
    asyncio.run(matcher.index_guardrails(guardrails))
    index_time = time.time() - start

    results["index_time_ms"] = index_time * 1000

    # Measure search time (multiple iterations)
    search_times = []
    for _ in range(10):
        start = time.time()
        asyncio.run(
            matcher.find_relevant(
                prompt="Implement SQL injection prevention",
                guardrails=guardrails,
                top_k=5,
                threshold=0.3,
            )
        )
        search_times.append(time.time() - start)

    results["avg_search_ms"] = statistics.mean(search_times) * 1000
    results["max_search_ms"] = max(search_times) * 1000

    print(f"  Indexing 50 rules: {results['index_time_ms']:.1f}ms")
    print(f"  Avg search time:   {results['avg_search_ms']:.1f}ms")
    print(f"  Max search time:   {results['max_search_ms']:.1f}ms")

    return results


def benchmark_budget_allocation() -> Dict[str, float]:
    """Benchmark budget calculation performance."""
    from guardloop.core.budget_manager import ContextBudgetManager

    manager = ContextBudgetManager()

    results = {}

    # Measure budget calculation time
    iterations = 1000
    calc_times = []

    for _ in range(iterations):
        start = time.time()
        budget = manager.get_budget("claude-sonnet-4", "medium")
        allocation = manager.allocate_budget(budget)
        calc_times.append(time.time() - start)

    results["avg_calc_us"] = statistics.mean(calc_times) * 1_000_000  # microseconds
    results["max_calc_us"] = max(calc_times) * 1_000_000

    # Test all models
    models = [
        "claude-opus-4",
        "claude-sonnet-4",
        "gpt-4",
        "gpt-3.5-turbo",
        "gemini-pro",
    ]

    for model in models:
        budget = manager.get_budget(model, "medium")
        results[f"{model}_budget"] = budget

        print(f"  {model:20s}: {budget:6,} tokens (medium complexity)")

    print(f"\n  Avg calculation time: {results['avg_calc_us']:.1f}μs")

    return results


def print_summary(
    context_results: Dict[str, float],
    chain_results: Dict[str, int],
    semantic_results: Dict[str, float],
    budget_results: Dict[str, float],
):
    """Print benchmark summary."""
    print("\n" + "=" * 60)
    print("OPTIMIZATION BENCHMARK SUMMARY")
    print("=" * 60)

    # Context size
    avg_context = statistics.mean(
        [v for k, v in context_results.items() if k != "creative"]
    )
    print(f"\nContext Size:")
    print(f"  Average (code tasks): {avg_context:,.0f} tokens")
    print(f"  Creative tasks:       {context_results.get('creative', 0):,.0f} tokens")
    print(f"  Target:               <5,000 tokens")
    print(f"  Status:               {'✅ PASS' if avg_context < 5000 else '❌ FAIL'}")

    # Agent chains
    avg_chain = statistics.mean(chain_results.values())
    print(f"\nAgent Chains:")
    print(f"  Average agents:       {avg_chain:.1f}")
    print(f"  Simple tasks:         {chain_results.get('fix_typo', 0)} agents")
    print(f"  Critical tasks:       {chain_results.get('build_auth_system', 0)} agents")
    print(f"  Target:               <5 avg")
    print(f"  Status:               {'✅ PASS' if avg_chain < 5 else '❌ FAIL'}")

    # Semantic matching
    print(f"\nSemantic Matching:")
    print(f"  Indexing:             {semantic_results.get('index_time_ms', 0):.1f}ms")
    print(f"  Search (avg):         {semantic_results.get('avg_search_ms', 0):.1f}ms")
    print(f"  Target:               <100ms search")
    print(
        f"  Status:               {'✅ PASS' if semantic_results.get('avg_search_ms', 999) < 100 else '❌ FAIL'}"
    )

    # Budget allocation
    print(f"\nBudget Allocation:")
    print(f"  Calculation time:     {budget_results.get('avg_calc_us', 0):.1f}μs")
    print(f"  Target:               <1ms (1000μs)")
    print(
        f"  Status:               {'✅ PASS' if budget_results.get('avg_calc_us', 9999) < 1000 else '❌ FAIL'}"
    )

    # Overall metrics
    print(f"\n" + "=" * 60)
    print("OVERALL OPTIMIZATION METRICS")
    print("=" * 60)

    metrics = [
        ("Context Size", avg_context < 5000),
        ("Agent Efficiency", avg_chain < 5),
        ("Semantic Speed", semantic_results.get("avg_search_ms", 999) < 100),
        ("Budget Speed", budget_results.get("avg_calc_us", 9999) < 1000),
    ]

    passed = sum(1 for _, status in metrics if status)
    total = len(metrics)

    for metric, status in metrics:
        print(f"  {metric:20s}: {'✅ PASS' if status else '❌ FAIL'}")

    print(f"\n  TOTAL: {passed}/{total} metrics passed")
    print("=" * 60)


def main():
    """Run all benchmarks."""
    print("=" * 60)
    print("GUARDRAIL OPTIMIZATION BENCHMARKS")
    print("=" * 60)

    print("\n1. Context Size Reduction")
    print("-" * 60)
    context_results = benchmark_context_size()

    print("\n2. Agent Chain Optimization")
    print("-" * 60)
    chain_results = benchmark_agent_chains()

    print("\n3. Semantic Matching Performance")
    print("-" * 60)
    semantic_results = benchmark_semantic_matching()

    print("\n4. Budget Allocation Performance")
    print("-" * 60)
    budget_results = benchmark_budget_allocation()

    # Print summary
    print_summary(context_results, chain_results, semantic_results, budget_results)


if __name__ == "__main__":
    main()
