"""Guardrail validator for checking AI outputs against rules"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import structlog

from .parser import ParsedResponse

logger = structlog.get_logger(__name__)


class Severity(Enum):
    """Violation severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GuardrailType(Enum):
    """Types of guardrails"""

    BPSBS = "bpsbs"
    AI_GUARDRAILS = "ai_guardrails"
    UX_UI = "ux_ui"
    AGENT = "agent"


@dataclass
class Violation:
    """Represents a guardrail violation"""

    guardrail_type: str
    rule: str
    severity: str
    description: str
    suggestion: str
    line_number: Optional[int] = None
    file_path: Optional[str] = None


class GuardrailValidator:
    """Validates AI outputs against guardrail rules"""

    # BPSBS validation patterns
    BPSBS_PATTERNS = {
        "three_layer": {
            "patterns": [
                r"\b(database|db)\b",
                r"\b(backend|api|server)\b",
                r"\b(frontend|ui|client)\b",
            ],
            "severity": Severity.HIGH,
            "description": "Missing 3-layer architecture (DB + Backend + Frontend)",
            "suggestion": "Implement all three layers: Database, Backend API, and Frontend",
        },
        "mfa_azure_ad": {
            "patterns": [r"\b(mfa|multi.?factor)\b", r"\b(azure\s+ad|entra)\b"],
            "severity": Severity.CRITICAL,
            "description": "Missing MFA + Azure AD authentication",
            "suggestion": "Add MFA and Azure AD/Entra ID authentication",
        },
        "emergency_admin": {
            "patterns": [r"\b(emergency|panic|admin.*account)\b"],
            "severity": Severity.CRITICAL,
            "description": "Missing emergency admin/panic button feature",
            "suggestion": "Implement emergency admin access mechanism",
        },
        "rbac": {
            "patterns": [r"\b(rbac|role.?based|permission|authorization)\b"],
            "severity": Severity.HIGH,
            "description": "Missing RBAC (Role-Based Access Control)",
            "suggestion": "Implement role-based access control system",
        },
        "audit_logging": {
            "patterns": [r"\b(audit|log|logging|tracking)\b"],
            "severity": Severity.HIGH,
            "description": "Missing audit logging",
            "suggestion": "Add comprehensive audit logging for all actions",
        },
        "test_coverage": {
            "patterns": [r"(?:coverage[:\s]+)?(\d+(?:\.\d+)?)\s*%"],
            "severity": Severity.HIGH,
            "description": "Test coverage below 100%",
            "suggestion": "Achieve 100% test coverage",
            "check_numeric": True,
            "min_value": 100,
        },
        "export_features": {
            "patterns": [r"\b(export|csv|pdf|xlsx|excel)\b"],
            "severity": Severity.MEDIUM,
            "description": "Missing export features (CSV, PDF, XLSX)",
            "suggestion": "Add export functionality for CSV, PDF, and XLSX formats",
        },
    }

    # AI Guardrails patterns
    AI_PATTERNS = {
        "unit_tests": {
            "patterns": [r"\b(unit\s+test|test\s+case)\b"],
            "severity": Severity.HIGH,
            "description": "Missing unit tests",
            "suggestion": "Add comprehensive unit tests",
        },
        "e2e_tests": {
            "patterns": [r"\b(e2e|end.?to.?end|integration\s+test)\b"],
            "severity": Severity.HIGH,
            "description": "Missing E2E/integration tests",
            "suggestion": "Add end-to-end and integration tests",
        },
        "incremental_edits": {
            "patterns": [r"\b(incremental|partial|edit|modify)\b"],
            "severity": Severity.MEDIUM,
            "description": "Full file rewrite instead of incremental edits",
            "suggestion": "Use incremental edits rather than full file rewrites",
        },
        "error_handling": {
            "patterns": [r"\b(try|catch|error|exception|handle)\b"],
            "severity": Severity.HIGH,
            "description": "Missing proper error handling",
            "suggestion": "Add comprehensive error handling with try/catch blocks",
        },
        "debug_logging": {
            "patterns": [r"\b(debug|log|logger|console\.\w+)\b"],
            "severity": Severity.MEDIUM,
            "description": "Missing debug/logging statements",
            "suggestion": "Add debugging and logging for troubleshooting",
        },
    }

    # UX/UI Guardrails patterns
    UX_UI_PATTERNS = {
        "vague_labels": {
            "patterns": [r'\b(ok|more|click\s+here|submit)\b(?!["\']?\w)'],
            "severity": Severity.MEDIUM,
            "description": "Vague button labels detected (OK, More, etc.)",
            "suggestion": "Use descriptive labels like 'Save Changes', 'View Details'",
        },
        "dark_mode": {
            "patterns": [r"\b(dark\s+mode|theme|color\s+scheme)\b"],
            "severity": Severity.LOW,
            "description": "Missing dark mode support",
            "suggestion": "Add dark mode/theme switching capability",
        },
        "tooltips": {
            "patterns": [r"\b(tooltip|hint|help\s+text)\b"],
            "severity": Severity.LOW,
            "description": "Missing tooltips for user guidance",
            "suggestion": "Add tooltips to explain features and inputs",
        },
        "accessibility": {
            "patterns": [r"\b(aria|accessibility|a11y|screen\s+reader)\b"],
            "severity": Severity.MEDIUM,
            "description": "Missing accessibility considerations",
            "suggestion": "Add ARIA labels and accessibility features",
        },
        "export_buttons": {
            "patterns": [r"\b(export|download|save\s+as)\b"],
            "severity": Severity.MEDIUM,
            "description": "Missing export buttons",
            "suggestion": "Add export/download buttons for data",
        },
        "max_elements": {
            "patterns": [r"\b(button|input|select|checkbox|radio)\b"],
            "severity": Severity.LOW,
            "description": "Too many interactive elements per screen",
            "suggestion": "Limit to 7 interactive elements per screen",
            "count_limit": 7,
        },
    }

    def __init__(self, mode: str = "standard"):
        """Initialize validator

        Args:
            mode: Operating mode (standard or strict)
        """
        self.mode = mode
        logger.info("GuardrailValidator initialized", mode=mode)

    async def validate(self, parsed: ParsedResponse, raw_text: str) -> List[Violation]:
        """Validate parsed response against all guardrails

        Args:
            parsed: Parsed AI response
            raw_text: Original response text

        Returns:
            List of violations found
        """
        logger.info("Starting validation", mode=self.mode)

        violations = []

        # Run all validation checks
        violations.extend(await self._check_bpsbs(parsed, raw_text))
        violations.extend(await self._check_ai_guardrails(parsed, raw_text))
        violations.extend(await self._check_ux_ui(parsed, raw_text))

        logger.info(
            "Validation complete",
            total_violations=len(violations),
            critical=sum(1 for v in violations if v.severity == Severity.CRITICAL.value),
            high=sum(1 for v in violations if v.severity == Severity.HIGH.value),
            medium=sum(1 for v in violations if v.severity == Severity.MEDIUM.value),
            low=sum(1 for v in violations if v.severity == Severity.LOW.value),
        )

        return violations

    async def _check_bpsbs(self, parsed: ParsedResponse, text: str) -> List[Violation]:
        """Check BPSBS (Best Practices, Security, Business Standards) guardrails

        Args:
            parsed: Parsed response
            text: Raw text

        Returns:
            List of violations
        """
        violations = []

        for rule_name, rule_config in self.BPSBS_PATTERNS.items():
            patterns = rule_config["patterns"]
            severity = rule_config["severity"]

            # Special handling for numeric checks (like test coverage)
            if rule_config.get("check_numeric"):
                # Use parsed coverage first, fallback to regex
                coverage_value = parsed.test_coverage
                if coverage_value is None:
                    coverage_match = re.search(patterns[0], text, re.IGNORECASE)
                    if coverage_match:
                        coverage_value = float(coverage_match.group(1))

                if coverage_value is not None:
                    min_value = rule_config.get("min_value", 100)
                    if coverage_value < min_value:
                        violations.append(
                            Violation(
                                guardrail_type=GuardrailType.BPSBS.value,
                                rule=rule_name,
                                severity=severity.value,
                                description=f"{rule_config['description']}: {coverage_value}%",
                                suggestion=rule_config["suggestion"],
                            )
                        )
                else:
                    # No coverage mentioned at all
                    violations.append(
                        Violation(
                            guardrail_type=GuardrailType.BPSBS.value,
                            rule=rule_name,
                            severity=severity.value,
                            description=rule_config["description"],
                            suggestion=rule_config["suggestion"],
                        )
                    )
                continue

            # Check if all patterns are present
            missing_patterns = []
            for pattern in patterns:
                if not re.search(pattern, text, re.IGNORECASE):
                    missing_patterns.append(pattern)

            if missing_patterns:
                violations.append(
                    Violation(
                        guardrail_type=GuardrailType.BPSBS.value,
                        rule=rule_name,
                        severity=severity.value,
                        description=rule_config["description"],
                        suggestion=rule_config["suggestion"],
                    )
                )

        logger.debug("BPSBS check complete", violations=len(violations))
        return violations

    async def _check_ai_guardrails(self, parsed: ParsedResponse, text: str) -> List[Violation]:
        """Check AI-specific guardrails

        Args:
            parsed: Parsed response
            text: Raw text

        Returns:
            List of violations
        """
        violations = []

        for rule_name, rule_config in self.AI_PATTERNS.items():
            patterns = rule_config["patterns"]
            severity = rule_config["severity"]

            # Check if patterns are present
            found = False
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    found = True
                    break

            if not found:
                violations.append(
                    Violation(
                        guardrail_type=GuardrailType.AI_GUARDRAILS.value,
                        rule=rule_name,
                        severity=severity.value,
                        description=rule_config["description"],
                        suggestion=rule_config["suggestion"],
                    )
                )

        logger.debug("AI guardrails check complete", violations=len(violations))
        return violations

    async def _check_ux_ui(self, parsed: ParsedResponse, text: str) -> List[Violation]:
        """Check UX/UI guardrails

        Args:
            parsed: Parsed response
            text: Raw text

        Returns:
            List of violations
        """
        violations = []

        for rule_name, rule_config in self.UX_UI_PATTERNS.items():
            patterns = rule_config["patterns"]
            severity = rule_config["severity"]

            # Special handling for element count
            if rule_config.get("count_limit"):
                total_count = 0
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    total_count += len(matches)

                limit = rule_config["count_limit"]
                if total_count > limit:
                    violations.append(
                        Violation(
                            guardrail_type=GuardrailType.UX_UI.value,
                            rule=rule_name,
                            severity=severity.value,
                            description=f"{rule_config['description']}: {total_count} found, max {limit}",
                            suggestion=rule_config["suggestion"],
                        )
                    )
                continue

            # Check for vague labels (negative check - violation if found)
            if rule_name == "vague_labels":
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        violations.append(
                            Violation(
                                guardrail_type=GuardrailType.UX_UI.value,
                                rule=rule_name,
                                severity=severity.value,
                                description=f"{rule_config['description']}: {', '.join(matches[:3])}",
                                suggestion=rule_config["suggestion"],
                            )
                        )
                continue

            # Regular pattern check
            found = False
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    found = True
                    break

            if not found:
                violations.append(
                    Violation(
                        guardrail_type=GuardrailType.UX_UI.value,
                        rule=rule_name,
                        severity=severity.value,
                        description=rule_config["description"],
                        suggestion=rule_config["suggestion"],
                    )
                )

        logger.debug("UX/UI check complete", violations=len(violations))
        return violations

    def should_block(self, violations: List[Violation]) -> bool:
        """Determine if violations should block execution

        Args:
            violations: List of violations

        Returns:
            True if should block (in strict mode with violations)
        """
        if self.mode != "strict":
            return False

        # In strict mode, any violation blocks
        return len(violations) > 0

    def get_critical_violations(self, violations: List[Violation]) -> List[Violation]:
        """Get only critical violations

        Args:
            violations: All violations

        Returns:
            Critical violations only
        """
        return [v for v in violations if v.severity == Severity.CRITICAL.value]

    def format_violations_report(self, violations: List[Violation]) -> str:
        """Format violations as a readable report

        Args:
            violations: List of violations

        Returns:
            Formatted report string
        """
        if not violations:
            return "✓ No violations found - all guardrails passed!"

        report_lines = [f"\n⚠️  Found {len(violations)} guardrail violation(s):\n"]

        # Group by severity
        by_severity = {}
        for v in violations:
            if v.severity not in by_severity:
                by_severity[v.severity] = []
            by_severity[v.severity].append(v)

        # Sort by severity (critical first)
        severity_order = [
            Severity.CRITICAL.value,
            Severity.HIGH.value,
            Severity.MEDIUM.value,
            Severity.LOW.value,
        ]

        for sev in severity_order:
            if sev in by_severity:
                icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}
                report_lines.append(
                    f"\n{icon[sev]} {sev.upper()} ({len(by_severity[sev])} issues):"
                )

                for v in by_severity[sev]:
                    report_lines.append(f"  • [{v.guardrail_type}] {v.description}")
                    report_lines.append(f"    → {v.suggestion}")

        return "\n".join(report_lines)
