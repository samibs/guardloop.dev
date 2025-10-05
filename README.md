# 🛡️ GuardLoop v2 [Experimental]
**Exploring Self-Learning AI Governance**

![Status](https://img.shields.io/badge/status-experimental-orange)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Contributors Welcome](https://img.shields.io/badge/contributors-welcome-brightgreen)

> An experimental system that learns from LLM failures and generates adaptive guardrails.

⚠️ **This is a research project and proof-of-concept.** Core ideas are validated, production deployment requires hardening.

---

## 💡 The Core Idea

**Problem**: LLMs make mistakes. Static rules can't catch evolving failure patterns.

**Hypothesis**: What if AI governance could learn from failures and adapt automatically?

**GuardLoop's Approach**:
1. 📝 **Capture** every AI interaction and outcome
2. 🔍 **Analyze** patterns in failures (missing tests, security issues, etc.)
3. 🧠 **Learn** and generate dynamic guardrails
4. 🛡️ **Prevent** repeated mistakes automatically

---

## ✅ What Works Today

**Core Features (Validated & Working)**:
- ✅ AI interaction logging and pattern detection
- ✅ Dynamic guardrail generation from failures
- ✅ Task classification (skip guardrails for creative work)
- ✅ Basic enforcement with Claude CLI
- ✅ Pre-warm cache for instant guardrail loading (99.9% faster first request)
- ✅ File safety validation and auto-save
- ✅ Conversation history across sessions

**Tested & Reliable**:
- ✅ Claude CLI integration (primary adapter)
- ✅ SQLite failure logging with analytics
- ✅ 3 core agents (architect, coder, tester)
- ✅ Context optimization (pre-warm cache: 0.22ms vs 300ms cold start)

---

## 🚧 What's Theoretical/In Progress

**Features Under Development**:
- 🚧 Full 13-agent orchestration (10 agents are basic stubs)
- 🚧 Multi-tool support (Gemini/Codex adapters incomplete)
- 🚧 Semantic guardrail matching (embeddings not yet implemented)
- 🚧 Advanced compliance validation (GDPR/ISO rules exist but not legally validated)
- 🚧 Performance metrics (some claims are projections, not benchmarked)

**Known Limitations**:
- ⚠️ Only Claude adapter is fully functional
- ⚠️ Agent chain optimization is hardcoded, not dynamic yet
- ⚠️ Large contexts (>10K tokens) may timeout
- ⚠️ File auto-save has edge cases with binary/system files

**See [CRITICAL.md](CRITICAL.md) for complete limitations list.**

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Claude CLI installed (`pip install claude-cli`)
- ⚠️ **Note**: Only Claude is fully supported. Gemini/Codex coming soon.

### Installation

```bash
# Clone the repository
git clone https://github.com/samibs/guardloop.dev.git
cd guardloop.dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Initialize guardrail
guardrail init

# Verify installation
guardrail --version
```

### First Run

```bash
# Test with a simple command
guardrail run claude "create a hello world function"

# Expected: Should work with basic guardrails
# If it fails: Check logs at ~/.guardrail/logs/
```

⚠️ **Troubleshooting**: See [CRITICAL.md](CRITICAL.md) for common issues and workarounds.

---

## 💡 Core Concepts Demonstrated

### 1. Pattern Detection (Working)

After multiple failures with similar issues, GuardLoop learns:

```bash
# After 5 sessions where Claude forgot error handling
$ guardrail analyze --days 7

📊 Pattern Detected:
   - Missing try-catch blocks in async functions
   - Occurrences: 5
   - Confidence: 0.85

🧠 Generated Guardrail:
   "Always wrap async database calls in try-catch blocks"
   Status: trial → validated → enforced
```

### 2. Task Classification (Working)

Intelligently skips guardrails for non-code tasks:

```bash
# Code task - guardrails applied ✅
>>> implement user authentication
📋 Classified: code (confidence: 0.95)
🛡️ Guardrails: Applied

# Creative task - guardrails skipped ⏭️
>>> write a product launch blog post
📋 Classified: creative (confidence: 0.92)
🛡️ Guardrails: Skipped (not needed)
```

### 3. Pre-Warm Cache (Working)

Instant guardrail loading eliminates cold-start latency:

```bash
# Performance Results:
- Pre-warm time: 1.74ms (initialization overhead)
- First request: 0.22ms (cached) vs ~300ms (cold)
- Improvement: 99.9% faster
```

### 4. File Safety (Working)

Validates and auto-saves LLM-generated files:

```bash
>>> create auth service

💾 Auto-saved (safety score: 0.95):
   - auth/jwt_manager.py ✅
   - auth/middleware.py ✅
   - tests/test_auth.py ✅

⚠️ Requires confirmation (system path):
   - /etc/auth.conf (blocked)
```

---

## 🎯 Use Cases

**Good Fit (Early Adopters)**:
- ✅ Experimenting with AI governance concepts
- ✅ Research projects exploring LLM safety
- ✅ Developers comfortable with alpha-quality software
- ✅ Contributors who want to shape the direction
- ✅ Teams learning from LLM failure patterns

**Not Ready For**:
- ❌ Production environments requiring 99.9% uptime
- ❌ Enterprise compliance (legal validation needed)
- ❌ Multi-tool orchestration (only Claude works well)
- ❌ Teams needing commercial support

---

## 📊 Current Project Status

**Tests**: 223 passing (includes core + optimization tests)
**Coverage**: 75%
**Agents**: 3 working (architect, coder, tester) + 10 basic stubs
**Adapters**: 1 complete (Claude), 2 incomplete (Gemini, Codex)
**v2 Features**: 5 adaptive learning capabilities (validated)
**Performance**: Pre-warm cache optimized (99.9% faster)

---

## 🗺️ Roadmap

See [ROADMAP.md](ROADMAP.md) for detailed development plan.

**Next Milestones**:
- **v2.1** (4 weeks): Complete all 13 agents, finish adapters
- **v2.2** (8 weeks): Semantic matching, performance benchmarking
- **v3.0** (Future): Enterprise features, VS Code extension

**Want to influence priorities?** [Open an issue](https://github.com/samibs/guardloop.dev/issues) or [start a discussion](https://github.com/samibs/guardloop.dev/discussions)!

---

## 📖 Documentation

- 📚 [Getting Started](docs/getting-started.md)
- ⚙️ [Configuration Guide](docs/configuration.md)
- 🚨 **[Known Issues & Limitations](CRITICAL.md)** ← Read this first!
- 🗺️ [Roadmap](ROADMAP.md)
- 🤖 [Agent System](docs/phase5-agents.md)
- ⚡ [Performance Optimization](docs/PERFORMANCE_OPTIMIZATION_PREWARM.md)

---

## 🛠️ Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=src/guardrail --cov-report=html

# Test specific components
pytest tests/core/test_task_classifier.py
pytest tests/core/test_pattern_analyzer.py
```

### Project Structure

```
guardloop.dev/
├── src/guardrail/
│   ├── core/           # Core orchestration engine
│   ├── adapters/       # LLM tool adapters (Claude, Gemini, etc.)
│   └── utils/          # Shared utilities
├── tests/              # Test suite (223 tests)
├── docs/               # Documentation
└── ~/.guardrail/       # User configuration & data
    ├── config.yaml
    ├── guardrails/     # Static + dynamic rules
    └── data/           # SQLite database
```

---

## 🤝 Contributing

**We're actively seeking contributors!**

**High-Impact Areas**:
1. 🚧 Complete Gemini/Codex adapters
2. 🚧 Implement remaining 10 agents
3. 🚧 Add semantic matching with embeddings
4. 🧪 Write more tests and edge case coverage
5. 📚 Improve documentation and examples

**How to Contribute**:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Commit with clear messages (`git commit -m 'Add semantic matching'`)
5. Push and open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 🌟 Why This Matters

**The Vision**: AI governance that evolves with your team's actual usage patterns, not just theoretical rules.

**Current State**: Proof-of-concept validating the core hypothesis - yes, AI can learn from failures and improve governance automatically.

**What's Next**: Hardening for production, expanding beyond Claude, validating at scale.

**Star ⭐ if the idea resonates. Contribute if you want to build it together.**

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

**Built by developers, for developers. Shaped by the community.**

*Questions? [Open an issue](https://github.com/samibs/guardloop.dev/issues) | [Join discussions](https://github.com/samibs/guardloop.dev/discussions)*
