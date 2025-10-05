#!/usr/bin/env python3
"""Test and validate agent summary token counts"""

import tiktoken
from pathlib import Path

AGENTS_PATH = Path.home() / ".guardrail" / "guardrails" / "agents"

AGENTS = [
    "orchestrator",
    "business-analyst",
    "cold-blooded-architect",
    "ux-ui-designer",
    "dba",
    "ruthless-coder",
    "ruthless-tester",
    "support-debug-hunter",
    "secops-engineer",
    "sre-ops",
    "standards-oracle",
    "merciless-evaluator",
    "documentation-codifier",
]

def count_tokens(text: str) -> int:
    """Count tokens using cl100k_base encoding (GPT-4)"""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def test_agent_files():
    """Test all agent files and report token counts"""
    print("🧪 Testing Agent Summary Token Counts\n")
    print("=" * 70)

    total_summary_tokens = 0
    total_checklist_tokens = 0
    total_full_tokens = 0

    issues = []

    for agent in AGENTS:
        agent_dir = AGENTS_PATH / agent

        # Test summary
        summary_file = agent_dir / "summary.md"
        if summary_file.exists():
            content = summary_file.read_text()
            tokens = count_tokens(content)
            total_summary_tokens += tokens

            status = "✅" if tokens <= 400 else "❌"
            print(f"{status} {agent}/summary.md: {tokens} tokens (limit: 400)")

            if tokens > 400:
                issues.append(f"{agent}/summary.md exceeds limit: {tokens} tokens")
        else:
            print(f"❌ {agent}/summary.md: MISSING")
            issues.append(f"{agent}/summary.md is missing")

        # Test checklist
        checklist_file = agent_dir / "checklist.md"
        if checklist_file.exists():
            content = checklist_file.read_text()
            tokens = count_tokens(content)
            total_checklist_tokens += tokens

            status = "✅" if tokens <= 200 else "❌"
            print(f"{status} {agent}/checklist.md: {tokens} tokens (limit: 200)")

            if tokens > 200:
                issues.append(f"{agent}/checklist.md exceeds limit: {tokens} tokens")
        else:
            print(f"❌ {agent}/checklist.md: MISSING")
            issues.append(f"{agent}/checklist.md is missing")

        # Count full version for comparison
        full_file = agent_dir / "full.md"
        if full_file.exists():
            content = full_file.read_text()
            tokens = count_tokens(content)
            total_full_tokens += tokens
            print(f"ℹ️  {agent}/full.md: {tokens} tokens (original)")

        print("-" * 70)

    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY STATISTICS")
    print("=" * 70)
    print(f"Total agents: {len(AGENTS)}")
    print(f"\nToken counts:")
    print(f"  Full versions:     {total_full_tokens:,} tokens")
    print(f"  Summary versions:  {total_summary_tokens:,} tokens")
    print(f"  Checklist versions: {total_checklist_tokens:,} tokens")
    print(f"\nToken savings:")
    print(f"  vs Full: {total_full_tokens - total_summary_tokens:,} tokens ({((total_full_tokens - total_summary_tokens) / total_full_tokens * 100):.1f}%)")

    # Issues
    if issues:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✅ All tests passed!")
        return True

if __name__ == "__main__":
    success = test_agent_files()
    exit(0 if success else 1)
