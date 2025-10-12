# 🚨 Known Issues & Limitations

**Before you install, know this:**

This is an experimental research project. Core ideas are validated, but there are significant gaps between the current implementation and the future vision.

---

## ⚠️ Current Limitations

### Features Not Fully Implemented

#### 1. Multi-Tool Support (Incomplete)
- ❌ **Gemini adapter**: Basic structure exists, but it is a non-functional stub.
- ❌ **Codex adapter**: Stub implementation only.
- ✅ **Claude adapter**: Fully functional and tested.

**Impact**: You can only use GuardLoop with the Claude CLI today. Other tools will fail.

**Workaround**: Stick with Claude for now. Other adapters are planned for a future release.

---

#### 2. Agent System (Partially Implemented)
- ✅ **6+ core agents work well**: Architect, Coder, Tester, SecOps, DBA, and Evaluator are functional.
- ⚠️ **7 agents are basic stubs**: Business Analyst, SRE, etc., have basic logic but require further development.
- ⚠️ **Dynamic agent selection**: The agent chain is selected based on task type, but more advanced, context-aware routing is still under development.

**Impact**: You get a robust validation chain for common tasks, but the full 13-agent orchestration is not yet complete.

**Workaround**: Use task-specific prompts to trigger the appropriate agent chains.

---

#### 3. Compliance Validation (Not Legally Validated)
- ⚠️ **GDPR/ISO/SOC 2 checks**: Rules exist but have not been reviewed by legal/compliance experts.
- ⚠️ **Enforcement**: Basic pattern matching, not comprehensive auditing.

**Impact**: Do not rely on GuardLoop for actual compliance. These are development guidelines, not legal validation.

**Workaround**: Use external compliance tools for production. Treat GuardLoop's checks as helpful reminders.

---

#### 4. Performance Metrics (Some Are Projections)
- ✅ **Pre-warm cache**: Validated (99.9% faster, 0.22ms vs 300ms).
- ⚠️ **Context reduction claims**: Based on design, not benchmarked yet.
- ⚠️ **Agent optimization**: Theoretical savings, not measured.

**Impact**: Some performance claims in the README are estimates, not proven at scale.

**Workaround**: Measure your own performance. Report findings to help validate/adjust claims.

---

#### 5. File Auto-Save (Has Edge Cases)
- ✅ **Works for**: `.py`, `.js`, `.ts`, `.json`, `.md`, `.txt` files.
- ⚠️ **Edge cases**: Binary files, system paths, permission issues.
- ❌ **Not handled well**: Concurrent file modifications, large files (>10MB).

**Impact**: File auto-save may fail or require confirmation more often than expected.

**Workaround**: Review `~/.guardloop/logs/` if files aren't saved. Use the `--no-auto-save` flag for manual control.

---

## ✅ What Definitely Works

These features are tested and reliable:

1. ✅ **Claude CLI Integration**: Fully functional and tested.
2. ✅ **Pattern Detection & Learning**: The core loop of learning from failures is implemented.
3. ✅ **Task Classification**: A keyword-based system for selecting guardrails is functional.
4. ✅ **Semantic Guardrail Matching**: A functional semantic search for guardrails using embeddings is implemented.
5. ✅ **Pre-Warm Cache**: Instant guardloop loading is validated and working.
6. ✅ **File Safety Validation**: A robust system for validating and auto-saving files is in place.
7. ✅ **Conversation History**: Multi-turn context is tracked across sessions.
8. ✅ **Core Agent System**: At least 6 agents are functional and provide a solid validation chain.

---

## 🐛 Known Bugs

### High Priority

1. **Large Context Timeout** (Severity: High)
   - **Issue**: Requests with >10K token context may timeout.
   - **Trigger**: Complex prompts + many guardloops + full agent chain.
   - **Workaround**: Use `--mode standard` or reduce guardloop scope.
   - **Status**: Investigating optimization strategies.

2. **Multi-Tool Switching in Interactive Mode** (Severity: Medium)
   - **Issue**: Switching tools mid-conversation may lose context.
   - **Trigger**: `>>> switch gemini` in an interactive session.
   - **Workaround**: Exit and restart with the new tool.
   - **Status**: Known issue, fix planned for a future release.

### Recently Fixed

- ✅ **Test Suite Health**: All 289 tests in the main suite are now passing, providing a stable foundation for future development.

---

## 📋 Missing Features

Features mentioned in the vision but not yet implemented:

- 📋 **MCP Server Support**: Design exists, implementation not started.
- 📋 **VS Code Extension**: Planned for v3.0.
- 📋 **Team Collaboration**: Multi-user support not built.
- 📋 **Web Dashboard**: Analytics UI planned but not started.
- 📋 **Performance Benchmarking**: Automated metrics collection is incomplete.
- 📋 **Dynamic Budget Management**: Token allocation logic exists but is not fully tested.

---

## 🤔 Should You Use This?

### ✅ Yes, if you:
- Want to experiment with AI governance concepts.
- Are comfortable with alpha-quality software.
- Can handle bugs and contribute fixes.
- Want to shape the project's direction.
- Need basic Claude CLI guardrail enforcement.
- Are researching LLM failure patterns.

### ❌ No, if you:
- Need production-ready tooling.
- Require guaranteed uptime or SLAs.
- Can't tolerate breaking changes.
- Need multi-tool support (Gemini, Codex).
- Require enterprise compliance validation.
- Need commercial support.

---

## 🆘 Getting Help

### Before Opening an Issue

1. **Check logs**: `~/.guardloop/logs/guardloop.log`
2. **Verify Python version**: `python --version` (needs 3.10+)
3. **Check Claude CLI**: `claude --version`
4. **Review this file**: Your issue might be a known limitation.

### Reporting Bugs

When opening an issue, include:
```bash
# System info
python --version
claude --version
guardloop --version

# Logs
tail -50 ~/.guardloop/logs/guardloop.log

# Command that failed
guardloop run claude "your command here"

# Expected vs actual behavior
```

### Community Support

- 🐛 **Found a bug?** [Open an issue](https://github.com/samibs/guardloop.dev/issues)
- 💬 **Questions?** [Start a discussion](https://github.com/samibs/guardloop.dev/discussions)
- 🤝 **Want to contribute?** See [CONTRIBUTING.md](CONTRIBUTING.md)
- 📧 **Security issue?** Email security@guardloop.dev (if set up)

---

## 🔄 Update Frequency

This file is updated with every release. Last updated: **v2.2 (Stable)**

Check the [ROADMAP.md](ROADMAP.md) for the planned feature timeline.

---

## 🎯 Expectations

**This is a research project, not a product.**

- Expect bugs and rough edges.
- Features may change or be removed.
- Breaking changes are possible between versions.
- No SLA or support guarantees.
- Community-driven development.

**If you need production-ready AI governance, this isn't it (yet).**

**If you want to help build the future of AI governance, welcome aboard! 🚀**

---

*Last Updated: 2025-10-07*