"""Shared test fixtures for guardrail tests"""

import pytest
from pathlib import Path
from typing import List

from guardloop.core.daemon import GuardrailDaemon
from guardloop.core.parser import ParsedResponse, CodeBlock
from guardloop.core.validator import Violation
from guardloop.core.failure_detector import DetectedFailure
from guardloop.utils.config import Config, DatabaseConfig, LoggingConfig
from datetime import datetime


@pytest.fixture
def config():
    """Test configuration with in-memory database"""
    return Config(
        mode="standard",
        database=DatabaseConfig(path=":memory:"),
        logging=LoggingConfig(level="DEBUG", file=None),
        tool="claude",
        strict=False,
    )


@pytest.fixture
def strict_config():
    """Strict mode configuration"""
    return Config(
        mode="strict",
        database=DatabaseConfig(path=":memory:"),
        logging=LoggingConfig(level="DEBUG", file=None),
        tool="claude",
        strict=True,
    )


@pytest.fixture
def daemon(config):
    """Guardrail daemon instance"""
    return GuardrailDaemon(config)


@pytest.fixture
def sample_ai_response():
    """Sample AI response with code and tests"""
    return """
Here's the implementation:

```python
def login(username: str, password: str) -> bool:
    \"\"\"Authenticate user with username and password

    Args:
        username: User's username
        password: User's password

    Returns:
        True if authentication successful
    \"\"\"
    try:
        user = db.get_user(username)
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid credentials")
        return True
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise
```

```python
def test_login_success():
    assert login("user", "pass") == True

def test_login_failure():
    with pytest.raises(AuthenticationError):
        login("invalid", "wrong")

def test_sql_injection():
    with pytest.raises(ValidationError):
        login("admin' OR '1'='1", "any")
```

Test Coverage: 100%
Security: MFA + Azure AD configured
Error handling: Comprehensive with logging
"""


@pytest.fixture
def sample_parsed_response():
    """Sample parsed response object"""
    code_blocks = [
        CodeBlock(
            language="python",
            content="""
def login(username: str, password: str) -> bool:
    try:
        user = db.get_user(username)
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid credentials")
        return True
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise
            """,
            file_path="auth.py",
        ),
        CodeBlock(
            language="python",
            content="""
def test_login_success():
    assert login("user", "pass") == True

def test_login_failure():
    with pytest.raises(AuthenticationError):
        login("invalid", "wrong")
            """,
            file_path="test_auth.py",
        ),
    ]

    return ParsedResponse(
        code_blocks=code_blocks,
        file_paths=["auth.py", "test_auth.py"],
        commands=[],
        explanations=["Implementation with authentication and tests"],
        test_coverage=100.0,
        metadata={"security": "MFA + Azure AD"},
    )


@pytest.fixture
def sample_violations():
    """Sample violations list"""
    return [
        Violation(
            guardrail_type="security",
            rule="Input validation",
            severity="high",
            description="Missing input sanitization",
            suggestion="Add input validation and sanitization",
            line_number=5,
            file_path="auth.py",
        ),
        Violation(
            guardrail_type="standards",
            rule="Type annotations",
            severity="medium",
            description="Missing type annotations",
            suggestion="Add type hints to function signature",
            line_number=10,
            file_path="auth.py",
        ),
    ]


@pytest.fixture
def sample_failures():
    """Sample failures list"""
    return [
        DetectedFailure(
            category="JWT/Auth",
            pattern="authentication failed",
            timestamp=datetime.now(),
            severity="high",
            context="User authentication",
            suggestion="Check token validation logic",
            tool="claude",
        ),
        DetectedFailure(
            category="File Overwrite",
            pattern="large code block",
            timestamp=datetime.now(),
            severity="medium",
            context="Full file rewrite detected",
            suggestion="Use incremental edits instead",
            tool="claude",
        ),
    ]


@pytest.fixture
def temp_guardrail_dir(tmp_path):
    """Temporary guardrail directory for tests"""
    guardrail_dir = tmp_path / ".guardrail"
    guardrail_dir.mkdir()

    # Create subdirectories
    (guardrail_dir / "guardrails").mkdir()
    (guardrail_dir / "guardrails" / "agents").mkdir()
    (guardrail_dir / "logs").mkdir()

    return guardrail_dir


@pytest.fixture
def sample_guardrail_files(temp_guardrail_dir):
    """Sample guardrail markdown files"""
    # BPSBS guardrail
    bpsbs_file = temp_guardrail_dir / "guardrails" / "bpsbs.md"
    bpsbs_file.write_text(
        """
# BPSBS Guardrail

## Rules
1. Always use Edit tool for incremental changes
2. Never use Write tool for full file rewrites
3. Include tests with every implementation
4. 100% test coverage required
"""
    )

    # Security guardrail
    security_file = temp_guardrail_dir / "guardrails" / "security.md"
    security_file.write_text(
        """
# Security Guardrail

## Rules
1. MFA + Azure AD required
2. Input validation and sanitization
3. No SQL injection vulnerabilities
4. No hardcoded secrets
"""
    )

    return {"bpsbs": bpsbs_file, "security": security_file}


@pytest.fixture
def sample_agent_instructions(temp_guardrail_dir):
    """Sample agent instruction files"""
    agents_dir = temp_guardrail_dir / "guardrails" / "agents"

    architect_file = agents_dir / "architect.md"
    architect_file.write_text(
        """
# Architect Agent Instructions

## Validation Criteria
1. Clear requirements
2. Three-layer architecture
3. Security measures
4. Scalability design
"""
    )

    return {"architect": architect_file}


@pytest.fixture
def mock_db_session(monkeypatch):
    """Mock database session for testing"""

    class MockSession:
        def __init__(self):
            self.data = {}
            self.committed = False

        def add(self, obj):
            self.data[id(obj)] = obj

        def commit(self):
            self.committed = True

        def query(self, model):
            return MockQuery(self.data)

        def close(self):
            pass

    class MockQuery:
        def __init__(self, data):
            self.data = list(data.values())

        def filter_by(self, **kwargs):
            return self

        def first(self):
            return self.data[0] if self.data else None

        def all(self):
            return self.data

    session = MockSession()
    return session
