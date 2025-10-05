# ⚙️ Guardrail Configuration Guide

Complete configuration reference for Guardrail v2.1 with optimization settings.

## Configuration File Location

```
~/.guardloop/config.yaml
```

The configuration file is created during `guardloop init` and contains all system settings.

## Core Configuration

### Basic Settings

```yaml
# System Configuration
system:
  version: "2.1.0"
  mode: "standard"              # standard | strict
  log_level: "INFO"             # DEBUG | INFO | WARNING | ERROR

# Database Configuration
database:
  path: "~/.guardloop/data/guardloop.db"
  backup_enabled: true
  backup_interval: "24h"

# LLM Tool Configuration
tools:
  claude:
    enabled: true
    cli_path: "claude"
    timeout: 30
    default_model: "claude-sonnet-4"

  gemini:
    enabled: false
    api_key: "${GEMINI_API_KEY}"
    timeout: 30

  openai:
    enabled: false
    api_key: "${OPENAI_API_KEY}"
    timeout: 30
```

## Feature Flags

### v2.1 Optimization Features

```yaml
features:
  # v2.1 Performance Optimization
  v2_1_smart_routing: true         # Agent chain optimization
  v2_1_semantic_matching: true     # AI embedding matching
  v2_1_dynamic_budgets: true       # Model-aware budgets

  # v2.0 Adaptive Learning
  v2_adaptive_learning: true       # Pattern analysis & dynamic guardloops
  v2_task_classification: true     # Code vs creative task detection
  v2_auto_save_files: true         # Auto-save safe file operations
  v2_conversation_history: true    # Multi-turn context
  v2_dynamic_guardloops: true      # Learned rules from DB
```

## v2.1 Optimization Settings

### Smart Agent Routing

```yaml
agent_chain_optimizer:
  # Complexity Detection
  complexity_detection: "auto"     # auto | manual
  min_chain_length: 1             # Minimum agents for simple tasks
  max_chain_length: 13            # Maximum agents for critical tasks

  # Task Complexity Keywords
  complexity_keywords:
    simple:
      - "typo"
      - "fix"
      - "update"
      - "docs"
      - "format"
      - "comment"

    medium:
      - "implement"
      - "function"
      - "bug"
      - "refactor"
      - "test"
      - "endpoint"

    complex:
      - "feature"
      - "module"
      - "system"
      - "design"
      - "architecture"
      - "database"

    critical:
      - "security"
      - "auth"
      - "authentication"
      - "payment"
      - "compliance"
      - "audit"
```

### Task Mappings

Define task → complexity mappings:

```yaml
task_mappings:
  # Simple Tasks (1 agent, 30% budget)
  simple_tasks:
    - "fix_typo"
    - "update_docs"
    - "format_code"
    - "add_comments"
    - "update_readme"

  # Medium Tasks (3 agents, 60% budget)
  medium_tasks:
    - "implement_function"
    - "fix_bug"
    - "refactor_module"
    - "add_tests"
    - "create_endpoint"
    - "update_schema"

  # Complex Tasks (5 agents, 90% budget)
  complex_tasks:
    - "implement_feature"
    - "database_design"
    - "api_design"
    - "performance_optimization"
    - "system_refactor"

  # Critical Tasks (9 agents, 100% budget)
  critical_tasks:
    - "build_auth_system"
    - "implement_payment"
    - "security_audit"
    - "compliance_check"
    - "production_deployment"
```

### Agent Chain Mappings

Customize agent chains per complexity and mode:

```yaml
agent_chains:
  simple:
    standard: ["coder"]
    strict: ["coder", "tester"]

  medium:
    standard: ["architect", "coder", "tester"]
    strict: ["architect", "coder", "tester", "secops"]

  complex:
    standard:
      - "orchestrator"
      - "architect"
      - "coder"
      - "tester"
      - "sre"
    strict:
      - "orchestrator"
      - "architect"
      - "coder"
      - "tester"
      - "secops"
      - "sre"
      - "standards"

  critical:
    standard:
      - "orchestrator"
      - "architect"
      - "coder"
      - "tester"
      - "secops"
      - "sre"
      - "compliance"
      - "auditor"
      - "standards"
    strict:
      - "orchestrator"
      - "architect"
      - "coder"
      - "tester"
      - "secops"
      - "sre"
      - "compliance"
      - "auditor"
      - "standards"
      - "legal"
      - "privacy"
      - "qa"
      - "devops"
```

### Semantic Matching

```yaml
semantic_matcher:
  # Embedding Model
  model: "all-MiniLM-L6-v2"       # Sentence-transformers model

  # Matching Parameters
  threshold: 0.3                   # Minimum similarity score (0.0-1.0)
  top_k: 5                        # Max guardloops to return

  # Performance
  cache_embeddings: true          # Cache for speed (recommended)
  lazy_loading: true              # Load model on first use
  batch_size: 32                  # Batch encoding size

  # Advanced
  normalize_vectors: true         # L2 normalization
  device: "cpu"                   # cpu | cuda | mps
```

### Dynamic Budget Management

```yaml
budget_manager:
  # Model Budgets (tokens)
  model_budgets:
    # Claude Models
    claude-opus-4: 10000
    claude-sonnet-4: 6000
    claude-haiku: 4000

    # OpenAI Models
    gpt-4-turbo: 8000
    gpt-4: 4000
    gpt-3.5-turbo: 2000

    # Google Models
    gemini-ultra: 8000
    gemini-pro: 5000

    # Fallback
    default: 5000

  # Complexity Multipliers
  complexity_multipliers:
    simple: 0.3      # 30% of base budget
    medium: 0.6      # 60% of base budget
    complex: 0.9     # 90% of base budget
    critical: 1.0    # 100% of base budget

  # Allocation Ratios (must sum to 1.0)
  allocation_ratios:
    core: 0.30          # 30% to core guardloops
    agents: 0.40        # 40% to agent instructions
    specialized: 0.20   # 20% to specialized rules
    learned: 0.10       # 10% to learned patterns

  # Mode Adjustments
  strict_mode_multiplier: 1.3     # +30% budget for strict mode

  # Model Name Normalization
  normalize_model_names: true     # Handle variations (GPT-4, gpt4, etc.)
```

## Guardrail Configuration

### Static Guardrails

```yaml
guardloops:
  base_path: "~/.guardloop/guardloops"
  agents_path: "~/.guardloop/guardloops/agents"

  # Core Guardrails (always loaded)
  files:
    - "BPSBS.md"
    - "AI_Guardrails.md"
    - "UXUI_Guardrails.md"

  # Specialized Guardrails (task-specific)
  specialized:
    security:
      - "security/auth_patterns.md"
      - "security/injection_prevention.md"

    performance:
      - "performance/optimization.md"
      - "performance/caching.md"

    compliance:
      - "compliance/gdpr.md"
      - "compliance/iso27001.md"
```

### Dynamic Guardrails

```yaml
dynamic_guardloops:
  # Pattern Analysis
  min_occurrences: 3              # Min failures to create pattern
  confidence_threshold: 0.7       # Min confidence to promote

  # Lifecycle
  trial_period_days: 7            # Trial period before validation
  validation_uses: 5              # Uses needed for validation
  deprecation_threshold: 0.3      # Confidence below which to deprecate

  # Enforcement
  enforce_validated: true         # Apply validated guardloops
  enforce_trial: false            # Don't enforce trial guardloops
```

## File Safety

```yaml
file_executor:
  auto_save_enabled: true

  # Safe Extensions
  safe_extensions:
    - ".py"
    - ".js"
    - ".ts"
    - ".tsx"
    - ".jsx"
    - ".json"
    - ".yaml"
    - ".yml"
    - ".md"
    - ".txt"

  # Safety Score Threshold (0.0-1.0)
  min_safety_score: 0.8

  # Require Confirmation
  require_confirmation_for:
    - system_paths           # /etc/, /usr/, /bin/, etc.
    - dangerous_patterns     # rm, delete, drop, etc.
    - hardcoded_secrets     # API keys, passwords, tokens

  # Blocked Patterns
  blocked_patterns:
    - "rm -rf /"
    - "DROP DATABASE"
    - "DELETE FROM users WHERE 1=1"
```

## Conversation Management

```yaml
conversation:
  # History Settings
  max_turns: 50                   # Max turns per session
  context_window: 10              # Turns to include in context

  # Storage
  persist_history: true           # Save to database
  compress_old_turns: true        # Compress turns > 10

  # Context Management
  max_context_tokens: 15000       # Max tokens in conversation context
  summarize_threshold: 10000      # Summarize when exceeding this
```

## Logging and Monitoring

```yaml
logging:
  # Log Levels
  console_level: "INFO"           # DEBUG | INFO | WARNING | ERROR
  file_level: "DEBUG"

  # Log Files
  log_dir: "~/.guardloop/logs"
  max_file_size: "10MB"
  max_files: 10

  # Performance Logging
  log_performance: true
  log_token_usage: true
  log_agent_chains: true

  # Sensitive Data
  mask_secrets: true              # Mask API keys, passwords, etc.
  log_llm_prompts: false          # Don't log full prompts (privacy)
```

### Metrics Collection

```yaml
metrics:
  enabled: true

  # Collection
  collect_performance: true       # Context size, response time
  collect_optimization: true      # Agent count, budget usage
  collect_quality: true           # Validation results, failures

  # Retention
  retention_days: 90
  aggregate_after_days: 30        # Aggregate old metrics

  # Reporting
  daily_summary: true
  weekly_report: true
```

## Advanced Configuration

### Performance Tuning

```yaml
performance:
  # Caching
  cache_guardloops: true
  cache_embeddings: true
  cache_ttl: 3600                 # Seconds

  # Parallel Execution
  parallel_agents: true
  max_parallel_agents: 3

  # Resource Limits
  max_memory_mb: 1024
  max_execution_time: 300         # Seconds
```

### Integration Settings

```yaml
integrations:
  # Git Integration
  git:
    auto_commit: false
    commit_message_template: "guardloop: {task_type} - {summary}"
    require_tests: true

  # CI/CD Integration
  ci:
    enabled: false
    webhook_url: ""
    notify_on_failure: true

  # IDE Integration
  ide:
    vscode_extension: true
    jetbrains_plugin: false
```

## Environment-Specific Settings

### Development Environment

```yaml
# ~/.guardloop/config.dev.yaml
system:
  mode: "standard"
  log_level: "DEBUG"

features:
  v2_1_smart_routing: true
  v2_1_semantic_matching: true

agent_chain_optimizer:
  min_chain_length: 1              # Allow single agent for dev speed

logging:
  console_level: "DEBUG"
  log_performance: true
```

### Production Environment

```yaml
# ~/.guardloop/config.prod.yaml
system:
  mode: "strict"
  log_level: "WARNING"

features:
  v2_1_smart_routing: true
  v2_1_semantic_matching: true
  v2_1_dynamic_budgets: true

agent_chain_optimizer:
  min_chain_length: 3              # Minimum validation in prod

file_executor:
  require_confirmation_for:
    - system_paths
    - dangerous_patterns
    - hardcoded_secrets
    - production_changes           # Extra safety

logging:
  mask_secrets: true
  log_llm_prompts: false           # Privacy in production
```

## Configuration Validation

### Validate Configuration

```bash
# Check configuration syntax
guardloop config --validate

# Output:
# ✅ Configuration valid
# ✅ All required fields present
# ✅ Feature flags compatible
# ✅ Budget ratios sum to 1.0
# ✅ Agent chains defined for all complexities
```

### View Active Configuration

```bash
# Display current configuration
guardloop config --show

# Display specific section
guardloop config --show budget_manager

# Export configuration
guardloop config --export > config-backup.yaml
```

## Migration Guide

### From v2.0 to v2.1

1. **Backup existing configuration**:
```bash
cp ~/.guardloop/config.yaml ~/.guardloop/config.v2.0.yaml
```

2. **Add v2.1 feature flags**:
```yaml
features:
  v2_1_smart_routing: true
  v2_1_semantic_matching: true
  v2_1_dynamic_budgets: true
```

3. **Add optimization sections**:
```yaml
agent_chain_optimizer:
  complexity_detection: "auto"

semantic_matcher:
  model: "all-MiniLM-L6-v2"
  threshold: 0.3

budget_manager:
  model_budgets:
    claude-sonnet-4: 6000
```

4. **Install dependencies**:
```bash
pip install sentence-transformers
```

5. **Test configuration**:
```bash
guardloop config --validate
guardloop run claude "test optimization" --dry-run
```

## Troubleshooting

### Configuration Issues

**Issue**: Configuration validation fails

**Solution**:
```bash
# Check syntax
guardloop config --validate --verbose

# Reset to defaults
guardloop config --reset

# Restore from backup
cp ~/.guardloop/config.v2.0.yaml ~/.guardloop/config.yaml
```

**Issue**: Feature flags not working

**Solution**:
```yaml
# Ensure proper boolean values
features:
  v2_1_smart_routing: true  # Not "true" or 1
```

**Issue**: Budget allocation errors

**Solution**:
```yaml
# Verify ratios sum to 1.0
allocation_ratios:
  core: 0.30
  agents: 0.40
  specialized: 0.20
  learned: 0.10  # Total: 1.0
```

## Best Practices

1. **Version Control**: Keep `config.yaml` in version control (without secrets)
2. **Environment Variables**: Use `${VAR_NAME}` for sensitive values
3. **Regular Validation**: Run `guardloop config --validate` after changes
4. **Backup**: Backup before major configuration changes
5. **Testing**: Test configuration changes in development first
6. **Monitoring**: Enable metrics to track configuration effectiveness

## See Also

- [Performance Optimization Guide](optimization.md)
- [Agent System Documentation](phase5-agents.md)
- [Adaptive Learning Guide](adaptive-learning.md)
- [Getting Started](getting-started.md)
