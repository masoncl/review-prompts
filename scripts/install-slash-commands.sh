#!/bin/bash

set -e

# Check arguments
if [ $# -ne 2 ]; then
    echo "Usage: $0 <path-to-review-prompts-directory> <path-to-project>"
    echo "Example: $0 ../review-prompts ~/my-kernel-project"
    exit 1
fi

PROMPTS_DIR="$1"
PROJECT_DIR="$2"

# Convert to absolute paths
PROMPTS_DIR=$(cd "$PROMPTS_DIR" && pwd)
PROJECT_DIR=$(cd "$PROJECT_DIR" && pwd)

# Validate directories exist
if [ ! -d "$PROMPTS_DIR" ]; then
    echo "Error: Prompts directory not found: $PROMPTS_DIR"
    exit 1
fi

if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project directory not found: $PROJECT_DIR"
    exit 1
fi

# Validate required directories exist
if [ ! -d "$PROMPTS_DIR/slash-commands" ]; then
    echo "Error: slash-commands directory not found in $PROMPTS_DIR"
    exit 1
fi

# Validate required slash command templates exist
for cmd in kreview kdebug kverify; do
    if [ ! -f "$PROMPTS_DIR/slash-commands/$cmd.md" ]; then
        echo "Error: slash-commands/$cmd.md not found in $PROMPTS_DIR"
        exit 1
    fi
done

# Create .claude/commands directory
COMMANDS_DIR="$PROJECT_DIR/.claude/commands"
mkdir -p "$COMMANDS_DIR"

echo "Installing slash commands to $COMMANDS_DIR"

# Install each slash command by substituting placeholders
for cmd in kreview kdebug kverify; do
    sed "s|REVIEW_DIR|$PROMPTS_DIR|g" \
        "$PROMPTS_DIR/slash-commands/$cmd.md" > "$COMMANDS_DIR/$cmd.md"
    echo "  ✓ Created /$cmd command"
done

echo ""
echo "Installation complete!"
echo ""
echo "Available commands in $PROJECT_DIR:"
echo "  /kreview - Review the top commit for regressions"
echo "  /kdebug  - Debug current issues using kernel debugging guide"
echo "  /kverify - Verify findings against false positive patterns"
echo ""
echo "Usage:"
echo "  cd $PROJECT_DIR"
echo "  claude -p \"/kreview\""
echo "  # or in interactive mode:"
echo "  claude"
echo "  > /kreview"
