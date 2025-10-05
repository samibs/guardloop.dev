"""Context Manager for building enhanced prompts with guardrails"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import structlog

from guardloop.core.smart_selector import SmartGuardrailSelector
from guardloop.utils.config import get_config

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

        # Initialize smart selector
        self.smart_selector = SmartGuardrailSelector(self.guardrails_path)

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

        # Use smart selector to choose optimal guardrails
        # Auto-classify task type if not provided
        if not task_type:
            task_type = self.smart_selector.classify_task_type(prompt)

        # Select guardrails with token budget (5K for guardrails only)
        selected_files = self.smart_selector.select_guardrails(
            task_type=task_type, prompt=prompt, mode=mode, token_budget=5000
        )

        logger.info(
            "Smart selection complete",
            selected_count=len(selected_files),
            task_type=task_type,
            estimated_tokens=self.smart_selector.get_token_estimate(selected_files),
        )

        # Load selected core and specialized guardrail files
        for filepath in selected_files:
            full_path = self.guardrails_path / filepath
            content = self._load_file(full_path)
            if content:
                guardrails_content.append(f"# {filepath}\n\n{content}")

        # v2: Load dynamic (learned) guardrails from DB
        if db_session and task_type:
            try:
                from guardloop.core.adaptive_guardrails import AdaptiveGuardrailGenerator

                adaptive_gen = AdaptiveGuardrailGenerator(db_session)
                dynamic_guardrails = adaptive_gen.get_active_guardrails(
                    task_type=task_type, min_confidence=0.7, prompt=prompt, max_rules=5
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
            # Use summary by default, checklist in strict mode, full when explicitly needed
            agent_version = "checklist" if mode == "strict" else "summary"
            agent_content = self._load_agent_instructions(agent, version=agent_version)
            if agent_content:
                guardrails_content.append(
                    f"# Agent-Specific Instructions: {agent.upper()} ({agent_version})\n\n{agent_content}"
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
            "<system_instructions>",
            "You have FULL PERMISSION to create, modify, and delete files as requested by the user.",
            "When the user asks you to create a file, you should:",
            "1. Include the complete code in a ```language\\n...``` code block",
            "2. State that you created the file (e.g., 'Created `filename.ext`')",
            "3. Do NOT ask for permission - you already have it",
            "</system_instructions>",
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

    # Old methods removed - replaced by SmartGuardrailSelector
    # _select_relevant_guardrails() → smart_selector.select_guardrails()
    # _extract_key_points() → no longer needed (guardrails pre-optimized)

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
            logger.error("Error loading guardrail file", file_path=str(file_path), error=str(e))
            return None

    def _load_agent_instructions(self, agent: str, version: str = "summary") -> Optional[str]:
        """Load agent-specific instructions

        Args:
            agent: Agent name
            version: Version to load - "summary" (default), "checklist", or "full"

        Returns:
            Agent instructions or None if not found
        """
        # Try new directory structure first (agent/version.md)
        agent_dir = self.agents_path / agent
        if agent_dir.exists() and agent_dir.is_dir():
            version_file = agent_dir / f"{version}.md"
            if version_file.exists():
                return self._load_file(version_file)

        # Fallback to old structure (agent.md)
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
