# 🚨 Known Issues & Limitations

**Before you install, know this:**

This is an experimental research project. Core concepts work, but there are significant gaps between current implementation and future vision.

---

## ⚠️ Current Limitations

### Features Not Fully Implemented

#### 1. Multi-Tool Support (Incomplete)
- ❌ **Gemini adapter**: Basic structure exists, but not tested/validated
- ❌ **Codex adapter**: Stub implementation only
- ✅ **Claude adapter**: Fully functional and tested

**Impact**: You can only use Guardrail with Claude CLI today. Other tools will fail.

**Workaround**: Stick with Claude for now. Other adapters coming in v2.1.

---

#### 2. Agent System (Partially Implemented)
- ✅ **3 core agents work well**: Architect, Coder, Tester
- ⚠️ **10 agents are basic stubs**: SecOps, SRE, Compliance, etc.
- ❌ **Dynamic agent selection**: Hardcoded chains, not complexity-based yet

**Impact**: You'll get basic validation, but not the full 13-agent orchestration shown in examples.

**Workaround**: Use `--mode standard` for working agents. Strict mode may trigger unimplemented agents.

---

#### 3. Compliance Validation (Not Legally Validated)
- ⚠️ **GDPR/ISO/SOC 2 checks**: Rules exist but not reviewed by legal/compliance experts
- ⚠️ **Enforcement**: Basic pattern matching, not comprehensive auditing

**Impact**: Don't rely on Guardrail for actual compliance. These are development guidelines, not legal validation.

**Workaround**: Use external compliance tools for production. Treat Guardrail's checks as helpful reminders.

---

#### 4. Performance Metrics (Some Are Projections)
- ✅ **Pre-warm cache**: Validated (99.9% faster, 0.22ms vs 300ms)
- ⚠️ **Context reduction claims**: Based on design, not benchmarked yet
- ⚠️ **Agent optimization**: Theoretical savings, not measured

**Impact**: Some performance claims in README are estimates, not proven at scale.

**Workaround**: Measure your own performance. Report findings to help validate/adjust claims.

---

#### 5. File Auto-Save (Has Edge Cases)
- ✅ **Works for**: `.py`, `.js`, `.ts`, `.json`, `.md`, `.txt` files
- ⚠️ **Edge cases**: Binary files, system paths, permission issues
- ❌ **Not handled well**: Concurrent file modifications, large files (>10MB)

**Impact**: File auto-save may fail or require confirmation more often than expected.

**Workaround**: Review `~/.guardrail/logs/` if files aren't saved. Use `--no-auto-save` flag for manual control.

---

#### 6. Semantic Guardrail Matching (Not Implemented Yet)
- ❌ **Current**: Keyword-based matching only
- 🚧 **Planned**: AI embeddings for semantic similarity

**Impact**: Guardrail selection is less intelligent than described. May miss relevant rules.

**Workaround**: Manually review which guardrails are applied. Add keywords to custom rules.

---

## ✅ What Definitely Works

These features are tested and reliable:

1. ✅ **Claude CLI Integration**
   - Guardrail injection works correctly
   - Conversation history maintained
   - Task classification functional

2. ✅ **Pattern Detection & Learning**
   - SQLite logging of all interactions
   - Basic pattern analysis (>3 occurrences)
   - Dynamic guardrail generation

3. ✅ **Task Classification**
   - Code vs creative detection
   - Confidence scoring
   - Guardrail bypass for creative work

4. ✅ **Pre-Warm Cache**
   - Instant guardrail loading (0.22ms cached vs 300ms cold)
   - 99.9% improvement for first request
   - Minimal initialization overhead (1.74ms)

5. ✅ **File Safety Validation**
   - Safety score calculation
   - Extension-based filtering
   - Dangerous pattern detection

6. ✅ **Conversation History**
   - Multi-turn context across sessions
   - Token-aware summarization
   - Interactive mode support

---

## 🐛 Known Bugs

### High Priority

1. **Large Context Timeout** (Severity: High)
   - **Issue**: Requests with >10K token context may timeout
   - **Trigger**: Complex prompts + many guardrails + full agent chain
   - **Workaround**: Use `--mode standard` or reduce guardrail scope
   - **Status**: Investigating optimization strategies

2. **Multi-Tool Switching in Interactive Mode** (Severity: Medium)
   - **Issue**: Switching tools mid-conversation may lose context
   - **Trigger**: `>>> switch gemini` in interactive session
   - **Workaround**: Exit and restart with new tool
   - **Status**: Known issue, fix planned for v2.1

3. **Agent Chain Optimization** (Severity: Medium)
   - **Issue**: Agent selection is hardcoded, not dynamic
   - **Trigger**: All tasks get same agent chain regardless of complexity
   - **Workaround**: Manually specify agents if needed (not yet exposed in CLI)
   - **Status**: Design complete, implementation in progress

### Medium Priority

4. **Binary File Handling** (Severity: Low)
   - **Issue**: Auto-save may corrupt binary files
   - **Trigger**: LLM generates binary content (images, etc.)
   - **Workaround**: Use `.gitignore` for binary files
   - **Status**: File type detection improvement needed

5. **Concurrent File Access** (Severity: Low)
   - **Issue**: Multiple Guardrail instances may conflict on same files
   - **Trigger**: Running multiple `guardloop run` commands simultaneously
   - **Workaround**: Avoid parallel runs on same project
   - **Status**: File locking mechanism planned

---

## 📋 Missing Features

Features mentioned in vision but not yet implemented:

- 📋 **MCP Server Support**: Design exists, implementation not started
- 📋 **VS Code Extension**: Planned for v3.0
- 📋 **Team Collaboration**: Multi-user support not built
- 📋 **Web Dashboard**: Analytics UI planned but not started
- 📋 **Performance Benchmarking**: Automated metrics collection incomplete
- 📋 **Dynamic Budget Management**: Token allocation logic exists but not tested
- 📋 **Semantic Matching**: Embedding-based matching not implemented

---

## 🤔 Should You Use This?

### ✅ Yes, if you:
- Want to experiment with AI governance concepts
- Are comfortable with alpha-quality software
- Can handle bugs and contribute fixes
- Want to shape the project direction
- Need basic Claude CLI guardrail enforcement
- Are researching LLM failure patterns

### ❌ No, if you:
- Need production-ready tooling
- Require guaranteed uptime or SLAs
- Can't tolerate breaking changes
- Need multi-tool support (Gemini, Codex)
- Require enterprise compliance validation
- Need commercial support

---

## 🆘 Getting Help

### Before Opening an Issue

1. **Check logs**: `~/.guardrail/logs/guardrail.log`
2. **Verify Python version**: `python --version` (needs 3.10+)
3. **Check Claude CLI**: `claude --version`
4. **Review this file**: Your issue might be a known limitation

### Reporting Bugs

When opening an issue, include:

```bash
# System info
python --version
claude --version
guardloop --version

# Logs
tail -50 ~/.guardrail/logs/guardrail.log

# Command that failed
guardloop run claude "your command here"

# Expected vs actual behavior
```

### Community Support

- 🐛 **Found a bug?** [Open an issue](https://github.com/samibs/guardloop.dev/issues)
- 💬 **Questions?** [Start a discussion](https://github.com/samibs/guardloop.dev/discussions)
- 🤝 **Want to contribute?** See [CONTRIBUTING.md](CONTRIBUTING.md)
- 📧 **Security issue?** Email security@guardrail.dev (if set up)

---

## 🔄 Update Frequency

This file is updated with every release. Last updated: **v2.0 (Experimental)**

Check the [ROADMAP.md](ROADMAP.md) for planned fixes and feature timeline.

---

## 🎯 Expectations

**This is a research project, not a product.**

- Expect bugs and rough edges
- Features may change or be removed
- Breaking changes possible between versions
- No SLA or support guarantees
- Community-driven development

**If you need production-ready AI governance, this isn't it (yet).**

**If you want to help build the future of AI governance, welcome aboard! 🚀**

---

*Last Updated: 2025-10-05*
