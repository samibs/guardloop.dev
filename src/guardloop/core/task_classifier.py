"""Task Classification System for Guardrail v2

Classifies prompts into task types to determine whether guardrails should be applied.
Enables smart skipping of validation for creative/content tasks.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class TaskClassification:
    """Task classification result"""

    task_type: str  # code, content, creative, mixed, unknown
    confidence: float  # 0.0 to 1.0
    requires_guardrails: bool
    detected_features: Dict[str, float]  # Feature scores
    reasoning: str


class TaskClassifier:
    """Classify user prompts to determine task type and guardrail requirements"""

    # Keyword patterns with weights
    CODE_KEYWORDS = {
        # Programming actions
        "implement": 0.9,
        "code": 0.8,
        "function": 0.8,
        "class": 0.7,
        "method": 0.7,
        "api": 0.8,
        "endpoint": 0.8,
        "database": 0.7,
        "authentication": 0.9,
        "authorization": 0.9,
        "refactor": 0.7,
        "optimize": 0.6,
        "debug": 0.8,
        "fix bug": 0.9,
        "test": 0.6,
        "deploy": 0.7,
        # Technical terms
        "algorithm": 0.7,
        "data structure": 0.8,
        "async": 0.7,
        "promise": 0.6,
        "callback": 0.6,
        "exception": 0.7,
        "import": 0.5,
        "module": 0.6,
        "package": 0.6,
        # Frameworks/Tech
        "react": 0.6,
        "vue": 0.6,
        "angular": 0.6,
        "django": 0.7,
        "flask": 0.7,
        "fastapi": 0.7,
        "express": 0.6,
        "typescript": 0.7,
        "python": 0.6,
        "javascript": 0.6,
    }

    CONTENT_KEYWORDS = {
        "write": 0.7,
        "article": 0.9,
        "blog": 0.9,
        "post": 0.7,
        "documentation": 0.8,
        "guide": 0.8,
        "tutorial": 0.8,
        "readme": 0.9,
        "explain": 0.7,
        "describe": 0.7,
        "summarize": 0.8,
        "paragraph": 0.9,
        "section": 0.6,
        "content": 0.6,
    }

    CREATIVE_KEYWORDS = {
        "create": 0.6,
        "design": 0.7,
        "infographic": 0.9,
        "illustration": 0.9,
        "logo": 0.9,
        "banner": 0.8,
        "poster": 0.9,
        "flyer": 0.9,
        "brochure": 0.9,
        "visual": 0.8,
        "graphic": 0.8,
        "artistic": 0.9,
        "creative": 0.9,
        "mockup": 0.8,
        "wireframe": 0.7,
        "prototype": 0.6,
        "html page": 0.5,  # Could be either creative or code
        "landing page": 0.5,
    }

    # Code indicators (syntax patterns)
    CODE_PATTERNS = [
        r"\bdef\s+\w+",  # Python function
        r"\bfunction\s+\w+",  # JavaScript function
        r"\bclass\s+\w+",  # Class definition
        r"\b(async|await)\b",  # Async patterns
        r"\b(import|from)\s+\w+",  # Imports
        r"\b(if|else|for|while)\b",  # Control flow
        r"[{}\[\]();]",  # Code syntax
        r"===|!==|&&|\|\|",  # Operators
        r"@\w+",  # Decorators/annotations
    ]

    # File extension patterns
    CODE_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".go",
        ".java",
        ".cpp",
        ".c",
        ".rs",
        ".rb",
        ".php",
    }
    CONTENT_EXTENSIONS = {".md", ".txt", ".rst", ".adoc"}
    CREATIVE_EXTENSIONS = {".html", ".svg", ".css", ".scss"}

    def __init__(self, code_threshold: float = 0.6, creative_threshold: float = 0.7):
        """Initialize task classifier

        Args:
            code_threshold: Confidence threshold for code classification
            creative_threshold: Confidence threshold for creative classification
        """
        self.code_threshold = code_threshold
        self.creative_threshold = creative_threshold

    def classify(self, prompt: str) -> TaskClassification:
        """Classify a prompt into task type

        Args:
            prompt: User prompt to classify

        Returns:
            TaskClassification with type, confidence, and guardrail requirement
        """
        prompt_lower = prompt.lower()

        # Calculate feature scores
        features = {
            "code_keywords": self._score_keywords(prompt_lower, self.CODE_KEYWORDS),
            "content_keywords": self._score_keywords(prompt_lower, self.CONTENT_KEYWORDS),
            "creative_keywords": self._score_keywords(prompt_lower, self.CREATIVE_KEYWORDS),
            "code_patterns": self._score_patterns(prompt, self.CODE_PATTERNS),
            "file_extensions": self._score_extensions(prompt_lower),
        }

        # Combine scores with weights
        code_score = (
            features["code_keywords"] * 0.5
            + features["code_patterns"] * 0.3
            + (features["file_extensions"] if features["file_extensions"] > 0 else 0) * 0.2
        )

        creative_score = features["creative_keywords"] * 0.8 + (
            0.2 if ".html" in prompt_lower or ".svg" in prompt_lower else 0
        )

        content_score = features["content_keywords"] * 0.7

        # Determine task type
        task_type, confidence, requires_guardrails, reasoning = self._determine_type(
            code_score, creative_score, content_score, prompt_lower
        )

        classification = TaskClassification(
            task_type=task_type,
            confidence=confidence,
            requires_guardrails=requires_guardrails,
            detected_features=features,
            reasoning=reasoning,
        )

        logger.info(
            "Task classified",
            task_type=task_type,
            confidence=confidence,
            requires_guardrails=requires_guardrails,
            features=features,
        )

        return classification

    def _score_keywords(self, text: str, keywords: Dict[str, float]) -> float:
        """Score text based on keyword presence

        Args:
            text: Text to score
            keywords: Dictionary of keywords and their weights

        Returns:
            Score between 0.0 and 1.0
        """
        total_score = 0.0
        matches = 0

        for keyword, weight in keywords.items():
            if keyword in text:
                total_score += weight
                matches += 1

        # Normalize by number of matches (prevent over-scoring)
        if matches > 0:
            return min(total_score / matches, 1.0)
        return 0.0

    def _score_patterns(self, text: str, patterns: List[str]) -> float:
        """Score text based on regex pattern matches

        Args:
            text: Text to score
            patterns: List of regex patterns

        Returns:
            Score between 0.0 and 1.0
        """
        matches = sum(1 for pattern in patterns if re.search(pattern, text))
        return min(matches / len(patterns), 1.0)

    def _score_extensions(self, text: str) -> float:
        """Score based on file extensions mentioned

        Args:
            text: Text to score

        Returns:
            Score: 1.0 for code, 0.5 for content, -0.5 for creative, 0.0 for none
        """
        for ext in self.CODE_EXTENSIONS:
            if ext in text:
                return 1.0

        for ext in self.CONTENT_EXTENSIONS:
            if ext in text:
                return 0.5

        for ext in self.CREATIVE_EXTENSIONS:
            if ext in text:
                return -0.5  # Negative score for creative

        return 0.0

    def _determine_type(
        self, code_score: float, creative_score: float, content_score: float, prompt: str
    ) -> Tuple[str, float, bool, str]:
        """Determine final task type from scores

        Args:
            code_score: Code classification score
            creative_score: Creative classification score
            content_score: Content classification score
            prompt: Original prompt for context

        Returns:
            Tuple of (task_type, confidence, requires_guardrails, reasoning)
        """
        # Check for clear code indicators
        if code_score >= self.code_threshold:
            return (
                "code",
                code_score,
                True,
                f"High code score ({code_score:.2f}), guardrails required",
            )

        # Check for creative tasks (skip guardrails)
        if creative_score >= self.creative_threshold:
            return (
                "creative",
                creative_score,
                False,
                f"Creative task detected ({creative_score:.2f}), skipping guardrails",
            )

        # Check for content tasks (skip guardrails)
        if content_score >= 0.6:
            return (
                "content",
                content_score,
                False,
                f"Content task detected ({content_score:.2f}), skipping guardrails",
            )

        # Mixed or ambiguous
        if code_score > 0.3 and (creative_score > 0.3 or content_score > 0.3):
            max_score = max(code_score, creative_score, content_score)
            return (
                "mixed",
                max_score,
                True,  # Apply guardrails when uncertain
                f"Mixed task type (code: {code_score:.2f}, creative: {creative_score:.2f}, content: {content_score:.2f}), applying guardrails",
            )

        # Unknown - default to requiring guardrails (safe default)
        return (
            "unknown",
            0.5,
            True,
            "Task type unclear, applying guardrails as safety measure",
        )

    def should_apply_guardrails(self, classification: TaskClassification) -> bool:
        """Determine if guardrails should be applied

        Args:
            classification: Task classification result

        Returns:
            True if guardrails should be applied
        """
        return classification.requires_guardrails
