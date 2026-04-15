#!/bin/bash
#
# Agent setup script for opencode.
#
# Sourced by setup.sh to configure where skills and slash commands are
# installed. Exports the install paths and skill filename expected by the
# agent; additional per-agent setup steps (if any) can be added here.

export SKILL_BASE_DIR="$HOME/.opencode/skills"
export COMMANDS_DIR="$HOME/.opencode/commands"
export SKILL_FILE_NAME="SKILL.md"
