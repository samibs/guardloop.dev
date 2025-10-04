"""Pattern Analysis System for Guardrail v2

Analyzes database for LLM failure patterns and extracts recurring mistakes.
Enables adaptive learning from real interactions.
"""

import hashlib
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import structlog
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from guardrail.utils.db import (
    DynamicGuardrailModel,
    FailureModeModel,
    LearnedPatternModel,
    SessionModel,
    ViolationModel,
)

logger = structlog.get_logger(__name__)


class PatternAnalyzer:
    """Analyze database for LLM failure patterns"""

    def __init__(self, db_session: Session, min_frequency: int = 3, min_confidence: float = 0.6):
        """Initialize pattern analyzer

        Args:
            db_session: Database session
            min_frequency: Minimum occurrences to consider a pattern
            min_confidence: Minimum confidence score for pattern
        """
        self.session = db_session
        self.min_frequency = min_frequency
        self.min_confidence = min_confidence

    def analyze_failures(
        self, days: int = 30, categories: Optional[List[str]] = None
    ) -> List[LearnedPatternModel]:
        """Analyze failure modes and extract patterns

        Args:
            days: Number of days to analyze
            categories: Specific categories to analyze (None for all)

        Returns:
            List of learned pattern models
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Query failures
        query = self.session.query(FailureModeModel).filter(
            FailureModeModel.timestamp >= cutoff_date
        )

        if categories:
            query = query.filter(FailureModeModel.category.in_(categories))

        failures = query.all()

        logger.info(
            "Analyzing failures",
            total_failures=len(failures),
            days=days,
            categories=categories,
        )

        # Group by category and pattern
        pattern_groups = defaultdict(list)

        for failure in failures:
            key = (failure.category, failure.pattern)
            pattern_groups[key].append(failure)

        # Extract patterns
        learned_patterns = []

        for (category, pattern), failure_list in pattern_groups.items():
            frequency = len(failure_list)

            if frequency < self.min_frequency:
                continue

            # Calculate confidence based on frequency and severity
            confidence = self._calculate_confidence(failure_list)

            if confidence < self.min_confidence:
                continue

            # Create pattern signature
            signature = self._create_signature(failure_list)
            pattern_hash = self._hash_signature(signature)

            # Check if pattern already exists
            existing = (
                self.session.query(LearnedPatternModel)
                .filter(LearnedPatternModel.pattern_hash == pattern_hash)
                .first()
            )

            if existing:
                # Update existing pattern
                existing.frequency = frequency
                existing.last_seen = datetime.utcnow()
                existing.confidence_score = confidence
                existing.example_sessions = [str(f.session_id) for f in failure_list[:5]]
                learned_patterns.append(existing)
            else:
                # Create new pattern
                most_severe = self._get_most_severe(failure_list)

                pattern_model = LearnedPatternModel(
                    pattern_hash=pattern_hash,
                    category=category,
                    signature=signature,
                    description=self._generate_description(failure_list),
                    frequency=frequency,
                    severity=most_severe,
                    first_seen=min(f.timestamp for f in failure_list),
                    last_seen=max(f.timestamp for f in failure_list),
                    confidence_score=confidence,
                    example_sessions=[str(f.session_id) for f in failure_list[:5]],
                    metadata={
                        "common_issues": [f.issue for f in failure_list[:3]],
                        "affected_tools": list(set(f.tool for f in failure_list)),
                    },
                )

                self.session.add(pattern_model)
                learned_patterns.append(pattern_model)

        self.session.commit()

        logger.info(
            "Pattern analysis complete", patterns_found=len(learned_patterns), days=days
        )

        return learned_patterns

    def analyze_violations(
        self, days: int = 30, guardrail_types: Optional[List[str]] = None
    ) -> List[LearnedPatternModel]:
        """Analyze violations and extract patterns

        Args:
            days: Number of days to analyze
            guardrail_types: Specific guardrail types to analyze

        Returns:
            List of learned pattern models
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = self.session.query(ViolationModel).filter(
            ViolationModel.timestamp >= cutoff_date
        )

        if guardrail_types:
            query = query.filter(ViolationModel.guardrail_type.in_(guardrail_types))

        violations = query.all()

        logger.info(
            "Analyzing violations",
            total_violations=len(violations),
            days=days,
            types=guardrail_types,
        )

        # Group by rule violated
        violation_groups = defaultdict(list)

        for violation in violations:
            key = (violation.guardrail_type, violation.rule_violated)
            violation_groups[key].append(violation)

        learned_patterns = []

        for (gtype, rule), violation_list in violation_groups.items():
            frequency = len(violation_list)

            if frequency < self.min_frequency:
                continue

            confidence = min(frequency / 10.0, 1.0)  # Simple frequency-based confidence

            if confidence < self.min_confidence:
                continue

            signature = f"{gtype}::{rule}"
            pattern_hash = hashlib.sha256(signature.encode()).hexdigest()

            existing = (
                self.session.query(LearnedPatternModel)
                .filter(LearnedPatternModel.pattern_hash == pattern_hash)
                .first()
            )

            if existing:
                existing.frequency = frequency
                existing.last_seen = datetime.utcnow()
                existing.confidence_score = confidence
                learned_patterns.append(existing)
            else:
                most_severe = max(
                    violation_list, key=lambda v: self._severity_rank(v.severity)
                ).severity

                pattern_model = LearnedPatternModel(
                    pattern_hash=pattern_hash,
                    category=f"violation_{gtype}",
                    signature=signature,
                    description=f"Repeated violation: {rule}",
                    frequency=frequency,
                    severity=most_severe,
                    first_seen=min(v.timestamp for v in violation_list),
                    last_seen=max(v.timestamp for v in violation_list),
                    confidence_score=confidence,
                    example_sessions=[
                        str(v.session_id) for v in violation_list[:5]
                    ],
                    metadata={
                        "guardrail_type": gtype,
                        "rule": rule,
                        "common_suggestions": [
                            v.suggestion for v in violation_list[:3] if v.suggestion
                        ],
                    },
                )

                self.session.add(pattern_model)
                learned_patterns.append(pattern_model)

        self.session.commit()

        logger.info(
            "Violation analysis complete", patterns_found=len(learned_patterns), days=days
        )

        return learned_patterns

    def get_trending_patterns(self, limit: int = 10) -> List[LearnedPatternModel]:
        """Get most frequent recent patterns

        Args:
            limit: Maximum patterns to return

        Returns:
            List of trending patterns
        """
        return (
            self.session.query(LearnedPatternModel)
            .order_by(LearnedPatternModel.frequency.desc())
            .limit(limit)
            .all()
        )

    def get_high_severity_patterns(self, limit: int = 10) -> List[LearnedPatternModel]:
        """Get highest severity patterns

        Args:
            limit: Maximum patterns to return

        Returns:
            List of high-severity patterns
        """
        return (
            self.session.query(LearnedPatternModel)
            .filter(
                LearnedPatternModel.severity.in_(["high", "critical"]),
                LearnedPatternModel.confidence_score >= self.min_confidence,
            )
            .order_by(LearnedPatternModel.severity.desc(), LearnedPatternModel.frequency.desc())
            .limit(limit)
            .all()
        )

    def _create_signature(self, failures: List[FailureModeModel]) -> str:
        """Create unique signature for pattern

        Args:
            failures: List of failures

        Returns:
            Pattern signature string
        """
        # Extract common elements
        categories = [f.category for f in failures]
        patterns = [f.pattern for f in failures]

        # Most common category and pattern
        category = Counter(categories).most_common(1)[0][0]
        pattern = Counter(patterns).most_common(1)[0][0]

        return f"{category}::{pattern}"

    def _hash_signature(self, signature: str) -> str:
        """Generate hash for signature

        Args:
            signature: Pattern signature

        Returns:
            SHA256 hash
        """
        return hashlib.sha256(signature.encode()).hexdigest()

    def _calculate_confidence(self, failures: List[FailureModeModel]) -> float:
        """Calculate confidence score for pattern

        Args:
            failures: List of failures

        Returns:
            Confidence score (0.0 to 1.0)
        """
        frequency = len(failures)
        severity_scores = [self._severity_rank(f.severity) for f in failures]
        avg_severity = sum(severity_scores) / len(severity_scores)

        # Confidence based on frequency and severity
        freq_score = min(frequency / 10.0, 0.7)  # Max 0.7 from frequency
        severity_score = avg_severity / 4.0 * 0.3  # Max 0.3 from severity

        return min(freq_score + severity_score, 1.0)

    def _severity_rank(self, severity: str) -> int:
        """Convert severity to numeric rank

        Args:
            severity: Severity level

        Returns:
            Numeric rank (1-4)
        """
        ranks = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return ranks.get(severity, 1)

    def _get_most_severe(self, failures: List[FailureModeModel]) -> str:
        """Get most severe level from failures

        Args:
            failures: List of failures

        Returns:
            Severity level
        """
        return max(failures, key=lambda f: self._severity_rank(f.severity)).severity

    def _generate_description(self, failures: List[FailureModeModel]) -> str:
        """Generate human-readable description

        Args:
            failures: List of failures

        Returns:
            Description string
        """
        category = failures[0].category
        issue_counts = Counter(f.issue for f in failures)
        most_common_issue = issue_counts.most_common(1)[0][0]

        return f"{category}: {most_common_issue} (seen {len(failures)} times)"
