#!/usr/bin/env python3
"""Test and validate core guardrail token counts"""

import tiktoken
from pathlib import Path

GUARDRAILS_PATH = Path.home() / ".guardrail" / "guardrails"

CORE_FILES = {
    "core/always.md": 500,
    "core/security_baseline.md": 300,
    "core/testing_baseline.md": 300,
}

SPECIALIZED_FILES = {
    "specialized/auth_security.md": 600,
    "specialized/database_design.md": 600,
    "specialized/api_patterns.md": 600,
    "specialized/ui_accessibility.md": 600,
    "specialized/compliance_gdpr.md": 600,
    "specialized/deployment_ops.md": 600,
}

def count_tokens(text: str) -> int:
    """Count tokens using cl100k_base encoding (GPT-4)"""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def test_guardrail_files():
    """Test all guardrail files and report token counts"""
    print("🧪 Testing Core Guardrail Token Counts\n")
    print("=" * 70)

    total_core_tokens = 0
    total_specialized_tokens = 0
    issues = []

    # Test core files
    print("\n📋 Core Guardrails:")
    print("-" * 70)
    for filepath, limit in CORE_FILES.items():
        file_path = GUARDRAILS_PATH / filepath

        if file_path.exists():
            content = file_path.read_text()
            tokens = count_tokens(content)
            total_core_tokens += tokens

            status = "✅" if tokens <= limit else "❌"
            print(f"{status} {filepath}: {tokens} tokens (limit: {limit})")

            if tokens > limit:
                issues.append(f"{filepath} exceeds limit: {tokens} tokens")
        else:
            print(f"❌ {filepath}: MISSING")
            issues.append(f"{filepath} is missing")

    # Test specialized files
    print("\n🎯 Specialized Modules:")
    print("-" * 70)
    for filepath, limit in SPECIALIZED_FILES.items():
        file_path = GUARDRAILS_PATH / filepath

        if file_path.exists():
            content = file_path.read_text()
            tokens = count_tokens(content)
            total_specialized_tokens += tokens

            status = "✅" if tokens <= limit else "❌"
            print(f"{status} {filepath}: {tokens} tokens (limit: {limit})")

            if tokens > limit:
                issues.append(f"{filepath} exceeds limit: {tokens} tokens")
        else:
            print(f"❌ {filepath}: MISSING")
            issues.append(f"{filepath} is missing")

    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY STATISTICS")
    print("=" * 70)

    total_files = len(CORE_FILES) + len(SPECIALIZED_FILES)
    core_limit = sum(CORE_FILES.values())
    specialized_limit = sum(SPECIALIZED_FILES.values())
    total_limit = core_limit + specialized_limit

    print(f"Total files: {total_files}")
    print(f"\nToken counts:")
    print(f"  Core files:        {total_core_tokens:,} / {core_limit:,} tokens")
    print(f"  Specialized files: {total_specialized_tokens:,} / {specialized_limit:,} tokens")
    print(f"  Total:            {total_core_tokens + total_specialized_tokens:,} / {total_limit:,} tokens")

    usage_percent = ((total_core_tokens + total_specialized_tokens) / total_limit * 100)
    print(f"\nBudget usage: {usage_percent:.1f}%")

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
    success = test_guardrail_files()
    exit(0 if success else 1)
