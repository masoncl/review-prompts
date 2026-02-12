#!/bin/bash
#
# Setup script for iproute2 review prompts
# Installs skills and slash commands for Claude Code
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPT_DIR="$(dirname "$SCRIPT_DIR")"

# Claude Code directories
CLAUDE_SKILLS_DIR="${HOME}/.claude/skills"
CLAUDE_COMMANDS_DIR="${HOME}/.claude/commands"

echo "Installing iproute2 review prompts..."

# Create directories if they don't exist
mkdir -p "$CLAUDE_SKILLS_DIR"
mkdir -p "$CLAUDE_COMMANDS_DIR"

# Install skill
if [ -f "$PROMPT_DIR/skills/iproute2-skill.md" ]; then
    cp "$PROMPT_DIR/skills/iproute2-skill.md" "$CLAUDE_SKILLS_DIR/"
    echo "  Installed iproute2-skill.md"
fi

# Install slash commands
for cmd in "$PROMPT_DIR/slash-commands"/*.md; do
    if [ -f "$cmd" ]; then
        cp "$cmd" "$CLAUDE_COMMANDS_DIR/"
        echo "  Installed $(basename "$cmd")"
    fi
done

echo ""
echo "Installation complete!"
echo ""
echo "Available commands:"
echo "  /ireview  - Deep patch regression analysis"
echo "  /idebug   - Debug iproute2 issues"
echo "  /iverify  - Verify patch correctness"
echo ""
echo "Context files are in: $PROMPT_DIR"
