# Guardrail Scripts

Shell scripts for installation, configuration, and tool wrapping.

## Available Scripts

### Installation & Setup

#### `install.sh`
Complete installation script with automatic setup.

**Features**:
- Python version verification (3.10+)
- Virtual environment creation
- Dependency installation
- Directory structure setup
- Database initialization
- Shell alias configuration

**Usage**:
```bash
bash scripts/install.sh
```

**Post-installation**:
```bash
# Activate environment
source ~/.guardrail/venv/bin/activate

# Reload shell
source ~/.bashrc  # or ~/.zshrc

# Test
guardrail --version
```

#### `uninstall.sh`
Safe uninstallation with confirmation prompts.

**Features**:
- Interactive confirmation
- Database backup before removal
- Shell alias cleanup
- Configuration directory removal
- Package uninstallation

**Usage**:
```bash
bash scripts/uninstall.sh
```

### Tool Wrapper

#### `guardrail-wrapper.sh`
Transparent wrapper for AI CLI tools.

**Purpose**: Intercept AI tool calls and route through guardrails

**Usage**:
```bash
guardrail-wrapper <tool> <prompt>
```

**Environment Variables**:
- `GUARDRAIL_MODE` - standard (default) or strict
- `GUARDRAIL_AGENT` - auto (default) or specific agent
- `GUARDRAIL_VERBOSE` - true or false (default)

**Example**:
```bash
# Basic usage
guardrail-wrapper claude "Create a login form"

# With environment variables
GUARDRAIL_MODE=strict GUARDRAIL_AGENT=architect guardrail-wrapper claude "Design auth service"
```

## Shell Aliases

After installation, these aliases are available:

### Tool Wrappers
```bash
claude <prompt>   # Wrapped claude
gemini <prompt>   # Wrapped gemini
codex <prompt>    # Wrapped codex
```

### Command Shortcuts
```bash
gr               # Short for guardrail
gr-strict        # Set strict mode
gr-verbose       # Enable verbose output
```

### Helper Functions
```bash
gr-agent <name>  # Set agent
gr-mode <mode>   # Set mode
```

## Configuration

### Environment Variables

Set in shell config (`~/.bashrc` or `~/.zshrc`):

```bash
# Default mode
export GUARDRAIL_MODE="standard"  # or "strict"

# Default agent
export GUARDRAIL_AGENT="auto"  # or specific

# Verbosity
export GUARDRAIL_VERBOSE="false"  # or "true"

# Custom config path (optional)
export GUARDRAIL_CONFIG_PATH="/path/to/config.yaml"
```

### Configuration File

Located at: `~/.guardrail/config.yaml`

Edit directly or use: `guardrail config`

## Workflow Examples

### Development Workflow

```bash
# 1. Install
bash scripts/install.sh

# 2. Configure tools
vim ~/.guardrail/config.yaml

# 3. Use wrapped tools
claude "Create user authentication"
gemini "Design database schema"
codex "Implement API endpoints"
```

### Strict Mode Workflow

```bash
# Enable strict mode globally
export GUARDRAIL_MODE=strict

# Or per-command
GUARDRAIL_MODE=strict claude "Implement payment processing"

# Or using helper
gr-mode strict
claude "Create admin panel"
```

### Agent-Specific Workflow

```bash
# Set architect agent
gr-agent architect

# Use for design tasks
claude "Design microservices architecture"
gemini "Design API contracts"

# Switch to security agent
gr-agent security

# Use for security tasks
claude "Implement JWT authentication"
codex "Add input validation"
```

## Troubleshooting

### Installation Issues

**Python version error**:
```bash
# Check version
python3 --version

# Must be 3.10+
```

**Permission denied**:
```bash
chmod +x scripts/*.sh
bash scripts/install.sh
```

### Wrapper Issues

**Tool not found**:
```bash
# Check tool installation
which claude
which gemini
which codex
```

**Guardrail not found**:
```bash
# Check installation
which guardrail

# If missing, run install again
bash scripts/install.sh
```

### Alias Issues

**Aliases not working**:
```bash
# Reload shell config
source ~/.bashrc  # or ~/.zshrc

# Or restart terminal
```

**Wrong shell detected**:
```bash
# Manually add aliases to your shell config
vim ~/.bashrc  # or ~/.zshrc
```

## Development

### Testing Scripts

```bash
# Test wrapper
bash scripts/guardrail-wrapper.sh claude "test prompt"

# Test with environment
GUARDRAIL_MODE=strict bash scripts/guardrail-wrapper.sh claude "test"
```

### Modifying Scripts

1. Edit script:
   ```bash
   vim scripts/guardrail-wrapper.sh
   ```

2. Make executable:
   ```bash
   chmod +x scripts/guardrail-wrapper.sh
   ```

3. Test changes:
   ```bash
   bash scripts/guardrail-wrapper.sh <tool> <prompt>
   ```

## Security Considerations

### Installation
- Scripts use `set -e` for error handling
- Confirmation prompts for destructive actions
- Database backups before removal

### Wrapper
- Tool availability checks
- Proper quoting of user input
- Environment variable validation

### Best Practices
- Review scripts before execution
- Keep backups of configuration
- Use version control for guardrail files
- Monitor database size

## Support

- **Documentation**: `docs/`
- **Issues**: GitHub Issues
- **Examples**: `docs/PHASE_4_COMPLETION.md`
