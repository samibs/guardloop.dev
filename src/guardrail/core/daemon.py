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
from guardrail.core.adaptive_guardrails import AdaptiveGuardrailGenerator
from guardrail.core.context_manager import ContextManager
from guardrail.core.conversation_manager import ConversationManager
from guardrail.core.failure_detector import FailureDetector, DetectedFailure
from guardrail.core.file_executor import FileExecutor
from guardrail.core.logger import get_logger
from guardrail.core.parser import ParsedResponse, ResponseParser
from guardrail.core.pattern_analyzer import PatternAnalyzer
from guardrail.core.task_classifier import TaskClassifier
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
    conversation_id: Optional[str] = None  # v2: For interactive sessions
    project_root: Optional[str] = None  # v2: For file execution


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
    task_classification: Optional[any] = None  # v2: Task classification result
    file_operations: Optional[List[any]] = None  # v2: Executed file operations
    guardrails_applied: bool = True  # v2: Whether guardrails were applied


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

        # v2 components
        db_session = self.db.get_session()
        self.task_classifier = TaskClassifier()
        self.pattern_analyzer = PatternAnalyzer(db_session)
        self.adaptive_guardrails = AdaptiveGuardrailGenerator(db_session)
        self.conversation_manager = ConversationManager(db_session)
        self.file_executor = None  # Initialized per request with project_root

        # Check if v2 features enabled (will add to config later)
        self.v2_enabled = getattr(config.features, 'v2_adaptive_learning', True)
        self.v2_auto_save = getattr(config.features, 'v2_auto_save_files', True)
        self.v2_task_classification = getattr(config.features, 'v2_task_classification', True)

        logger.info(
            "GuardrailDaemon initialized",
            mode=config.mode,
            enabled_tools=list(config.tools.keys()),
            v2_enabled=self.v2_enabled,
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
        """Main orchestration flow with v2 enhancements

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
            v2_enabled=self.v2_enabled,
        )

        try:
            # v2 STEP 0: Task Classification
            task_classification = None
            guardrails_required = True

            if self.v2_enabled and self.v2_task_classification:
                task_classification = self.task_classifier.classify(request.prompt)
                guardrails_required = task_classification.requires_guardrails

                logger.info(
                    "Task classified",
                    session_id=request.session_id,
                    task_type=task_classification.task_type,
                    confidence=task_classification.confidence,
                    guardrails_required=guardrails_required,
                )

            # v2: Build context with conversation history if interactive
            if request.conversation_id and self.v2_enabled:
                context_prompt = self.conversation_manager.build_context(
                    request.conversation_id, request.prompt
                )
            else:
                context_prompt = request.prompt

            # 1. Load and inject guardrails (skip if not required)
            if guardrails_required:
                db_session = self.db.get_session()
                context = self.context_manager.build_context(
                    prompt=context_prompt,
                    agent=request.agent,
                    mode=request.mode,
                    task_type=task_classification.task_type if task_classification else None,
                    db_session=db_session,
                )
            else:
                # Skip guardrails for creative/content tasks
                context = context_prompt

            logger.debug(
                "Context built",
                session_id=request.session_id,
                context_length=len(context),
                guardrails_applied=guardrails_required,
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

            # v2 STEP 7: File Execution (if enabled and safe)
            file_operations = []
            if self.v2_enabled and self.v2_auto_save and request.project_root:
                self.file_executor = FileExecutor(
                    request.project_root, auto_save_enabled=True
                )
                operations = self.file_executor.extract_operations(ai_response.raw_output)

                if operations:
                    exec_results = self.file_executor.execute_all(
                        operations, confirm_all=False  # Auto-save safe files
                    )
                    file_operations = exec_results.get("created_files", [])

                    logger.info(
                        "File operations executed",
                        session_id=request.session_id,
                        succeeded=exec_results["succeeded"],
                        failed=exec_results["failed"],
                    )

            # v2 STEP 8: Update conversation history (if interactive)
            if request.conversation_id and self.v2_enabled:
                # Add user message
                self.conversation_manager.add_message(
                    request.conversation_id,
                    "user",
                    request.prompt,
                    tokens_used=self.conversation_manager.estimate_tokens(request.prompt),
                )

                # Add assistant response
                self.conversation_manager.add_message(
                    request.conversation_id,
                    "assistant",
                    ai_response.raw_output,
                    tokens_used=self.conversation_manager.estimate_tokens(
                        ai_response.raw_output
                    ),
                )

            # 9. Log session (async, non-blocking)
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
                    task_classification,
                )
            )

            # 10. Return result
            return AIResult(
                raw_output=ai_response.raw_output,
                parsed=parsed,
                violations=violations if guardrails_required else [],
                failures=failures,
                approved=approved,
                execution_time_ms=execution_time,
                session_id=request.session_id,
                task_classification=task_classification,
                file_operations=file_operations,
                guardrails_applied=guardrails_required,
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
        task_classification: Optional[any] = None,
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
            task_classification: Task classification result (v2)
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
