"""Smart guardrail selection based on task type and token budget"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class GuardrailFile:
    """Represents a guardrail file with metadata"""

    path: Path
    category: str  # core or specialized
    name: str
    keywords: Set[str]
    token_estimate: int
    priority: int  # 1=always load, 2=task-specific, 3=optional


class SmartGuardrailSelector:
    """Intelligently selects guardrails based on task type and token budget"""

    # Task type to guardrail mapping
    TASK_GUARDRAIL_MAP = {
        # Authentication/Security tasks
        "authentication": [
            "core/always.md",
            "core/security_baseline.md",
            "specialized/auth_security.md",
        ],
        "security": ["core/always.md", "core/security_baseline.md", "specialized/auth_security.md"],
        "vulnerability": ["core/security_baseline.md", "specialized/auth_security.md"],
        # Database tasks
        "database": ["core/always.md", "specialized/database_design.md"],
        "schema": ["specialized/database_design.md"],
        "migration": ["specialized/database_design.md"],
        # API tasks
        "api": ["core/always.md", "specialized/api_patterns.md"],
        "endpoint": ["specialized/api_patterns.md"],
        "rest": ["specialized/api_patterns.md"],
        # Frontend/UI tasks
        "ui": ["core/always.md", "specialized/ui_accessibility.md"],
        "component": ["specialized/ui_accessibility.md"],
        "frontend": ["specialized/ui_accessibility.md"],
        "accessibility": ["specialized/ui_accessibility.md"],
        # Testing tasks
        "testing": ["core/always.md", "core/testing_baseline.md"],
        "test": ["core/testing_baseline.md"],
        "e2e": ["core/testing_baseline.md"],
        # Compliance tasks
        "gdpr": ["specialized/compliance_gdpr.md"],
        "compliance": ["specialized/compliance_gdpr.md"],
        "privacy": ["specialized/compliance_gdpr.md"],
        # DevOps/Deployment tasks
        "deployment": ["specialized/deployment_ops.md"],
        "ci": ["specialized/deployment_ops.md"],
        "cd": ["specialized/deployment_ops.md"],
        "docker": ["specialized/deployment_ops.md"],
        # Creative/General tasks (minimal guardrails)
        "creative": ["core/always.md"],
        "brainstorm": ["core/always.md"],
        "ideation": ["core/always.md"],
    }

    # Keyword mappings for intelligent detection
    KEYWORD_MAP = {
        "core/always.md": {
            "architecture",
            "testing",
            "security",
            "quality",
            "documentation",
            "compliance",
            "workflow",
            "mandatory",
            "universal",
            "required",
        },
        "core/security_baseline.md": {
            "mfa",
            "azure",
            "rbac",
            "authentication",
            "authorization",
            "audit",
            "security",
            "token",
            "session",
            "permission",
            "access",
        },
        "core/testing_baseline.md": {
            "test",
            "coverage",
            "unit",
            "e2e",
            "mock",
            "assertion",
            "regression",
            "integration",
            "testing",
            "validation",
        },
        "specialized/auth_security.md": {
            "mfa",
            "azure",
            "ad",
            "active directory",
            "rbac",
            "role",
            "permission",
            "jwt",
            "session",
            "oauth",
            "sso",
            "saml",
            "authentication",
            "login",
        },
        "specialized/database_design.md": {
            "database",
            "schema",
            "table",
            "migration",
            "index",
            "constraint",
            "foreign key",
            "normalization",
            "sql",
            "query",
            "transaction",
        },
        "specialized/api_patterns.md": {
            "api",
            "endpoint",
            "rest",
            "http",
            "request",
            "response",
            "json",
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "versioning",
        },
        "specialized/ui_accessibility.md": {
            "ui",
            "component",
            "accessibility",
            "wcag",
            "aria",
            "responsive",
            "mobile",
            "keyboard",
            "screen reader",
            "contrast",
            "semantic",
        },
        "specialized/compliance_gdpr.md": {
            "gdpr",
            "privacy",
            "data protection",
            "consent",
            "retention",
            "erasure",
            "portability",
            "right to access",
            "dpo",
        },
        "specialized/deployment_ops.md": {
            "deployment",
            "ci/cd",
            "pipeline",
            "docker",
            "kubernetes",
            "monitoring",
            "logging",
            "alerting",
            "health check",
            "scaling",
            "backup",
        },
    }

    # Token estimates (from validation)
    TOKEN_ESTIMATES = {
        "core/always.md": 354,
        "core/security_baseline.md": 168,
        "core/testing_baseline.md": 194,
        "specialized/auth_security.md": 312,
        "specialized/database_design.md": 292,
        "specialized/api_patterns.md": 412,
        "specialized/ui_accessibility.md": 423,
        "specialized/compliance_gdpr.md": 405,
        "specialized/deployment_ops.md": 516,
    }

    def __init__(self, guardrails_path: Path):
        """Initialize selector with guardrails directory path

        Args:
            guardrails_path: Path to guardrails directory
        """
        self.guardrails_path = guardrails_path
        self.guardrail_files = self._load_guardrail_metadata()

    def _load_guardrail_metadata(self) -> Dict[str, GuardrailFile]:
        """Load metadata for all guardrail files

        Returns:
            Dictionary mapping file paths to GuardrailFile objects
        """
        files = {}

        for filepath, keywords in self.KEYWORD_MAP.items():
            full_path = self.guardrails_path / filepath
            category = "core" if filepath.startswith("core/") else "specialized"

            # Priority: core/always.md = 1, other core = 2, specialized = 3
            if filepath == "core/always.md":
                priority = 1
            elif category == "core":
                priority = 2
            else:
                priority = 3

            files[filepath] = GuardrailFile(
                path=full_path,
                category=category,
                name=filepath,
                keywords=keywords,
                token_estimate=self.TOKEN_ESTIMATES.get(filepath, 500),
                priority=priority,
            )

        logger.debug("Loaded GuardLoop metadata", count=len(files))
        return files

    def select_guardrails(
        self,
        task_type: Optional[str] = None,
        prompt: str = "",
        mode: str = "standard",
        token_budget: int = 5000,
        model: Optional[str] = None,
        task_complexity: Optional[str] = None,
    ) -> List[str]:
        """Select optimal guardrails based on task and constraints

        Args:
            task_type: Optional task type classification
            prompt: User prompt for keyword analysis
            mode: Operating mode (standard or strict)
            token_budget: Maximum tokens allowed for guardrails (overridden if model provided)
            model: Optional LLM model name for dynamic budget calculation
            task_complexity: Optional task complexity (simple/medium/complex/critical)

        Returns:
            List of guardrail file paths to load (relative to guardrails_path)
        """
        # Dynamic budget calculation if model and complexity provided
        if model and task_complexity:
            from guardloop.core.budget_manager import ContextBudgetManager

            budget_manager = ContextBudgetManager()
            token_budget = budget_manager.get_budget(model, task_complexity)
            token_budget = budget_manager.adjust_for_mode(token_budget, mode)

            logger.info(
                "Dynamic budget calculated",
                model=model,
                complexity=task_complexity,
                mode=mode,
                budget=token_budget,
            )

        selected = set()
        total_tokens = 0

        # Step 1: Always include core/always.md
        always_file = "core/always.md"
        selected.add(always_file)
        total_tokens += self.TOKEN_ESTIMATES.get(always_file, 0)

        logger.debug(
            "Starting guardrail selection",
            task_type=task_type,
            mode=mode,
            token_budget=token_budget,
        )

        # Step 2: Add task-specific guardrails if task_type provided
        if task_type and task_type.lower() in self.TASK_GUARDRAIL_MAP:
            for filepath in self.TASK_GUARDRAIL_MAP[task_type.lower()]:
                if filepath not in selected:
                    tokens = self.TOKEN_ESTIMATES.get(filepath, 500)
                    if total_tokens + tokens <= token_budget:
                        selected.add(filepath)
                        total_tokens += tokens
                        logger.debug("Added task-specific policy", file=filepath, tokens=tokens)

        # Step 3: Keyword-based selection from prompt
        prompt_lower = prompt.lower()
        keyword_matches = []

        for filepath, file_obj in self.guardrail_files.items():
            if filepath in selected:
                continue

            # Count matching keywords
            matches = sum(1 for keyword in file_obj.keywords if keyword in prompt_lower)
            if matches > 0:
                keyword_matches.append((filepath, matches, file_obj.token_estimate))

        # Sort by match count (descending) and token estimate (ascending)
        keyword_matches.sort(key=lambda x: (-x[1], x[2]))

        # Add keyword-matched files within budget
        for filepath, matches, tokens in keyword_matches:
            if total_tokens + tokens <= token_budget:
                selected.add(filepath)
                total_tokens += tokens
                logger.debug(
                    "Added keyword-matched guardrail",
                    file=filepath,
                    matches=matches,
                    tokens=tokens,
                )

        # Step 4: Strict mode adds all core files
        if mode == "strict":
            for filepath, file_obj in self.guardrail_files.items():
                if file_obj.category == "core" and filepath not in selected:
                    tokens = file_obj.token_estimate
                    if total_tokens + tokens <= token_budget:
                        selected.add(filepath)
                        total_tokens += tokens
                        logger.debug("Added core policy (strict mode)", file=filepath)

        # Step 5: Creative tasks - minimal guardrails
        creative_keywords = {"creative", "brainstorm", "ideation", "idea"}
        is_creative = any(kw in prompt_lower for kw in creative_keywords)

        if is_creative and len(selected) > 1:
            # For creative tasks, keep only core/always.md
            selected = {always_file}
            total_tokens = self.TOKEN_ESTIMATES.get(always_file, 0)
            logger.info("Creative task detected - using minimal guardrails")

        selected_list = sorted(selected, key=lambda x: self.guardrail_files[x].priority)

        budget_usage_percent = (
            round(total_tokens / token_budget * 100, 1) if token_budget > 0 else 0
        )
        budget_pct = round(total_tokens / token_budget * 100, 1) if token_budget > 0 else 0
        logger.info(
            "GuardLoop selection complete",
            selected_count=len(selected_list),
            total_tokens=total_tokens,
            budget_usage_percent=budget_usage_percent,
            budget_usage_percent=budget_pct,
        )

        return selected_list

    def get_token_estimate(self, filepaths: List[str]) -> int:
        """Get total token estimate for given guardrail files

        Args:
            filepaths: List of guardrail file paths

        Returns:
            Total estimated tokens
        """
        return sum(self.TOKEN_ESTIMATES.get(fp, 500) for fp in filepaths)

    def classify_task_type(self, prompt: str) -> Optional[str]:
        """Classify task type from prompt keywords

        Args:
            prompt: User prompt to analyze

        Returns:
            Detected task type or None
        """
        prompt_lower = prompt.lower()

        # Count keyword matches for each task type
        task_scores = {}
        for task_type, guardrails in self.TASK_GUARDRAIL_MAP.items():
            score = 0

            # Check if task type keyword in prompt
            if task_type in prompt_lower:
                score += 10

            # Check related keywords
            for filepath in guardrails:
                if filepath in self.KEYWORD_MAP:
                    keywords = self.KEYWORD_MAP[filepath]
                    matches = sum(1 for kw in keywords if kw in prompt_lower)
                    score += matches

            if score > 0:
                task_scores[task_type] = score

        if task_scores:
            best_match = max(task_scores.items(), key=lambda x: x[1])
            logger.debug(
                "Task classification result",
                task_type=best_match[0],
                confidence=best_match[1],
            )
            return best_match[0]

        return None
