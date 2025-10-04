# Guardrail Testing Guide

## Local Testing Instructions

This guide will help you test Guardrail locally before deployment.

## Prerequisites

- Python 3.10, 3.11, or 3.12
- Virtual environment activated
- Package installed in development mode

## Installation for Testing

```bash
# Activate virtual environment
source venv/bin/activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
guardrail --version
# Should output: guardrail, version 1.0.0
```

## Test Suite

### 1. Run All Tests

```bash
# Run all tests with coverage
pytest --cov=src/guardrail --cov-report=html --cov-report=term-missing -v

# Expected output:
# - 173 tests passing
# - 75%+ coverage
```

### 2. Run Specific Test Categories

```bash
# Core engine tests
pytest tests/test_core/ -v

# Agent tests
pytest tests/test_agents/ -v

# Adapter tests
pytest tests/test_adapters/ -v

# Integration tests
pytest tests/test_integration.py -v

# CLI tests
pytest tests/test_cli/ -v
```

### 3. Code Quality Checks

```bash
# Run black formatter (check only)
black --check src/ tests/

# Run ruff linter
ruff check src/

# Run mypy type checker
mypy src/ --ignore-missing-imports
```

## Manual Testing

### Test 1: CLI Commands

```bash
# Test help command
guardrail --help

# Test init command (creates ~/.guardrail directory)
guardrail init

# Test version command
guardrail --version
```

### Test 2: Configuration

```bash
# Check if config was created
ls -la ~/.guardrail/
cat ~/.guardrail/config.yaml

# Expected structure:
# ~/.guardrail/
#   ├── config.yaml
#   ├── guardrails/
#   ├── data/
#   └── logs/
```

### Test 3: Database

```bash
# Check database creation
ls -la ~/.guardrail/data/
sqlite3 ~/.guardrail/data/guardrail.db ".tables"

# Expected tables:
# - requests
# - violations
# - failures
# - agent_decisions
```

### Test 4: Mock AI Request

Create a test script to simulate AI interaction:

```python
# test_mock_request.py
import asyncio
from guardrail.core.daemon import GuardrailDaemon, AIRequest
from guardrail.utils.config import Config, DatabaseConfig

async def test_request():
    config = Config(
        mode="standard",
        database=DatabaseConfig(path=":memory:"),
        default_agent="coder"
    )

    daemon = GuardrailDaemon(config)

    request = AIRequest(
        tool="claude",
        prompt="create a simple login function",
        agent="coder",
        mode="standard"
    )

    # This will fail gracefully if Claude CLI is not installed
    # but will test the daemon workflow
    try:
        result = await daemon.process_request(request)
        print(f"Success: {result.success}")
        print(f"Tool: {result.tool}")
        print(f"Agent: {result.agent}")
    except Exception as e:
        print(f"Expected error (Claude CLI not configured): {e}")

if __name__ == "__main__":
    asyncio.run(test_request())
```

Run it:
```bash
python test_mock_request.py
```

## Package Build Testing

### Test Package Build

```bash
# Clean previous builds
rm -rf dist/ build/ src/guardrail.egg-info/

# Build package
python -m build

# Verify build artifacts
ls -lh dist/
# Should see:
# - guardrail-1.0.0.tar.gz (~54KB)
# - guardrail-1.0.0-py3-none-any.whl (~61KB)
```

### Test Package Installation

```bash
# Create a new test virtual environment
python -m venv test_venv
source test_venv/bin/activate

# Install from wheel
pip install dist/guardrail-1.0.0-py3-none-any.whl

# Test installation
guardrail --version
guardrail --help

# Test init in clean environment
guardrail init

# Deactivate and remove test environment
deactivate
rm -rf test_venv
```

## Integration Testing Scenarios

### Scenario 1: Standard Mode (Suggestions)

Test that guardrails provide suggestions without blocking:

```bash
# This requires Claude CLI to be installed
# guardrail execute --tool claude --prompt "create a login endpoint" --mode standard
```

Expected behavior:
- AI generates code
- Guardrails analyze output
- Suggestions provided (warnings, not blockers)

### Scenario 2: Strict Mode (Enforcement)

Test that strict mode blocks violations:

```bash
# guardrail execute --tool claude --prompt "create auth without MFA" --mode strict
```

Expected behavior:
- AI generates code
- Guardrails detect violations (missing MFA)
- Request blocked with clear error message

### Scenario 3: Agent Chain

Test multi-agent orchestration:

```bash
# guardrail execute --tool claude --prompt "design and implement user authentication" --agent architect
```

Expected behavior:
- Orchestrator routes to architect
- Architect analyzes requirements
- Chain to coder, tester, secops as needed

## Performance Testing

### Test Response Time

```python
# test_performance.py
import asyncio
import time
from guardrail.core.daemon import GuardrailDaemon, AIRequest
from guardrail.utils.config import Config, DatabaseConfig

async def performance_test():
    config = Config(
        mode="standard",
        database=DatabaseConfig(path=":memory:")
    )

    daemon = GuardrailDaemon(config)

    start = time.time()

    request = AIRequest(
        tool="claude",
        prompt="test performance",
        agent="coder",
        mode="standard"
    )

    try:
        await daemon.process_request(request)
    except:
        pass  # Expected if Claude not configured

    elapsed = time.time() - start
    print(f"Processing time: {elapsed:.3f}s")

    # Should be < 1s for daemon initialization and processing
    assert elapsed < 5.0, "Performance degradation detected"

if __name__ == "__main__":
    asyncio.run(performance_test())
```

## Security Testing

### Test 1: SQL Injection Detection

```python
# Should be detected by parser
malicious_code = """
def login(username):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return db.execute(query)
"""
```

### Test 2: Secret Detection

```python
# Should be flagged by security validator
code_with_secret = """
API_KEY = "sk-1234567890abcdef"
PASSWORD = "hardcoded123"
"""
```

### Test 3: XSS Prevention

```python
# Should be detected
xss_code = """
def render_user_input(user_data):
    return f"<div>{user_data}</div>"  # No sanitization
"""
```

## Common Issues & Solutions

### Issue 1: Import Errors

```bash
# Solution: Reinstall in development mode
pip install -e ".[dev]"
```

### Issue 2: Database Locked

```bash
# Solution: Close other connections or use :memory:
rm ~/.guardrail/data/guardrail.db
guardrail init
```

### Issue 3: Test Failures

```bash
# Solution: Check test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run with verbose output
pytest -vv --tb=short
```

### Issue 4: Coverage Below Threshold

```bash
# Check which files need more tests
coverage report --show-missing

# Focus on files with <75% coverage
```

## Continuous Testing

### Pre-commit Hook Testing

```bash
# Install pre-commit hooks
pre-commit install

# Test hooks on all files
pre-commit run --all-files

# Expected: black, ruff, mypy checks pass
```

### GitHub Actions Local Testing

```bash
# Install act (GitHub Actions local runner)
# brew install act  # macOS
# or download from: https://github.com/nektos/act

# Run test workflow locally
act -j test

# Run lint workflow
act -j lint
```

## Test Coverage Goals

- **Overall**: 75%+ (current)
- **Target**: 90%+
- **Core Engine**: 80%+
- **Agents**: 70%+
- **Adapters**: 75%+
- **CLI**: 65%+

## Test Reporting

### Generate HTML Coverage Report

```bash
pytest --cov=src/guardrail --cov-report=html
open htmlcov/index.html  # macOS/Linux
# or
start htmlcov/index.html  # Windows
```

### Generate XML Coverage Report (for CI)

```bash
pytest --cov=src/guardrail --cov-report=xml
cat coverage.xml
```

## Testing Checklist

Before deployment, ensure:

- [ ] All 173 tests passing
- [ ] Coverage ≥75%
- [ ] Black formatting passes
- [ ] Ruff linting passes
- [ ] Mypy type checking passes (with --ignore-missing-imports)
- [ ] Security checks pass (bandit, safety)
- [ ] Package builds successfully
- [ ] Package installs in clean environment
- [ ] CLI commands work (--help, --version, init)
- [ ] Database initializes correctly
- [ ] Pre-commit hooks installed and passing

## Next Steps After Testing

1. Fix any failing tests
2. Increase coverage to 90%+
3. Document any known issues
4. Prepare for PyPI upload
5. Test installation from PyPI (Test PyPI first)

---

**Last Updated**: 2025-10-04
**Guardrail Version**: 1.0.0
