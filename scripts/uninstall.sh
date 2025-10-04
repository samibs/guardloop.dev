#!/bin/bash

set -e

echo "🗑️  Uninstalling Guardrail..."
echo ""

# Confirmation
read -p "Are you sure you want to uninstall Guardrail? This will remove all data. (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Remove shell aliases
echo "🔧 Removing shell aliases..."

SHELL_RC=""
if [ -n "$BASH_VERSION" ]; then
    SHELL_RC="${HOME}/.bashrc"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="${HOME}/.zshrc"
fi

if [ -n "$SHELL_RC" ] && [ -f "$SHELL_RC" ]; then
    # Remove Guardrail aliases section
    sed -i.bak '/# Guardrail aliases/,/^$/d' "$SHELL_RC"
    echo "   ✅ Aliases removed from $SHELL_RC"
fi

# Remove configuration directory
echo "📁 Removing configuration directory..."
read -p "Remove ~/.guardrail directory? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Backup database before removal
    if [ -f ~/.guardrail/data/guardrail.db ]; then
        BACKUP_FILE=~/guardrail_backup_$(date +%Y%m%d_%H%M%S).db
        cp ~/.guardrail/data/guardrail.db "$BACKUP_FILE"
        echo "   💾 Database backed up to: $BACKUP_FILE"
    fi

    rm -rf ~/.guardrail
    echo "   ✅ Configuration directory removed"
else
    echo "   ⏭️  Keeping configuration directory"
fi

# Uninstall Python package
echo "📦 Uninstalling Python package..."
pip uninstall -y guardrail || echo "   ⚠️  Package not installed via pip"

echo ""
echo "✅ Uninstallation complete!"
echo ""

if [ -n "$SHELL_RC" ]; then
    echo "📋 Note: Restart your terminal or run:"
    echo "   source $SHELL_RC"
fi

echo ""
