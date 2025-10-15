"""Tests for SmartGuardrailSelector"""

import pytest
from pathlib import Path

from guardloop.core.smart_selector import SmartGuardrailSelector


@pytest.fixture
def selector():
    """Create selector with test guardrails path"""
    guardrails_path = Path.home() / ".guardrail" / "guardrails"
    return SmartGuardrailSelector(guardrails_path)


class TestTaskClassification:
    """Test task type classification from prompts"""

    def test_classify_authentication_task(self, selector):
        prompt = "Implement MFA authentication with Azure AD"
        task_type = selector.classify_task_type(prompt)
        assert task_type in ["authentication", "security"]

    def test_classify_database_task(self, selector):
        prompt = "Design database schema with foreign key constraints"
        task_type = selector.classify_task_type(prompt)
        assert task_type == "database"

    def test_classify_api_task(self, selector):
        prompt = "Create REST API endpoints for user management"
        task_type = selector.classify_task_type(prompt)
        assert task_type == "api"

    def test_classify_ui_task(self, selector):
        prompt = "Build accessible React component with ARIA labels"
        task_type = selector.classify_task_type(prompt)
        assert task_type in ["ui", "component", "accessibility"]

    def test_classify_creative_task(self, selector):
        prompt = "Brainstorm ideas for new feature concepts"
        task_type = selector.classify_task_type(prompt)
        assert task_type == "brainstorm"

    def test_no_classification_for_generic_prompt(self, selector):
        prompt = "Write some code"
        task_type = selector.classify_task_type(prompt)
        # Should return None or default
        assert task_type is None or task_type == "creative"


class TestGuardrailSelection:
    """Test guardrail selection logic"""

    def test_always_includes_core_always(self, selector):
        selected = selector.select_guardrails(prompt="Do something")
        assert "core/always.md" in selected

    def test_task_specific_selection_auth(self, selector):
        selected = selector.select_guardrails(task_type="authentication", prompt="Implement MFA")
        assert "core/always.md" in selected
        assert "core/security_baseline.md" in selected
        assert "specialized/auth_security.md" in selected

    def test_task_specific_selection_database(self, selector):
        selected = selector.select_guardrails(task_type="database", prompt="Design schema")
        assert "core/always.md" in selected
        assert "specialized/database_design.md" in selected

    def test_keyword_based_selection(self, selector):
        prompt = "Create API with JWT authentication and database schema"
        selected = selector.select_guardrails(prompt=prompt)

        # Should include API, auth, and database guardrails
        assert "core/always.md" in selected
        # At least one of the specialized modules
        specialized = [f for f in selected if f.startswith("specialized/")]
        assert len(specialized) > 0

    def test_creative_mode_minimal_guardrails(self, selector):
        prompt = "Brainstorm creative ideas for UI redesign"
        selected = selector.select_guardrails(prompt=prompt)

        # Creative tasks should only have core/always.md
        assert selected == ["core/always.md"]

    def test_strict_mode_includes_all_core(self, selector):
        selected = selector.select_guardrails(prompt="Write code", mode="strict", token_budget=2000)

        # Should include all core files in strict mode
        assert "core/always.md" in selected
        assert "core/security_baseline.md" in selected
        assert "core/testing_baseline.md" in selected


class TestTokenBudgetEnforcement:
    """Test token budget enforcement"""

    def test_respects_token_budget(self, selector):
        # Very low budget - should only include core/always.md (354 tokens)
        selected = selector.select_guardrails(
            prompt="Implement authentication with database and API",
            token_budget=400,
        )

        total_tokens = selector.get_token_estimate(selected)
        assert total_tokens <= 400
        assert "core/always.md" in selected

    def test_uses_available_budget(self, selector):
        # Generous budget - should include multiple guardrails
        selected = selector.select_guardrails(
            prompt="Implement authentication with database and API",
            token_budget=2000,
        )

        total_tokens = selector.get_token_estimate(selected)
        assert total_tokens <= 2000
        assert len(selected) > 1  # Should include multiple files

    def test_prioritizes_by_relevance(self, selector):
        # With limited budget, should prioritize most relevant
        selected = selector.select_guardrails(
            prompt="Implement GDPR compliance",
            token_budget=800,  # Enough for core/always + one specialized
        )

        total_tokens = selector.get_token_estimate(selected)
        assert total_tokens <= 800
        assert "core/always.md" in selected
        assert "specialized/compliance_gdpr.md" in selected


class TestTokenEstimation:
    """Test token estimation"""

    def test_get_token_estimate_single_file(self, selector):
        tokens = selector.get_token_estimate(["core/always.md"])
        assert tokens == 354

    def test_get_token_estimate_multiple_files(self, selector):
        files = ["core/always.md", "core/security_baseline.md"]
        tokens = selector.get_token_estimate(files)
        assert tokens == 354 + 168

    def test_get_token_estimate_unknown_file(self, selector):
        # Unknown files should default to 500 tokens
        tokens = selector.get_token_estimate(["unknown/file.md"])
        assert tokens == 500


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_prompt(self, selector):
        selected = selector.select_guardrails(prompt="")
        # Should at least include core/always.md
        assert len(selected) >= 1
        assert "core/always.md" in selected

    def test_invalid_task_type(self, selector):
        selected = selector.select_guardrails(task_type="invalid_type_xyz", prompt="Do something")
        # Should fall back to keyword matching
        assert "core/always.md" in selected

    def test_zero_token_budget(self, selector):
        # Even with 0 budget, should include minimal guardrails
        selected = selector.select_guardrails(prompt="Do something", token_budget=0)
        # Should gracefully handle or include core/always.md
        assert len(selected) >= 1
        assert "core/always.md" in selected
