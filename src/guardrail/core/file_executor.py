"""File Execution System for Guardrail v2

Safely executes file operations from LLM output with validation and user confirmation.
Enables auto-save for code files when safe.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


class FileOperation:
    """Represents a file operation"""

    def __init__(
        self,
        operation_type: str,
        file_path: str,
        content: Optional[str] = None,
        mode: str = "w",
    ):
        self.operation_type = operation_type  # create, update, delete
        self.file_path = file_path
        self.content = content
        self.mode = mode
        self.validated = False
        self.safety_score = 0.0
        self.warnings = []


class FileExecutor:
    """Execute file operations from LLM output with safety validation"""

    # Dangerous paths/patterns
    SYSTEM_PATHS = {
        "/etc",
        "/bin",
        "/sbin",
        "/usr/bin",
        "/usr/sbin",
        "/boot",
        "/sys",
        "/proc",
        "/dev",
        "C:\\Windows",
        "C:\\Program Files",
    }

    DANGEROUS_PATTERNS = [
        r"\.\.\/",  # Path traversal
        r"\bsudo\b",  # Sudo commands
        r"\brm\s+-rf\b",  # Dangerous delete
        r"\beval\b",  # Code evaluation
        r"\bexec\b",  # Code execution
        r"__import__",  # Dynamic imports
        r"\.exe$",  # Executables
        r"\.bat$",
        r"\.sh$",
    ]

    # Safe file extensions
    SAFE_CODE_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".java",
        ".go",
        ".rs",
        ".cpp",
        ".c",
        ".h",
        ".css",
        ".scss",
        ".html",
        ".json",
        ".yaml",
        ".yml",
        ".md",
        ".txt",
        ".sql",
    }

    def __init__(self, project_root: str, auto_save_enabled: bool = True):
        """Initialize file executor

        Args:
            project_root: Root directory for file operations
            auto_save_enabled: Enable automatic saving of safe files
        """
        self.project_root = Path(project_root).resolve()
        self.auto_save_enabled = auto_save_enabled

    def extract_operations(self, llm_output: str) -> List[FileOperation]:
        """Extract file operations from LLM output

        Args:
            llm_output: Raw LLM output text

        Returns:
            List of file operations
        """
        operations = []

        # Pattern 1: Code blocks with file paths
        # ```python:path/to/file.py
        pattern1 = r"```(\w+):([^\n]+)\n(.*?)```"
        for match in re.finditer(pattern1, llm_output, re.DOTALL):
            lang, file_path, content = match.groups()
            operations.append(
                FileOperation(
                    operation_type="create",
                    file_path=file_path.strip(),
                    content=content.strip(),
                )
            )

        # Pattern 2: Explicit file creation
        # File: path/to/file.py
        # Content: ...
        pattern2 = r"File:\s*([^\n]+)\s*\n\s*Content:\s*(.*?)(?=\n\s*File:|\Z)"
        for match in re.finditer(pattern2, llm_output, re.DOTALL):
            file_path, content = match.groups()
            operations.append(
                FileOperation(
                    operation_type="create",
                    file_path=file_path.strip(),
                    content=content.strip(),
                )
            )

        # Pattern 3: Save to file
        # Save to: path/to/file.py
        pattern3 = r"Save to:\s*([^\n]+)"
        for match in re.finditer(pattern3, llm_output):
            file_path = match.group(1).strip()
            # Look for code block before this
            code_match = re.search(
                r"```(?:\w+)?\n(.*?)```", llm_output[: match.start()], re.DOTALL
            )
            if code_match:
                operations.append(
                    FileOperation(
                        operation_type="create",
                        file_path=file_path,
                        content=code_match.group(1).strip(),
                    )
                )

        logger.info("Extracted file operations", count=len(operations))
        return operations

    def validate_operation(self, operation: FileOperation) -> Tuple[bool, List[str]]:
        """Validate file operation for safety

        Args:
            operation: File operation to validate

        Returns:
            Tuple of (is_safe, warnings)
        """
        warnings = []
        safety_score = 1.0

        # Resolve full path
        try:
            full_path = (self.project_root / operation.file_path).resolve()
        except Exception as e:
            warnings.append(f"Invalid path: {e}")
            return False, warnings

        # Check if path is within project root
        if not str(full_path).startswith(str(self.project_root)):
            warnings.append("Path outside project root (potential path traversal)")
            safety_score -= 0.5

        # Check system paths
        for sys_path in self.SYSTEM_PATHS:
            if str(full_path).startswith(sys_path):
                warnings.append(f"System path detected: {sys_path}")
                return False, warnings

        # Check dangerous patterns in path
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, str(full_path)):
                warnings.append(f"Dangerous pattern in path: {pattern}")
                safety_score -= 0.3

        # Check file extension
        ext = Path(operation.file_path).suffix.lower()
        if ext not in self.SAFE_CODE_EXTENSIONS:
            warnings.append(f"Uncommon file extension: {ext}")
            safety_score -= 0.2

        # Check content if present
        if operation.content:
            # Check for dangerous patterns in content
            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, operation.content):
                    warnings.append(f"Dangerous pattern in content: {pattern}")
                    safety_score -= 0.3

            # Check for hardcoded secrets/credentials
            secret_patterns = [
                r"password\s*=\s*['\"][^'\"]+['\"]",
                r"api_key\s*=\s*['\"][^'\"]+['\"]",
                r"secret\s*=\s*['\"][^'\"]+['\"]",
                r"token\s*=\s*['\"][^'\"]+['\"]",
            ]
            for pattern in secret_patterns:
                if re.search(pattern, operation.content, re.IGNORECASE):
                    warnings.append("Potential hardcoded secret detected")
                    safety_score -= 0.2
                    break

        operation.safety_score = max(safety_score, 0.0)
        operation.warnings = warnings
        operation.validated = True

        is_safe = safety_score >= 0.5 and not any(
            "System path" in w for w in warnings
        )

        logger.debug(
            "Operation validated",
            file=operation.file_path,
            safe=is_safe,
            score=safety_score,
            warnings=len(warnings),
        )

        return is_safe, warnings

    def execute_operation(
        self, operation: FileOperation, confirm: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """Execute file operation

        Args:
            operation: File operation to execute
            confirm: Require confirmation (False for auto-save)

        Returns:
            Tuple of (success, error_message)
        """
        if not operation.validated:
            is_safe, warnings = self.validate_operation(operation)
            if not is_safe:
                return False, f"Unsafe operation: {'; '.join(warnings)}"

        # Check auto-save eligibility
        can_auto_save = (
            self.auto_save_enabled
            and operation.safety_score >= 0.8
            and not operation.warnings
        )

        if confirm and not can_auto_save:
            # In real implementation, this would prompt user
            logger.info(
                "Confirmation required",
                file=operation.file_path,
                score=operation.safety_score,
                warnings=operation.warnings,
            )
            # For now, we'll auto-approve safe operations
            if operation.safety_score < 0.7:
                return False, "User confirmation required but not provided"

        # Execute operation
        try:
            full_path = (self.project_root / operation.file_path).resolve()
            full_path.parent.mkdir(parents=True, exist_ok=True)

            if operation.operation_type == "create" or operation.operation_type == "update":
                with open(full_path, operation.mode) as f:
                    f.write(operation.content or "")

                logger.info(
                    "File operation executed",
                    type=operation.operation_type,
                    file=str(full_path),
                    auto_save=can_auto_save,
                )
                return True, None

            elif operation.operation_type == "delete":
                if full_path.exists():
                    full_path.unlink()
                    logger.info("File deleted", file=str(full_path))
                    return True, None
                else:
                    return False, "File does not exist"

        except Exception as e:
            logger.error("File operation failed", error=str(e), file=operation.file_path)
            return False, str(e)

    def execute_all(
        self, operations: List[FileOperation], confirm_all: bool = True
    ) -> Dict[str, any]:
        """Execute multiple file operations

        Args:
            operations: List of file operations
            confirm_all: Require confirmation for all operations

        Returns:
            Execution summary
        """
        results = {
            "total": len(operations),
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
            "created_files": [],
        }

        for operation in operations:
            success, error = self.execute_operation(operation, confirm=confirm_all)

            if success:
                results["succeeded"] += 1
                results["created_files"].append(operation.file_path)
            elif error and "confirmation required" in error.lower():
                results["skipped"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(
                    {"file": operation.file_path, "error": error}
                )

        logger.info(
            "Batch execution complete",
            total=results["total"],
            succeeded=results["succeeded"],
            failed=results["failed"],
            skipped=results["skipped"],
        )

        return results

    def get_execution_summary(self, llm_output: str) -> str:
        """Get summary of what would be executed

        Args:
            llm_output: LLM output text

        Returns:
            Human-readable summary
        """
        operations = self.extract_operations(llm_output)

        if not operations:
            return "No file operations detected"

        lines = ["📁 Detected File Operations:\n"]

        for op in operations:
            is_safe, warnings = self.validate_operation(op)

            status = "✅" if is_safe else "⚠️"
            lines.append(
                f"{status} {op.operation_type.upper()}: {op.file_path}"
            )

            if warnings:
                for warning in warnings:
                    lines.append(f"   ⚠️  {warning}")

            if op.safety_score < 0.7:
                lines.append("   ℹ️  Requires manual confirmation")
            elif op.safety_score >= 0.8:
                lines.append("   🔒 Auto-save eligible")

            lines.append("")

        return "\n".join(lines)
