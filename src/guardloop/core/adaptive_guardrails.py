"""Adaptive Guardrail System for Guardrail v2

Generates dynamic guardrails from learned patterns and manages their lifecycle.
Implements feedback loop to remind LLM not to repeat mistakes.
"""

from datetime import datetime
from typing import List, Optional

import structlog
from sqlalchemy import func
from sqlalchemy.orm import Session

from guardloop.utils.db import DynamicGuardrailModel, LearnedPatternModel, RuleEffectivenessModel

logger = structlog.get_logger(__name__)


class AdaptiveGuardrailGenerator:
    """Generate and manage dynamic guardrails from learned patterns"""

    def __init__(self, db_session: Session, confidence_threshold: float = 0.7):
        """Initialize adaptive guardrail generator

        Args:
            db_session: Database session
            confidence_threshold: Minimum confidence to create guardrail
        """
        self.session = db_session
        self.confidence_threshold = confidence_threshold

    def generate_from_pattern(
        self, pattern: LearnedPatternModel, task_types: Optional[List[str]] = None
    ) -> Optional[DynamicGuardrailModel]:
        """Generate guardrail from learned pattern

        Args:
            pattern: Learned pattern model
            task_types: Task types this guardrail applies to

        Returns:
            Dynamic guardrail model or None if pattern doesn't qualify
        """
        if pattern.confidence_score < self.confidence_threshold:
            logger.debug(
                "Pattern confidence too low",
                pattern_id=pattern.id,
                confidence=pattern.confidence_score,
            )
            return None

        # Check if guardrail already exists for this pattern
        existing = (
            self.session.query(DynamicGuardrailModel)
            .filter(DynamicGuardrailModel.pattern_id == pattern.id)
            .filter(DynamicGuardrailModel.status.in_(["trial", "validated", "enforced"]))
            .first()
        )

        if existing:
            logger.debug("Guardrail already exists", pattern_id=pattern.id, rule_id=existing.id)
            return existing

        # Generate rule text
        rule_text = self._generate_rule_text(pattern)

        # Determine enforcement mode based on severity
        enforcement_mode = self._determine_enforcement_mode(pattern.severity)

        # Default task types
        if task_types is None:
            task_types = ["code", "mixed"]  # Apply to code and mixed tasks by default

        guardrail = DynamicGuardrailModel(
            pattern_id=pattern.id,
            rule_text=rule_text,
            rule_category=pattern.category,
            confidence=pattern.confidence_score,
            status="trial",  # Start in trial mode
            enforcement_mode=enforcement_mode,
            task_types=task_types,
            activated_at=datetime.utcnow(),
            created_by="pattern_analyzer",
            metadata={
                "pattern_hash": pattern.pattern_hash,
                "frequency": pattern.frequency,
                "severity": pattern.severity,
            },
        )

        self.session.add(guardrail)
        self.session.commit()

        logger.info(
            "Dynamic guardrail created",
            rule_id=guardrail.id,
            pattern_id=pattern.id,
            confidence=guardrail.confidence,
            enforcement=enforcement_mode,
        )

        return guardrail

    def generate_from_patterns(
        self, patterns: List[LearnedPatternModel], task_types: Optional[List[str]] = None
    ) -> List[DynamicGuardrailModel]:
        """Generate guardrails from multiple patterns

        Args:
            patterns: List of learned patterns
            task_types: Task types guardrails apply to

        Returns:
            List of created guardrails
        """
        guardrails = []

        for pattern in patterns:
            guardrail = self.generate_from_pattern(pattern, task_types)
            if guardrail:
                guardrails.append(guardrail)

        logger.info(
            "Batch guardrail generation complete",
            total_patterns=len(patterns),
            guardrails_created=len(guardrails),
        )

        return guardrails

    def get_active_guardrails(
        self,
        task_type: Optional[str] = None,
        min_confidence: float = 0.6,
        prompt: Optional[str] = None,
        max_rules: int = 5,
        use_semantic_matching: bool = False,
    ) -> List[DynamicGuardrailModel]:
        """Get active guardrails for context injection with relevance scoring

        Args:
            task_type: Filter by task type
            min_confidence: Minimum confidence threshold
            prompt: User prompt for relevance scoring (optional)
            max_rules: Maximum number of rules to return (default: 5)
            use_semantic_matching: Use embeddings for semantic similarity (default: False)

        Returns:
            List of active guardrails, sorted by relevance
        """
        query = (
            self.session.query(DynamicGuardrailModel)
            .filter(DynamicGuardrailModel.status.in_(["validated", "enforced"]))
            .filter(DynamicGuardrailModel.confidence >= min_confidence)
            .filter(DynamicGuardrailModel.deactivated_at.is_(None))
        )

        if task_type:
            # Filter by task type in JSON array
            query = query.filter(DynamicGuardrailModel.task_types.contains([task_type]))

        guardrails = query.all()

        # Use semantic matching if enabled and prompt provided
        if use_semantic_matching and prompt and guardrails:
            import asyncio

            from guardloop.core.semantic_matcher import SemanticGuardrailMatcher

            # Run async semantic matching
            matcher = SemanticGuardrailMatcher()
            loop = asyncio.get_event_loop()

            # Index guardrails
            loop.run_until_complete(matcher.index_guardrails(guardrails))

            # Find relevant with semantic similarity
            relevant_pairs = loop.run_until_complete(
                matcher.find_relevant(
                    prompt=prompt,
                    guardrails=guardrails,
                    top_k=max_rules,
                    threshold=0.3,
                )
            )

            # Store semantic similarity scores in metadata
            for guardrail, similarity in relevant_pairs:
                if not guardrail.rule_metadata:
                    guardrail.rule_metadata = {}
                guardrail.rule_metadata["semantic_similarity"] = similarity

            # Return only semantically matched guardrails
            guardrails = [g for g, _ in relevant_pairs]

            logger.info(
                "Semantic matching applied",
                original_count=len(query.all()),
                matched_count=len(guardrails),
            )

        # Apply keyword relevance scoring if prompt provided (fallback or supplement)
        elif prompt and guardrails:
            guardrails = self._score_by_relevance(guardrails, prompt, task_type)

            # Sort by score (relevance + confidence + recency + success)
            guardrails.sort(
                key=lambda gr: self._calculate_priority_score(gr, task_type), reverse=True
            )

            # Limit to top N most relevant
            guardrails = guardrails[:max_rules]

        logger.debug(
            "Retrieved active guardrails",
            count=len(guardrails),
            task_type=task_type,
            min_confidence=min_confidence,
            max_rules=max_rules,
            semantic_matching=use_semantic_matching,
        )

        return guardrails

    def format_for_context(self, guardrails: List[DynamicGuardrailModel]) -> str:
        """Format guardrails for LLM context injection

        Args:
            guardrails: List of guardrails

        Returns:
            Formatted text for context
        """
        if not guardrails:
            return ""

        lines = ["# Learned Guardrails - DO NOT REPEAT THESE MISTAKES\n"]

        # Group by category
        by_category = {}
        for gr in guardrails:
            if gr.rule_category not in by_category:
                by_category[gr.rule_category] = []
            by_category[gr.rule_category].append(gr)

        for category, rules in by_category.items():
            lines.append(f"\n## {category.replace('_', ' ').title()}\n")

            for rule in rules:
                severity_icon = self._get_severity_icon(
                    rule.rule_metadata.get("severity", "medium") if rule.rule_metadata else "medium"
                )
                lines.append(f"- {severity_icon} **{rule.rule_text}**")

                if rule.enforcement_mode == "block":
                    lines.append("  - ⛔ **BLOCKING**: This will be rejected")
                elif rule.enforcement_mode == "auto_fix":
                    lines.append("  - 🔧 **AUTO-FIX**: Will be automatically corrected")

                lines.append(f"  - Confidence: {rule.confidence:.0%}")
                lines.append("")

        return "\n".join(lines)

    def promote_to_validated(self, rule_id: int) -> bool:
        """Promote rule from trial to validated status

        Args:
            rule_id: Rule ID

        Returns:
            True if promoted successfully
        """
        rule = self.session.query(DynamicGuardrailModel).filter_by(id=rule_id).first()

        if not rule or rule.status != "trial":
            return False

        rule.status = "validated"
        self.session.commit()

        logger.info("Rule promoted to validated", rule_id=rule_id)
        return True

    def promote_to_enforced(self, rule_id: int) -> bool:
        """Promote rule from validated to enforced status

        Args:
            rule_id: Rule ID

        Returns:
            True if promoted successfully
        """
        rule = self.session.query(DynamicGuardrailModel).filter_by(id=rule_id).first()

        if not rule or rule.status != "validated":
            return False

        rule.status = "enforced"
        rule.enforcement_mode = "block"  # Upgrade to blocking
        self.session.commit()

        logger.info("Rule promoted to enforced", rule_id=rule_id)
        return True

    def deprecate_rule(self, rule_id: int, reason: str = "low_effectiveness") -> bool:
        """Deprecate a rule

        Args:
            rule_id: Rule ID
            reason: Deprecation reason

        Returns:
            True if deprecated successfully
        """
        rule = self.session.query(DynamicGuardrailModel).filter_by(id=rule_id).first()

        if not rule:
            return False

        rule.status = "deprecated"
        rule.deactivated_at = datetime.utcnow()
        if rule.rule_metadata is None:
            rule.rule_metadata = {}
        rule.rule_metadata["deprecation_reason"] = reason
        self.session.commit()

        logger.info("Rule deprecated", rule_id=rule_id, reason=reason)
        return True

    def track_effectiveness(
        self,
        rule_id: int,
        prevented_failure: bool = False,
        false_positive: bool = False,
        true_positive: bool = False,
    ) -> None:
        """Track rule effectiveness

        Args:
            rule_id: Rule ID
            prevented_failure: If rule prevented a failure
            false_positive: If rule triggered incorrectly
            true_positive: If rule triggered correctly
        """
        today = datetime.utcnow().date()

        # Get or create effectiveness record for today
        effectiveness = (
            self.session.query(RuleEffectivenessModel)
            .filter(
                RuleEffectivenessModel.rule_id == rule_id,
                func.date(RuleEffectivenessModel.date) == today,
            )
            .first()
        )

        if not effectiveness:
            effectiveness = RuleEffectivenessModel(rule_id=rule_id, date=datetime.utcnow())
            self.session.add(effectiveness)

        # Update metrics
        effectiveness.times_triggered += 1

        if prevented_failure:
            effectiveness.prevented_failures += 1
        if false_positive:
            effectiveness.false_positives += 1
        if true_positive:
            effectiveness.true_positives += 1

        self.session.commit()

    def _generate_rule_text(self, pattern: LearnedPatternModel) -> str:
        """Generate rule text from pattern

        Args:
            pattern: Learned pattern

        Returns:
            Rule text
        """
        # Use pattern description as base
        base_text = pattern.description

        # Add context based on category
        if "missing" in base_text.lower():
            return f"MUST include: {base_text}"
        elif "forgot" in base_text.lower() or "omit" in base_text.lower():
            return f"DO NOT forget: {base_text}"
        elif "incorrect" in base_text.lower() or "wrong" in base_text.lower():
            return f"AVOID: {base_text}"
        else:
            return f"LEARNED: {base_text}"

    def _determine_enforcement_mode(self, severity: str) -> str:
        """Determine enforcement mode from severity

        Args:
            severity: Severity level

        Returns:
            Enforcement mode
        """
        modes = {"low": "warn", "medium": "warn", "high": "auto_fix", "critical": "block"}
        return modes.get(severity, "warn")

    def _get_severity_icon(self, severity: str) -> str:
        """Get icon for severity level

        Args:
            severity: Severity level

        Returns:
            Icon string
        """
        icons = {
            "low": "ℹ️",
            "medium": "⚠️",
            "high": "🚨",
            "critical": "🔴",
        }
        return icons.get(severity, "⚠️")

    def _score_by_relevance(
        self,
        guardrails: List[DynamicGuardrailModel],
        prompt: str,
        task_type: Optional[str] = None,
    ) -> List[DynamicGuardrailModel]:
        """Score guardrails by relevance to prompt

        Args:
            guardrails: List of guardrails to score
            prompt: User prompt
            task_type: Task type

        Returns:
            Guardrails with relevance scores added to metadata
        """
        prompt_lower = prompt.lower()

        for gr in guardrails:
            relevance_score = 0.0

            # Keyword overlap in rule text
            rule_words = set(gr.rule_text.lower().split())
            prompt_words = set(prompt_lower.split())
            overlap = len(rule_words & prompt_words)
            if overlap > 0:
                relevance_score += min(overlap * 0.2, 1.0)  # Max 1.0 for keyword overlap

            # Category matching
            category_keywords = {
                "security": ["auth", "security", "token", "permission", "access"],
                "performance": ["slow", "optimize", "performance", "speed", "cache"],
                "quality": ["bug", "error", "fix", "quality", "test"],
                "architecture": ["design", "architecture", "pattern", "structure"],
            }

            if gr.rule_category in category_keywords:
                category_matches = sum(
                    1 for kw in category_keywords[gr.rule_category] if kw in prompt_lower
                )
                if category_matches > 0:
                    relevance_score += min(category_matches * 0.3, 1.0)  # Max 1.0 for category

            # Store relevance score in metadata
            if not gr.rule_metadata:
                gr.rule_metadata = {}
            gr.rule_metadata["relevance_score"] = relevance_score

        return guardrails

    def _calculate_priority_score(
        self, guardrail: DynamicGuardrailModel, task_type: Optional[str] = None
    ) -> float:
        """Calculate priority score for guardrail

        Args:
            guardrail: Guardrail to score
            task_type: Task type

        Returns:
            Priority score (higher = higher priority)
        """
        score = 0.0

        # Relevance score (0-2 points)
        if guardrail.rule_metadata and "relevance_score" in guardrail.rule_metadata:
            score += guardrail.rule_metadata["relevance_score"] * 2.0

        # Confidence (0-2 points)
        score += guardrail.confidence * 2.0

        # Recency bonus (0-1 points) - prefer recently activated rules
        if guardrail.activated_at:
            days_since_activation = (datetime.utcnow() - guardrail.activated_at).days
            recency_score = max(0, 1.0 - (days_since_activation / 30.0))  # Decays over 30 days
            score += recency_score

        # Success rate from effectiveness tracking (0-2 points)
        effectiveness = (
            self.session.query(RuleEffectivenessModel)
            .filter(RuleEffectivenessModel.rule_id == guardrail.id)
            .all()
        )

        if effectiveness:
            total_triggered = sum(e.times_triggered for e in effectiveness)
            prevented = sum(e.prevented_failures for e in effectiveness)
            false_pos = sum(e.false_positives for e in effectiveness)

            if total_triggered > 0:
                success_rate = (prevented - false_pos) / total_triggered
                score += max(0, success_rate * 2.0)  # Max 2 points for 100% success

        # Task type match bonus (0-1 points)
        if task_type and guardrail.task_types and task_type in guardrail.task_types:
            score += 1.0

        # Enforcement mode priority
        enforcement_weights = {"block": 0.5, "auto_fix": 0.3, "warn": 0.1}
        score += enforcement_weights.get(guardrail.enforcement_mode, 0.0)

        return score
