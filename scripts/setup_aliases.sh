#!/bin/bash
# Shell alias setup for guardrail.dev

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SHELL_RC=""

# Detect shell
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
else
    echo -e "${YELLOW}⚠${NC} Could not detect shell type. Please add aliases manually."
    exit 0
fi

echo -e "${YELLOW}→${NC} Setting up aliases in $SHELL_RC..."

# Backup existing shell config
cp "$SHELL_RC" "${SHELL_RC}.backup.$(date +%Y%m%d_%H%M%S)"

# Remove old guardrail aliases if they exist
sed -i.bak '/# Guardrail.dev aliases/,/# End Guardrail.dev aliases/d' "$SHELL_RC"

# Add new aliases
cat >> "$SHELL_RC" << 'EOF'

# Guardrail.dev aliases
alias gr='guardrail'
alias grc='guardrail claude'
alias grg='guardrail gemini'
alias grx='guardrail codex'
alias gr-strict='guardrail --mode strict'
alias gr-stats='guardrail stats'
alias gr-config='guardrail config'
alias gr-logs='guardrail logs'

# Agent-specific aliases
alias gr-arch='guardrail --agent architect'
alias gr-code='guardrail --agent coder'
alias gr-test='guardrail --agent tester'
alias gr-review='guardrail --agent reviewer'
alias gr-sec='guardrail --agent security'
alias gr-perf='guardrail --agent performance'
alias gr-ux='guardrail --agent ux'
alias gr-docs='guardrail --agent docs'
alias gr-debug='guardrail --agent debug'
# End Guardrail.dev aliases
EOF

echo -e "${GREEN}✓${NC} Aliases added successfully!"
echo ""
echo -e "${YELLOW}Available aliases:${NC}"
echo -e "  ${GREEN}gr${NC}              - Short for 'guardrail'"
echo -e "  ${GREEN}grc${NC}             - guardrail claude"
echo -e "  ${GREEN}grg${NC}             - guardrail gemini"
echo -e "  ${GREEN}grx${NC}             - guardrail codex"
echo -e "  ${GREEN}gr-strict${NC}       - Run in strict mode"
echo -e "  ${GREEN}gr-stats${NC}        - Show statistics"
echo -e "  ${GREEN}gr-config${NC}       - Manage configuration"
echo -e "  ${GREEN}gr-logs${NC}         - View logs"
echo ""
echo -e "${YELLOW}Agent-specific:${NC}"
echo -e "  ${GREEN}gr-arch${NC}         - Architect agent"
echo -e "  ${GREEN}gr-code${NC}         - Coder agent"
echo -e "  ${GREEN}gr-test${NC}         - Tester agent"
echo -e "  ${GREEN}gr-review${NC}       - Reviewer agent"
echo -e "  ${GREEN}gr-sec${NC}          - Security agent"
echo -e "  ${GREEN}gr-perf${NC}         - Performance agent"
echo -e "  ${GREEN}gr-ux${NC}           - UX agent"
echo -e "  ${GREEN}gr-docs${NC}         - Documentation agent"
echo -e "  ${GREEN}gr-debug${NC}        - Debug agent"
echo ""
echo -e "${YELLOW}Remember to reload your shell:${NC}"
echo -e "  source $SHELL_RC"
