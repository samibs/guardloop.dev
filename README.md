# 🛡️ Guardrail v2

**Self-Learning AI Governance System**

[![Tests](https://img.shields.io/badge/tests-173%20passing-brightgreen)](https://github.com/samibs/guardrail.dev)
[![Coverage](https://img.shields.io/badge/coverage-75%25-yellow)](https://github.com/samibs/guardrail.dev)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Guardrail is a **self-improving AI governance system** that learns from LLM mistakes, generates dynamic guardrails, and prevents repeated failures. It automatically enforces coding standards, security requirements, and compliance rules across Claude, Gemini, Codex, and other AI tools.

## 🎯 What Makes v2 Different?

**The Problem**: Static guardrails miss evolving LLM failure patterns. You repeat the same mistakes.

**The Solution**: Guardrail v2 captures ALL LLM interactions → Analyzes failure patterns → Generates dynamic guardrails → Reminds LLM not to repeat mistakes.

## ✨ Key Features

### **Version 2 (Adaptive Learning)**
- 🧠 **Adaptive Learning System** - Analyzes DB for LLM failure patterns and auto-generates guardrails
- 🎯 **Task Classification** - Detects code vs content/creative tasks, skips guardrails when irrelevant
- 💾 **Auto-Save Files** - Safely executes file operations from LLM output with validation
- 💬 **Conversation History** - Maintains context across interactive sessions for proper Q&A flow
- 📈 **Dynamic Guardrails** - Learned rules from real failures, not just static templates

### **Version 1 (Foundation)**
- 🛡️ **Automatic Guardrail Injection** - Every AI prompt includes your organization's standards
- 🔍 **Real-time Violation Detection** - Catch security issues, bad patterns, and failures before they reach code
- 📊 **AI Failure Analytics** - ML-powered failure pattern detection with actionable insights
- 👥 **Multi-Agent Orchestration** - 13 specialized agents ensure comprehensive quality validation
- 🔐 **Security-First Design** - MFA, Azure AD, RBAC enforced by default
- 📈 **Compliance Tracking** - Built-in support for ISO 27001, GDPR, SOC 2

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
- 🧠 **v2**: [Adaptive Learning](docs/adaptive-learning.md)
- 🎯 **v2**: [Task Classification](docs/task-classification.md)
- 💾 **v2**: [File Safety System](docs/file-safety.md)

## 🏗️ Architecture

### v2: Adaptive Learning Pipeline

```
LLM Interaction → Database → Pattern Analysis → Guardrail Generation → Enforcement
      ↓              ↓              ↓                    ↓                 ↓
   Capture       Store All      Find Patterns      Create Rules      Prevent Repeats
```

**Core v2 Components**:

1. **TaskClassifier** - Determines if guardrails are needed (code vs creative)
2. **PatternAnalyzer** - Extracts recurring failures from database
3. **AdaptiveGuardrailGenerator** - Creates and manages dynamic rules
4. **ConversationManager** - Maintains context across interactive sessions
5. **FileExecutor** - Safely executes file operations with validation
6. **ContextManager** - Injects static + dynamic guardrails into LLM context

### v1: Multi-Agent System

Guardrail uses 13 specialized agents in orchestrated chains:

1. **Orchestrator** - Routes requests to appropriate specialized agents
2. **Architect** - Ensures system design quality and scalability
3. **Coder** - Enforces implementation best practices (100% test coverage)
4. **Tester** - Validates comprehensive test coverage
5. **SecOps** - Security validation (MFA, injection prevention)
6. **SRE** - Reliability and operational concerns
7. **And 7 more specialized agents...**

## 💡 Usage Examples

### v2: Task Classification in Action

**Code Task** - Guardrails applied:
```bash
>>> implement user authentication with JWT

📋 Task: code (confidence: 0.95)
🛡️ Guardrails: ✅ Applied (static + 12 learned rules)

✅ Implementation validated
⚠️  Suggestions from SecOps:
    - Add input sanitization
    - Implement rate limiting

💾 Created 3 file(s):
    - auth/jwt_manager.py (auto-saved)
    - auth/middleware.py (auto-saved)
    - tests/test_auth.py (auto-saved)
```

**Creative Task** - Guardrails skipped:
```bash
>>> create an HTML infographic showing our product features

📋 Task: creative (confidence: 0.92)
🛡️ Guardrails: ⏭️  Skipped (not a code task)

✨ Generated infographic.html
💾 Created 1 file(s):
    - marketing/infographic.html (auto-saved)
```

### v2: Interactive Mode with Conversation History

**Multi-turn conversation** - Context maintained:
```bash
$ guardrail interactive

✨ Session started: claude in standard mode

>>> implement user authentication
[Claude responds with authentication options...]

>>> option 2 - create a web application with OAuth
💬 Conversation: Turn 2 (context: 1.2K tokens)
[Claude remembers your choice and implements OAuth...]

>>> add password reset functionality
💬 Conversation: Turn 3 (context: 2.8K tokens)
[Claude adds reset to the existing auth system...]

>>> exit
```

### v2: Adaptive Learning System

**Pattern Detection**:
```bash
# After 5 sessions where Claude forgot to add error handling
$ guardrail analyze --days 7

📊 Analysis Results:
   - 5 failures: Missing try-catch blocks in async functions
   - Confidence: 0.85
   - Severity: high

🧠 Generated Dynamic Guardrail:
   "Always wrap async database calls in try-catch blocks"
   Status: validated → enforced
```

**Learned Guardrail in Action**:
```bash
>>> create a user service with database queries

🛡️ Guardrails: ✅ Applied (static + 13 learned rules)
📈 Learned Rule #7: "Always wrap async database calls in try-catch blocks"

[Claude's implementation includes proper error handling...]

✅ Implementation validated (no violations)
```

### Standard Mode (Suggestions)

```bash
$ guardrail run claude "create login API endpoint"

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

## ⚙️ v2: Configuration & Pattern Management

### Feature Flags

Control v2 features in `~/.guardrail/config.yaml`:

```yaml
features:
  # v2 Adaptive Learning
  v2_adaptive_learning: true     # Enable pattern analysis & dynamic guardrails
  v2_task_classification: true    # Classify code vs creative tasks
  v2_auto_save_files: true       # Auto-save safe file operations
  v2_conversation_history: true  # Maintain context across turns
  v2_dynamic_guardrails: true    # Load learned rules from DB
```

### Pattern Analysis

```bash
# Analyze recent failures and generate guardrails
guardrail analyze --days 30

# View learned patterns
guardrail patterns list

# Promote a trial guardrail to enforced
guardrail patterns promote <pattern_id>

# Deprecate outdated guardrail
guardrail patterns deprecate <pattern_id>

# Export learned guardrails
guardrail patterns export --output learned_rules.md
```

### Guardrail Lifecycle

```
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐
│  trial  │ ──> │validated │ ──> │ enforced │ ──> │ deprecated │
└─────────┘     └──────────┘     └──────────┘     └────────────┘
   3+ uses        confidence       production        obsolete
               score >= 0.7       ready             or wrong
```

### File Safety Settings

Control auto-save behavior:

```yaml
file_executor:
  auto_save_enabled: true
  safe_extensions: [".py", ".js", ".ts", ".json", ".md", ".txt"]
  min_safety_score: 0.8          # 0.0-1.0
  require_confirmation_for:
    - system_paths
    - dangerous_patterns
    - hardcoded_secrets
```

## 🛠️ Development

```bash
# Setup
pip install -e ".[dev]"

# Run tests
pytest

# Coverage
pytest --cov=src/guardrail --cov-report=html

# Test v2 components
pytest tests/core/test_task_classifier.py
pytest tests/core/test_pattern_analyzer.py
pytest tests/core/test_adaptive_guardrails.py
```

## 📊 Project Status

- **Tests**: 173 passing
- **Coverage**: 75%
- **Agents**: 13 specialized
- **Guardrails**: 3 built-in + dynamic learning
- **v2 Features**: 5 adaptive learning capabilities

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

**Made with ❤️ by developers, for developers**
