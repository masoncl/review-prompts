#!/bin/bash
#
# Agent setup script for agy.
#
# Sourced by setup.sh to configure where skills and slash commands are
# installed. Exports the install paths and skill filename expected by the
# agent, and provides agent_post_install() to convert and install custom
# subagents.

export SKILL_BASE_DIR="$HOME/.gemini/config/skills"
export COMMANDS_DIR="$HOME/.gemini/config/skills"
export AGENTS_DIR="$HOME/.gemini/config/agents"
export SKILL_FILE_NAME="SKILL.md"
export COMMANDS_AS_SKILLS=1

agent_post_install() {
    local project_dir="$1"
    local converter="$project_dir/scripts/claude2agy-agent.py"

    if [ -d "$SKILL_BASE_DIR" ]; then
        find "$SKILL_BASE_DIR" -name "$SKILL_FILE_NAME" -exec \
            sed -i "s|$project_dir/agent/|$AGENTS_DIR/|g" {} +
    fi

    if [ -d "$project_dir/agent" ] && [ -x "$converter" ]; then
        echo ""
        echo "Installed custom subagents:"
        "$converter" -o "$AGENTS_DIR" "$project_dir/agent" | sed 's/^/  /'
    fi
}
