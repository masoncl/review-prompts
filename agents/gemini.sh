#!/bin/bash
#
# Agent setup script for Gemini CLI.
#
# Sourced by setup.sh to configure where skills and slash commands are
# installed. Exports the install paths and skill filename expected by the
# agent; additional per-agent setup steps (if any) can be added here.

export SKILL_BASE_DIR="$HOME/.gemini/skills"
export COMMANDS_DIR="$HOME/.gemini/commands"
export SKILL_FILE_NAME="SKILL.md"
