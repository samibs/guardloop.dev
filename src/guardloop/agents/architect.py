"""Architect agent for system design validation"""

from guardloop.agents.base import AgentContext, AgentDecision, BaseAgent
from guardloop.utils.config import Config


class ArchitectAgent(BaseAgent):
    """Cold-Blooded Architect - System design and architecture validation"""

    def __init__(self, config: Config):
        """Initialize architect agent

        Args:
            config: Guardrail configuration
        """
        super().__init__("architect", "~/.guardrail/guardrails/agents/cold-blooded-architect.md")
        self.config = config

    async def evaluate(self, context: AgentContext) -> AgentDecision:
        """Evaluate architecture and design

        Args:
            context: Agent context

        Returns:
            Agent decision
        """
        suggestions = []
        approved = True
        total_checks = 0
        issues_count = 0

        # Check 1: Clear requirements
        total_checks += 1
        if not self._has_clear_requirements(context.prompt):
            approved = False
            issues_count += 1
            suggestions.append(
                "Requirements are vague. Please specify: file path, framework, expected behavior"
            )

        # Check 2: Three-layer design (DB + Backend + Frontend)
        if context.parsed_response:
            total_checks += 1
            if not self._has_three_layers(context.parsed_response):
                approved = False
                issues_count += 1
                suggestions.append("Must include 3-layer design: Database + Backend + Frontend")

        # Check 3: Security considerations
        total_checks += 1
        if not self._mentions_security(context):
            issues_count += 1
            suggestions.append("Include security measures: MFA + Azure AD + RBAC in design")

        # Check 4: Scalability considerations
        total_checks += 1
        if not self._mentions_scalability(context):
            issues_count += 1
            suggestions.append("Consider scalability: caching, load balancing, horizontal scaling")

        # Check 5: Error handling strategy
        total_checks += 1
        if context.parsed_response and not self._has_error_handling_design(context):
            issues_count += 1
            suggestions.append("Define error handling strategy and fallback mechanisms")

        # Determine next agent
        next_agent = "dba" if approved else None

        # Calculate confidence
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason=(
                "Architecture validation complete"
                if approved
                else "Architecture incomplete or missing critical elements"
            ),
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _has_clear_requirements(self, prompt: str) -> bool:
        """Check if requirements are clear

        Args:
            prompt: User prompt

        Returns:
            True if requirements seem clear
        """
        # Check for specificity indicators
        specificity_indicators = [
            # File/path references
            any(char in prompt for char in [".", "/"]),
            # Framework mentions
            self._contains_keywords(
                prompt,
                [
                    "react",
                    "vue",
                    "angular",
                    "django",
                    "flask",
                    "fastapi",
                    "express",
                    "next.js",
                ],
            ),
            # Behavior specifications
            self._contains_keywords(prompt, ["should", "must", "will", "when", "if", "then"]),
            # Data/model mentions
            self._contains_keywords(prompt, ["model", "schema", "table", "entity", "data"]),
        ]

        # Require at least 2 specificity indicators
        return sum(specificity_indicators) >= 2

    def _has_three_layers(self, parsed) -> bool:
        """Check for three-layer architecture

        Args:
            parsed: Parsed response

        Returns:
            True if all three layers present
        """
        if not parsed or not parsed.code_blocks:
            return False

        # Check for database layer
        has_db = any(
            self._contains_keywords(block.content, ["create table", "schema", "migration", "model"])
            or block.language in ["sql", "postgresql", "mysql"]
            for block in parsed.code_blocks
        )

        # Check for backend layer
        has_backend = any(
            self._contains_keywords(
                block.content, ["router", "controller", "api", "endpoint", "service"]
            )
            or block.language in ["python", "javascript", "typescript", "go", "java"]
            for block in parsed.code_blocks
        )

        # Check for frontend layer
        has_frontend = any(
            self._contains_keywords(
                block.content, ["component", "render", "jsx", "template", "view"]
            )
            or block.language in ["jsx", "tsx", "vue", "html"]
            for block in parsed.code_blocks
        )

        return has_db and has_backend and has_frontend

    def _mentions_security(self, context: AgentContext) -> bool:
        """Check if security is mentioned

        Args:
            context: Agent context

        Returns:
            True if security considerations present
        """
        security_keywords = [
            "mfa",
            "multi-factor",
            "azure ad",
            "oauth",
            "rbac",
            "role-based",
            "authentication",
            "authorization",
            "jwt",
            "token",
            "security",
            "encrypt",
        ]

        # Check in prompt
        if self._contains_keywords(context.prompt, security_keywords):
            return True

        # Check in raw output
        if self._contains_keywords(context.raw_output, security_keywords):
            return True

        # Check in code blocks
        if context.parsed_response and context.parsed_response.code_blocks:
            for block in context.parsed_response.code_blocks:
                if self._contains_keywords(block.content, security_keywords):
                    return True

        return False

    def _mentions_scalability(self, context: AgentContext) -> bool:
        """Check if scalability is mentioned

        Args:
            context: Agent context

        Returns:
            True if scalability considerations present
        """
        scalability_keywords = [
            "cache",
            "redis",
            "memcached",
            "load balanc",
            "horizontal scal",
            "vertical scal",
            "cdn",
            "queue",
            "async",
            "worker",
            "cluster",
        ]

        # Check in prompt or output
        return self._contains_keywords(
            context.prompt, scalability_keywords
        ) or self._contains_keywords(context.raw_output, scalability_keywords)

    def _has_error_handling_design(self, context: AgentContext) -> bool:
        """Check if error handling is designed

        Args:
            context: Agent context

        Returns:
            True if error handling present
        """
        error_keywords = [
            "try",
            "catch",
            "except",
            "error",
            "fallback",
            "retry",
            "timeout",
            "circuit breaker",
        ]

        # Check in code blocks
        if context.parsed_response and context.parsed_response.code_blocks:
            for block in context.parsed_response.code_blocks:
                if self._contains_keywords(block.content, error_keywords):
                    return True

        return False
