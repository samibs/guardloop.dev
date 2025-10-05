# ⚡ v2.1 Performance Optimization Guide

## Overview

Guardrail v2.1 introduces intelligent optimization that delivers **60%+ faster execution** with **80%+ less context** while maintaining the same quality standards. This guide explains how the optimization system works and how to configure it for your use case.

## Core Optimization Technologies

### 1. Smart Agent Routing

**Problem**: v2.0 always used the full 13-agent chain, even for simple tasks like fixing typos.

**Solution**: Task complexity analysis determines the minimal effective agent chain.

#### Agent Chain Optimization

| Task Complexity | Example | Agents Used | Time Saved |
|-----------------|---------|-------------|------------|
| **Simple** | Fix typo, update docs | 1 agent (coder) | 85%+ |
| **Medium** | Implement function, fix bug | 3 agents (architect → coder → tester) | 77%+ |
| **Complex** | Build feature, refactor module | 5 agents (+ security, sre) | 60%+ |
| **Critical** | Auth system, payment processing | 9 agents (full validation) | 31%+ |

#### How It Works

```python
from guardloop.agents.chain_optimizer import AgentChainOptimizer

optimizer = AgentChainOptimizer()

# Automatically selects minimal chain
chain = optimizer.select_chain("fix_typo", mode="standard")
# Returns: ["coder"]

chain = optimizer.select_chain("implement_authentication", mode="strict")
# Returns: ["orchestrator", "architect", "coder", "tester",
#           "secops_engineer", "sre_specialist", "standards_oracle"]
```

#### Complexity Detection

The system analyzes:
- **Keywords**: "implement", "build", "fix", "refactor", "security"
- **Scope**: File, module, system-wide changes
- **Risk**: Security implications, data handling, compliance needs

### 2. Semantic Guardrail Matching

**Problem**: v2.0 used keyword matching, missing semantically related guardloops.

**Solution**: AI embeddings (sentence-transformers) match guardloops by meaning.

#### Semantic vs Keyword Matching

**Example Prompt**: "Prevent SQL injection attacks"

**Keyword Matching** (v2.0):
```python
# Only matches exact keywords: "SQL", "injection"
matches = [
    "Prevent SQL injection"  # ✅ Direct match
]
# Misses semantically related rules ❌
```

**Semantic Matching** (v2.1):
```python
# Matches by meaning using AI embeddings
matches = [
    "Prevent SQL injection" (0.95),           # Direct
    "Use parameterized queries" (0.87),       # Related concept
    "Sanitize database inputs" (0.76),        # Security practice
    "Validate all user input" (0.71),         # General principle
    "Never concatenate SQL strings" (0.68)    # Implementation detail
]
```

#### How It Works

```python
from guardloop.core.semantic_matcher import SemanticGuardrailMatcher
from guardloop.core.adaptive_guardloops import AdaptiveGuardrailGenerator

# Enable semantic matching
guardloops = adaptive_gen.get_active_guardloops(
    task_type="code",
    prompt="Implement user authentication with password hashing",
    use_semantic_matching=True,  # 🆕 AI-powered matching
    max_rules=5,
    min_confidence=0.7
)

# Results include similarity scores
for g in guardloops:
    similarity = g.rule_metadata.get('semantic_similarity', 0)
    print(f"{g.rule_text} (similarity: {similarity:.2f})")
```

#### Embedding Model

- **Model**: all-MiniLM-L6-v2 (sentence-transformers)
- **Size**: 80MB (lightweight)
- **Dimensions**: 384
- **Speed**: ~50ms per guardloop
- **Similarity**: Cosine similarity (0.0-1.0)

#### Installation

```bash
pip install sentence-transformers
```

### 3. Dynamic Budget Management

**Problem**: v2.0 used fixed 5K token budget for all models and tasks.

**Solution**: Model-aware, complexity-scaled token allocation.

#### Model-Specific Budgets

| Model | Base Budget | Simple (30%) | Medium (60%) | Critical (100%) |
|-------|-------------|--------------|--------------|-----------------|
| **claude-opus-4** | 10,000 | 3,000 | 6,000 | 10,000 |
| **claude-sonnet-4** | 6,000 | 1,800 | 3,600 | 6,000 |
| **claude-haiku** | 4,000 | 1,200 | 2,400 | 4,000 |
| **gpt-4-turbo** | 8,000 | 2,400 | 4,800 | 8,000 |
| **gpt-4** | 4,000 | 1,200 | 2,400 | 4,000 |
| **gpt-3.5-turbo** | 2,000 | 600 | 1,200 | 2,000 |
| **gemini-ultra** | 8,000 | 2,400 | 4,800 | 8,000 |
| **gemini-pro** | 5,000 | 1,500 | 3,000 | 5,000 |

#### Budget Allocation Strategy

Budget is distributed across 4 categories:

```yaml
core_guardloops: 30%      # Universal rules (always applicable)
agent_instructions: 40%   # Agent-specific guidance
specialized_rules: 20%    # Task-specific guardloops
learned_patterns: 10%     # Dynamic guardloops from failures
```

#### How It Works

```python
from guardloop.core.budget_manager import ContextBudgetManager
from guardloop.core.smart_selector import SmartGuardrailSelector

manager = ContextBudgetManager()
selector = SmartGuardrailSelector(guardloops_path)

# Dynamic budget calculation
selected = selector.select_guardloops(
    task_type="implement_authentication",
    prompt="Build OAuth2 login system",
    model="claude-sonnet-4",        # 🆕 Model-aware
    task_complexity="critical",     # 🆕 Complexity-scaled
    mode="strict"
)

# Budget calculation:
# 6,000 (base) * 1.0 (critical) * 1.3 (strict mode) = 7,800 tokens
```

#### Complexity Multipliers

```python
COMPLEXITY_MULTIPLIERS = {
    "simple": 0.3,    # Typo fixes, doc updates
    "medium": 0.6,    # Function implementation, bug fixes
    "complex": 0.9,   # Feature development, refactoring
    "critical": 1.0   # Security systems, payments
}
```

#### Mode Adjustments

- **Standard Mode**: Base budget
- **Strict Mode**: +30% budget (more validation requires more context)

## Performance Benchmarks

### Context Size Reduction

```python
# Old System (v2.0)
all_guardloops = load_all_guardloops()  # 24K tokens
context = build_context(prompt, all_guardloops)
# Result: 24,000 tokens every time

# New System (v2.1)
smart_guardloops = select_smart(prompt, complexity, model)  # <5K tokens
context = build_context(prompt, smart_guardloops)
# Result: 354 tokens (simple) to 8,500 tokens (critical)
# Average: 80%+ reduction
```

### Agent Chain Optimization

```python
# Old System (v2.0)
agents = get_all_agents()  # Always 13 agents
execute_chain(agents, task)
# Result: 390s execution time

# New System (v2.1)
agents = optimize_chain(task, mode)  # 1-9 agents based on complexity
execute_chain(agents, task)
# Result: 30s (simple) to 270s (critical)
# Average: 60%+ faster
```

### Semantic Matching Performance

```python
# Benchmark results (100 guardloops, 10 searches)
indexing_time = 120ms      # One-time cost
avg_search_time = 45ms     # Per search
cache_hit_rate = 92%       # Embedding reuse
```

### Budget Calculation Speed

```python
# Benchmark results (1000 calculations)
avg_calculation_time = 0.15ms  # Ultra-fast
overhead = negligible          # <1% of total time
```

## Configuration

### Enable v2.1 Optimizations

Add to `~/.guardloop/config.yaml`:

```yaml
# v2.1 Optimization Features
features:
  v2_1_smart_routing: true         # Enable agent chain optimization
  v2_1_semantic_matching: true     # Enable AI embedding matching
  v2_1_dynamic_budgets: true       # Enable model-aware budgets

# Smart Routing Configuration
agent_chain_optimizer:
  complexity_detection: "auto"     # auto | manual
  min_chain_length: 1             # Minimum agents for simple tasks
  max_chain_length: 13            # Maximum agents for critical tasks

  # Task complexity mappings
  complexity_keywords:
    simple: ["typo", "fix", "update", "docs"]
    medium: ["implement", "function", "bug", "refactor"]
    complex: ["feature", "module", "system", "design"]
    critical: ["security", "auth", "payment", "compliance"]

# Semantic Matching Configuration
semantic_matcher:
  model: "all-MiniLM-L6-v2"       # Embedding model
  threshold: 0.3                   # Minimum similarity score
  top_k: 5                        # Max guardloops to return
  cache_embeddings: true          # Cache for performance

# Budget Manager Configuration
budget_manager:
  # Model budgets (tokens)
  model_budgets:
    claude-opus-4: 10000
    claude-sonnet-4: 6000
    gpt-4-turbo: 8000
    gpt-3.5-turbo: 2000

  # Complexity multipliers
  complexity_multipliers:
    simple: 0.3
    medium: 0.6
    complex: 0.9
    critical: 1.0

  # Allocation ratios
  allocation_ratios:
    core: 0.30        # 30% to core guardloops
    agents: 0.40      # 40% to agent instructions
    specialized: 0.20  # 20% to specialized rules
    learned: 0.10     # 10% to learned patterns

  # Mode adjustments
  strict_mode_multiplier: 1.3  # +30% for strict mode
```

### Task Mappings

Define custom task → complexity mappings:

```yaml
task_mappings:
  # Simple tasks (1 agent, 30% budget)
  simple_tasks:
    - "fix_typo"
    - "update_docs"
    - "format_code"
    - "add_comments"

  # Medium tasks (3 agents, 60% budget)
  medium_tasks:
    - "implement_function"
    - "fix_bug"
    - "refactor_module"
    - "add_tests"

  # Complex tasks (5 agents, 90% budget)
  complex_tasks:
    - "implement_feature"
    - "database_design"
    - "api_endpoint"
    - "performance_optimization"

  # Critical tasks (9 agents, 100% budget)
  critical_tasks:
    - "build_auth_system"
    - "implement_payment"
    - "security_audit"
    - "compliance_check"
```

### Agent Chain Mappings

Customize agent chains per task type:

```yaml
agent_chains:
  simple:
    standard: ["coder"]
    strict: ["coder", "tester"]

  medium:
    standard: ["architect", "coder", "tester"]
    strict: ["architect", "coder", "tester", "secops"]

  complex:
    standard: ["orchestrator", "architect", "coder", "tester", "sre"]
    strict: ["orchestrator", "architect", "coder", "tester", "secops", "sre", "standards"]

  critical:
    standard: ["orchestrator", "architect", "coder", "tester", "secops", "sre", "compliance", "auditor", "standards"]
    strict: ["orchestrator", "architect", "coder", "tester", "secops", "sre", "compliance", "auditor", "standards", "legal", "privacy", "qa", "devops"]
```

## Usage Examples

### Example 1: Simple Task Optimization

```bash
$ guardloop run claude "fix typo in README"

📋 Task Classification:
   - Type: simple
   - Confidence: 0.95
   - Complexity: simple

🎯 Smart Routing:
   - Agent Chain: 1 agent (coder)
   - Budget: 600 tokens (gpt-3.5-turbo, simple)
   - Guardrails: core/always.md only (354 tokens)

⚡ Optimization:
   - Context: 354 tokens (98% less than v2.0)
   - Agents: 1 (92% fewer than v2.0)
   - Time: 30s (85% faster than v2.0)

✅ Result:
   - README.md updated
   - Validation: passed
   - Auto-saved: ✓
```

### Example 2: Critical Task with Full Validation

```bash
$ guardloop run claude "implement OAuth2 authentication" --mode strict

📋 Task Classification:
   - Type: critical
   - Confidence: 0.95
   - Complexity: critical

🎯 Smart Routing:
   - Agent Chain: 9 agents (full security validation)
   - Budget: 7,800 tokens (claude-sonnet-4, critical, strict)
   - Guardrails: 12 relevant (semantic matching)

🔍 Semantic Matching:
   - "OAuth2 security best practices" (0.92)
   - "Token validation and refresh" (0.87)
   - "Secure credential storage" (0.84)
   - "PKCE flow implementation" (0.81)
   - "Session management" (0.78)

⚡ Optimization:
   - Context: 7,800 tokens (67% less than v2.0)
   - Agents: 9 (31% fewer than v2.0)
   - Time: 270s (31% faster than v2.0)

✅ Result:
   - 12 files created
   - Security validation: passed
   - Test coverage: 95%
   - Auto-saved: ✓
```

### Example 3: Creative Task Bypass

```bash
$ guardloop run claude "write blog post about new features"

📋 Task Classification:
   - Type: creative
   - Confidence: 0.92
   - Complexity: N/A (skipped)

🎯 Smart Routing:
   - Agent Chain: 0 (direct to LLM)
   - Budget: 0 tokens (no guardloops needed)
   - Guardrails: skipped (not a code task)

⚡ Optimization:
   - Context: 0 tokens (100% reduction)
   - Agents: 0 (100% reduction)
   - Time: 15s (96% faster)

✅ Result:
   - blog_post.md created
   - No validation needed
   - Auto-saved: ✓
```

## Monitoring and Metrics

### Performance Dashboard

```bash
# View optimization metrics
$ guardloop metrics --period 30d

📊 v2.1 Optimization Metrics (Last 30 Days)

Context Size:
  Average: 3,247 tokens (86% reduction from v2.0)
  Simple: 412 tokens
  Medium: 2,134 tokens
  Critical: 8,123 tokens

Agent Usage:
  Average: 2.3 agents (82% fewer than v2.0)
  Simple: 1.0 agents
  Medium: 3.2 agents
  Critical: 8.7 agents

Response Time:
  Average: 87s (78% faster than v2.0)
  Simple: 28s
  Medium: 94s
  Critical: 258s

Semantic Matching:
  Cache hit rate: 94%
  Avg search time: 42ms
  Relevance improvement: +67%

Budget Utilization:
  Model coverage: 8 models
  Budget efficiency: 91%
  Token savings: 23M tokens
```

### Regression Testing

```bash
# Run optimization benchmarks
$ python scripts/benchmark_optimization.py

============================================================
GUARDRAIL OPTIMIZATION BENCHMARKS
============================================================

1. Context Size Reduction
------------------------------------------------------------
  authentication    :  2,847 tokens
  database          :  3,124 tokens
  api               :  2,456 tokens
  creative          :    127 tokens

2. Agent Chain Optimization
------------------------------------------------------------
  fix_typo          : 1 agents, simple   , ~30s
  implement_function: 3 agents, medium   , ~90s
  implement_feature : 5 agents, complex  , ~150s
  build_auth_system : 9 agents, critical , ~270s

3. Semantic Matching Performance
------------------------------------------------------------
  Indexing 50 rules: 124.3ms
  Avg search time:   41.2ms
  Max search time:   67.8ms

4. Budget Allocation Performance
------------------------------------------------------------
  claude-opus-4    : 10,000 tokens (medium complexity)
  claude-sonnet-4  :  6,000 tokens (medium complexity)
  gpt-4-turbo      :  8,000 tokens (medium complexity)

  Avg calculation time: 0.14μs

============================================================
OVERALL OPTIMIZATION METRICS
============================================================
  Context Size      : ✅ PASS
  Agent Efficiency  : ✅ PASS
  Semantic Speed    : ✅ PASS
  Budget Speed      : ✅ PASS

  TOTAL: 4/4 metrics passed
============================================================
```

## Troubleshooting

### Issue: Semantic matching not working

**Symptoms**: Falling back to keyword matching, no similarity scores

**Solution**:
```bash
# Install sentence-transformers
pip install sentence-transformers

# Verify in config
features:
  v2_1_semantic_matching: true
```

### Issue: Agent chain too long for simple tasks

**Symptoms**: Simple tasks using 5+ agents

**Solution**:
```yaml
# Adjust complexity detection
agent_chain_optimizer:
  complexity_keywords:
    simple: ["typo", "fix", "update", "docs", "format"]

# Or use manual override
task_mappings:
  simple_tasks:
    - "your_task_pattern"
```

### Issue: Budget allocation errors

**Symptoms**: "Budget overflow" or "Allocation mismatch" errors

**Solution**:
```yaml
# Verify allocation ratios sum to 1.0
allocation_ratios:
  core: 0.30
  agents: 0.40
  specialized: 0.20
  learned: 0.10  # Total: 1.0

# Check model budgets are sufficient
model_budgets:
  your-model: 5000  # Increase if needed
```

## Migration from v2.0

### Step 1: Enable v2.1 Features

```yaml
# ~/.guardloop/config.yaml
features:
  v2_1_smart_routing: true
  v2_1_semantic_matching: true
  v2_1_dynamic_budgets: true
```

### Step 2: Install Dependencies

```bash
pip install sentence-transformers
```

### Step 3: Test Optimization

```bash
# Run benchmarks
python scripts/benchmark_optimization.py

# Test with simple task
guardloop run claude "fix typo in README"

# Test with critical task
guardloop run claude "implement authentication" --mode strict
```

### Step 4: Monitor Performance

```bash
# Check metrics
guardloop metrics --period 7d

# View optimization savings
guardloop analyze --focus optimization
```

## Best Practices

### 1. Task Classification

- Use descriptive task names that include complexity keywords
- Leverage built-in classification for standard tasks
- Define custom mappings for domain-specific tasks

### 2. Semantic Matching

- Keep guardloops concise and focused
- Use clear, semantic rule descriptions
- Regularly review and refine guardloops based on similarity scores
- Adjust threshold (default: 0.3) based on precision needs

### 3. Budget Management

- Configure model budgets based on your LLM subscriptions
- Adjust complexity multipliers for your workflow
- Monitor budget utilization and adjust allocation ratios
- Use strict mode (+30% budget) only when needed

### 4. Performance Optimization

- Enable all v2.1 features for maximum benefit
- Use regression testing to prevent performance degradation
- Monitor metrics regularly
- Adjust configuration based on actual usage patterns

## Further Reading

- [Phase 2: Smart Agent Routing](PHASE2_SMART_ROUTING.md)
- [Phase 3: Advanced Features](PHASE3_ADVANCED_FEATURES.md)
- [Configuration Guide](configuration.md)
- [Agent System](phase5-agents.md)
