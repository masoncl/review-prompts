#!/bin/bash
#
# Agent setup script for opencode-v2.
#
# Sourced by setup.sh to configure where skills and slash commands are
# installed. Exports the install paths and skill filename expected by the
# agent; additional per-agent setup steps (if any) can be added here.
#
# OpenCode V2 discovers user-level skills and slash commands under
# ~/.config/opencode (skills/ and commands/); the legacy singular
# command/ directory is also discovered.

export SKILL_BASE_DIR="$HOME/.config/opencode/skills"
export COMMANDS_DIR="$HOME/.config/opencode/commands"
export SKILL_FILE_NAME="SKILL.md"
