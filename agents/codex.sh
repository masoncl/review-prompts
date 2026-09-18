#!/bin/bash
#
# Agent setup script for Codex.
#
# Sourced by setup.sh to configure where skills are installed. Codex custom
# prompts are deprecated, so both the project context and the explicit review
# commands are installed as skills.

_CODEX_CONFIG_DIR="${CODEX_HOME:-$HOME/.codex}"

export SKILL_BASE_DIR="$_CODEX_CONFIG_DIR/skills"
export COMMANDS_DIR="$SKILL_BASE_DIR"
export SKILL_FILE_NAME="SKILL.md"
export COMMANDS_AS_SKILLS=1
export COMMAND_PREFIX='$'
export COMMAND_SKILLS_EXPLICIT_ONLY=1
export INSTALL_RESTART_NOTICE="Start a new Codex session to load the installed skills."
