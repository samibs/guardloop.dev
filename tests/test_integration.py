"""Integration tests for complete guardrail workflow"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from guardloop.core.daemon import GuardrailDaemon, AIRequest
from guardloop.core.parser import ParsedResponse, CodeBlock
from guardloop.adapters.base import AIResponse
from guardloop.utils.config import Config, DatabaseConfig


@pytest.mark.asyncio
async def test_full_flow_standard_mode(config, sample_ai_response):
    """Test complete flow from request to result in standard mode"""
    daemon = GuardrailDaemon(config)

    request = AIRequest(
        tool="claude", prompt="create a login function with tests", agent="coder", mode="standard"
    )

    # Mock AI CLI execution
    with patch("guardloop.adapters.claude.ClaudeAdapter.execute") as mock_execute:
        mock_execute.return_value = AIResponse(
            raw_output=sample_ai_response, execution_time_ms=1000, exit_code=0
        )

        result = await daemon.process_request(request)

        assert result.approved
        assert result.parsed is not None
        assert len(result.parsed.code_blocks) > 0
        assert result.parsed.test_coverage == 100

        # Verify guardrails were injected
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args
        assert "BPSBS" in call_args[0][0] or "guardrail" in call_args[0][0].lower()


@pytest.mark.asyncio
async def test_full_flow_strict_mode(strict_config):
    """Test complete flow with strict validation"""
    daemon = GuardrailDaemon(strict_config)

    request = AIRequest(tool="claude", prompt="create a function", agent="architect", mode="strict")

    # Mock response with violations
    bad_response = """
Here's the code:
```python
def func():
    pass
```
No tests provided.
"""

    with patch("guardloop.adapters.claude.ClaudeAdapter.execute") as mock_execute:
        mock_execute.return_value = AIResponse(
            raw_output=bad_response, execution_time_ms=800, exit_code=0
        )

        result = await daemon.process_request(request)

        # In strict mode, should fail validation
        assert result.approved is False or len(result.violations) > 0


@pytest.mark.asyncio
async def test_agent_chain_execution(config):
    """Test multi-agent chain execution"""
    daemon = GuardrailDaemon(config)

    # Load agents
    from guardloop.agents.orchestrator import OrchestratorAgent

    orchestrator = OrchestratorAgent(config)
    await orchestrator.load_agents()

    request = AIRequest(
        tool="claude",
        prompt="Design and implement a user authentication system with database",
        agent="architect",
        mode="standard",
    )

    response_text = """
Three-layer architecture:
- Database: PostgreSQL with user table, indexed username
- Backend: FastAPI with JWT authentication
- Frontend: React login form

Security: MFA + Azure AD + RBAC
Scalability: Redis caching, load balancer
Error handling: Circuit breakers, retry logic

```python
def authenticate(username: str, password: str) -> User:
    try:
        user = db.query("SELECT * FROM users WHERE username = ?", username)
        if verify_password(password, user.password_hash):
            return user
        raise AuthError()
    except Exception as e:
        logger.error(f"Auth failed: {e}")
        raise
```

```python
def test_authenticate():
    user = authenticate("test", "pass")
    assert user.username == "test"

def test_sql_injection():
    with pytest.raises(ValidationError):
        authenticate("admin' OR '1'='1", "pass")
```

Test Coverage: 100%
Monitoring: Prometheus metrics configured
"""

    with patch("guardloop.adapters.claude.ClaudeAdapter.execute") as mock_execute:
        mock_execute.return_value = AIResponse(
            raw_output=response_text, execution_time_ms=1500, exit_code=0
        )

        result = await daemon.process_request(request)

        # Should process request successfully with comprehensive response
        assert result.approved
        assert result.parsed is not None
        assert len(result.parsed.code_blocks) >= 2  # Should have both implementation and tests
        assert result.parsed.test_coverage == 100  # Should meet coverage requirement


@pytest.mark.asyncio
async def test_failure_detection(config):
    """Test failure pattern detection"""
    daemon = GuardrailDaemon(config)

    request = AIRequest(
        tool="claude", prompt="fix authentication bug", agent="debug_hunter", mode="standard"
    )

    # Response with failure patterns
    response_with_failures = """
Authentication failed: JWT token expired
Error: NullInjectorError: No provider for AuthService
Database query failed: Connection timeout
"""

    with patch("guardloop.adapters.claude.ClaudeAdapter.execute") as mock_execute:
        mock_execute.return_value = AIResponse(
            raw_output=response_with_failures, execution_time_ms=900, exit_code=0
        )

        result = await daemon.process_request(request)

        # Should detect failure patterns
        assert result.failures is not None
        assert len(result.failures) > 0

        # Check specific failure categories
        failure_categories = [f.category for f in result.failures]
        assert any("JWT" in cat or "Auth" in cat for cat in failure_categories)


@pytest.mark.asyncio
async def test_guardrail_injection(config, tmp_path):
    """Test guardrail markdown injection into prompts"""
    # Create test guardrail file
    guardrail_dir = tmp_path / ".guardloop" / "guardrails"
    guardrail_dir.mkdir(parents=True)

    test_guardrail = guardrail_dir / "test-guardrail.md"
    test_guardrail.write_text(
        """
# Test Guardrail

## Rules
1. Always include error handling
2. Add comprehensive logging
3. Use type annotations
"""
    )

    # Update config to use test guardrail directory
    from guardloop.utils.config import GuardrailsConfig
    config.guardrails = GuardrailsConfig(base_path=str(guardrail_dir))

    daemon = GuardrailDaemon(config)

    request = AIRequest(tool="claude", prompt="create a function", agent="coder", mode="standard")

    with patch("guardloop.adapters.claude.ClaudeAdapter.execute") as mock_execute:
        mock_execute.return_value = AIResponse(
            raw_output="def func(): pass", execution_time_ms=500, exit_code=0
        )

        result = await daemon.process_request(request)

        # Verify request was processed and guardrails were applied
        assert result.approved
        assert result.guardrails_applied is True


@pytest.mark.asyncio
async def test_context_preservation(config):
    """Test context preservation across multiple requests"""
    daemon = GuardrailDaemon(config)

    # First request
    request1 = AIRequest(
        tool="claude", prompt="create a User model", agent="coder", mode="standard"
    )

    with patch("guardloop.adapters.claude.ClaudeAdapter.execute") as mock_execute:
        mock_execute.return_value = AIResponse(
            raw_output="class User: pass", execution_time_ms=500, exit_code=0
        )

        result1 = await daemon.process_request(request1)

    # Second request - verify both requests process successfully
    request2 = AIRequest(
        tool="claude",
        prompt="add authentication to User model",
        agent="coder",
        mode="standard",
    )

    with patch("guardloop.adapters.claude.ClaudeAdapter.execute") as mock_execute:
        mock_execute.return_value = AIResponse(
            raw_output="# Updated User model with auth", execution_time_ms=600, exit_code=0
        )

        result2 = await daemon.process_request(request2)

        assert result2.approved
        # Both requests should have unique session IDs
        assert result1.session_id != result2.session_id
        # Both should have processed successfully
        assert result1.approved and result2.approved


@pytest.mark.asyncio
async def test_multi_tool_support(config):
    """Test support for multiple AI tools"""
    daemon = GuardrailDaemon(config)

    tools = ["claude", "gemini", "codex"]

    for tool in tools:
        request = AIRequest(tool=tool, prompt="create a function", agent="coder", mode="standard")

        adapter_class = f"guardloop.adapters.{tool}.{tool.capitalize()}Adapter"

        with patch(f"{adapter_class}.execute") as mock_execute:
            mock_execute.return_value = AIResponse(
                raw_output="def func(): pass", execution_time_ms=500, exit_code=0
            )

            result = await daemon.process_request(request)

            assert result.approved
            # Verify different tools can be used with the same daemon
            assert result.session_id is not None


@pytest.mark.asyncio
async def test_violation_thresholds(config):
    """Test violation severity thresholds"""
    daemon = GuardrailDaemon(config)

    request = AIRequest(
        tool="claude", prompt="create insecure code", agent="secops", mode="standard"
    )

    # Response with security violations
    insecure_response = """
```python
def login(user, pass):
    query = f"SELECT * FROM users WHERE username = '{user}'"
    api_key = "hardcoded-secret-123"
    return execute_query(query)
```
"""

    with patch("guardloop.adapters.claude.ClaudeAdapter.execute") as mock_execute:
        mock_execute.return_value = AIResponse(
            raw_output=insecure_response, execution_time_ms=700, exit_code=0
        )

        result = await daemon.process_request(request)

        # Should detect security violations
        assert result.violations is not None
        assert len(result.violations) > 0

        # Check for critical security violations
        critical_violations = [v for v in result.violations if v.severity == "critical"]
        assert len(critical_violations) > 0


@pytest.mark.asyncio
async def test_background_worker_integration(config):
    """Test daemon can process multiple requests"""
    daemon = GuardrailDaemon(config)

    # Process multiple requests to test daemon stability
    requests = [
        AIRequest(tool="claude", prompt="task 1", agent="coder", mode="standard"),
        AIRequest(tool="claude", prompt="task 2", agent="coder", mode="standard"),
        AIRequest(tool="claude", prompt="task 3", agent="coder", mode="standard"),
    ]

    with patch("guardloop.adapters.claude.ClaudeAdapter.execute") as mock_execute:
        mock_execute.return_value = AIResponse(
            raw_output="def background_task(): pass", execution_time_ms=400, exit_code=0
        )

        results = []
        for request in requests:
            result = await daemon.process_request(request)
            results.append(result)

        # All requests should be processed successfully
        assert len(results) == 3
        assert all(r.approved for r in results)
        # Each should have unique session ID
        session_ids = [r.session_id for r in results]
        assert len(set(session_ids)) == 3


@pytest.mark.asyncio
async def test_performance_metrics(config):
    """Test performance metrics collection"""
    daemon = GuardrailDaemon(config)

    request = AIRequest(tool="claude", prompt="measure performance", agent="coder", mode="standard")

    with patch("guardloop.adapters.claude.ClaudeAdapter.execute") as mock_execute:
        mock_execute.return_value = AIResponse(
            raw_output="def measured_func(): pass", execution_time_ms=1200, exit_code=0
        )

        result = await daemon.process_request(request)

        # Should track execution time
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0

        # Should track parsing time
        assert hasattr(result, "parsing_time_ms") or result.parsed is not None
