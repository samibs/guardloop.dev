#!/bin/bash

# Guardrail wrapper for AI CLI tools
# Usage: guardrail-wrapper <tool> <prompt>

set -e

TOOL=$1
shift
PROMPT="$@"

# Check if tool is installed
if ! command -v "$TOOL" &> /dev/null; then
    echo "❌ Error: $TOOL is not installed"
    exit 1
fi

# Check if guardrail is installed
if ! command -v guardrail &> /dev/null; then
    echo "❌ Error: guardrail is not installed"
    echo "Run: pip install guardrail"
    exit 1
fi

# Get configuration from environment variables
AGENT=${GUARDRAIL_AGENT:-auto}
MODE=${GUARDRAIL_MODE:-standard}
VERBOSE=${GUARDRAIL_VERBOSE:-false}

# Build guardrail command
GUARDRAIL_CMD="guardrail run $TOOL \"$PROMPT\" --agent \"$AGENT\" --mode \"$MODE\""

if [ "$VERBOSE" = "true" ]; then
    GUARDRAIL_CMD="$GUARDRAIL_CMD --verbose"
fi

# Execute with guardrails
eval "$GUARDRAIL_CMD"
