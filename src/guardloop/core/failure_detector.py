"""Failure detector for identifying AI failure patterns"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class DetectedFailure:
    """Represents a detected AI failure"""

    category: str
    pattern: str
    timestamp: datetime
    severity: str
    context: str
    suggestion: Optional[str] = None
    tool: Optional[str] = None


class FailureDetector:
    """Detects common AI failure patterns in responses"""

    # Comprehensive failure patterns based on real-world AI issues
    PATTERNS: Dict[str, Dict] = {
        "JWT/Auth": {
            "regex": r"\b(jwt|token|unauthorized|expired|authentication\s+failed|invalid\s+token|bearer)\b",
            "severity": "high",
            "suggestion": "Ensure MFA + Azure AD is configured. Check token validation logic.",
            "context_words": 50,
        },
        ".NET Code": {
            "regex": r"\b(csproj|dependency\s+injection|di\s+error|async\s+issue|broken\s+reference|nuget)\b",
            "severity": "medium",
            "suggestion": "Review .NET dependency injection configuration and project references.",
            "context_words": 50,
        },
        "Angular DI": {
            "regex": r"\b(translateservice|apiservice|provider\s+not\s+found|no\s+provider\s+for|nullinjectorerror)\b",
            "severity": "medium",
            "suggestion": "Check Angular TestBed providers and module imports.",
            "context_words": 50,
        },
        "File Overwrite": {
            "regex": r"(\)\)\)\)\)+|0{10,}|#{10,}|={10,}|\*{10,})",
            "severity": "critical",
            "suggestion": "AI corrupted file with repetitive characters - restore from backup immediately!",
            "context_words": 20,
        },
        "Environment": {
            "regex": r"\b(node|npm|version|dependency\s+conflict|python\s+version|incompatible|missing\s+package)\b",
            "severity": "medium",
            "suggestion": "Check environment compatibility and dependency versions.",
            "context_words": 50,
        },
        "Pipeline": {
            "regex": r"\b(coverage|sonarqube|lint|pipeline\s+failed|build\s+error|ci\s+failed|test\s+failed)\b",
            "severity": "high",
            "suggestion": "Review CI/CD configuration and fix failing pipeline steps.",
            "context_words": 50,
        },
        "Security": {
            "regex": r"\b(mfa|azure\s+ad|rbac|audit\s+log|panic\s+button|security\s+vulnerability|sql\s+injection|xss|csrf)\b",
            "severity": "critical",
            "suggestion": "Address security requirements immediately. Follow OWASP guidelines.",
            "context_words": 50,
        },
        "UI/UX": {
            "regex": r"\b(button|tooltip|dark\s+mode|export\s+missing|vague\s+label|accessibility\s+issue)\b",
            "severity": "low",
            "suggestion": "Apply UX/UI guardrails for better user experience.",
            "context_words": 40,
        },
        "Compliance": {
            "regex": r"\b(gdpr|iso|27001|27002|retention|compliance\s+gap|data\s+privacy|regulation)\b",
            "severity": "high",
            "suggestion": "Review compliance requirements (GDPR, ISO 27001/27002).",
            "context_words": 50,
        },
        "Looping": {
            "regex": r"\b(retrying|loop\s+detected|infinite|recursion|stack\s+overflow|maximum\s+recursion)\b",
            "severity": "critical",
            "suggestion": "AI entered infinite loop - abort and retry with different prompt.",
            "context_words": 30,
        },
        "Database": {
            "regex": r"\b(connection\s+failed|timeout|deadlock|migration\s+failed|constraint\s+violation|duplicate\s+key)\b",
            "severity": "high",
            "suggestion": "Check database connection, schema, and query optimization.",
            "context_words": 50,
        },
        "Type Errors": {
            "regex": r"\b(type\s+error|undefined|null\s+reference|cannot\s+read\s+property|typeerror)\b",
            "severity": "medium",
            "suggestion": "Add type checking and null safety guards.",
            "context_words": 40,
        },
        "Memory Issues": {
            "regex": r"\b(out\s+of\s+memory|memory\s+leak|heap\s+overflow|allocation\s+failed)\b",
            "severity": "critical",
            "suggestion": "Investigate memory usage and potential leaks.",
            "context_words": 40,
        },
        "API Errors": {
            "regex": r"\b(400|401|403|404|500|502|503|504|bad\s+request|not\s+found|server\s+error)\b",
            "severity": "high",
            "suggestion": "Check API endpoint configuration and error handling.",
            "context_words": 50,
        },
        "Configuration": {
            "regex": r"\b(missing\s+config|invalid\s+configuration|env\s+variable|config\s+error|settings\s+not\s+found)\b",
            "severity": "medium",
            "suggestion": "Verify configuration files and environment variables.",
            "context_words": 50,
        },
        "Import Errors": {
            "regex": r"\b(cannot\s+find\s+module|import\s+error|module\s+not\s+found|no\s+module\s+named)\b",
            "severity": "medium",
            "suggestion": "Check import paths and installed packages.",
            "context_words": 40,
        },
        "Test Failures": {
            "regex": r"\b(test\s+failed|assertion\s+failed|expected.*but\s+got|test\s+suite\s+failed)\b",
            "severity": "medium",
            "suggestion": "Review test assertions and implementation.",
            "context_words": 50,
        },
        "Performance": {
            "regex": r"\b(slow|performance\s+issue|bottleneck|n\+1\s+query|inefficient|optimization)\b",
            "severity": "medium",
            "suggestion": "Profile and optimize performance bottlenecks.",
            "context_words": 50,
        },
        "Race Condition": {
            "regex": r"\b(race\s+condition|concurrent|synchronization|mutex|deadlock|thread\s+safety)\b",
            "severity": "high",
            "suggestion": "Add proper synchronization and thread safety mechanisms.",
            "context_words": 50,
        },
        "Deployment": {
            "regex": r"\b(deployment\s+failed|rollback|downtime|service\s+unavailable|container\s+error)\b",
            "severity": "high",
            "suggestion": "Check deployment configuration and service health.",
            "context_words": 50,
        },
    }

    def __init__(self):
        """Initialize failure detector"""
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._compile_patterns()
        logger.info("FailureDetector initialized", pattern_count=len(self.PATTERNS))

    def _compile_patterns(self) -> None:
        """Pre-compile all regex patterns for performance"""
        for category, config in self.PATTERNS.items():
            self._compiled_patterns[category] = re.compile(
                config["regex"], re.IGNORECASE | re.MULTILINE
            )

    def scan(self, text: str, tool: Optional[str] = None) -> List[DetectedFailure]:
        """Scan text for failure patterns

        Args:
            text: Text to scan
            tool: Optional AI tool name (claude, gemini, codex)

        Returns:
            List of detected failures
        """
        logger.info("Scanning for failures", text_length=len(text), tool=tool)

        failures = []
        seen_contexts: Set[str] = set()  # Deduplication

        for category, pattern in self._compiled_patterns.items():
            matches = pattern.finditer(text)

            for match in matches:
                # Extract context around match
                context = self._extract_context(
                    text, match.start(), self.PATTERNS[category]["context_words"]
                )

                # Deduplicate using context hash
                context_hash = f"{category}:{context[:100]}"
                if context_hash in seen_contexts:
                    continue
                seen_contexts.add(context_hash)

                failure = DetectedFailure(
                    category=category,
                    pattern=match.group(0),
                    timestamp=datetime.now(),
                    severity=self.PATTERNS[category]["severity"],
                    context=context,
                    suggestion=self.PATTERNS[category]["suggestion"],
                    tool=tool,
                )

                failures.append(failure)
                logger.debug(
                    "Failure detected",
                    category=category,
                    severity=failure.severity,
                    pattern=match.group(0),
                )

        # Sort by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        failures.sort(key=lambda f: (severity_order.get(f.severity, 99), f.category))

        logger.info(
            "Scan complete",
            total_failures=len(failures),
            critical=sum(1 for f in failures if f.severity == "critical"),
            high=sum(1 for f in failures if f.severity == "high"),
            medium=sum(1 for f in failures if f.severity == "medium"),
            low=sum(1 for f in failures if f.severity == "low"),
        )

        return failures

    def _extract_context(self, text: str, position: int, context_words: int) -> str:
        """Extract context around a match position

        Args:
            text: Full text
            position: Match position
            context_words: Number of words to extract

        Returns:
            Context string
        """
        # Find word boundaries
        words = text.split()
        word_positions = []
        current_pos = 0

        for word in words:
            word_start = text.find(word, current_pos)
            word_positions.append((word_start, word_start + len(word), word))
            current_pos = word_start + len(word)

        # Find words around position
        context_words_list = []
        for i, (start, end, word) in enumerate(word_positions):
            if start <= position <= end:
                # Found the word containing the match
                start_idx = max(0, i - context_words // 2)
                end_idx = min(len(word_positions), i + context_words // 2)
                context_words_list = [w for _, _, w in word_positions[start_idx:end_idx]]
                break

        if not context_words_list:
            # Fallback: get characters around position
            start = max(0, position - 100)
            end = min(len(text), position + 100)
            return text[start:end]

        context = " ".join(context_words_list)
        return context[:200]  # Limit context length

    def has_critical_failures(self, failures: List[DetectedFailure]) -> bool:
        """Check if there are any critical failures

        Args:
            failures: List of detected failures

        Returns:
            True if any critical failures found
        """
        return any(f.severity == "critical" for f in failures)

    def get_failures_by_severity(
        self, failures: List[DetectedFailure], severity: str
    ) -> List[DetectedFailure]:
        """Filter failures by severity

        Args:
            failures: All failures
            severity: Severity level to filter

        Returns:
            Filtered failures
        """
        return [f for f in failures if f.severity == severity]

    def get_failures_by_category(
        self, failures: List[DetectedFailure], category: str
    ) -> List[DetectedFailure]:
        """Filter failures by category

        Args:
            failures: All failures
            category: Category to filter

        Returns:
            Filtered failures
        """
        return [f for f in failures if f.category == category]

    def format_failures_report(self, failures: List[DetectedFailure]) -> str:
        """Format failures as a readable report

        Args:
            failures: List of detected failures

        Returns:
            Formatted report string
        """
        if not failures:
            return "✓ No failures detected!"

        report_lines = [f"\n🔍 Detected {len(failures)} potential failure(s):\n"]

        # Group by severity
        by_severity = {}
        for f in failures:
            if f.severity not in by_severity:
                by_severity[f.severity] = []
            by_severity[f.severity].append(f)

        # Sort by severity
        severity_order = ["critical", "high", "medium", "low"]
        severity_icons = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵",
        }

        for sev in severity_order:
            if sev in by_severity:
                report_lines.append(
                    f"\n{severity_icons[sev]} {sev.upper()} ({len(by_severity[sev])} issues):"
                )

                for f in by_severity[sev]:
                    report_lines.append(f"  • [{f.category}] Pattern: '{f.pattern}'")
                    report_lines.append(f"    Context: {f.context[:100]}...")
                    report_lines.append(f"    → {f.suggestion}")

        return "\n".join(report_lines)

    def get_stats(self) -> Dict[str, any]:
        """Get failure detector statistics

        Returns:
            Statistics dictionary
        """
        return {
            "total_patterns": len(self.PATTERNS),
            "categories": list(self.PATTERNS.keys()),
            "severity_distribution": {
                "critical": sum(1 for p in self.PATTERNS.values() if p["severity"] == "critical"),
                "high": sum(1 for p in self.PATTERNS.values() if p["severity"] == "high"),
                "medium": sum(1 for p in self.PATTERNS.values() if p["severity"] == "medium"),
                "low": sum(1 for p in self.PATTERNS.values() if p["severity"] == "low"),
            },
        }
