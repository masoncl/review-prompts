#!/bin/bash
#
# OpenCode setup for iproute2 development
#
# Installs:
#   - iproute2 skill to ~/.config/opencode/skills/iproute2/SKILL.md
#   - Slash commands to ~/.config/opencode/commands/
#
# The prompts directory is determined from this script's location.

set -e

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The review-prompts directory is the parent of the scripts directory
PROMPTS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Review prompts directory: $PROMPTS_DIR"
echo ""

# --- Install Skill ---

SKILL_DIR="$HOME/.config/opencode/skills/iproute2"
SKILL_FILE="$SKILL_DIR/SKILL.md"
SOURCE_SKILL="$PROMPTS_DIR/skills/iproute2.md"

if [ ! -f "$SOURCE_SKILL" ]; then
    echo "Error: Source skill file not found: $SOURCE_SKILL"
    exit 1
fi

mkdir -p "$SKILL_DIR"

cp "$SOURCE_SKILL" "$SKILL_FILE"

echo "Installed skill:"
echo "  $SKILL_FILE"

# --- Install Slash Commands ---

COMMANDS_DIR="$HOME/.config/opencode/commands"
SLASH_COMMANDS_SRC="$PROMPTS_DIR/slash-commands"

if [ ! -d "$SLASH_COMMANDS_SRC" ]; then
    echo "Warning: slash-commands directory not found, skipping"
else
    mkdir -p "$COMMANDS_DIR"

    echo ""
    echo "Installed slash commands:"

    for cmd_file in "$SLASH_COMMANDS_SRC"/*.md; do
        if [ -f "$cmd_file" ]; then
            cmd_name=$(basename "$cmd_file")
            cp "$cmd_file" "$COMMANDS_DIR/$cmd_name"
            echo "  /${cmd_name%.md}"
        fi
    done
fi

echo ""
echo "Setup complete!"
echo ""
echo "Installed into native OpenCode paths:"
echo "  Skill:    $SKILL_FILE"
echo "  Commands: $COMMANDS_DIR"
echo ""
echo "Available commands:"
echo "  /iproute-review - Review commits for regressions"
echo "  /iproute-debug  - Debug iproute2 crashes and issues"
echo "  /iproute-verify - Verify findings against false positive patterns"
echo ""
echo "The iproute2 skill can now be discovered by OpenCode."
