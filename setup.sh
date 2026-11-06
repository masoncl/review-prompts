#!/bin/bash
#
# Setup script for AI-assisted code review prompts
#
# Installs skills and slash commands for the specified agent on their respective
# locations.
#
# Usage: ./setup.sh [OPTIONS] <agent> <project>
#
# Each project directory must contain a skill file at:
#   <project>/skills/<project>.md
#
# The skill filename is derived from the directory name (e.g. the "iproute"
# project uses iproute/skills/iproute.md).  Inside that file, use the
# placeholder {{<PROJECT>_REVIEW_PROMPTS_DIR}} (uppercased project name)
# for paths that should resolve to the project directory at install time.
#
# Slash commands live in <project>/slash-commands/*.md and may use
# {{REVIEW_DIR}} as a placeholder for the project directory path.
#
# By default the placeholders resolve to this repository checkout, so the
# installed skills read the prompt files in place.  With --install-prompts,
# the project's prompt files (*.md outside skills/, slash-commands/ and
# scripts/) are also copied into the agent's skill directory next to the
# skill file (e.g. ~/.claude/skills/<project>/), and the placeholders resolve
# to that copy instead, so the checkout is no longer needed at runtime.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    echo "Usage: $0 [OPTIONS] <agent> <project>"
    echo "Setup script for AI-assisted code review prompts."
    echo "Installs skills and slash commands for the specified agent."
    echo ""
    echo "Arguments:"
    echo "  <agent>     Install skill and commands for this code agent"
    echo "              Available agents: claude, codex, opencode, gemini,"
    echo "                                goose, kiro-cli"
    echo "  <project>   Install skills and commands for this project"
    echo "              Available projects: iproute, kernel, nfs-utils, pahole,"
    echo "                                  systemd"
    echo ""
    echo "Options:"
    echo "  -p, --install-prompts  Also copy the project's prompt files into the"
    echo "                         agent's skill directory (alongside the skill"
    echo "                         file) and point the skill and commands at that"
    echo "                         copy instead of this checkout"
    echo "  -h, --help             Show this help message and exit"
}

# Directory that the {{REVIEW_DIR}} / {{<PROJECT>_REVIEW_PROMPTS_DIR}}
# placeholders resolve to: the installed copy with --install-prompts,
# otherwise the project directory in this checkout.
# Args: $1 = project
prompts_ref_dir() {
    local project="$1"
    if [ "${INSTALL_PROMPTS:-0}" = "1" ]; then
        echo "$SKILL_BASE_DIR/$project"
    else
        echo "$SCRIPT_DIR/$project"
    fi
}

# Copy the project's prompt files into the agent's skill directory, keeping
# their relative layout.  Skill templates, slash commands and helper scripts
# are installed separately (or not at all) and are skipped.  No-op unless
# --install-prompts was given.
# Args: $1 = project
install_prompt_files() {
    local project="$1"
    local project_dir="$SCRIPT_DIR/$project"
    local dest_dir prompts_dir_var rel count=0

    [ "${INSTALL_PROMPTS:-0}" = "1" ] || return 0

    dest_dir="$(prompts_ref_dir "$project")"
    prompts_dir_var="${project^^}_REVIEW_PROMPTS_DIR"

    while IFS= read -r -d '' rel; do
        rel="${rel#./}"
        mkdir -p "$dest_dir/$(dirname "$rel")"
        sed -e "s|{{REVIEW_DIR}}|$dest_dir|g" \
            -e "s|{{${prompts_dir_var}}}|$dest_dir|g" \
            "$project_dir/$rel" > "$dest_dir/$rel"
        count=$((count + 1))
    done < <(cd "$project_dir" && find . \
                \( -path ./skills -o -path ./slash-commands -o -path ./scripts \) -prune \
                -o -type f -name '*.md' -print0)

    echo "Installed $count prompt files:"
    echo "  $dest_dir"
    echo ""
}

# Skill and slash commands installation process.
# Args: $1 = project
install_project() {
    local project="$1"
    local src_skill_fn="${project}.md"
    local project_dir
    project_dir="$(prompts_ref_dir "$project")"
    local prompts_dir_var="${project^^}_REVIEW_PROMPTS_DIR"

    echo "--- Installing $project prompts ---"

    # Install skills from the source to the agent specific path
    local agent_skills_dir="$SKILL_BASE_DIR/$project"
    local agent_skill_path="$agent_skills_dir/$SKILL_FILE_NAME"
    local src_skill_path="$SCRIPT_DIR/$project/skills/$src_skill_fn"

    if [ ! -f "$src_skill_path" ]; then
        echo "Error: Source skill file not found: $src_skill_path"
        exit 1
    fi

    mkdir -p "$agent_skills_dir"
    sed "s|{{${prompts_dir_var}}}|$project_dir|g" "$src_skill_path" > "$agent_skill_path"

    echo "Installed skill:"
    echo "  $agent_skill_path"

    # Install slash commands to agent specific path
    local src_commands="$SCRIPT_DIR/$project/slash-commands"

    if [ ! -d "$src_commands" ]; then
        echo "Warning: commands directory not found for $project, skipping"
    else
        mkdir -p "$COMMANDS_DIR"

        echo ""
        echo "Installed slash commands:"

        for cmd_file in "$src_commands"/*.md; do
            if [ -f "$cmd_file" ]; then
                local cmd_name=$(basename "$cmd_file")
                if [ "${COMMANDS_AS_SKILLS:-0}" = "1" ]; then
                    # The agent has no standalone slash-command files; install
                    # each command as a skill (<name>/SKILL.md) so the agent
                    # exposes it as /<name>.  Skills require frontmatter with
                    # a name, so generate it when the source file has none.
                    local cmd_skill_dir="$COMMANDS_DIR/${cmd_name%.md}"
                    mkdir -p "$cmd_skill_dir"
                    {
                        if ! head -n 1 "$cmd_file" | grep -q '^---$'; then
                            printf -- '---\n'
                            printf 'name: %s\n' "${cmd_name%.md}"
                            printf 'description: "/%s slash command from the %s review prompts; load only when invoked explicitly"\n' \
                                "${cmd_name%.md}" "$project"
                            printf -- '---\n\n'
                        fi
                        sed "s|{{REVIEW_DIR}}|$project_dir|g" "$cmd_file"
                    } > "$cmd_skill_dir/$SKILL_FILE_NAME"
                else
                    sed "s|{{REVIEW_DIR}}|$project_dir|g" "$cmd_file" > "$COMMANDS_DIR/$cmd_name"
                fi
                echo "  ${COMMAND_PREFIX:-/}${cmd_name%.md}"
            fi
        done
    fi

    echo ""
}

# Handle args and flags
INSTALL_PROMPTS=0
POSITIONAL=()
while [ "$#" -gt 0 ]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        -p|--install-prompts)
            INSTALL_PROMPTS=1
            ;;
        --)
            shift
            POSITIONAL+=("$@")
            break
            ;;
        -*)
            echo "Error: unknown option '$1'"
            echo ""
            usage
            exit 1
            ;;
        *)
            POSITIONAL+=("$1")
            ;;
    esac
    shift
done

if [ "${#POSITIONAL[@]}" -ne 2 ]; then
    echo "Error: expected 2 arguments (<agent> <project>), got ${#POSITIONAL[@]}"
    echo ""
    usage
    exit 1
fi

AGENT="${POSITIONAL[0]}"
PROJECT="${POSITIONAL[1]}"

AGENT_SCRIPT="$SCRIPT_DIR/agents/${AGENT}.sh"

if [ ! -f "$AGENT_SCRIPT" ]; then
    echo "Error: Setup script for agent '$AGENT' not found at $AGENT_SCRIPT"
    exit 1
fi

PROJECT_DIR="$SCRIPT_DIR/$PROJECT"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project '$PROJECT' not found at $PROJECT_DIR"
    exit 1
fi

# Load agent configuration
source "$AGENT_SCRIPT"

echo "Review prompts directory: $SCRIPT_DIR/$PROJECT"
echo "Setting up for agent: $AGENT"
echo "Setting up for project: $PROJECT"
echo ""

install_prompt_files "$PROJECT"
install_project "$PROJECT"

echo "Setup complete!"
echo ""
echo "The skills load automatically in their respective project trees."
