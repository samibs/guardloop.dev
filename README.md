# 🛡️ Guardrail v2

**Self-Learning AI Governance System**

[![Tests](https://img.shields.io/badge/tests-173%20passing-brightgreen)](https://github.com/samibs/guardrail.dev)
[![Coverage](https://img.shields.io/badge/coverage-75%25-yellow)](https://github.com/samibs/guardrail.dev)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Guardrail is a **self-improving AI governance system** that learns from LLM mistakes, generates dynamic guardrails, and prevents repeated failures. It automatically enforces coding standards, security requirements, and compliance rules across Claude, Gemini, Codex, and other AI tools.

## 🎯 What Makes v2.1 Different?

**The Problem**: Static guardrails miss evolving LLM failure patterns. You repeat the same mistakes. Even with adaptive learning, bloated context and inefficient routing waste tokens and time.

**The Solution**: Guardrail v2.1 combines adaptive learning with intelligent optimization → Smart agent routing (40-70% fewer agents) → Semantic guardrail matching → Dynamic budget management → 60%+ faster with 80%+ less context.

## 🚀 v2.1 Performance Optimization

### Performance Metrics

| Metric | v2.0 (Baseline) | v2.1 (Optimized) | Improvement |
|--------|-----------------|------------------|-------------|
| **Context Size** | 24K tokens (all guardrails) | <5K tokens (smart selection) | **80%+ reduction** |
| **Agent Count** | 13 agents (always) | 1-5 agents (task-based) | **40-70% fewer** |
| **Response Time** | 390s (full chain) | 60-195s (optimized) | **50-85% faster** |
| **Creative Tasks** | Full validation (unnecessary) | Skipped (intelligent bypass) | **95%+ faster** |
| **Semantic Matching** | Keyword only | AI embeddings | **Better relevance** |
| **Budget Management** | Fixed 5K tokens | Dynamic (2K-13K) | **Model-optimized** |

### Smart Selection Examples

**Before v2.1** (All Tasks Get Full Treatment):
```bash
>>> fix typo in README
🛡️ Guardrails: All 3 core + 13 agents
⏱️  Time: 390s (full chain)
📊 Context: 24K tokens
```

**After v2.1** (Intelligent Task Routing):

**Simple Task** - Minimal agents:
```bash
>>> fix typo in README
📋 Task: simple (confidence: 0.95)
🛡️ Guardrails: core/always.md only (354 tokens)
👥 Agents: 1 (coder)
⏱️  Time: 30s
💾 Auto-saved: README.md

✅ 85% faster, 98% less context
```

**Medium Task** - Focused chain:
```bash
>>> implement user authentication
📋 Task: medium (confidence: 0.90)
🛡️ Guardrails: 3 relevant (2.1K tokens)
👥 Agents: 3 (architect → coder → secops)
⏱️  Time: 90s
💾 Auto-saved: 3 files

✅ 77% faster, 91% less context
```

**Critical Task** - Full validation (when needed):
```bash
>>> build OAuth2 authentication system
📋 Task: critical (confidence: 0.95)
🛡️ Guardrails: All relevant (8.5K tokens)
👥 Agents: 9 (full security validation)
⏱️  Time: 270s
💾 Auto-saved: 12 files

✅ 31% faster, 65% less context (full quality)
```

**Creative Task** - Intelligent bypass:
```bash
>>> write product launch blog post
📋 Task: creative (confidence: 0.92)
🛡️ Guardrails: ⏭️  Skipped (not code)
👥 Agents: 0 (direct LLM)
⏱️  Time: 15s

✅ 96% faster (no unnecessary validation)
```

### Semantic Matching in Action

**Old System** (Keyword Matching):
```python
# Prompt: "prevent SQL injection"
# Matches: Only rules with exact keywords "SQL" and "injection"
# Misses: "Use parameterized queries", "Sanitize database inputs"
```

**New System** (Semantic AI):
```python
# Prompt: "prevent SQL injection"
# Matches (by meaning):
# - "Use parameterized queries" (similarity: 0.87)
# - "Sanitize all database inputs" (similarity: 0.76)
# - "Validate user input before queries" (similarity: 0.71)
# - "Never concatenate SQL strings" (similarity: 0.68)
```

### Dynamic Budget Management

**Model-Aware Token Allocation**:

| Model | Simple Task | Medium Task | Critical Task |
|-------|-------------|-------------|---------------|
| claude-opus-4 | 3,000 tokens | 6,000 tokens | 10,000 tokens |
| claude-sonnet-4 | 1,800 tokens | 3,600 tokens | 6,000 tokens |
| gpt-4-turbo | 2,400 tokens | 4,800 tokens | 8,000 tokens |
| gpt-3.5-turbo | 600 tokens | 1,200 tokens | 2,000 tokens |

**Budget Allocation** (Intelligent Distribution):
- **Core** (30%): Universal rules (always applicable)
- **Agents** (40%): Agent-specific instructions
- **Specialized** (20%): Task-specific guardrails
- **Learned** (10%): Dynamic patterns from failures

## ✨ Key Features

### **Version 2.1 (Intelligent Optimization)** 🆕
- ⚡ **Smart Agent Routing** - Task complexity determines agent chain (1-9 agents vs always 13)
- 🎯 **Semantic Guardrail Matching** - AI embeddings find relevant rules by meaning, not just keywords
- 📊 **Dynamic Budget Management** - Model-aware token allocation (2K-13K based on LLM and complexity)
- 🚀 **Performance Optimization** - 60%+ faster with 80%+ less context while maintaining quality

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
- ⚡ **v2.1**: [Performance Optimization](docs/optimization.md)
- 🧠 **v2**: [Adaptive Learning](docs/adaptive-learning.md)
- 🎯 **v2**: [Task Classification](docs/task-classification.md)
- 💾 **v2**: [File Safety System](docs/file-safety.md)

## 🏗️ Architecture

### v2.1: Intelligent Optimization Layer 🆕

```
Request → Complexity Analysis → Smart Routing → Optimized Execution
   ↓              ↓                    ↓              ↓
Classify    Simple/Medium/     1-9 Agents    Context <5K
Task        Critical           (not 13)      (not 24K)
```

**Core v2.1 Components**:

1. **AgentChainOptimizer** - Selects minimal agent chain based on task complexity
2. **SemanticGuardrailMatcher** - Uses AI embeddings for intelligent rule matching
3. **ContextBudgetManager** - Dynamically allocates tokens based on model and complexity
4. **SmartGuardrailSelector** - Combines semantic + budget optimization

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

- **Tests**: 223 passing (50+ new optimization tests)
- **Coverage**: 75%
- **Agents**: 1-13 (smart routing based on complexity)
- **Guardrails**: 3 built-in + dynamic learning + semantic matching
- **v2.1 Features**: 4 optimization capabilities
- **v2 Features**: 5 adaptive learning capabilities
- **Performance**: 60%+ faster, 80%+ less context

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

**Made with ❤️ by developers, for developers**
