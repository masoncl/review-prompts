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
export SKILL_FILE_NAME="SKILL.md"
export COMMANDS_AS_SKILLS=1

agent_post_install() {
    local project_dir="$1"
    shift
    local installed_files=("$@")
    local converter="$project_dir/scripts/claude2agy-agent.py"
    local agents_dir="$(dirname "$SKILL_BASE_DIR")/agents"
    local main_skill="${installed_files[0]:-}"
    local output
    local file

    if [ -n "$main_skill" ] && [ -f "$main_skill" ] && \
       grep -q '^invocation_policy: automatic$' "$main_skill"; then
        sed 's/^invocation_policy: automatic$/disable-slash-command: true/' \
            "$main_skill" > "$main_skill.tmp"
        mv "$main_skill.tmp" "$main_skill"
    fi

    if [ ! -d "$project_dir/agent" ]; then
        return 0
    fi

    if [ ! -x "$converter" ]; then
        echo "Error: Agent converter not found or not executable: $converter" >&2
        return 1
    fi

    output=$("$converter" -o "$agents_dir" "$project_dir")

    echo ""
    echo "Installed custom subagents:"
    printf '%s\n' "$output" | sed 's/^/  /'

    for file in "${installed_files[@]}"; do
        if [ -f "$file" ] && grep -qF "$project_dir/agent/" "$file"; then
            sed "s|$project_dir/agent/|$agents_dir/|g" "$file" > "$file.tmp"
            mv "$file.tmp" "$file"
        fi
    done
}
