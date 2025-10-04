#!/bin/bash
# Guardrail.dev Installation Script

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="$HOME/.guardrail"
CONFIG_FILE="$INSTALL_DIR/config.yaml"
VENV_DIR="$INSTALL_DIR/venv"

echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Guardrail.dev Installation Script  ║${NC}"
echo -e "${BLUE}║   AI Safety Layer for Code Tools     ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
echo ""

# Check Python version
check_python() {
    echo -e "${YELLOW}→${NC} Checking Python version..."

    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗${NC} Python 3 is not installed. Please install Python 3.10 or higher."
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.10"

    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        echo -e "${RED}✗${NC} Python $PYTHON_VERSION is installed, but Python $REQUIRED_VERSION or higher is required."
        exit 1
    fi

    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION detected"
}

# Create installation directory
create_directories() {
    echo -e "${YELLOW}→${NC} Creating installation directories..."

    mkdir -p "$INSTALL_DIR"/{guardrails/agents,data,logs}

    echo -e "${GREEN}✓${NC} Directories created at $INSTALL_DIR"
}

# Create virtual environment
create_venv() {
    echo -e "${YELLOW}→${NC} Creating Python virtual environment..."

    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"

    echo -e "${GREEN}✓${NC} Virtual environment created"
}

# Install dependencies
install_dependencies() {
    echo -e "${YELLOW}→${NC} Installing Python dependencies..."

    pip install --upgrade pip setuptools wheel
    pip install -e .

    echo -e "${GREEN}✓${NC} Dependencies installed"
}

# Copy guardrail documents
copy_guardrails() {
    echo -e "${YELLOW}→${NC} Copying guardrail documents..."

    if [ -d "guardrails" ]; then
        cp -r guardrails/* "$INSTALL_DIR/guardrails/"
        echo -e "${GREEN}✓${NC} Guardrail documents copied"
    else
        echo -e "${YELLOW}⚠${NC}  Guardrail documents not found in current directory"
        echo -e "   You can add them later to $INSTALL_DIR/guardrails/"
    fi
}

# Create configuration file
create_config() {
    echo -e "${YELLOW}→${NC} Creating configuration file..."

    if [ -f "config.example.yaml" ]; then
        cp config.example.yaml "$CONFIG_FILE"
        echo -e "${GREEN}✓${NC} Configuration file created at $CONFIG_FILE"
    else
        echo -e "${YELLOW}⚠${NC}  Example config not found, creating default config"
        cat > "$CONFIG_FILE" << 'EOF'
version: "1.0"
mode: "standard"
default_agent: "auto"

tools:
  claude:
    cli_path: "claude"
    enabled: true
    timeout: 30
  gemini:
    cli_path: "gemini"
    enabled: true
    timeout: 30
  codex:
    cli_path: "codex"
    enabled: true
    timeout: 30

guardrails:
  base_path: "~/.guardrail/guardrails"
  files:
    - "BPSBS.md"
    - "AI_Guardrails.md"
    - "UX_UI_Guardrails.md"
  agents_path: "~/.guardrail/guardrails/agents"

database:
  path: "~/.guardrail/data/guardrail.db"
  backup_enabled: true
  backup_interval_hours: 24

logging:
  level: "INFO"
  file: "~/.guardrail/logs/guardrail.log"
  max_size_mb: 100
  backup_count: 5

features:
  background_analysis: true
  failure_prediction: false
  prompt_optimization: false
  team_sync: false

team:
  enabled: false
  sync_repo: ""
  sync_interval_hours: 1
  branch: "main"
EOF
        echo -e "${GREEN}✓${NC} Default configuration created"
    fi
}

# Initialize database
init_database() {
    echo -e "${YELLOW}→${NC} Initializing database..."

    python3 -c "
from guardrail.utils.db import DatabaseManager
from guardrail.utils.config import get_config

config = get_config()
db = DatabaseManager(config.database.path)
db.init_db()
print('Database initialized successfully')
"

    echo -e "${GREEN}✓${NC} Database initialized"
}

# Setup shell aliases
setup_aliases() {
    echo -e "${YELLOW}→${NC} Setting up shell aliases..."

    bash scripts/setup_aliases.sh

    echo -e "${GREEN}✓${NC} Aliases configured"
}

# Main installation flow
main() {
    check_python
    create_directories
    create_venv
    install_dependencies
    copy_guardrails
    create_config
    init_database
    setup_aliases

    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   Installation Complete! 🎉           ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  1. Activate the virtual environment:"
    echo -e "     ${YELLOW}source $VENV_DIR/bin/activate${NC}"
    echo ""
    echo -e "  2. Reload your shell configuration:"
    echo -e "     ${YELLOW}source ~/.bashrc${NC}  # or ~/.zshrc for zsh"
    echo ""
    echo -e "  3. Test the installation:"
    echo -e "     ${YELLOW}guardrail --help${NC}"
    echo ""
    echo -e "  4. Configure your AI tools in:"
    echo -e "     ${YELLOW}$CONFIG_FILE${NC}"
    echo ""
    echo -e "${BLUE}Usage examples:${NC}"
    echo -e "  ${YELLOW}guardrail claude 'create a login form'${NC}"
    echo -e "  ${YELLOW}gr gemini --agent architect 'design user service'${NC}"
    echo -e "  ${YELLOW}guardrail codex --strict 'implement JWT auth'${NC}"
    echo ""
    echo -e "${BLUE}Documentation:${NC} https://docs.guardrail.dev"
    echo -e "${BLUE}Issues:${NC} https://github.com/guardrail-dev/guardrail/issues"
    echo ""
}

# Run installation
main
