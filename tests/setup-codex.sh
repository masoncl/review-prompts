#!/bin/bash

set -eu

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT

fail() {
    echo "FAIL: $*" >&2
    exit 1
}

assert_valid_skill() {
    local skill_dir="$1"
    local skill_file="$skill_dir/SKILL.md"

    [ -f "$skill_file" ] || fail "missing $skill_file"
    [ "$(sed -n '1p' "$skill_file")" = "---" ] || \
        fail "$skill_file has no YAML frontmatter"
    grep -q '^name: [a-z0-9-][a-z0-9-]*$' "$skill_file" || \
        fail "$skill_file has no valid name"
    grep -q '^description: .\+$' "$skill_file" || \
        fail "$skill_file has no description"
    if grep -q '^invocation_policy:' "$skill_file"; then
        fail "$skill_file contains unsupported invocation_policy"
    fi
}

for project in iproute kernel systemd; do
    project_home="$TEST_ROOT/$project/home"
    codex_home="$TEST_ROOT/$project/codex-home"
    output="$TEST_ROOT/$project/setup.out"
    mkdir -p "$project_home"

    HOME="$project_home" CODEX_HOME="$codex_home" \
        "$REPO_DIR/setup.sh" codex "$project" > "$output"

    project_skill="$codex_home/skills/$project"
    assert_valid_skill "$project_skill"
    grep -Fq "$REPO_DIR/$project" "$project_skill/SKILL.md" || \
        fail "$project skill does not contain the expanded prompt path"

    for source_command in "$REPO_DIR/$project/slash-commands/"*.md; do
        command_name="$(basename "$source_command" .md)"
        command_skill="$codex_home/skills/$command_name"

        assert_valid_skill "$command_skill"
        grep -q '^  allow_implicit_invocation: false$' \
            "$command_skill/agents/openai.yaml" || \
            fail "$command_name is not explicit-only"
        grep -Fq "  \$$command_name" "$output" || \
            fail "setup output does not advertise \$$command_name"
    done

    if [ -d "$codex_home/prompts" ]; then
        fail "Codex custom prompts directory should not be created"
    fi
    if grep -R -n '{{[A-Z_][A-Z_]*}}' "$codex_home/skills"; then
        fail "unexpanded placeholder in installed $project skills"
    fi

    find "$codex_home/skills" -type f -print0 | sort -z | \
        xargs -0 sha256sum > "$TEST_ROOT/$project/before.sha256"
    HOME="$project_home" CODEX_HOME="$codex_home" \
        "$REPO_DIR/setup.sh" codex "$project" > /dev/null
    find "$codex_home/skills" -type f -print0 | sort -z | \
        xargs -0 sha256sum > "$TEST_ROOT/$project/after.sha256"
    cmp "$TEST_ROOT/$project/before.sha256" \
        "$TEST_ROOT/$project/after.sha256" || \
        fail "$project installation is not idempotent"
done

default_home="$TEST_ROOT/default-home"
mkdir -p "$default_home"
env -u CODEX_HOME HOME="$default_home" \
    "$REPO_DIR/setup.sh" codex kernel > /dev/null
assert_valid_skill "$default_home/.codex/skills/kernel"
assert_valid_skill "$default_home/.codex/skills/kreview"

legacy_home="$TEST_ROOT/legacy/home"
legacy_codex_home="$TEST_ROOT/legacy/codex-home"
mkdir -p "$legacy_home"
HOME="$legacy_home" CODEX_HOME="$legacy_codex_home" \
    "$REPO_DIR/kernel/scripts/codex-setup.sh" > /dev/null
assert_valid_skill "$legacy_codex_home/skills/kernel"
assert_valid_skill "$legacy_codex_home/skills/kreview"

claude_home="$TEST_ROOT/claude/home"
mkdir -p "$claude_home"
HOME="$claude_home" "$REPO_DIR/setup.sh" claude kernel > /dev/null
[ -f "$claude_home/.claude/skills/kernel/SKILL.md" ] || \
    fail "Claude project skill was not installed"
[ -f "$claude_home/.claude/commands/kreview.md" ] || \
    fail "Claude slash command was not installed"

echo "Codex setup tests passed"
