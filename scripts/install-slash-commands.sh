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

# Validate required files exist
if [ ! -f "$PROMPTS_DIR/review-core.md" ]; then
    echo "Error: review-core.md not found in $PROMPTS_DIR"
    exit 1
fi

if [ ! -f "$PROMPTS_DIR/debugging.md" ]; then
    echo "Error: debugging.md not found in $PROMPTS_DIR"
    exit 1
fi

if [ ! -f "$PROMPTS_DIR/false-positive-guide.md" ]; then
    echo "Error: false-positive-guide.md not found in $PROMPTS_DIR"
    exit 1
fi

# Create .claude/commands directory
COMMANDS_DIR="$PROJECT_DIR/.claude/commands"
mkdir -p "$COMMANDS_DIR"

echo "Installing slash commands to $COMMANDS_DIR"

# Create /review command
cat > "$COMMANDS_DIR/review.md" << EOF
Using the prompt $PROMPTS_DIR/review-core.md and the review prompt directory $PROMPTS_DIR, review the top commit.
EOF
echo "  ✓ Created /review command"

# Create /debug command
cat > "$COMMANDS_DIR/debug.md" << EOF
Using the debugging guide at $PROMPTS_DIR/debugging.md and the review prompt directory $PROMPTS_DIR, help analyze and debug the current issue.
EOF
echo "  ✓ Created /debug command"

# Create /verify command
cat > "$COMMANDS_DIR/verify.md" << EOF
Using the false positive guide at $PROMPTS_DIR/false-positive-guide.md, verify the current regression analysis and eliminate any false positives.

Apply all verification steps systematically to ensure the findings are accurate.
EOF
echo "  ✓ Created /verify command"

echo ""
echo "Installation complete!"
echo ""
echo "Available commands in $PROJECT_DIR:"
echo "  /review - Review the top commit for regressions"
echo "  /debug  - Debug current issues using kernel debugging guide"
echo "  /verify - Verify findings against false positive patterns"
echo ""
echo "Usage:"
echo "  cd $PROJECT_DIR"
echo "  claude -p \"/review\""
echo "  # or in interactive mode:"
echo "  claude"
echo "  > /review"
