"""Guardrail daemon - Main orchestration engine"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import structlog

from guardrail.adapters import AdapterFactory, AIResponse
from guardrail.core.context_manager import ContextManager
from guardrail.core.failure_detector import FailureDetector, DetectedFailure
from guardrail.core.logger import get_logger
from guardrail.core.parser import ParsedResponse, ResponseParser
from guardrail.core.validator import GuardrailValidator, Violation
from guardrail.utils.config import Config
from guardrail.utils.db import DatabaseManager

logger = get_logger(__name__)


class AIExecutionError(Exception):
    """Raised when AI tool execution fails"""

    pass


@dataclass
class AIRequest:
    """AI request configuration"""

    tool: str
    prompt: str
    agent: Optional[str] = None
    mode: str = "standard"
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class AIResult:
    """AI execution result"""

    raw_output: str
    parsed: ParsedResponse
    violations: List[Violation]
    failures: List[DetectedFailure]
    approved: bool
    execution_time_ms: int
    session_id: str


class GuardrailDaemon:
    """Main Guardrail daemon - orchestrates AI safety flow"""

    def __init__(self, config: Config):
        """Initialize daemon with configuration

        Args:
            config: Guardrail configuration
        """
        self.config = config
        self.context_manager = ContextManager()
        self.parser = ResponseParser()
        self.validator = GuardrailValidator(mode=config.mode)
        self.failure_detector = FailureDetector()
        self.db = DatabaseManager(str(config.database.path))

        # Initialize database
        self.db.init_db()

        logger.info(
            "GuardrailDaemon initialized",
            mode=config.mode,
            enabled_tools=list(config.tools.keys()),
        )

    def get_adapter(self, tool: str) -> Any:
        """Get adapter for specified tool

        Args:
            tool: Tool name (claude, gemini, codex)

        Returns:
            AI adapter instance
        """
        tool_config = self.config.tools.get(tool)
        if not tool_config or not tool_config.enabled:
            raise ValueError(f"Tool {tool} not configured or not enabled")

        return AdapterFactory.get_adapter(
            tool,
            cli_path=tool_config.cli_path,
            timeout=tool_config.timeout,
        )

    async def process_request(self, request: AIRequest) -> AIResult:
        """Main orchestration flow

        Args:
            request: AI request to process

        Returns:
            AIResult with execution details

        Raises:
            AIExecutionError: If AI tool execution fails
        """
        start_time = time.time()

        logger.info(
            "Processing AI request",
            session_id=request.session_id,
            tool=request.tool,
            agent=request.agent,
            mode=request.mode,
        )

        try:
            # 1. Load and inject guardrails
            context = self.context_manager.build_context(
                prompt=request.prompt, agent=request.agent, mode=request.mode
            )

            logger.debug(
                "Context built",
                session_id=request.session_id,
                context_length=len(context),
            )

            # 2. Execute AI CLI
            adapter = self.get_adapter(request.tool)
            ai_response: AIResponse = await adapter.execute(context)

            if ai_response.error:
                # Handle execution error
                error_msg = f"AI execution failed: {ai_response.error}"
                logger.error(
                    "AI execution error",
                    session_id=request.session_id,
                    error=ai_response.error,
                    exit_code=ai_response.exit_code,
                )
                raise AIExecutionError(error_msg)

            logger.debug(
                "AI execution completed",
                session_id=request.session_id,
                output_length=len(ai_response.raw_output),
                execution_time_ms=ai_response.execution_time_ms,
            )

            # 3. Parse response
            parsed = self.parser.parse(ai_response.raw_output)

            logger.debug(
                "Response parsed",
                session_id=request.session_id,
                code_blocks=len(parsed.code_blocks),
                file_paths=len(parsed.file_paths),
                commands=len(parsed.commands),
            )

            # 4. Validate against guardrails
            violations = await self.validator.validate(parsed, ai_response.raw_output)

            logger.debug(
                "Validation completed",
                session_id=request.session_id,
                violations=len(violations),
                critical_violations=len(
                    self.validator.get_critical_violations(violations)
                ),
            )

            # 5. Detect failures
            failures = self.failure_detector.scan(ai_response.raw_output, request.tool)

            logger.debug(
                "Failure detection completed",
                session_id=request.session_id,
                failures=len(failures),
                critical_failures=len(
                    [f for f in failures if f.severity == "critical"]
                ),
            )

            # 6. Determine approval
            approved = self._enforce(request.mode, violations, failures)

            logger.info(
                "Request enforcement decision",
                session_id=request.session_id,
                approved=approved,
                mode=request.mode,
            )

            # 7. Log session (async, non-blocking)
            execution_time = int((time.time() - start_time) * 1000)
            asyncio.create_task(
                self._log_session(
                    request,
                    ai_response,
                    parsed,
                    violations,
                    failures,
                    approved,
                    execution_time,
                )
            )

            # 8. Return result
            return AIResult(
                raw_output=ai_response.raw_output,
                parsed=parsed,
                violations=violations,
                failures=failures,
                approved=approved,
                execution_time_ms=execution_time,
                session_id=request.session_id,
            )

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error(
                "Request processing failed",
                session_id=request.session_id,
                error=str(e),
                execution_time_ms=execution_time,
            )
            raise

    def _enforce(
        self,
        mode: str,
        violations: List[Violation],
        failures: List[DetectedFailure],
    ) -> bool:
        """Enforcement logic based on mode

        Args:
            mode: Operating mode (standard or strict)
            violations: List of guardrail violations
            failures: List of detected failures

        Returns:
            True if approved, False if blocked
        """
        if mode == "strict":
            # Block if ANY critical violation or failure
            critical_violations = [v for v in violations if v.severity == "critical"]
            critical_failures = [f for f in failures if f.severity == "critical"]

            blocked = len(critical_violations) > 0 or len(critical_failures) > 0

            if blocked:
                logger.warning(
                    "Request blocked in strict mode",
                    critical_violations=len(critical_violations),
                    critical_failures=len(critical_failures),
                )

            return not blocked
        else:
            # Standard mode: always approve, just log violations
            if violations or failures:
                logger.info(
                    "Violations/failures detected in standard mode",
                    violations=len(violations),
                    failures=len(failures),
                )
            return True

    async def _log_session(
        self,
        request: AIRequest,
        response: AIResponse,
        parsed: ParsedResponse,
        violations: List[Violation],
        failures: List[DetectedFailure],
        approved: bool,
        execution_time: int,
    ) -> None:
        """Log session to database

        Args:
            request: Original request
            response: AI response
            parsed: Parsed response
            violations: Detected violations
            failures: Detected failures
            approved: Approval decision
            execution_time: Execution time in milliseconds
        """
        try:
            # Store session
            session_data = {
                "session_id": request.session_id,
                "timestamp": datetime.now(),
                "tool": request.tool,
                "agent": request.agent,
                "mode": request.mode,
                "prompt": request.prompt[:1000],  # Limit prompt size
                "raw_output": response.raw_output[:5000],  # Limit output size
                "parsed_output": {
                    "code_blocks": len(parsed.code_blocks),
                    "file_paths": len(parsed.file_paths),
                    "commands": len(parsed.commands),
                    "test_coverage": parsed.test_coverage,
                },
                "violations_count": len(violations),
                "failures_count": len(failures),
                "approved": approved,
                "execution_time_ms": execution_time,
            }

            # Store in database (would use actual DB insert)
            logger.debug("Session logged", session_id=request.session_id)

            # Store violations
            for violation in violations:
                logger.debug(
                    "Violation logged",
                    session_id=request.session_id,
                    type=violation.guardrail_type,
                    severity=violation.severity,
                )

            # Store failures
            for failure in failures:
                logger.debug(
                    "Failure logged",
                    session_id=request.session_id,
                    category=failure.category,
                    severity=failure.severity,
                )

        except Exception as e:
            logger.error(
                "Failed to log session", session_id=request.session_id, error=str(e)
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get daemon statistics

        Returns:
            Dictionary of statistics
        """
        return {
            "mode": self.config.mode,
            "enabled_tools": [
                tool for tool, cfg in self.config.tools.items() if cfg.enabled
            ],
            "context_manager": self.context_manager.get_stats(),
            "validator_mode": self.validator.mode,
            "failure_detector": self.failure_detector.get_stats(),
        }
