#!/bin/bash
#
# Agent setup script for Cline (https://cline.bot).
#
# Sourced by setup.sh.  Cline models both the project context and each
# slash command as a "skill": a directory under ~/.cline/skills/<name>/
# containing a SKILL.md with YAML frontmatter (name + description).
# Reference: https://docs.cline.bot/customization/skills
#
# This layout does not match the flat slash-command layout the other
# agents use, so we override install_project() here rather than touching
# setup.sh.  setup.sh sources this file before calling install_project,
# so this definition takes precedence.
#
# Author: Breno Leitao <leitao@debian.org>

export SKILL_BASE_DIR="$HOME/.cline/skills"
export COMMANDS_DIR="$HOME/.cline/skills"
export SKILL_FILE_NAME="SKILL.md"

# Write a SKILL.md, expanding {{REVIEW_DIR}} and the project's
# {{<PROJECT>_REVIEW_PROMPTS_DIR}} placeholder, and prepending a minimal
# YAML frontmatter when the source file does not already have one.
# Cline requires `name:` and `description:` to register a skill.
#
# Args: $1 = source markdown file
#       $2 = absolute project dir (for placeholder expansion)
#       $3 = project name (drives {{<PROJECT>_REVIEW_PROMPTS_DIR}})
#       $4 = skill name (must match the containing directory)
#       $5 = destination SKILL.md path
#       $6 = synthesised description used when no frontmatter is present
_cline_write_skill() {
    local src="$1" project_dir="$2" project="$3" name="$4" dst="$5" desc="$6"
    local proj_var="${project^^}_REVIEW_PROMPTS_DIR"
    local first_nonblank
    first_nonblank="$(awk 'NF{print; exit}' "$src")"

    mkdir -p "$(dirname "$dst")"

    if [ "$first_nonblank" = "---" ]; then
        sed -e "s|{{REVIEW_DIR}}|$project_dir|g" \
            -e "s|{{${proj_var}}}|$project_dir|g" \
            "$src" > "$dst"
    else
        {
            printf -- '---\n'
            printf 'name: %s\n' "$name"
            printf 'description: %s\n' "$desc"
            printf -- '---\n\n'
            sed -e "s|{{REVIEW_DIR}}|$project_dir|g" \
                -e "s|{{${proj_var}}}|$project_dir|g" \
                "$src"
        } > "$dst"
    fi
}

# Override the default install_project (defined in setup.sh) with a
# Cline-specific implementation.  Keeps the same contract: $1 is the
# project name, and $SCRIPT_DIR is the repo root.
install_project() {
    local project="$1"
    local project_dir="$SCRIPT_DIR/$project"
    local src_skill="$project_dir/skills/${project}.md"

    echo "--- Installing $project prompts ---"

    if [ ! -f "$src_skill" ]; then
        echo "Error: Source skill file not found: $src_skill"
        exit 1
    fi

    # Project context skill: ~/.cline/skills/<project>/SKILL.md
    local proj_skill="$SKILL_BASE_DIR/$project/$SKILL_FILE_NAME"
    _cline_write_skill "$src_skill" "$project_dir" "$project" "$project" \
        "$proj_skill" "$project review prompts and context"

    echo "Installed skill:"
    echo "  $proj_skill"

    # One Cline skill per slash command:
    # ~/.cline/skills/<cmd>/SKILL.md, invoked as /<cmd> in chat.
    local src_commands="$project_dir/slash-commands"
    if [ ! -d "$src_commands" ]; then
        echo "Warning: commands directory not found for $project, skipping"
        echo ""
        return
    fi

    echo ""
    echo "Installed slash commands:"

    local cmd_file cmd_name
    for cmd_file in "$src_commands"/*.md; do
        [ -f "$cmd_file" ] || continue
        cmd_name="$(basename "$cmd_file" .md)"
        _cline_write_skill "$cmd_file" "$project_dir" "$project" "$cmd_name" \
            "$SKILL_BASE_DIR/$cmd_name/$SKILL_FILE_NAME" \
            "/$cmd_name slash command for the $project project"
        echo "  /$cmd_name"
    done

    echo ""
}
