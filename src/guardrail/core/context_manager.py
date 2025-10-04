"""Context Manager for building enhanced prompts with guardrails"""

import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import structlog

from guardrail.utils.config import get_config

logger = structlog.get_logger(__name__)


class GuardrailCache:
    """Cache for guardrail content with TTL"""

    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[str, datetime]] = {}

    def get(self, key: str) -> Optional[str]:
        """Get cached content if not expired"""
        if key not in self._cache:
            return None

        content, timestamp = self._cache[key]
        if datetime.now() - timestamp > timedelta(seconds=self.ttl_seconds):
            del self._cache[key]
            return None

        return content

    def set(self, key: str, content: str) -> None:
        """Cache content with timestamp"""
        self._cache[key] = (content, datetime.now())

    def clear(self) -> None:
        """Clear all cached content"""
        self._cache.clear()

    def invalidate(self, key: str) -> None:
        """Invalidate specific cache entry"""
        if key in self._cache:
            del self._cache[key]


class ContextManager:
    """Manages context building with guardrails for AI prompts"""

    # Agent names mapping
    AGENTS = [
        "orchestrator",
        "architect",
        "coder",
        "tester",
        "reviewer",
        "security",
        "performance",
        "ux",
        "docs",
        "refactor",
        "debug",
        "deployment",
        "integration",
    ]

    # Token limits (approximate)
    MAX_CONTEXT_TOKENS = 50000  # Conservative limit
    CHARS_PER_TOKEN = 4  # Rough estimate

    def __init__(self, cache_ttl: int = 300):
        self.config = get_config()
        self.cache = GuardrailCache(ttl_seconds=cache_ttl)
        self.guardrails_path = Path(self.config.guardrails.base_path).expanduser()
        self.agents_path = Path(self.config.guardrails.agents_path).expanduser()

        logger.info(
            "ContextManager initialized",
            guardrails_path=str(self.guardrails_path),
            agents_path=str(self.agents_path),
            cache_ttl=cache_ttl,
        )

    def load_guardrails(
        self,
        agent: Optional[str] = None,
        mode: str = "standard",
        prompt: str = "",
        task_type: Optional[str] = None,
        db_session: Optional[any] = None,
    ) -> str:
        """Load relevant guardrails based on agent, mode, and prompt content

        Args:
            agent: Optional agent name (orchestrator, architect, etc.)
            mode: Operating mode (standard or strict)
            prompt: User prompt to analyze for relevance
            task_type: Task type from classifier (v2)
            db_session: Database session for loading dynamic guardrails (v2)

        Returns:
            Combined guardrail content as string
        """
        cache_key = f"guardrails_{agent}_{mode}_{task_type or 'none'}"

        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug("Guardrails loaded from cache", cache_key=cache_key)
            return cached

        logger.info("Loading guardrails", agent=agent, mode=mode, task_type=task_type)

        guardrails_content = []

        # Smart selection: Only load relevant guardrails based on prompt keywords
        relevant_files = self._select_relevant_guardrails(prompt)

        # Load only relevant core guardrail files
        for filename in relevant_files:
            if filename in self.config.guardrails.files:
                content = self._load_file(self.guardrails_path / filename)
                if content:
                    # Extract only key points (summaries/rules) to reduce size
                    summarized = self._extract_key_points(content, filename)
                    guardrails_content.append(f"# {filename}\n\n{summarized}")

        # v2: Load dynamic (learned) guardrails from DB
        if db_session and task_type:
            try:
                from guardrail.core.adaptive_guardrails import AdaptiveGuardrailGenerator

                adaptive_gen = AdaptiveGuardrailGenerator(db_session)
                dynamic_guardrails = adaptive_gen.get_active_guardrails(
                    task_type=task_type, min_confidence=0.7
                )

                if dynamic_guardrails:
                    dynamic_text = adaptive_gen.format_for_context(dynamic_guardrails)
                    guardrails_content.append(dynamic_text)

                    logger.info(
                        "Dynamic guardrails loaded",
                        count=len(dynamic_guardrails),
                        task_type=task_type,
                    )
            except Exception as e:
                logger.warning("Failed to load dynamic guardrails", error=str(e))

        # Load agent-specific instructions
        if agent and agent in self.AGENTS:
            agent_content = self._load_agent_instructions(agent)
            if agent_content:
                # Agents are typically smaller, include full content
                guardrails_content.append(
                    f"# Agent-Specific Instructions: {agent.upper()}\n\n{agent_content}"
                )

        # Combine all content
        combined = "\n\n---\n\n".join(guardrails_content)

        # Cache the result
        self.cache.set(cache_key, combined)

        # Warn if content is too large
        self._check_token_count(combined)

        return combined

    def build_context(
        self,
        prompt: str,
        agent: Optional[str] = None,
        mode: str = "standard",
        task_type: Optional[str] = None,
        db_session: Optional[any] = None,
    ) -> str:
        """Build complete context with guardrails and user prompt

        Args:
            prompt: User's original prompt
            agent: Optional agent name
            mode: Operating mode (standard or strict)
            task_type: Task type from classifier (v2)
            db_session: Database session for dynamic guardrails (v2)

        Returns:
            Complete enhanced prompt with guardrails
        """
        logger.info(
            "Building context",
            agent=agent,
            mode=mode,
            task_type=task_type,
            prompt_length=len(prompt),
        )

        guardrails = self.load_guardrails(
            agent=agent, mode=mode, prompt=prompt, task_type=task_type, db_session=db_session
        )

        # Build structured context
        context_parts = [
            "<guardrails>",
            guardrails,
            f"\n<mode>{mode}</mode>",
            self._get_mode_instructions(mode),
            "</guardrails>",
            "",
            "<user_request>",
            prompt,
            "</user_request>",
        ]

        full_context = "\n".join(context_parts)

        # Final token check
        self._check_token_count(full_context, is_final=True)

        logger.info(
            "Context built successfully",
            total_length=len(full_context),
            estimated_tokens=self._estimate_tokens(full_context),
        )

        return full_context

    def _select_relevant_guardrails(self, prompt: str) -> List[str]:
        """Select relevant guardrail files based on prompt content

        Args:
            prompt: User prompt to analyze

        Returns:
            List of relevant guardrail filenames
        """
        prompt_lower = prompt.lower()

        # Keywords for each guardrail type
        guardrail_keywords = {
            "BPSBS.md": [
                "authentication", "security", "mfa", "azure", "rbac", "login",
                "auth", "user", "permission", "access", "token", "session"
            ],
            "AI_Guardrails.md": [
                "ai", "llm", "prompt", "model", "claude", "gemini", "openai",
                "training", "inference", "embedding", "vector", "ml", "machine learning"
            ],
            "UX_UI_Guardrails.md": [
                "ui", "ux", "interface", "component", "design", "responsive",
                "accessibility", "frontend", "react", "vue", "css", "button", "form"
            ],
        }

        relevant = []

        # Check each guardrail file for keyword matches
        for filename, keywords in guardrail_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                relevant.append(filename)

        # If no specific match, include BPSBS (core standards) only
        if not relevant:
            relevant.append("BPSBS.md")

        logger.debug("Selected relevant guardrails", files=relevant, prompt_preview=prompt[:100])
        return relevant

    def _extract_key_points(self, content: str, filename: str) -> str:
        """Extract key points/rules from guardrail content to reduce size

        Args:
            content: Full guardrail content
            filename: Guardrail filename for context

        Returns:
            Summarized key points
        """
        lines = content.split('\n')
        key_points = []
        in_rule_section = False

        for line in lines:
            line_stripped = line.strip()

            # Keep headers
            if line_stripped.startswith('#'):
                key_points.append(line)
                in_rule_section = True
                continue

            # Keep bullet points (rules/requirements)
            if line_stripped.startswith(('-', '*', '•')):
                key_points.append(line)
                continue

            # Keep numbered lists
            if line_stripped and line_stripped[0].isdigit() and '.' in line_stripped[:3]:
                key_points.append(line)
                continue

            # Keep "MUST", "REQUIRED", "CRITICAL" lines
            if any(keyword in line_stripped.upper() for keyword in ['MUST', 'REQUIRED', 'CRITICAL', 'MANDATORY']):
                key_points.append(line)
                continue

            # Add blank lines for readability (but limit consecutive blanks)
            if not line_stripped and key_points and key_points[-1].strip():
                key_points.append('')

        # Join and clean up
        summarized = '\n'.join(key_points)

        # Remove excessive blank lines
        while '\n\n\n' in summarized:
            summarized = summarized.replace('\n\n\n', '\n\n')

        reduction = (1 - len(summarized) / len(content)) * 100
        logger.debug(
            "Extracted key points",
            filename=filename,
            original_size=len(content),
            summarized_size=len(summarized),
            reduction_percent=f"{reduction:.1f}%"
        )

        return summarized.strip()

    def _load_file(self, file_path: Path) -> Optional[str]:
        """Load content from a file with error handling

        Args:
            file_path: Path to the file to load

        Returns:
            File content or None if error
        """
        try:
            if not file_path.exists():
                logger.warning("Guardrail file not found", file_path=str(file_path))
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                logger.warning("Guardrail file is empty", file_path=str(file_path))
                return None

            logger.debug("Loaded guardrail file", file_path=str(file_path), size=len(content))
            return content

        except Exception as e:
            logger.error(
                "Error loading guardrail file", file_path=str(file_path), error=str(e)
            )
            return None

    def _load_agent_instructions(self, agent: str) -> Optional[str]:
        """Load agent-specific instructions

        Args:
            agent: Agent name

        Returns:
            Agent instructions or None if not found
        """
        agent_file = self.agents_path / f"{agent}.md"
        return self._load_file(agent_file)

    def _get_mode_instructions(self, mode: str) -> str:
        """Get mode-specific instructions

        Args:
            mode: Operating mode (standard or strict)

        Returns:
            Mode-specific instructions
        """
        if mode == "strict":
            return """
<strict_mode_instructions>
STRICT MODE ENABLED - Enhanced Validation:
- All security requirements are MANDATORY
- Test coverage must be >= 100%
- All guardrail violations must be addressed before approval
- No shortcuts or workarounds allowed
- Complete documentation required
- Full compliance with BPSBS, AI, and UX/UI guardrails
- Any violation results in REJECTION
</strict_mode_instructions>
"""
        else:
            return """
<standard_mode_instructions>
STANDARD MODE - Balanced Validation:
- Follow guardrails as guidance
- Address critical and high-severity violations
- Aim for comprehensive test coverage
- Document major decisions and changes
- Consider security and UX best practices
</standard_mode_instructions>
"""

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        return len(text) // self.CHARS_PER_TOKEN

    def _check_token_count(self, text: str, is_final: bool = False) -> None:
        """Check if token count is within limits and warn if needed

        Args:
            text: Text to check
            is_final: Whether this is the final context check
        """
        estimated_tokens = self._estimate_tokens(text)

        if estimated_tokens > self.MAX_CONTEXT_TOKENS:
            logger.warning(
                "Context size exceeds recommended limit",
                estimated_tokens=estimated_tokens,
                max_tokens=self.MAX_CONTEXT_TOKENS,
                is_final=is_final,
            )

            if is_final:
                logger.error(
                    "ALERT: Final context is too large - may cause issues",
                    estimated_tokens=estimated_tokens,
                    chars=len(text),
                )

    def refresh_cache(self) -> None:
        """Manually refresh all cached content"""
        logger.info("Refreshing guardrail cache")
        self.cache.clear()

    def get_available_agents(self) -> List[str]:
        """Get list of available agents

        Returns:
            List of agent names
        """
        return self.AGENTS.copy()

    def validate_agent(self, agent: str) -> bool:
        """Validate if agent exists

        Args:
            agent: Agent name to validate

        Returns:
            True if agent is valid
        """
        return agent in self.AGENTS

    def get_guardrail_files_status(self) -> Dict[str, bool]:
        """Check which guardrail files exist

        Returns:
            Dictionary mapping file names to existence status
        """
        status = {}

        # Check core guardrail files
        for filename in self.config.guardrails.files:
            file_path = self.guardrails_path / filename
            status[filename] = file_path.exists()

        # Check agent files
        for agent in self.AGENTS:
            agent_file = self.agents_path / f"{agent}.md"
            status[f"agents/{agent}.md"] = agent_file.exists()

        return status

    def get_stats(self) -> Dict[str, any]:
        """Get context manager statistics

        Returns:
            Dictionary with statistics
        """
        file_status = self.get_guardrail_files_status()
        total_files = len(file_status)
        existing_files = sum(1 for exists in file_status.values() if exists)

        return {
            "cache_size": len(self.cache._cache),
            "cache_ttl_seconds": self.cache.ttl_seconds,
            "total_guardrail_files": total_files,
            "existing_guardrail_files": existing_files,
            "missing_guardrail_files": total_files - existing_files,
            "available_agents": len(self.AGENTS),
            "guardrails_path": str(self.guardrails_path),
            "agents_path": str(self.agents_path),
        }
