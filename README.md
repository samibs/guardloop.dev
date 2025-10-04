# 🛡️ Guardrail

**Enterprise-Grade Governance for AI-Assisted Development**

[![Tests](https://img.shields.io/badge/tests-173%20passing-brightgreen)](https://github.com/samibs/guardrail.dev)
[![Coverage](https://img.shields.io/badge/coverage-75%25-yellow)](https://github.com/samibs/guardrail.dev)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Guardrail is an intelligent governance system that automatically enforces coding standards, security requirements, and compliance rules across Claude, Gemini, Codex, and other AI tools. Stop reviewing AI output manually—let Guardrail validate it in real-time.

## ✨ Key Features

- 🛡️ **Automatic Guardrail Injection** - Every AI prompt includes your organization's standards
- 🔍 **Real-time Violation Detection** - Catch security issues, bad patterns, and failures before they reach code
- 📊 **AI Failure Analytics** - ML-powered failure pattern detection with actionable insights
- 👥 **Multi-Agent Orchestration** - 13 specialized agents ensure comprehensive quality validation
- 🔐 **Security-First Design** - MFA, Azure AD, RBAC enforced by default
- 📈 **Compliance Tracking** - Built-in support for ISO 27001, GDPR, SOC 2
- 🚀 **Zero Configuration** - Works seamlessly with existing AI CLI tools

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (when published)
pip install guardrail

# Or install from source
git clone https://github.com/samibs/guardrail.dev.git
cd guardrail.dev

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Verify installation
guardrail --version
```

### Initialize

```bash
# Setup guardrail in your project
guardrail init

# This creates:
# ~/.guardrail/
#   ├── config.yaml
#   ├── guardrails/          # Your organization's guardrail rules
#   │   ├── BPSBS.md
#   │   ├── AI_Guardrails.md
#   │   └── agents/
#   ├── data/
#   └── logs/
```

### Use with Any AI Tool

```bash
# Single request (one-shot)
guardrail run claude "implement user authentication"

# Interactive session (for conversations)
guardrail interactive

# Check system status
guardrail status

# View configuration
guardrail config

# Analyze violations and failures
guardrail analyze --days 7

# Export failure reports
guardrail export --output failures.md
```

## 📖 Documentation

- 📚 [Getting Started](docs/getting-started.md)
- ⚙️ [Configuration Guide](docs/configuration.md)
- 🤖 [Agent System](docs/phase5-agents.md)
- 🔌 [API Documentation](docs/api.md)

## 🏗️ Architecture

Guardrail uses 13 specialized agents in orchestrated chains:

1. **Orchestrator** - Routes requests to appropriate specialized agents
2. **Architect** - Ensures system design quality and scalability
3. **Coder** - Enforces implementation best practices (100% test coverage)
4. **Tester** - Validates comprehensive test coverage
5. **SecOps** - Security validation (MFA, injection prevention)
6. **SRE** - Reliability and operational concerns
7. **And 7 more specialized agents...**

## 💡 Usage Examples

### Interactive vs One-Shot Mode

**Interactive Mode** - For conversations with Claude:
```bash
$ guardrail interactive

Select AI tool:
  1. Claude
  2. Gemini
  3. Codex

Tool (1-3): 1

Select mode:
  1. Standard (warn only)
  2. Strict (block violations)

Mode (1-2): 1

✨ Session started: claude in standard mode

>>> implement user authentication
[Claude responds with questions...]

>>> option 2 - create a web application
[Conversation continues...]

>>> exit
```

**One-Shot Mode** - For single requests:
```bash
$ guardrail run claude "create a REST API with FastAPI"
[Response displayed and exits]
```

### Standard Mode (Suggestions)

```bash
$ claude "create login API endpoint"

✅ Implementation validated
⚠️  Suggestions from SecOps:
    - Add input sanitization
    - Implement rate limiting
    
✅ Test coverage: 95%
```

### Strict Mode (Enforcement)

```bash
$ guardrail run claude "create auth system" --mode strict

❌ Blocked by SecOps Agent
   Reason: Missing MFA implementation
   Required: MFA + Azure AD + RBAC
```

## 🛠️ Development

```bash
# Setup
pip install -e ".[dev]"

# Run tests
pytest

# Coverage
pytest --cov=src/guardrail --cov-report=html
```

## 📊 Project Status

- **Tests**: 173 passing
- **Coverage**: 75%
- **Agents**: 13 specialized
- **Guardrails**: 3 built-in + custom support

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

**Made with ❤️ by developers, for developers**
