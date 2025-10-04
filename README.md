# 🛡️ Guardrail

**Enterprise-Grade Governance for AI-Assisted Development**

[![Tests](https://img.shields.io/badge/tests-173%20passing-brightgreen)](https://github.com/yourusername/guardrail)
[![Coverage](https://img.shields.io/badge/coverage-75%25-yellow)](https://github.com/yourusername/guardrail)
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
# Install from PyPI
pip install guardrail

# Or install from source
git clone https://github.com/yourusername/guardrail.git
cd guardrail
pip install -e .
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
# Guardrail automatically wraps AI tool commands
claude "create a login function with JWT authentication"

# Or use explicitly
guardrail execute --tool claude --prompt "implement user authentication"

# Validate existing code
guardrail validate --file auth.py --agent secops
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
$ guardrail execute --mode strict --tool claude --prompt "create auth system"

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
